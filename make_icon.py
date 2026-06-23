"""
ساخت آیکون اختصاصی RTL View به‌صورت برنامه‌ای.
طرح: مربع تیره گوشه‌گرد (تم #18181b) + خطوط افقی راست‌چین (نماد متن RTL)،
یک خط کهربایی به‌عنوان رنگ تأکید. خروجی: assets/icon.ico (چندسایزه) + پیش‌نمایش PNG.
اجرا:  python make_icon.py
"""
import os
from PIL import Image, ImageDraw

S = 256                      # اندازه‌ی مرجع
SS = 4                       # ضریب super-sampling برای لبه‌های نرم
W = S * SS

img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# پس‌زمینه‌ی مربع گوشه‌گرد (zinc-900)
margin = 10 * SS
radius = 58 * SS
d.rounded_rectangle([margin, margin, W - margin, W - margin], radius=radius, fill="#18181b")

# قاب نازک روشن برای جداسازی از پس‌زمینه‌های تیره
d.rounded_rectangle([margin, margin, W - margin, W - margin], radius=radius, outline="#3f3f46", width=2 * SS)

# خطوط متن، راست‌چین (لبه‌ی راست ثابت، عرض‌های متفاوت → شبیه متن RTL)
right = (S - 56) * SS
bar_h = 26 * SS
gap = 22 * SS
top = 64 * SS

# (عرض خط, رنگ)
bars = [
    (132, "#e4e4e7"),
    (104, "#fbbf24"),   # خط تأکید کهربایی
    (148, "#e4e4e7"),
    (88,  "#e4e4e7"),
]

y = top
for width, color in bars:
    x_left = right - width * SS
    d.rounded_rectangle([x_left, y, right, y + bar_h], radius=bar_h // 2, fill=color)
    y += bar_h + gap

# کوچک‌سازی با کیفیت بالا
icon = img.resize((S, S), Image.LANCZOS)

os.makedirs("assets", exist_ok=True)
icon.save(
    os.path.join("assets", "icon.ico"),
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
icon.save(os.path.join("assets", "icon_preview.png"))
print("ساخته شد: assets/icon.ico و assets/icon_preview.png")
