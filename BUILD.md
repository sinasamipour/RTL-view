# 🏗️ Building the Installer | ساخت نصب‌کننده

This guide explains how to turn the project into a single **`RTLView-Setup.exe`** that any
Windows user can install **without having Python or AutoHotkey installed**.

این راهنما توضیح می‌دهد چگونه پروژه را به یک فایل **`RTLView-Setup.exe`** تبدیل کنید که هر کاربر
ویندوزی **بدون نصب Python یا AutoHotkey** بتواند نصبش کند.

---

## 🧰 Prerequisites (build machine only) | پیش‌نیازها (فقط روی سیستم سازنده)

These are needed **only on your machine to build** — the end user needs none of them.

این‌ها فقط **روی سیستم خودتان برای ساخت** لازم‌اند؛ کاربر نهایی به هیچ‌کدام نیاز ندارد.

1. **Python 3.x** with the runtime deps:
   ```bash
   pip install pywebview nh3 pyinstaller
   ```
2. **AutoHotkey v2** ([autohotkey.com](https://www.autohotkey.com/)) — only its interpreter
   `AutoHotkey64.exe` is needed. We do **not** compile the script with Ahk2Exe (that compiler
   and the exes it produces are frequently false-flagged by antivirus). Instead the official
   interpreter is bundled alongside the script, which is far less likely to be flagged.
3. **Inno Setup 6** (free) — [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php).

---

## ⚙️ Step 1 — Build the two executables | ساخت دو فایل اجرایی

From the project root, run:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

This produces:
- `dist\gui\gui.exe` — the popup renderer (Python bundled inside, onedir for fast startup).
- `RTLViewDaemon.exe` — a copy of the official AutoHotkey interpreter (renamed so the running
  process is identifiable). It runs `rtl_viewer.ahk`, which is shipped alongside it.

> If `build.ps1` can't find `AutoHotkey64.exe`, install AutoHotkey v2 and re-run.

---

## 📦 Step 2 — Build the installer | ساخت نصب‌کننده

1. Open **`installer.iss`** in Inno Setup Compiler.
2. Click **Build → Compile** (or press F9).
3. The installer appears at **`Output\RTLView-Setup.exe`**.

That single file is what you distribute.

---

## 🌐 WebView2 Runtime | درباره‌ی WebView2

The popup uses Microsoft Edge **WebView2**, which is preinstalled on Windows 11 and most
Windows 10. The installer checks for it; if missing it shows a note.

To make the installer **fully self-contained**, download the *Evergreen Bootstrapper*
(`MicrosoftEdgeWebView2Setup.exe`) from Microsoft, place it next to `installer.iss`, then
uncomment the two lines that reference it inside `installer.iss` (in `[Files]` and `[Code]`).

موتور نمایش از **WebView2** استفاده می‌کند که روی ویندوز ۱۱ و اکثر ویندوز ۱۰ از قبل نصب است.
برای اینکه نصب‌کننده کاملاً خودکفا شود، بوت‌استرپر آن را از مایکروسافت دانلود و کنار `installer.iss`
بگذارید و دو خط مربوطه را در فایل از حالت کامنت خارج کنید.

---

## 🧪 Testing without building the installer | تست بدون ساخت نصب‌کننده

The app still runs in **development mode** with no compilation:
- Run `run_rtl_viewer.bat` (needs AutoHotkey + Python installed).
- The AHK script auto-detects: if `gui.exe` exists beside it, it uses the compiled exe;
  otherwise it falls back to `pythonw gui.py`. So the same code works both ways.

---

## 📂 Install layout | ساختار نصب‌شده

```
C:\Users\<user>\AppData\Local\Programs\RTL View\
   ├── RTLViewDaemon.exe   ← AutoHotkey interpreter (launched at startup if chosen)
   ├── rtl_viewer.ahk      ← the hotkey script it runs
   ├── gui.exe             ← popup renderer
   └── _internal\          ← bundled Python libs + assets\Vazirmatn-Medium.ttf

C:\Users\<user>\AppData\Local\RTLView\
   └── temp_text_*.txt     ← short-lived clipboard exchange files (auto-deleted)
```
