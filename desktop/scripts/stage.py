from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAURI = ROOT / 'desktop' / 'src-tauri'
RESOURCES = TAURI / 'resources'
BINARIES = TAURI / 'binaries'
UV_VERSION = '0.12.1'


def target_triple() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == 'windows':
        return 'aarch64-pc-windows-msvc' if machine in {'arm64', 'aarch64'} else 'x86_64-pc-windows-msvc'
    if system == 'darwin':
        return 'aarch64-apple-darwin' if machine in {'arm64', 'aarch64'} else 'x86_64-apple-darwin'
    if system == 'linux':
        return 'aarch64-unknown-linux-gnu' if machine in {'arm64', 'aarch64'} else 'x86_64-unknown-linux-gnu'
    raise RuntimeError(f'Unsupported platform: {platform.system()} {platform.machine()}')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={'User-Agent': 'nurb-windows-stager'})
    with urllib.request.urlopen(request) as response, destination.open('wb') as fh:
        shutil.copyfileobj(response, fh)


def fetch_uv(target: str) -> Path:
    suffixes = ['.zip', '.tar.gz'] if 'windows' in target else ['.tar.gz']
    destination = BINARIES / ('uv-' + target + ('.exe' if 'windows' in target else ''))
    if destination.exists():
        return destination
    BINARIES.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        archive = None
        archive_url = None
        for suffix in suffixes:
            candidate = tmp / ('uv' + suffix)
            url = f'https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-{target}{suffix}'
            try:
                download(url, candidate)
                archive_url = url
                archive = candidate
                break
            except Exception:
                if candidate.exists():
                    candidate.unlink()
        if archive is None:
            raise RuntimeError(f'Could not download uv {UV_VERSION} for {target}')
        checksum = tmp / (archive.name + '.sha256')
        assert archive_url is not None
        download(archive_url + '.sha256', checksum)
        expected = checksum.read_text(encoding='utf-8').split()[0].lower()
        actual = sha256(archive)
        if expected != actual:
            raise RuntimeError(f'SHA-256 mismatch for {archive.name}')
        extract = tmp / 'extract'
        extract.mkdir()
        if archive.suffix == '.zip':
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(extract)
        else:
            subprocess.run(['tar', '-xzf', str(archive), '-C', str(extract)], check=True)
        found = next(extract.rglob('uv.exe' if 'windows' in target else 'uv'), None)
        if found is None:
            raise RuntimeError('uv executable was not found in the archive')
        shutil.copy2(found, destination)
    if os.name != 'nt':
        destination.chmod(0o755)
    return destination


def signable_targets() -> list:
    """Locate Windows executables that, once produced, are candidates for
    Authenticode signing. A staged build that hasn't produced these files
    is a no-op at the signing layer - their absence is not an error here,
    only the loud-fail decision lives in `check_authenticode_signing`."""
    out = []
    for candidate in (
        BINARIES / 'uv-x86_64-pc-windows-msvc.exe',
        BINARIES / 'uv-aarch64-pc-windows-msvc.exe',
    ):
        if candidate.exists():
            out.append(candidate)
    return out


def check_authenticode_signing(executables) -> int:
    """Validate or perform Authenticode (SmartScreen) signing on produced
    Windows executables. Behavior is fully env-gated so local dev builds
    keep working without ceremony:

    - When `NURB_WINDOWS_AUTHENTICODE_REQUIRED` is unset, this is a
      no-op that prints a one-line status.
    - When set to `1`, signing must succeed. The certificate material is
      read from `NURB_WINDOWS_AUTHENTICODE_PFX` (path to a .pfx) and the
      optional password from `NURB_WINDOWS_AUTHENTICODE_PFX_PASSWORD`,
      and `signtool.exe` must be on PATH (Windows SDK). A timestamp
      authority may be set in `NURB_WINDOWS_AUTHENTICODE_TIMESTAMP_URL`
      and defaults to DigiCert. Loud failure otherwise, so that the
      release pipeline never silently ships an unsigned executable when
      it asked for a signed one.

    The cert material itself is an EXTERNAL dependency: this repo never
    stores it, only references the path the CI environment passes in.
    """
    required = os.environ.get('NURB_WINDOWS_AUTHENTICODE_REQUIRED', '') == '1'
    if not required:
        if executables:
            print(
                'authenticode: not required '
                '(set NURB_WINDOWS_AUTHENTICODE_REQUIRED=1 to sign)'
            )
        return 0
    if not executables:
        raise RuntimeError(
            'authenticode required but no produced Windows executables '
            'were found'
        )
    pfx = os.environ.get('NURB_WINDOWS_AUTHENTICODE_PFX')
    if not pfx:
        raise RuntimeError(
            'authenticode required but NURB_WINDOWS_AUTHENTICODE_PFX is unset'
        )
    if not Path(pfx).is_file():
        raise RuntimeError(
            f'authenticode: PFX not found at {pfx}. ' 
            'Set NURB_WINDOWS_AUTHENTICODE_PFX to an existing .pfx file, ' 
            'or unset NURB_WINDOWS_AUTHENTICODE_REQUIRED to skip signing.'
        )
    signtool_path = shutil.which('signtool') or shutil.which('signtool.exe')
    if signtool_path is None:
        raise RuntimeError(
            'authenticode required but signtool.exe is not on PATH '
            '(install the Windows SDK)'
        )
    timestamp = os.environ.get(
        'NURB_WINDOWS_AUTHENTICODE_TIMESTAMP_URL',
        'http://timestamp.digicert.com',
    )
    password = os.environ.get('NURB_WINDOWS_AUTHENTICODE_PFX_PASSWORD')
    cmd = [
        signtool_path,
        'sign',
        '/fd', 'sha256',
        '/td', 'sha256',
        '/tr', timestamp,
        '/f', pfx,
    ]
    if password:
        cmd += ['/p', password]
    for exe in executables:
        subprocess.run(cmd + [str(exe)], check=True)
        print(f'authenticode: signed {exe.name}')
    return 0


def main() -> int:
    target = target_triple()
    RESOURCES.mkdir(parents=True, exist_ok=True)
    BINARIES.mkdir(parents=True, exist_ok=True)
    subprocess.run(['uv', 'build', '--wheel', '--project', str(ROOT), '-o', str(RESOURCES)], check=True)
    requirements = RESOURCES / 'requirements.lock'
    subprocess.run(['uv', 'pip', 'compile', str(ROOT / 'pyproject.toml'), '--universal', '--python-version', '3.13', '--generate-hashes', '--no-annotate', '-q', '-o', str(requirements)], check=True)
    adapter = ROOT / 'desktop' / 'adapter-runtime'
    shutil.copy2(adapter / 'package.json', RESOURCES / 'adapter-package.json')
    shutil.copy2(adapter / 'package-lock.json', RESOURCES / 'adapter-package-lock.json')
    uv = fetch_uv(target)
    print(f'stage: ready for {target}: {uv}')
    return 0


if __name__ == '__main__':
    code = main()
    if code == 0:
        code = check_authenticode_signing(signable_targets())
    raise SystemExit(code)
