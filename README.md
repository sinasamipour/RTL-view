# RTL Window 📐✨

A lightweight, modern Windows desktop utility that instantly displays any selected text in a beautiful, right-to-left (RTL) formatted popup. 

This tool is designed to solve the annoying problem of reading Persian (Farsi), Arabic, or any RTL text that is rendered left-to-right (LTR) or scrambled in applications like chat clients, terminal interfaces, or coding editors.

---

### [فارسی] راهنمای ابزار RTL Window

یک ابزار کمکی سبک و مدرن برای ویندوز که به شما امکان می‌دهد هر متن انتخاب‌شده در برنامه‌های مختلف را با فشردن یک کلید میانبر، در قالب یک پنجره‌ی پاپ‌آپ زیبا و کاملاً راست‌چین (RTL) مشاهده کنید. این ابزار به ویژه برای خواندن صحیح متون فارسی/عربی که در برخی برنامه‌ها (مانند ترمینال‌ها، پیام‌رسان‌ها یا ویرایشگرهای کد) چپ‌چین شده و خوانش آن‌ها سخت است، طراحی شده است.

---

## 🚀 Features | ویژگی‌ها

- **True RTL Layout & BiDi Rendering:** Uses Microsoft Edge Chromium WebView2 engine to render mixed Persian and English text flawlessly, preventing punctuation scrambling and word splitting.
- **Dynamic Popup Sizing:** The window dynamically sizes itself according to the length of the selected text.
- **Custom Font Support:** Embedded with the highly readable **Vazirmatn** font (Medium weight) from Google Fonts.
- **Smart English & Code Highlighting:** Automatically detects and formats English words, URLs, file paths, and code snippets in an "inline code block" style (amber text on dark gray background).
- **Clipboard Friendly:** Temporarily backs up and restores your clipboard, ensuring you don't lose your previously copied items.
- **Sleek Dark Mode:** Designed with a premium dark theme (Zinc-900 / `#18181b`).
- **Tray Icon Integration:** System tray menu to access the help dialog or exit the application completely.

---

## 📦 Project Structure | ساختار پروژه

```text
RTL-window/
│
├── assets/
│   ├── Vazirmatn-Medium.ttf     # Vazirmatn font file (loaded dynamically)
│   └── temp_text.txt            # Temporary clipboard exchange file (Git ignored)
│
├── .env                         # GitHub API configurations (Git ignored)
├── .gitignore                   # Standard Git ignore file
├── publish_to_github.py         # Automated helper script to publish to GitHub
├── rtl_viewer.ahk               # AutoHotkey background script (hotkey & clipboard hook)
├── gui.py                       # Modern WebView2 Python GUI (rendering & syntax highlighting)
├── README.md                    # Project documentation
└── run_rtl_viewer.bat           # Easy-to-use launch script
```

---

## 🛠️ Prerequisites | پیش‌نیازها

To run this utility, you need to have the following installed on your Windows machine:

برای اجرای این ابزار، نیاز دارید برنامه‌های زیر روی ویندوز شما نصب باشند:

1. **AutoHotkey v2** (Download from [autohotkey.com](https://www.autohotkey.com/))
2. **Python 3.x** (Download from [python.org](https://www.python.org/))
3. Python dependencies:
   ```bash
   pip install pywebview
   ```

---

## ⚡ How to Run & Use | نحوه اجرا و استفاده

### 1. Launching the App | اجرای برنامه
Double-click **`run_rtl_viewer.bat`** to start the program in the background. 
- You will receive a Windows toast notification: *"نمایشگر راست‌چین فعال شد"*.
- A custom tray icon will appear in the bottom-right corner of your screen (near the system clock).

برای اجرا، روی فایل **`run_rtl_viewer.bat`** دو بار کلیک کنید. یک اعلان در گوشه ویندوز با عنوان «نمایشگر راست‌چین فعال شد» دریافت خواهید کرد و آیکون برنامه در گوشه ساعت ویندوز قرار می‌گیرد.

### 2. Using the Shortcut | نمایش پاپ‌آپ
1. **Select** any Persian/RTL text in any application (browser, terminal, WhatsApp, VS Code, etc.).
2. Press **`Ctrl + Alt + F`**.
3. A beautiful dark popup will appear displaying the text perfectly right-aligned, with English words highlighted.
4. Press **`Esc`** or click **بستن** (Close) to close the popup.

۱. متن مورد نظر را در هر برنامه‌ای **انتخاب** کنید.
۲. کلیدهای میانبر **`Ctrl + Alt + F`** را فشار دهید.
۳. پاپ‌آپ راست‌چین شده با تم تاریک باز می‌شود و کلمات انگلیسی آن به صورت متمایز هایلایت شده‌اند.
۴. با فشردن کلید **`Esc`** یا کلیک روی دکمه **بستن** پنجره بسته می‌شود.

---

## 💡 Run on Windows Startup | اجرای خودکار با روشن شدن سیستم

If you want this utility to run automatically when you turn on your PC:
1. Press `Win + R`, type `shell:startup`, and press Enter.
2. Create a shortcut of `run_rtl_viewer.bat` and paste it inside the Startup folder.

اگر می‌خواهید این برنامه با روشن شدن سیستم به صورت خودکار اجرا شود:
1. کلیدهای میانبر `Win + R` را زده، عبارت `shell:startup` را بنویسید و Enter بزنید.
2. یک میانبر (Shortcut) از فایل `run_rtl_viewer.bat` بسازید و در این پوشه قرار دهید.

---

## 📄 License | لایسنس

This project is open-source and licensed under the **MIT License**.
