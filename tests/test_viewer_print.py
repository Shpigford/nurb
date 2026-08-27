"""The print-time printer picker: a question you can leave, not a native <select>.

Source reads cannot execute JS. Substring presence of id="printerpick" and the send
line already pass with a dead onchange, so these pin the click path, the dropped id
guard, and dismiss that only fires when the list was already closed.
"""

from nurb import server as server_mod


def _print_js():
    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    start = viewer.index("// ---- print time ----")
    end = viewer.index("// On by default, matching the server")
    return viewer[start:end]


def test_the_printer_picker_is_not_a_native_select():
    """A native <select> in the desktop WKWebView opens an OS menu that does not
    dismiss once it has been opened."""
    js = _print_js()
    css = server_mod.VIEWER.read_text(encoding="utf-8")
    assert 'id="printerpick"' in js
    assert "<select" not in js
    assert 'id="printerpick"' in css
    assert "#print select" not in css
    assert "#print:has(.open)" in css


def test_picking_a_printer_is_a_click_not_a_change():
    """Option buttons never fire change, and id=\"printerpick\" is the wrapper, so the
    old onchange + target.id guard would swallow every pick."""
    js = _print_js()
    assert "printbox.onchange" not in js
    assert "printbox.onclick" in js
    assert "event.target.id" not in js
    assert "type: 'printer', profile: event.target.value" in js
    assert "event.target.closest('#printerpick [value]')" in js
    assert "event.stopPropagation()" in js
    onclick = js[js.index("printbox.onclick") : js.index("function printDismiss")]
    assert "addEventListener" not in onclick


def test_dismiss_reads_open_before_it_mutates_and_only_then_clears_the_question():
    """Closing the list and dismissing the question are two events. Snapshot open
    first, or the same Escape or canvas click does both."""
    js = _print_js()
    dismiss = js[js.index("function printDismiss") :]
    open_at = dismiss.index("const open =")
    close_at = dismiss.index("classList.remove('open')")
    clear_at = dismiss.index("printAsk = null")
    assert open_at < close_at < clear_at
    assert "if (open)" in dismiss
    assert "addEventListener('click', printDismiss)" in js
    row = js[js.index("function printRow") : js.index("function printAnswer")]
    assert "addEventListener" not in row
    assert "if (sig === printSig) return" in row
    assert "printbox.innerHTML = html" in row
