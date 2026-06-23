; ============================================================================
; Inno Setup script for RTL View
; نصب‌کننده‌ی واحد که به Python یا AutoHotkey روی سیستم کاربر نیاز ندارد.
;
; پیش از کامپایل، خروجی‌های build باید آماده باشند (build.ps1 را اجرا کنید):
;   1) dist\gui\           ← خروجی PyInstaller (gui.exe و _internal)
;   2) RTLViewDaemon.exe   ← مفسر رسمی AutoHotkey (کپی‌شده توسط build.ps1)
;
; سپس:  & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
; خروجی: Output\RTLView-Setup.exe
; ============================================================================

#define AppName "RTL View"
#define AppVersion "1.0.0"
#define AppPublisher "Sina Samipour"
#define Daemon "RTLViewDaemon.exe"
#define Script "rtl_viewer.ahk"

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
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startup"; Description: "اجرای خودکار هنگام روشن شدن ویندوز"; GroupDescription: "گزینه‌ها:"

[Files]
; محتوای کامل خروجی PyInstaller (gui.exe + _internal + فونت) به ریشه‌ی نصب
Source: "dist\gui\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
; مفسر AutoHotkey و اسکریپت hotkey
Source: "RTLViewDaemon.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Script}"; DestDir: "{app}"; Flags: ignoreversion
; برای نصب‌کننده‌ی کاملاً خودکفا، بوت‌استرپر WebView2 را کنار این فایل بگذارید و خط زیر را فعال کنید:
; Source: "MicrosoftEdgeWebView2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
; شورتکات‌ها مفسر را با اسکریپت به‌عنوان پارامتر اجرا می‌کنند
Name: "{group}\{#AppName}"; Filename: "{app}\{#Daemon}"; Parameters: """{app}\{#Script}"""; WorkingDir: "{app}"
Name: "{group}\حذف {#AppName}"; Filename: "{uninstallexe}"

[Registry]
; اجرای خودکار هنگام لاگین کاربر (فقط اگر گزینه‌اش تیک خورده باشد)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "{#AppName}"; \
    ValueData: """{app}\{#Daemon}"" ""{app}\{#Script}"""; \
    Flags: uninsdeletevalue; Tasks: startup

[Run]
; اجرای برنامه بلافاصله پس از پایان نصب
Filename: "{app}\{#Daemon}"; Parameters: """{app}\{#Script}"""; WorkingDir: "{app}"; \
    Description: "اجرای {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; بستن دیمن در حال اجرا هنگام حذف برنامه (نام یکتا، پس به اسکریپت‌های AHK دیگر کاربر کاری ندارد)
Filename: "{cmd}"; Parameters: "/C taskkill /IM {#Daemon} /F"; Flags: runhidden; RunOnceId: "KillDaemon"

[Code]
// بررسی نصب بودن WebView2 Runtime روی سیستم کاربر
function IsWebView2Installed(): Boolean;
var
  Value: String;
begin
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
