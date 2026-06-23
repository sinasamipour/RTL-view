# ============================================================================
# build.ps1 - prepare build outputs for the RTL View installer
#   Step 1: gui.exe via PyInstaller (Python interpreter bundled inside)
#   Step 2: copy the official AutoHotkey interpreter as RTLViewDaemon.exe
#           (instead of compiling with Ahk2Exe, which antivirus often flags)
# Then compile installer.iss with Inno Setup (ISCC.exe).
#
# Run:  powershell -ExecutionPolicy Bypass -File build.ps1
# (ASCII-only on purpose so it parses under Windows PowerShell 5.1.)
# ============================================================================

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "==> [1/2] Building gui.exe with PyInstaller ..." -ForegroundColor Cyan

python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not installed. Installing ..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

if (Test-Path "$root\build") { Remove-Item "$root\build" -Recurse -Force }
if (Test-Path "$root\dist")  { Remove-Item "$root\dist"  -Recurse -Force }
python -m PyInstaller gui.spec --noconfirm
if (-not (Test-Path "$root\dist\gui\gui.exe")) {
    throw "gui.exe build failed."
}
Write-Host "    gui.exe built: dist\gui\gui.exe" -ForegroundColor Green

Write-Host "==> [2/2] Preparing AutoHotkey interpreter (RTLViewDaemon.exe) ..." -ForegroundColor Cyan

# Auto-locate the 64-bit AutoHotkey v2 interpreter
$ahkRoots = @(
    "$env:LOCALAPPDATA\Programs\AutoHotkey",
    "$env:ProgramFiles\AutoHotkey",
    "${env:ProgramFiles(x86)}\AutoHotkey"
)
$interp = $null
foreach ($r in $ahkRoots) {
    if (Test-Path $r) {
        $found = Get-ChildItem $r -Recurse -Filter "AutoHotkey64.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $interp = $found.FullName; break }
    }
}
if (-not $interp) {
    Write-Host "AutoHotkey64.exe not found. Install AutoHotkey v2." -ForegroundColor Red
    exit 1
}

# Copy the interpreter under a unique name so the running process is identifiable.
Copy-Item $interp "$root\RTLViewDaemon.exe" -Force
Write-Host "    RTLViewDaemon.exe ready (from: $interp)" -ForegroundColor Green

Write-Host ""
Write-Host "==> Done. Now compile installer.iss with Inno Setup (ISCC.exe)." -ForegroundColor Cyan
Write-Host "    Final output: Output\RTLView-Setup.exe" -ForegroundColor Cyan
