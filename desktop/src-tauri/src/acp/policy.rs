//! Every permission request is answered yes on the user's behalf. The guard
//! is not here: the adapter process runs under the OS sandbox (sandbox.rs),
//! which lets the agent read anything and write only inside the project and
//! the app's own directories. A dialog would ask the user to approve what
//! the kernel already enforces, and a dialog per step teaches the user to
//! click allow without reading. This module's parser-based predecessor
//! proved the alternative: approximating bash's lexer misses shapes forever,
//! and every miss was a dialog.
//!
//! The answer is always the adapter's own allow-once option, so nothing is
//! remembered on the agent side. A request offering no allow-once option
//! still falls to a dialog, which keeps the UI honest about anything novel.

use std::path::Path;

use agent_client_protocol::schema::v1::{
    PermissionOptionId, PermissionOptionKind, RequestPermissionRequest,
};

pub(super) fn auto_allow(request: &RequestPermissionRequest) -> Option<PermissionOptionId> {
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

    #[test]
    fn every_request_is_allowed_because_the_sandbox_is_the_guard() {
        // Shapes the old parser dialogued on, plus ones it never allowed:
        // all yes now, and the sandbox test in sandbox.rs proves the writes
        // among them would fail at the kernel instead.
        for tool_call in [
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
        ] {
            let req = request(tool_call);
            assert_eq!(
                auto_allow(&req).map(|id| id.to_string()),
                Some("allow-once".into())
            );
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
        assert!(auto_allow(&req).is_none());
    }
}
