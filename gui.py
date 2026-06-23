import os
import sys
import re
import html
import base64
import ctypes
import webview

# تابع متمایز کردن کلمات انگلیسی با مارکرهای موقت جهت جلوگیری از به هم ریختگی کاراکترهای اسکیپ شده HTML
def highlight_text(raw_text):
    start_marker = "@@ENG_START@@"
    end_marker = "@@ENG_END@@"
    
    # ریجکس شناسایی هوشمند کلمات انگلیسی، نام فایل‌ها و کدهای برنامه‌نویسی
    pattern = re.compile(r'\.?[a-zA-Z0-9_\-\:\=]*[a-zA-Z][a-zA-Z0-9_\-\.\:\=]*')
    
    # علامت‌گذاری کلمات انگلیسی
    def mark(match):
        return f"{start_marker}{match.group(0)}{end_marker}"
        
    marked_text = pattern.sub(mark, raw_text)
    
    # اسکیپ کردن تگ‌های HTML در متن اصلی جهت امنیت و رندر صحیح
    escaped_text = html.escape(marked_text)
    
    # جایگزینی مارکرها با تگ‌های code در HTML
    highlighted = escaped_text.replace(start_marker, "<code>").replace(end_marker, "</code>")
    return highlighted

# ۱. بارگذاری فونت اختصاصی وزیر و تبدیل آن به Base64 جهت لود بدون مشکل در WebView
font_path = os.path.join(os.path.dirname(__file__), "assets", "Vazirmatn-Medium.ttf")
font_loaded = False
font_base64 = ""

if os.path.exists(font_path):
    # بارگذاری فونت در حافظه موقت پروسه فعلی (FR_PRIVATE = 0x10)
    res = ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
    if res > 0:
        font_loaded = True
    try:
        with open(font_path, "rb") as f:
            font_base64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass

# ۲. خواندن متن موقت کپی‌شده
temp_file = os.path.join(os.path.dirname(__file__), "assets", "temp_text.txt")
text_content = ""
if os.path.exists(temp_file):
    try:
        with open(temp_file, "r", encoding="utf-8") as f:
            text_content = f.read()
        os.remove(temp_file) # حذف فایل موقت جهت حفظ حریم خصوصی
    except Exception:
        pass

if not text_content:
    text_content = "متنی برای نمایش انتخاب نشده است."

text_content = text_content.strip()

# ۳. آماده‌سازی متن با هایلایت کلمات انگلیسی
highlighted_text = highlight_text(text_content)

# ۴. ساخت قالب HTML با موتور رندرینگ بی نقص وب
html_template = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @font-face {{
            font-family: 'Vazirmatn';
            src: url('data:font/truetype;charset=utf-8;base64,{font_base64}') format('truetype');
            font-weight: normal;
            font-style: normal;
        }}
        body {{
            background-color: #18181b;
            color: #e4e4e7;
            font-family: 'Vazirmatn', Tahoma, sans-serif;
            font-size: 14.5px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            user-select: text;
            -webkit-user-select: text;
            overflow-x: hidden;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
            font-family: inherit;
        }}
        code {{
            font-family: 'Consolas', monospace;
            background-color: #27272a;
            color: #fbbf24;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
            unicode-bidi: embed;
            direction: ltr;
            display: inline-block;
        }}
        .container {{
            max-width: 100%;
            word-break: break-word;
            margin-bottom: 20px;
        }}
        .btn-container {{
            text-align: center;
            margin-top: 20px;
            padding-bottom: 10px;
        }}
        .btn-close {{
            background-color: #3f3f46;
            color: #e4e4e7;
            border: none;
            padding: 8px 24px;
            font-family: 'Vazirmatn', sans-serif;
            font-size: 13px;
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .btn-close:hover {{
            background-color: #52525b;
        }}
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: #18181b;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #3f3f46;
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #52525b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <pre id="text-content">{highlighted_text}</pre>
    </div>
    <div class="btn-container">
        <button onclick="pywebview.api.close_app()" class="btn-close">بستن</button>
    </div>
    
    <script>
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                pywebview.api.close_app();
            }}
        }});
    </script>
</body>
</html>
"""

# ۵. محاسبه پویای ابعاد پنجره متناسب با حجم متن
text_len = len(text_content)
if text_len < 150:
    width, height = 500, 240
elif text_len < 600:
    width, height = 720, 420
else:
    width, height = 900, 620

# ۶. ساخت پنجره WebView2
window = webview.create_window(
    "(RTL) نمایشگر راست‌چین شده",
    html=html_template,
    width=width,
    height=height,
    resizable=False,
    on_top=True,
    text_select=True,
    background_color="#18181b"
)

# تابع خروج و پاکسازی فونت در پایتون
def close_app():
    if font_loaded:
        ctypes.windll.gdi32.RemoveFontResourceExW(font_path, 0x10, 0)
    window.destroy()

# اکسپوز کردن مستقیم تابع خروج برای جاوااسکریپت
window.expose(close_app)

# ۷. اجرای رسمی وب‌ویو
webview.start()
