#Requires AutoHotkey v2.0
#SingleInstance Force

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
    
    ; بازگرداندن کلیپ‌بورد اصلی کاربر با کمی تاخیر برای پایداری بیشتر
    Sleep(50)
    A_Clipboard := clipSaved
    
    ; تمیز کردن فضاهای خالی ابتدا و انتهای متن
    selectedText := Trim(selectedText)
    if (selectedText == "")
        return
        
    ; ایجاد مسیر پوشه assets در صورت عدم وجود
    assetsDir := A_ScriptDir "\assets"
    if !DirExist(assetsDir) {
        DirCreate(assetsDir)
    }
    
    ; نوشتن متن کپی شده در یک فایل موقت برای انتقال امن به پایتون
    tempFile := assetsDir "\temp_text.txt"
    if FileExist(tempFile) {
        FileDelete(tempFile)
    }
    FileAppend(selectedText, tempFile, "UTF-8")
    
    ; اجرای برنامه گرافیکی پایتون در پس‌زمینه بدون نمایش پنجره ترمینال (با استفاده از pythonw.exe)
    guiScript := A_ScriptDir "\gui.py"
    Run('pythonw.exe "' guiScript '"')
}
