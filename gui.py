import os
import sys
import re
import html
import base64
import ctypes
import secrets
from html.parser import HTMLParser
import webview


# ----- پاک‌سازی (Sanitize) امن HTML دریافتی از کلیپ‌بورد -----
# محتوای HTML کلیپ‌بورد «نامطمئن» است (هر برنامه/سایتی می‌تواند آن را پر کند). پس پیش از رندر
# باید با فهرست‌سفید سخت‌گیرانه پاک‌سازی شود: فقط تگ‌های ساختاری امن مجاز و همه‌ی صفت‌ها حذف.
# این کار از اجرای اسکریپت، هندلرهای رویداد و بارگذاری منابع خارجی جلوگیری می‌کند.

# تگ‌های ساختاری مجاز (بدون هیچ صفتی؛ بدون script/style/iframe/img/a/link و ...)
_ALLOWED_TAGS = {
    "p", "br", "hr", "div", "span",
    "ul", "ol", "li",
    "table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
    "strong", "b", "em", "i", "u", "s", "code", "pre", "kbd",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
}
# تگ‌هایی که محتوای داخلشان باید کاملاً دور ریخته شود (نه فقط خود تگ)
_DROP_CONTENT_TAGS = {"script", "style", "head", "title", "meta", "link", "iframe", "object", "embed"}


