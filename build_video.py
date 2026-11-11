import os, subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
OUT = Path("output")
OUT.mkdir(exist_ok=True)

topic = Path("content/topic.txt").read_text(encoding="utf-8")
address = "Липецкая область, г. Грязи, ул. Чайковского, д. 3"
phone = "+7 (4742) 90-69-07"

slides = [
    ("АВТОПАРТНЕР", "Развал-схождение\nи диагностика ходовой"),
    ("МАШИНУ УВОДИТ В СТОРОНУ?", "Руль стоит неровно?\nШины изнашиваются неравномерно?"),
    ("НАЧИНАЕМ С ПРОВЕРКИ", "Сначала проверяем состояние\nподвески и рулевых элементов"),
    ("3D-РАЗВАЛ-СХОЖДЕНИЕ", "Измеряем углы установки колёс\nна диагностическом стенде"),
    ("ТОЧНАЯ РЕГУЛИРОВКА", "Проверяем параметры и выполняем\nнеобходимую регулировку"),
    ("ЗАПИШИТЕСЬ НА ДИАГНОСТИКУ", f"{address}\n{phone}"),
]

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def render_card(title, body, idx):
    im = Image.new("RGB", (W, H), (12, 19, 31))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((55, 65, W-55, H-65), radius=48, outline=(67, 145, 220), width=6)
    d.rounded_rectangle((90, 130, W-90, 155), radius=12, fill=(67, 145, 220))
    d.text((100, 250), f"ООО «АВТОПАРТНЕР»  •  {idx:02d}/{len(slides):02d}", font=font(34, True), fill=(140, 190, 235))
    y = 600
    for line in textwrap.wrap(title, width=22):
        box = d.textbbox((0,0), line, font=font(76, True))
        d.text(((W-(box[2]-box[0]))/2, y), line, font=font(76, True), fill=(255,255,255))
        y += 100
    y += 65
    for para in body.splitlines():
        for line in textwrap.wrap(para, width=27):
            box = d.textbbox((0,0), line, font=font(48))
            d.text(((W-(box[2]-box[0]))/2, y), line, font=font(48), fill=(210,222,236))
            y += 70
        y += 20
    d.text((100, H-210), "УСЛОВИЯ И СТОИМОСТЬ УТОЧНЯЙТЕ ПО ТЕЛЕФОНУ", font=font(25, True), fill=(150,170,190))
    path = OUT / f"slide_{idx:02d}.png"
    im.save(path)
    return path

def run(cmd):
    subprocess.run(cmd, check=True)

clips = []
for i, (title, body) in enumerate(slides, 1):
    img = render_card(title, body, i)
    audio = OUT / f"voice_{i:02d}.wav"
    speech = (title + ". " + body.replace("\n", ". ")).replace("«","").replace("»","")
    subprocess.run(["espeak-ng", "-v", "ru", "-s", "145", "-w", str(audio), speech], check=True)
    clip = OUT / f"clip_{i:02d}.mp4"
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-i", str(audio),
         "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "128k",
         "-pix_fmt", "yuv420p", "-shortest", "-vf", "scale=1080:1920", str(clip)])
    clips.append(clip)

concat = OUT / "concat.txt"
concat.write_text("".join(f"file '{p.resolve()}'\n" for p in clips), encoding="utf-8")
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
     "-c", "copy", "-movflags", "+faststart", "autopartner_promo.mp4"])
print("Created output/autopartner_promo.mp4")
