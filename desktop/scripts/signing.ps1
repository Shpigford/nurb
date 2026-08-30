# Loads the local updater signing key into the environment for a `tauri build`.
#
# The private key is gitignored (desktop/signing/tauri-updater.key) and is
# needed by tauri build whenever `createUpdaterArtifacts` is true. In CI the
# same two variables come from repository secrets; locally they come from the
# key file this script reads. The key is never printed.
#
# Usage:
#   .\scripts\signing.ps1
#   npm run tauri -- build
#
# The committed public key (signing/tauri-updater.key.pub) must match this
# private key, or the generated signature will not verify.

$ErrorActionPreference = "Stop"

$keyFile = Join-Path $PSScriptRoot "..\signing\tauri-updater.key"
$passwordFile = Join-Path $PSScriptRoot "..\signing\.password"

if (-not (Test-Path $keyFile)) {
    Write-Error @"
No signing key at $keyFile

Generate one (and keep the private key out of version control):

  cd desktop
  npx tauri signer generate --ci -w signing/tauri-updater.key

For CI, put the key contents and password in the repository secrets
TAURI_SIGNING_PRIVATE_KEY and TAURI_SIGNING_PRIVATE_KEY_PASSWORD instead.
"@
}

# The Tauri CLI wants the key contents (TAURI_SIGNING_PRIVATE_KEY_PATH is
# not honored for updater signing), so read the file into the variable.
$env:TAURI_SIGNING_PRIVATE_KEY = (Get-Content $keyFile -Raw)
if (Test-Path $passwordFile) {
    $env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = (Get-Content $passwordFile -Raw).Trim()
}
Write-Host "Signing key loaded from $keyFile"