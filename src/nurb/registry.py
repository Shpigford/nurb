"""Part registration. A part is a function; its defaults are its parameters."""

import inspect
import re
from dataclasses import dataclass


@dataclass
class PartDef:
    fn: callable
    name: str
    params: dict
    accepts_draft: bool
    docs: dict


def declared(fn):
    """The parameters a function declares, and whether it takes `draft`.

    This is the one place the keyword-defaults-are-parameters convention is read
    off a signature. Parts and assemblies both register through it, so they cannot
    drift on what counts as a parameter.
    """
    params = {}
    accepts_draft = False
    for name, p in inspect.signature(fn).parameters.items():
        if name == "draft":
            accepts_draft = True
            continue
        params[name] = None if p.default is inspect.Parameter.empty else p.default
    return params, accepts_draft


def param_docs(fn, params):
    """Per-parameter descriptions, read off `name: text` lines in the docstring.

    The docstring is where a function explains itself, so a slider's tooltip comes
    from the same place a reader would look rather than from a parallel declaration.
    Any line opening with a declared parameter's name and a colon counts, which is
    what a Google-style Args section already writes; a deeper-indented line continues
    the one above it, and a name the signature does not declare is ordinary prose.
    """
    docs = {}
    current, indent = None, 0
    for line in (inspect.getdoc(fn) or "").splitlines():
        m = re.match(r"(\s*)([A-Za-z_]\w*)\s*(?:\([^)]*\))?:\s+(\S.*)", line)
        if m and m.group(2) in params:
            current, indent = m.group(2), len(m.group(1))
            docs[current] = m.group(3).strip()
        elif current and line.strip() and len(line) - len(line.lstrip()) > indent:
            docs[current] += " " + line.strip()
        else:
            current = None
    return docs


def part(fn):
    """Mark a function as a part.

    The function's keyword defaults are the part's parameters. That's the whole
    convention -- one declaration feeds the CLI, the viewer sliders and the tests.

    An optional `draft` parameter is passed by the runtime, not the caller: when
    it's True the part should skip its polish pass (chamfers, fillets) so the
    live rebuild stays fast.
    """
    params, accepts_draft = declared(fn)
    fn._nurb = PartDef(
        fn=fn,
        name=fn.__name__,
        params=params,
        accepts_draft=accepts_draft,
        docs=param_docs(fn, params),
    )
    return fn
