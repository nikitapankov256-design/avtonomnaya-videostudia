#!/usr/bin/env python3
"""Build a free, narrated 2D motion-comic episode with Pillow, edge-tts and FFmpeg."""
from pathlib import Path
import asyncio, subprocess, math, os
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
WORK = OUT / "work"
W, H = 720, 1280
OUT.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

# Dialogue is deliberately short so every line remains readable on a phone.
SCENES = [
    ("ru-RU-SvetlanaNeural", "В тихом городе Анна приехала в старый дом. Она надеялась начать всё сначала.", "НОВАЯ СОСЕДКА", "Старый дом. Новая жизнь."),
    ("ru-RU-SvetlanaNeural", "Только бы никто не узнал, где я была…", "АННА", "У неё есть причина скрываться."),
    ("ru-RU-DmitryNeural", "Добрый вечер. Вы новенькая? Я Андрей, живу напротив.", "АНДРЕЙ", "Сосед оказался слишком внимательным."),
    ("ru-RU-SvetlanaNeural", "Анна крепче сжала старый латунный ключ. На его бородке был странный знак.", "СТАРЫЙ КЛЮЧ", "Ключ, который всё меняет."),
    ("ru-RU-DmitryNeural", "Подождите… Откуда у вас этот ключ? Он принадлежал прежним жильцам.", "АНДРЕЙ", "Он узнал этот ключ."),
    ("ru-RU-SvetlanaNeural", "Анна побледнела. Если Андрей знает правду, значит, тайна уже раскрыта.", "ЗА ЗАКРЫТОЙ ДВЕРЬЮ", "Продолжение следует…"),
]

def gradient():
    im = Image.new("RGB", (W,H)); p=im.load()
    for y in range(H):
        t=y/H
        c=(int(13+15*t), int(23+20*t), int(48+25*t))
        for x in range(W): p[x,y]=c
    return im

def draw_scene(i, label, caption):
    im=gradient(); d=ImageDraw.Draw(im)
    # apartment facade and glowing windows
    d.rectangle((0,300,W,1010), fill=(30,39,62))
    for row in range(4):
        for col in range(5):
            x=35+col*140; y=345+row*145
            glow=(255,190,105) if (row+col+i)%3 else (92,137,183)
            d.rectangle((x,y,x+76,y+95), fill=glow, outline=(13,20,37), width=7)
            d.line((x+38,y,x+38,y+95), fill=(36,39,52), width=4)
            d.line((x,y+48,x+76,y+48), fill=(36,39,52), width=4)
    # street
    d.rectangle((0,930,W,1280), fill=(13,18,31))
    d.ellipse((500,890,850,1100), fill=(37,47,68))
    # doorway
    d.rectangle((45,430,300,1050), fill=(73,45,39), outline=(189,132,72), width=12)
    d.rectangle((68,455,278,1045), fill=(26,30,44))
    # Anna, coat and hair
    ax=220 if i<3 else 265
    d.ellipse((ax-66,560,ax+66,690), fill=(224,173,139))
    d.ellipse((ax-75,540,ax+72,650), fill=(65,35,30))
    d.polygon([(ax-110,700),(ax+110,700),(ax+150,1030),(ax-150,1030)], fill=(166,111,77))
    d.polygon([(ax-38,700),(ax+38,700),(ax+75,930),(ax-72,930)], fill=(226,214,194))
    # Andrey appears from scene 2 onwards
    if i>=2:
        bx=500
        d.ellipse((bx-58,570,bx+58,690), fill=(190,143,116))
        d.ellipse((bx-64,552,bx+62,630), fill=(35,27,25))
        d.polygon([(bx-100,700),(bx+100,700),(bx+125,1035),(bx-125,1035)], fill=(33,43,60))
        d.line((bx-28,625,bx+28,625), fill=(35,25,22), width=6)
    # key motif on close-up scenes
    if i in (3,4,5):
        d.ellipse((480,840,600,960), outline=(225,174,75), width=16)
        d.line((575,900,675,900), fill=(225,174,75), width=18)
        d.line((640,900,640,935), fill=(225,174,75), width=12)
        d.line((665,900,665,925), fill=(225,174,75), width=12)
    # top label and lower caption panel
    d.rounded_rectangle((32,55,688,145), radius=22, fill=(8,13,27))
    d.text((55,78), label, font=font(31,True), fill=(255,205,130))
    d.rounded_rectangle((30,1070,690,1235), radius=24, fill=(5,10,23))
    words=caption.split(); lines=[]; line=""
    for word in words:
        test=(line+" "+word).strip()
        if d.textbbox((0,0),test,font=font(27))[2] > 600:
            lines.append(line); line=word
        else: line=test
    if line: lines.append(line)
    yy=1100
    for ln in lines[:3]:
        d.text((58,yy),ln,font=font(27),fill=(245,245,245)); yy+=42
    return im

async def make_voice(text, voice, path):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate="+2%", volume="+0%").save(str(path))

def run(cmd):
    subprocess.run(cmd, check=True)

async def main():
    clips=[]
    for i,(voice,line,label,caption) in enumerate(SCENES):
        img=WORK/f"scene_{i:02d}.png"; audio=WORK/f"voice_{i:02d}.mp3"; video=WORK/f"clip_{i:02d}.mp4"
        draw_scene(i,label,caption).save(img)
        await make_voice(line,voice,audio)
        # Each panel gets gentle camera movement; audio determines its duration.
        probe=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(audio)],text=True).strip()
        duration=float(probe)+0.45
        frames=max(24,int(duration*24))
        vf=f"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,zoompan=z='min(zoom+0.0007,1.06)':d={frames}:s=720x1280:fps=24,format=yuv420p"
        run(["ffmpeg","-y","-loop","1","-i",str(img),"-i",str(audio),"-vf",vf,"-t",f"{duration:.3f}","-r","24","-c:v","libx264","-preset","ultrafast","-crf","24","-c:a","aac","-b:a","128k","-shortest",str(video)])
        clips.append(video)
    listing=WORK/"concat.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips),encoding="utf-8")
    final=OUT/"za_zakrytoy_dveryu_ep01.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy","-movflags","+faststart",str(final)])
    print(f"CREATED {final} ({final.stat().st_size} bytes)")

if __name__=="__main__":
    asyncio.run(main())