class _HTMLSanitizer(HTMLParser):
    """یک پاک‌کننده‌ی فهرست‌سفیدی: فقط تگ‌های مجاز را نگه می‌دارد، همه‌ی صفت‌ها را حذف می‌کند،
    محتوای متنی را اسکیپ می‌کند، و محتوای تگ‌های خطرناک را کاملاً دور می‌ریزد."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self._skip_depth = 0  # عمق تو در توی تگ‌هایی که محتوایشان باید نادیده گرفته شود

    def handle_starttag(self, tag, attrs):
        if tag in _DROP_CONTENT_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in _ALLOWED_TAGS:
            self.out.append(f"<{tag}>")  # هیچ صفتی منتقل نمی‌شود

    def handle_startendtag(self, tag, attrs):
        if self._skip_depth or tag in _DROP_CONTENT_TAGS:
            return
        if tag in _ALLOWED_TAGS:
            self.out.append("<br>" if tag == "br" else f"<{tag}></{tag}>")

    def handle_endtag(self, tag):
        if tag in _DROP_CONTENT_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in _ALLOWED_TAGS and tag not in ("br", "hr"):
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if self._skip_depth:
            return
        self.out.append(html.escape(data))

    def result(self):
        return "".join(self.out)


def sanitize_html(raw_html):
    """HTML نامطمئن را با فهرست‌سفید پاک‌سازی می‌کند. در صورت در دسترس بودن کتابخانه‌ی nh3
    (پیاده‌سازی Rust/Ammonia) از آن استفاده می‌شود؛ وگرنه به پاک‌کننده‌ی داخلی استاندارد برمی‌گردد."""
    try:
        import nh3  # اختیاری: در صورت نصب، تضمین امنیتی قوی‌تری می‌دهد
        return nh3.clean(
            raw_html,
            tags=_ALLOWED_TAGS,
            attributes={},          # هیچ صفتی مجاز نیست
            link_rel=None,
            url_schemes=set(),      # هیچ URLی مجاز نیست
        )
    except ImportError:
        parser = _HTMLSanitizer()
        parser.feed(raw_html)
        parser.close()
        return parser.result()


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

# مسیر منابع همراه برنامه؛ هم در حالت توسعه و هم در حالت بسته‌بندی‌شده (PyInstaller) کار می‌کند
def resource_path(rel_path):
    # در حالت فریزشده، PyInstaller منابع را در sys._MEIPASS قرار می‌دهد
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)


# پوشه‌ی داده‌ی قابل‌نوشتن کاربر (هماهنگ با اسکریپت AHK): %LOCALAPPDATA%\RTLView
def user_data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "RTLView")


# ۱. بارگذاری فونت اختصاصی وزیر و تبدیل آن به Base64 جهت لود بدون مشکل در WebView
font_path = resource_path(os.path.join("assets", "Vazirmatn-Medium.ttf"))
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
data_dir = os.path.realpath(user_data_dir())
if len(sys.argv) > 1:
    temp_file = os.path.realpath(sys.argv[1])
else:
    temp_file = os.path.join(data_dir, "temp_text.txt")

# اعتبارسنجی مسیر: فایل موقت باید حتماً داخل پوشه‌ی داده‌ی کاربر باشد
# (جلوگیری از خواندن فایل دلخواه سیستم در صورت دستکاری آرگومان ورودی)
MAX_TEXT_LEN = 20000     # سقف طول متن قابل‌نمایش
MAX_RAW_LEN = 200000     # سقف خواندن خام (HTML با تگ‌ها حجیم‌تر است)
raw_payload = ""
if os.path.isdir(data_dir) and os.path.commonpath([data_dir, temp_file]) == data_dir and os.path.exists(temp_file):
    try:
        # utf-8-sig یک BOM احتمالی در ابتدای فایل را خودکار حذف می‌کند
        with open(temp_file, "r", encoding="utf-8-sig") as f:
            raw_payload = f.read(MAX_RAW_LEN + 1)
    except Exception:
        raw_payload = ""
    finally:
        # حذف قطعی فایل موقت جهت حفظ حریم خصوصی، حتی در صورت بروز خطا
        try:
            os.remove(temp_file)
        except OSError:
            pass


def split_mode(raw):
    """خط اول می‌تواند حالت را مشخص کند (MODE=HTML یا MODE=TEXT). در غیر این صورت کل
    محتوا متن ساده در نظر گرفته می‌شود (سازگاری با نسخه‌های قدیمی‌تر اسکریپت)."""
    nl = raw.find("\n")
    if nl != -1:
        first = raw[:nl].strip()
        if first == "MODE=HTML":
            return "HTML", raw[nl + 1:]
        if first == "MODE=TEXT":
            return "TEXT", raw[nl + 1:]
    return "TEXT", raw


mode, body = split_mode(raw_payload)

# ۳. آماده‌سازی محتوا بر اساس حالت
if mode == "HTML" and body.strip():
    # حالت HTML: پاک‌سازی امن و رندر ساختار واقعی (لیست‌ها و جدول‌ها)
    safe_html = sanitize_html(body)
    # طول متن قابل‌مشاهده (بدون تگ) برای محاسبه‌ی ابعاد پنجره
    visible_text = re.sub(r"<[^>]+>", "", safe_html)
    text_content = html.unescape(visible_text).strip() or " "
    highlighted_text = f'<div class="html-content">{safe_html}</div>'
else:
    # حالت متن ساده: تشخیص جدول و هایلایت کلمات انگلیسی
    text_content = body
    if len(text_content) > MAX_TEXT_LEN:
        text_content = text_content[:MAX_TEXT_LEN] + "\n\n[... متن طولانی بود و کوتاه شد ...]"
    if not text_content.strip():
        text_content = "متنی برای نمایش انتخاب نشده است."
    text_content = text_content.strip()
    highlighted_text = render_content(text_content)

# ۴. ساخت قالب HTML با موتور رندرینگ بی نقص وب
html_template = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <!-- لایه‌ی امنیتی دوم: حتی اگر چیزی از فیلتر sanitize عبور کند، CSP بارگذاری منابع خارجی و
         ارسال داده به بیرون را مسدود می‌کند (default-src none) و فقط فونت/تصویر data: مجاز است -->
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; font-src data:; img-src data:;">
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
        /* استایل محتوای HTML پاک‌سازی‌شده‌ی کلیپ‌بورد: لیست‌ها و جدول‌های واقعی و راست‌چین */
        .html-content ul, .html-content ol {{
            margin: 8px 0;
            padding-right: 26px;
            padding-left: 0;
        }}
        .html-content li {{
            margin: 5px 0;
            line-height: 1.7;
        }}
        .html-content li::marker {{
            color: #fbbf24;
        }}
        .html-content p {{
            margin: 7px 0;
        }}
        .html-content table {{
            border-collapse: collapse;
            margin: 10px 0;
            max-width: 100%;
        }}
        .html-content th, .html-content td {{
            border: 1px solid #3f3f46;
            padding: 6px 12px;
            text-align: right;
        }}
        .html-content th {{
            background-color: #27272a;
            font-weight: 700;
        }}
        .html-content pre {{
            background-color: #1f1f23;
            border: 1px solid #27272a;
            border-radius: 6px;
            padding: 12px;
            overflow-x: auto;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
        }}
        .html-content blockquote {{
            border-right: 3px solid #3f3f46;
            margin: 8px 0;
            padding: 4px 14px;
            color: #a1a1aa;
        }}
        .html-content h1, .html-content h2, .html-content h3,
        .html-content h4, .html-content h5, .html-content h6 {{
            margin: 10px 0 6px 0;
            line-height: 1.4;
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
