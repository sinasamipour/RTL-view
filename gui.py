import os
import sys
import re
import html
import base64
import ctypes
import webview

# تابع متمایز کردن کلمات انگلیسی (هایلایت درون‌خطی) با مارکرهای موقت جهت جلوگیری از به هم ریختگی HTML
def highlight_inline(raw_text):
    start_marker = "@@ENG_START@@"
    end_marker = "@@ENG_END@@"

    # حذف هرگونه مارکر از پیش موجود در ورودی کاربر تا با مارکرهای داخلی تداخل نکند
    # (مقاوم‌سازی در برابر دستکاری عمدی متن ورودی و خرابی تگ‌های code)
    raw_text = raw_text.replace(start_marker, "").replace(end_marker, "")

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


# ----- تشخیص جدول در متن -----
# نکته: لیست‌ها (بولت/شماره‌دار) عمداً به ساختار HTML تبدیل نمی‌شوند و مثل متن عادی نمایش
# داده می‌شوند؛ چون هنگام کپی از مرورگرها نشانه‌های لیست اغلب در کلیپ‌بورد قرار نمی‌گیرند و
# نمایش متنی ساده برای کاربر خواناتر است. فقط جدول‌ها برای حفظ هم‌ترازی جدا رندر می‌شوند.

# کاراکترهای رسم خط (Box Drawing) که در جدول‌ها و خط‌کش‌های ترمینال استفاده می‌شوند
_BOX_CHARS = set("│┃─━┌┐└┘├┤┬┴┼╭╮╰╯═║╔╗╚╝╠╣╦╩╬╪╫▏▕")


def _is_table_line(line):
    # خطی که کاراکتر رسم خط داشته باشد، بخشی از جدول/خط‌کش است
    if any(ch in _BOX_CHARS for ch in line):
        return True
    # ردیف جدول مارک‌داون: خطی که با | شروع شود و حداقل دو خط عمودی داشته باشد
    s = line.strip()
    if s.startswith('|') and s.count('|') >= 2:
        return True
    return False


def render_content(raw_text):
    """متن خام را به HTML تبدیل می‌کند. بلوک‌های جدول با فونت monospace رندر می‌شوند تا
    هم‌ترازی ستون‌ها حفظ شود؛ بقیه‌ی متن (از جمله لیست‌ها) به‌صورت متن عادی و خوانا نمایش داده می‌شود."""
    lines = raw_text.split('\n')
    blocks = []          # فهرست بلوک‌ها به صورت (نوع, [خطوط])
    cur_type = None
    cur_lines = []

    for line in lines:
        # خطوط خالی بلوک فعلی را نمی‌شکنند
        if line.strip() == "":
            if cur_lines:
                cur_lines.append(line)
            continue
        t = 'table' if _is_table_line(line) else 'text'
        if t != cur_type:
            if cur_lines:
                blocks.append((cur_type, cur_lines))
            cur_type, cur_lines = t, [line]
        else:
            cur_lines.append(line)
    if cur_lines:
        blocks.append((cur_type, cur_lines))

    parts = []
    for btype, blines in blocks:
        if btype == 'table':
            # جدول‌ها در بلوک monospace رندر می‌شوند تا هم‌ترازی ستون‌ها حفظ شود (بدون هایلایت)
            content = html.escape('\n'.join(blines))
            parts.append(f'<pre class="table-block">{content}</pre>')
        else:
            # متن عادی با هایلایت کلمات انگلیسی و حفظ شکستگی خطوط
            content = highlight_inline('\n'.join(blines))
            parts.append(f'<pre class="text-block">{content}</pre>')

    return '\n'.join(parts)

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

# ۲. تعیین مسیر فایل موقت کپی‌شده
# مسیر از آرگومان خط فرمان گرفته می‌شود (نام یکتا از سمت AHK) و در صورت نبود، به مسیر پیش‌فرض برمی‌گردد
assets_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "assets"))
if len(sys.argv) > 1:
    temp_file = os.path.realpath(sys.argv[1])
else:
    temp_file = os.path.join(assets_dir, "temp_text.txt")

# اعتبارسنجی مسیر: فایل موقت باید حتماً داخل پوشه‌ی assets باشد
# (جلوگیری از خواندن فایل دلخواه سیستم در صورت دستکاری آرگومان ورودی)
MAX_TEXT_LEN = 20000  # سقف طول متن جهت جلوگیری از مصرف بیش از حد حافظه
text_content = ""
if os.path.commonpath([assets_dir, temp_file]) == assets_dir and os.path.exists(temp_file):
    try:
        with open(temp_file, "r", encoding="utf-8") as f:
            text_content = f.read(MAX_TEXT_LEN + 1)
    except Exception:
        text_content = ""
    finally:
        # حذف قطعی فایل موقت جهت حفظ حریم خصوصی، حتی در صورت بروز خطا
        try:
            os.remove(temp_file)
        except OSError:
            pass

if len(text_content) > MAX_TEXT_LEN:
    text_content = text_content[:MAX_TEXT_LEN] + "\n\n[... متن طولانی بود و کوتاه شد ...]"

if not text_content:
    text_content = "متنی برای نمایش انتخاب نشده است."

text_content = text_content.strip()

# ۳. آماده‌سازی متن: تشخیص ساختار (جدول/لیست) و هایلایت کلمات انگلیسی
highlighted_text = render_content(text_content)

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
        .text-block {{
            margin: 0 0 4px 0;
        }}
        /* جدول‌ها با فونت monospace و چیدمان چپ‌چین رندر می‌شوند تا هم‌ترازی ستون‌ها دقیقاً مثل ترمینال حفظ شود */
        .table-block {{
            font-family: 'Consolas', 'Courier New', monospace;
            white-space: pre;
            direction: ltr;
            text-align: left;
            background-color: #1f1f23;
            border: 1px solid #27272a;
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
            font-size: 13px;
            line-height: 1.45;
            overflow-x: auto;
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
        <div id="text-content">{highlighted_text}</div>
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

# ۶. ساخت پنجره WebView2 (قابل تغییر اندازه توسط کاربر با حداقل ابعاد منطقی)
window = webview.create_window(
    "(RTL) نمایشگر راست‌چین شده",
    html=html_template,
    width=width,
    height=height,
    min_size=(360, 200),
    resizable=True,
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
