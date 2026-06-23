#Requires AutoHotkey v2.0
#SingleInstance Force

; تنظیم آیکون اختصاصی برنامه در System Tray
; حالت نصبی: icon.ico کنار اسکریپت؛ حالت توسعه: در پوشه‌ی assets
for iconPath in [A_ScriptDir "\icon.ico", A_ScriptDir "\assets\icon.ico"] {
    if FileExist(iconPath) {
        TraySetIcon(iconPath)
        break
    }
}

; منوی سفارشی در System Tray (گوشه ویندوز)
A_IconTip := "نمایشگر راست‌چین"
Tray := A_TrayMenu
Tray.Delete() ; حذف گزینه‌های پیش‌فرض
Tray.Add("راهنما", ShowHelp)
Tray.Add("خروج از برنامه", ExitAppHandler)

ShowHelp(*) {
    MsgBox("برنامه در حال اجراست.`n`nروش استفاده:`n1. متن دلخواه را در هر برنامه‌ای انتخاب (Select) کنید.`n2. کلیدهای میانبر Ctrl + Alt + F را فشار دهید.`n`nبرای بستن پاپ‌آپ می‌توانید از دکمه 'بستن' یا کلید Esc استفاده کنید.", "راهنمای نمایشگر راست‌چین", "Iconi")
}

ExitAppHandler(*) {
    ExitApp()
}

; نمایش نوتیفیکیشن در ویندوز هنگام اجرا شدن موفقیت‌آمیز برنامه
TrayTip("نمایشگر راست‌چین فعال شد", "از کلیدهای Ctrl + Alt + F استفاده کنید.", 1)

; کلید میانبر: Ctrl + Alt + F
^!f::
{
    ; ذخیره موقت محتوای کلیپ‌بورد فعلی کاربر
    clipSaved := ClipboardAll()
    A_Clipboard := ""
    
    ; ارسال فرمان کپی (Ctrl+C)
    Send("^c")
    
    ; انتظار برای کپی شدن متن (حداکثر 0.4 ثانیه)
    if !ClipWait(0.4)
    {
        ; بازگرداندن کلیپ‌بورد قبلی در صورت عدم کپی
        A_Clipboard := clipSaved
        return
    }
    
    selectedText := A_Clipboard

    ; خواندن نسخه‌ی HTML کلیپ‌بورد (قبل از بازگرداندن کلیپ‌بورد کاربر)
    ; این نسخه ساختار لیست‌ها و جدول‌ها را حفظ می‌کند، برخلاف متن ساده
    htmlFragment := GetClipboardHTMLFragment()

    ; بازگرداندن کلیپ‌بورد اصلی کاربر با کمی تاخیر برای پایداری بیشتر
    Sleep(50)
    A_Clipboard := clipSaved

    ; تمیز کردن فضاهای خالی ابتدا و انتهای متن
    selectedText := Trim(selectedText)
    if (selectedText == "" && Trim(htmlFragment) == "")
        return

    ; پوشه‌ی داده‌ی قابل‌نوشتن کاربر (%LOCALAPPDATA%\RTLView)
    ; در حالت نصبی، خود برنامه در Program Files (فقط‌خواندنی) است؛ پس فایل موقت اینجا نوشته می‌شود
    dataDir := GetDataDir()
    if !DirExist(dataDir) {
        DirCreate(dataDir)
    }

    ; تعیین حالت و محتوای ارسالی: اگر HTML در دسترس بود از آن استفاده کن، وگرنه متن ساده
    ; خط اول فایل، حالت را مشخص می‌کند (MODE=HTML یا MODE=TEXT) و بقیه محتواست
    if (Trim(htmlFragment) != "") {
        payload := "MODE=HTML`n" htmlFragment
    } else {
        payload := "MODE=TEXT`n" selectedText
    }

    ; نوشتن محتوا در یک فایل موقت یکتا برای انتقال امن به پایتون
    ; نام یکتا (تیک سیستم) از تداخل و Race Condition هنگام فشردن سریع کلید جلوگیری می‌کند
    tempFile := dataDir "\temp_text_" A_TickCount ".txt"
    if FileExist(tempFile) {
        FileDelete(tempFile)
    }
    ; UTF-8-RAW یعنی بدون BOM؛ تا خط اول (MODE=...) دقیقاً قابل تطبیق در پایتون باشد
    FileAppend(payload, tempFile, "UTF-8-RAW")

    ; اجرای نمایشگر گرافیکی و ارسال مسیر فایل موقت به‌عنوان آرگومان
    ; حالت نصبی: gui.exe کنار برنامه قرار دارد؛ حالت توسعه: با pythonw اجرای gui.py
    guiExe := A_ScriptDir "\gui.exe"
    if FileExist(guiExe) {
        Run('"' guiExe '" "' tempFile '"')
    } else {
        ; پیدا کردن مسیر مطلق pythonw.exe از روی PATH (بدون جست‌وجوی پوشه‌ی کاری)
        ; این کار از حمله‌ی PATH/Binary Hijacking با کاشتن pythonw.exe مخرب جلوگیری می‌کند
        pythonExe := FindPythonExe()
        if (pythonExe == "") {
            FileDelete(tempFile)
            MsgBox("gui.exe یا pythonw.exe یافت نشد. لطفاً برنامه را به‌درستی نصب کنید یا Python را نصب کنید.", "خطا", "Iconx")
            return
        }
        Run('"' pythonExe '" "' A_ScriptDir '\gui.py" "' tempFile '"')
    }
}

