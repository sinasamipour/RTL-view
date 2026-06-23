; ============================================================================
; Inno Setup script for RTL View
; نصب‌کننده‌ی واحد که به Python یا AutoHotkey روی سیستم کاربر نیاز ندارد.
;
; پیش از کامپایل این فایل، باید خروجی‌های build آماده باشند (به BUILD.md نگاه کنید):
;   1) dist\gui\           ← خروجی PyInstaller (شامل gui.exe و _internal)
;   2) rtl_viewer.exe      ← خروجی Ahk2Exe
;
; سپس این فایل را با Inno Setup Compiler باز کرده و Compile بزنید.
; خروجی: Output\RTLView-Setup.exe
; ============================================================================

#define AppName "RTL View"
#define AppVersion "1.0.0"
#define AppPublisher "Sina Samipour"
#define AppExeName "rtl_viewer.exe"

[Setup]
AppId={{8B3D5C7A-1F2E-4A6B-9C0D-RTLVIEW00001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; نصب در سطح کاربر (بدون نیاز به دسترسی Administrator)
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=RTLView-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "fa"; MessagesFile: "compiler:Languages\Persian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startup"; Description: "اجرای خودکار هنگام روشن شدن ویندوز"; GroupDescription: "گزینه‌ها:"

[Files]
; محتوای کامل خروجی PyInstaller (gui.exe + _internal + فونت) به ریشه‌ی نصب
Source: "dist\gui\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
; دیمن hotkey کامپایل‌شده
Source: "rtl_viewer.exe"; DestDir: "{app}"; Flags: ignoreversion
; اگر بوت‌استرپر WebView2 را کنار این فایل بگذارید، در صورت نیاز نصب می‌شود (اختیاری)
; Source: "MicrosoftEdgeWebView2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\حذف {#AppName}"; Filename: "{uninstallexe}"

[Registry]
; اجرای خودکار هنگام لاگین کاربر (فقط اگر گزینه‌اش تیک خورده باشد)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: startup

[Run]
; اجرای برنامه بلافاصله پس از پایان نصب
Filename: "{app}\{#AppExeName}"; Description: "اجرای {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; بستن دیمن در حال اجرا هنگام حذف برنامه
Filename: "{cmd}"; Parameters: "/C taskkill /IM {#AppExeName} /F"; Flags: runhidden; RunOnceId: "KillDaemon"

[Code]
// بررسی نصب بودن WebView2 Runtime روی سیستم کاربر
function IsWebView2Installed(): Boolean;
var
  Value: String;
begin
  // کلید نسخه‌ی Evergreen در هر دو شاخه‌ی ۶۴ و ۳۲ بیتی بررسی می‌شود
  Result :=
    RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Value) or
    RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Value) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Value);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    if not IsWebView2Installed() then
    begin
      // اگر بوت‌استرپر را در [Files] فعال کرده باشید، اینجا اجرا می‌شود
      if FileExists(ExpandConstant('{tmp}\MicrosoftEdgeWebView2Setup.exe')) then
        Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebView2Setup.exe'), '/silent /install',
             '', SW_HIDE, ewWaitUntilTerminated, ResultCode)
      else
        MsgBox('برای نمایش صحیح، به «WebView2 Runtime» نیاز است.' #13#10 +
               'اگر برنامه پاپ‌آپ را نشان نداد، آن را از سایت مایکروسافت نصب کنید.',
               mbInformation, MB_OK);
    end;
  end;
end;
