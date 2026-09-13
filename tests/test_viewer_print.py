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


def test_the_plate_caption_names_the_machine_and_picks_without_slicing():
    """Unnamed caption is the picker. Print-time receive must not estimate() unless
    that card's pick set slicing."""
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    assert 'id="platecap"' in viewer
    assert "function plateCaption" in viewer
    assert "type: 'printer', profile: event.target.value" in viewer
    socket = viewer.split("ws.onmessage =", 1)[1]
    assert "const finishSlice = pendingPrinterSlice || slicing" in socket
    assert "if (finishSlice) estimate()" in socket
    assert socket.index("const finishSlice = pendingPrinterSlice || slicing") < socket.index("slicing = false")
    plate_click = viewer[viewer.index("platecap.onclick") : viewer.index("function plateDismiss")]
    assert "slicing = true" not in plate_click
    assert "optimisticPrinterChange(profile, selectedProfileSource(profile))" in plate_click
    assert "sock.send(JSON.stringify({ type: 'printer', profile }))" in plate_click
    assert "use_workshop: true" in plate_click
    assert "invalidatePrinterState()" in plate_click
    # Every rebuild carries the printer; a rewrite mid-pick would close the open list.
    caption = viewer[viewer.index("function plateCaption") : viewer.index("cap.innerHTML")]
    assert "cap.classList.contains('open')" in caption


def test_the_plate_picker_distinguishes_workshop_and_project_profiles():
    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    caption = viewer[viewer.index("function plateCaption") : viewer.index("// Findings get a pin")]
    assert "default printer" in caption
    assert "project override" in caption
    assert "use default printer" in caption
    assert "data-make-default" in caption
    assert 'aria-pressed="${n === workshopProfile}"' in caption
    assert "n === workshopProfile ? '★' : '☆'" in caption
    assert "make_workshop: true" in viewer
    assert "printer.source === 'printer.toml'" in caption
    assert "#platecap.open { z-index: 2; }" in viewer
    assert "#platecap:has(.open)" not in viewer
    assert "#platecap > .pick::before" in viewer
    assert "#platecap.open > .pick::before" in viewer
    assert "content: '▶'" in viewer
    assert "content: '▲'" in viewer
    assert 'aria-haspopup="true"' in caption
    assert 'aria-expanded="false"' in caption
    plate_click = viewer[viewer.index("platecap.onclick") : viewer.index("function plateDismiss")]
    dismiss = viewer[viewer.index("function plateDismiss") : viewer.index("addEventListener('click', plateDismiss)")]
    assert "setAttribute('aria-expanded', String(platecap.classList.contains('open')))" in plate_click
    assert "setAttribute('aria-expanded', 'false')" in dismiss


def test_the_plate_picker_can_add_a_custom_printer_without_parsing_its_id():
    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    caption = viewer[viewer.index("function plateCaption") : viewer.index("// Findings get a pin")]
    click = viewer[viewer.index("platecap.onclick") : viewer.index("function plateDismiss")]
    assert 'class="addprinter"' in caption
    assert 'class="printerform"' in caption
    assert all(f'name="{field}"' in caption for field in ("brand", "model", "bed_x", "bed_y", "bed_z"))
    assert "plateProfileDetails" in caption
    assert "escapeText" in caption
    assert "Object.fromEntries(new FormData(form))" in click
    assert 'name="make_default" type="checkbox"' in caption
    assert "form.elements.make_default.checked" in click
    assert "make_workshop: makeDefault" in click
    assert "customPrinterPending" in viewer
    assert "preferred_slicer" not in caption
    assert 'class="cancelprinter"' in caption
    assert "form.reset()" in click
    assert "platecap.classList.remove('adding')" in click
    dismiss = viewer[viewer.index("function plateDismiss") : viewer.index("addEventListener('click', plateDismiss)")]
    assert "cap.classList.remove('open', 'adding')" in dismiss
    assert "form?.reset()" in dismiss


def test_custom_printers_can_be_deleted_and_profile_ids_are_attribute_escaped():
    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    caption = viewer[viewer.index("function plateCaption") : viewer.index("// Findings get a pin")]
    click = viewer[viewer.index("platecap.onclick") : viewer.index("function plateDismiss")]
    assert 'data-delete-profile="${escapeAttribute(n)}"' in caption
    assert 'value="${escapeAttribute(n)}"' in caption
    assert "delete_custom: true" in click
    assert "confirm(`Delete ${label}?`)" in click
    assert "printerActionPending = true" in click
    assert "platecap.classList.remove('open')" in click
    # A deletion acknowledgement carries a fresh registry. It must replace the
    # menu even if an open-menu state survived long enough to receive it.
    update = viewer[viewer.index("function plateCaption") : viewer.index("cap.innerHTML")]
    assert "&& !printerActionPending" in update


def test_switching_printers_invalidates_estimates_and_inflight_slices():
    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    invalidation = viewer[viewer.index("function invalidatePrinterState") : viewer.index("function printRow")]
    assert "printed.clear()" in invalidation
    assert "printerRevision += 1" in invalidation
    estimate = viewer[viewer.index("async function estimate") : viewer.index("// One listener on the card")]
    assert "const revision = printerRevision" in estimate
    assert estimate.index("if (revision !== printerRevision) return") < estimate.index("if (said.kind)")
    caught = estimate[estimate.index("} catch (e)") : estimate.index("} finally")]
    assert "if (revision === printerRevision)" in caught
    finished = estimate[estimate.index("} finally") :]
    assert "if (revision === printerRevision)" in finished
    assert "slicing = false" in invalidation
    socket = viewer.split("ws.onmessage =", 1)[1]
    assert "const finishSlice = pendingPrinterSlice || slicing" in socket


def test_plate_picker_updates_the_profile_and_bed_before_the_server_acknowledges():
    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    update = viewer[viewer.index("function printerUpdate") : viewer.index("// Findings get a pin")]
    click = viewer[viewer.index("platecap.onclick") : viewer.index("function plateDismiss")]
    socket = viewer.split("ws.onmessage =", 1)[1]

    assert "function optimisticPrinterChange" in update
    assert "bedUpdate(details.bed)" in update
    assert "plateCaption({ profile, source }, bedXY, undefined, workshop)" in update
    assert "optimisticPrinterChange(profile, selectedProfileSource(profile))" in click
    assert "optimisticPrinterChange(workshopProfile, 'global')" in click
    assert "optimisticPrinterChange(makeDefault.dataset.makeDefault, 'global', makeDefault.dataset.makeDefault)" in click
    assert "make_workshop: true, select: true" in click
    assert "msg.type === 'printer_state' && printerChangePending" in update
    assert "msg.error && printerChangePending" in socket
    assert "rollbackPrinterChange()" in socket
    assert "#platecap.pending > .pick::before" in viewer


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