; مسیر پوشه‌ی داده‌ی قابل‌نوشتن کاربر؛ در صورت نبود LOCALAPPDATA به پوشه‌ی موقت برمی‌گردد
GetDataDir() {
    base := EnvGet("LOCALAPPDATA")
    if (base == "")
        base := EnvGet("TEMP")
    return base "\RTLView"
}

; جست‌وجوی pythonw.exe فقط در مسیرهای معتبر PATH و بازگرداندن مسیر مطلق (پوشه‌ی کاری نادیده گرفته می‌شود)
FindPythonExe() {
    pathEnv := EnvGet("PATH")
    Loop Parse, pathEnv, ";" {
        dir := Trim(A_LoopField)
        if (dir == "")
            continue
        candidate := dir "\pythonw.exe"
        if FileExist(candidate)
            return candidate
    }
    return ""
}

; خواندن قطعه‌ی HTML از کلیپ‌بورد (فرمت "HTML Format" ویندوز) و استخراج بخش Fragment
; در صورت نبودِ نسخه‌ی HTML، رشته‌ی خالی برمی‌گرداند تا به متن ساده برگردیم
GetClipboardHTMLFragment() {
    static CF_HTML := DllCall("RegisterClipboardFormat", "Str", "HTML Format", "UInt")

    if !DllCall("IsClipboardFormatAvailable", "UInt", CF_HTML)
        return ""

    if !DllCall("OpenClipboard", "Ptr", 0)
        return ""

    raw := ""
    try {
        hData := DllCall("GetClipboardData", "UInt", CF_HTML, "Ptr")
        if (hData) {
            pData := DllCall("GlobalLock", "Ptr", hData, "Ptr")
            if (pData) {
                ; داده‌ی CF_HTML با انکودینگ UTF-8 و خاتمه‌یافته با NULL است
                raw := StrGet(pData, "UTF-8")
                DllCall("GlobalUnlock", "Ptr", hData)
            }
        }
    }
    DllCall("CloseClipboard")

    if (raw == "")
        return ""

    ; استخراج محتوای بین نشانگرهای StartFragment و EndFragment
    startTag := "<!--StartFragment-->"
    endTag := "<!--EndFragment-->"
    s := InStr(raw, startTag)
    e := InStr(raw, endTag)
    if (s && e && e > s) {
        s += StrLen(startTag)
        return SubStr(raw, s, e - s)
    }

    ; اگر نشانگرها نبودند، کل بدنه‌ی بعد از هدر را برگردان (هدر با یک خط خالی از بدنه جدا می‌شود)
    bodyStart := InStr(raw, "<html")
    if (bodyStart)
        return SubStr(raw, bodyStart)
    return ""
}
