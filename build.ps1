# ============================================================================
# build.ps1 — ساخت خروجی‌های اجرایی برای نصب‌کننده‌ی RTL View
# مرحله ۱: gui.exe با PyInstaller
# مرحله ۲: rtl_viewer.exe با Ahk2Exe
# سپس installer.iss را با Inno Setup کامپایل کنید.
#
# اجرا:  powershell -ExecutionPolicy Bypass -File build.ps1
# ============================================================================

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "==> [1/2] ساخت gui.exe با PyInstaller ..." -ForegroundColor Cyan

# اطمینان از نصب بودن PyInstaller
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller نصب نیست. در حال نصب ..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

# پاک‌سازی خروجی قبلی و build تازه
if (Test-Path "$root\build") { Remove-Item "$root\build" -Recurse -Force }
if (Test-Path "$root\dist")  { Remove-Item "$root\dist"  -Recurse -Force }
python -m PyInstaller gui.spec --noconfirm
if (-not (Test-Path "$root\dist\gui\gui.exe")) {
    throw "ساخت gui.exe ناموفق بود."
}
Write-Host "    gui.exe ساخته شد: dist\gui\gui.exe" -ForegroundColor Green

Write-Host "==> [2/2] ساخت rtl_viewer.exe با Ahk2Exe ..." -ForegroundColor Cyan

# جست‌وجوی خودکار کامپایلر Ahk2Exe در مسیرهای رایج
$ahkRoots = @(
    "$env:LOCALAPPDATA\Programs\AutoHotkey",
    "$env:ProgramFiles\AutoHotkey",
    "${env:ProgramFiles(x86)}\AutoHotkey"
)
$ahk2exe = $null
foreach ($r in $ahkRoots) {
    if (Test-Path $r) {
        $found = Get-ChildItem $r -Recurse -Filter "Ahk2Exe.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $ahk2exe = $found.FullName; break }
    }
}

if (-not $ahk2exe) {
    Write-Host "Ahk2Exe.exe یافت نشد." -ForegroundColor Red
    Write-Host "کامپایلر AutoHotkey را نصب کنید (بخش Compiler هنگام نصب AutoHotkey) یا از autohotkey.com دانلود کنید." -ForegroundColor Yellow
    Write-Host "سپس دوباره این اسکریپت را اجرا کنید." -ForegroundColor Yellow
    exit 1
}

# جست‌وجوی فایل پایه‌ی نسخه‌ی ۶۴ بیتی AHK v2
$baseBin = Get-ChildItem (Split-Path $ahk2exe -Parent) -Recurse -Filter "*.bin" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "64" } | Select-Object -First 1

$ahkArgs = @("/in", "$root\rtl_viewer.ahk", "/out", "$root\rtl_viewer.exe")
if ($baseBin) { $ahkArgs += @("/base", $baseBin.FullName) }

& $ahk2exe @ahkArgs
if (-not (Test-Path "$root\rtl_viewer.exe")) {
    throw "ساخت rtl_viewer.exe ناموفق بود."
}
Write-Host "    rtl_viewer.exe ساخته شد." -ForegroundColor Green

Write-Host ""
Write-Host "==> آماده شد! اکنون installer.iss را با Inno Setup باز کرده و Compile بزنید." -ForegroundColor Cyan
Write-Host "    خروجی نهایی: Output\RTLView-Setup.exe" -ForegroundColor Cyan
