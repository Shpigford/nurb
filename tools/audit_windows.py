from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
SKIP_PARTS = {'.git', 'node_modules', 'target', '__pycache__', '.venv', 'dist', 'binaries', 'resources'}
# evals/ is its own uv project with its own suite and its own Unix-only
# subprocess handling; it is not part of the Windows desktop or CLI surface.
SKIP_TOP_DIRS = {'evals'}
TEXT_EXTENSIONS = {'.py', '.ts', '.tsx', '.rs', '.json', '.sh', '.toml', '.md', '.ps1'}

PATTERNS = {
    'hard-coded Unix executable': re.compile(r'(?<![\w"\'])/(?:usr/)?bin/(?:sh|bash|zsh|curl|tar|open)(?![\w-])'),
    'Unix-only launcher': re.compile(r'#!/bin/(?:sh|bash|zsh)|\.command$|\.dmg$|\.app/'),
    'Unix path assumption': re.compile(r'(?<![\w])~/\.(?:config|cache|local)|(?<![\w])/tmp/'),
    'shell=True': re.compile(r'\bshell\s*=\s*True\b'),
    'os.system': re.compile(r'\bos\.system\s*\('),
    'Unix signal API': re.compile(r'killpg|std::os::unix::process|PermissionsExt'),
}

# A finding inside one of these contexts is the cross-platform code doing its
# job (a deliberate platform split) or a test exercising one side of it, not an
# accidental Unix assumption.
INTENTIONAL_CONTEXT = re.compile(
    r'os\.name|sys\.platform|platform\.system|target_os'
    r'|cfg\s*!\s*\(\s*(?:unix|windows|not\s*\(\s*windows\s*\))'
    r'|cfg\s*\(\s*(?:unix|windows|not\s*\(\s*windows\s*\))'
    r'|#\[cfg\s*\(\s*(?:test|unix|windows|not\s*\(\s*windows\s*\))\s*\)\]'
    r'|mod\s+tests\b|#\[test\]',
)

TEST_PATH = re.compile(r'(^|[\\/])tests([\\/]|$)|test_[^\\/]*\.py$|[^\\/]*_test\.rs$|\.test\.tsx?$')

BACKWARD_WINDOW = 60


def iter_source():
    for path in ROOT.rglob('*'):
        if not path.is_file() or path == SELF:
            continue
        parts = path.relative_to(ROOT).parts
        if any(part in SKIP_PARTS for part in parts):
            continue
        if parts and parts[0] in SKIP_TOP_DIRS:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield path


def is_test_path(path: Path) -> bool:
    return bool(TEST_PATH.search(path.relative_to(ROOT).as_posix()))


def _unbalanced_triple(line: str) -> bool:
    return line.count('"""') % 2 == 1 or line.count("'''") % 2 == 1


def findings_in_file(path: Path):
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    except OSError:
        return []

    ext = path.suffix.lower()
    test_path = is_test_path(path)
    in_py_doc = False
    in_block_comment = False
    findings = []

    for index, line in enumerate(lines):
        stripped = line.lstrip()

        # Track documentation and skip it: a docstring or comment describing
        # Unix behavior is documentation, not an incompatibility.
        documentation = False
        if ext == '.py':
            if in_py_doc:
                documentation = True
                if '"""' in line or "'''" in line:
                    in_py_doc = False
            elif stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                documentation = True
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_py_doc = _unbalanced_triple(line)
        elif ext in {'.rs', '.ts', '.tsx'}:
            if in_block_comment:
                documentation = True
                if '*/' in line:
                    in_block_comment = False
            elif stripped.startswith('//'):
                documentation = True
            elif '/*' in line:
                documentation = True
                if '*/' not in line:
                    in_block_comment = True

        # A URL is a reference (e.g. the Tauri $schema), not a Unix assumption.
        if '://' in line:
            documentation = True

        if documentation:
            continue

        for kind, pattern in PATTERNS.items():
            if not pattern.search(line):
                continue
            # Docs and shell scripts are reference material or Unix launchers by
            # definition; they may name Unix paths without being a portability bug.
            intentional = ext in {'.md', '.sh'} or test_path or any(
                INTENTIONAL_CONTEXT.search(prior)
                for prior in lines[max(0, index - BACKWARD_WINDOW):index]
            )
            findings.append((kind, index + 1, line.strip(), intentional))

    return findings


def main() -> int:
    findings = []
    for path in iter_source():
        for kind, line_no, line, intentional in findings_in_file(path):
            findings.append((kind, path.relative_to(ROOT), line_no, line, intentional))

    real = [f for f in findings if not f[4]]
    intentional = [f for f in findings if f[4]]

    print(f'Windows audit: {len(real)} actionable finding(s), {len(intentional)} intentional/reference finding(s).')
    if real:
        print('\n[ACTIONABLE]')
        for kind, path, line_no, line, _ in real:
            print(f'{path}:{line_no}: [{kind}] {line}')
    if intentional:
        print('\n[INTENTIONAL / REFERENCE]')
        for kind, path, line_no, line, _ in intentional[:100]:
            print(f'{path}:{line_no}: [{kind}] {line}')
        if len(intentional) > 100:
            print(f'... {len(intentional) - 100} more')
    return 1 if real else 0


if __name__ == '__main__':
    raise SystemExit(main())
