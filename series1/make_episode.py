#!/usr/bin/env python3
"""Render episode 1 as an animated illustrated drama with facial motion and a deeper Russian male voice."""
from pathlib import Path
import asyncio, subprocess, math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"output"; WORK=OUT/"work"
W,H,FPS=720,1280,12
OUT.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(n,b=False): return ImageFont.truetype(BOLD if b else FONT,n)
SCENES=[
("В тихом городе Анна приехала в старый дом. Она надеялась начать всё сначала.","НОВАЯ СОСЕДКА","Старый дом. Новая жизнь."),
("Только бы никто не узнал, где я была…","АННА","У неё есть причина скрываться."),
("Добрый вечер. Вы новенькая? Я Андрей, живу напротив.","АНДРЕЙ","Сосед оказался слишком внимательным."),
("Анна крепче сжала старый латунный ключ. На его бородке был странный знак.","СТАРЫЙ КЛЮЧ","Ключ, который всё меняет."),
("Подождите… Откуда у вас этот ключ? Он принадлежал прежним жильцам.","АНДРЕЙ","Он узнал этот ключ."),
("Анна побледнела. Если Андрей знает правду, значит, тайна уже раскрыта.","ЗА ЗАКРЫТОЙ ДВЕРЬЮ","Продолжение следует…"),
]
def run(cmd): subprocess.run(cmd,check=True)
def background():
    im=Image.new("RGB",(W,H)); p=im.load()
    for y in range(H):
        t=y/H; c=(int(10+17*t),int(18+24*t),int(38+30*t))
        for x in range(W): p[x,y]=c
    return im
def face(d,cx,cy,scale,hair,skin,mouth,blink,turn=0):
    # shaded, softly modeled illustrated face with animated eyes and mouth
    d.ellipse((cx-64*scale,cy-78*scale,cx+64*scale,cy+82*scale),fill=(91,59,49))
    d.ellipse((cx-58*scale,cy-78*scale,cx+58*scale,cy+78*scale),fill=skin)
    d.ellipse((cx-56*scale,cy-78*scale,cx+58*scale,cy-25*scale),fill=hair)
    # side locks
    d.polygon([(cx-56*scale,cy-55*scale),(cx-46*scale,cy+30*scale),(cx-63*scale,cy+60*scale)],fill=hair)
    d.polygon([(cx+52*scale,cy-58*scale),(cx+45*scale,cy+38*scale),(cx+63*scale,cy+55*scale)],fill=hair)
    for ex in (-23,23):
        ey=cy-5*scale
        if blink:
            d.line((cx+(ex-9)*scale,ey,cx+(ex+9)*scale,ey),fill=(42,30,27),width=max(2,int(3*scale)))
        else:
            d.ellipse((cx+(ex-8)*scale,ey-5*scale,cx+(ex+8)*scale,ey+6*scale),fill=(245,235,218))
            d.ellipse((cx+(ex-3)*scale,ey-5*scale,cx+(ex+4)*scale,ey+5*scale),fill=(44,38,33))
        d.line((cx+(ex-10)*scale,ey-14*scale,cx+(ex+10)*scale,ey-17*scale),fill=hair,width=max(2,int(4*scale)))
    d.line((cx+turn*scale,cy+2*scale,cx-4*scale+turn*scale,cy+28*scale),fill=(135,87,72),width=max(2,int(3*scale)))
    d.ellipse((cx-7*scale,cy+27*scale,cx+7*scale,cy+34*scale),fill=(164,100,85))
    if mouth:
        d.ellipse((cx-13*scale,cy+48*scale,cx+13*scale,cy+62*scale),fill=(75,28,32))
        d.arc((cx-14*scale,cy+42*scale,cx+14*scale,cy+65*scale),0,180,fill=(240,174,157),width=max(1,int(2*scale)))
    else:
        d.arc((cx-13*scale,cy+44*scale,cx+13*scale,cy+62*scale),5,175,fill=(105,48,46),width=max(2,int(3*scale)))
def draw_frame(i,label,caption,frame,total):
    im=background(); d=ImageDraw.Draw(im)
    t=frame/max(1,total-1)
    # old apartment facade, lit windows and doorway
    d.rectangle((0,280,W,1030),fill=(27,36,57))
    for r in range(4):
        for c in range(5):
            x=28+c*140; y=330+r*145
            col=(238,171,91) if (r+c+i)%3 else (92,130,169)
            d.rectangle((x,y,x+78,y+96),fill=col,outline=(10,16,30),width=7)
            d.line((x+39,y,x+39,y+96),fill=(35,37,47),width=4)
            d.line((x,y+48,x+78,y+48),fill=(35,37,47),width=4)
    d.rectangle((0,950,W,H),fill=(10,15,27))
    d.rectangle((38,415,300,1050),fill=(78,48,39),outline=(175,122,72),width=12)
    d.rectangle((62,440,277,1045),fill=(20,26,40))
    # subtle camera drift and character breathing
    drift=math.sin(t*math.pi*2)*5
    ax=int(205+drift); ay=int(625+math.sin(t*math.pi*2)*3)
    # Anna's coat and shoulders
    d.polygon([(ax-112,ay+76),(ax+112,ay+76),(ax+155,1055),(ax-150,1055)],fill=(104,72,62))
    d.polygon([(ax-35,ay+80),(ax+35,ay+80),(ax+68,945),(ax-70,945)],fill=(205,190,170))
    face(d,ax,ay,1.0,(61,33,29),(222,174,145),frame%8 in (1,2,3),frame%53 in (0,1),int(math.sin(t*6)*2))
    if i>=2:
        bx=int(510-math.sin(t*math.pi*2)*4); by=int(630+math.sin(t*math.pi*2+1)*3)
        d.polygon([(bx-100,by+78),(bx+100,by+78),(bx+125,1055),(bx-125,1055)],fill=(31,43,62))
        face(d,bx,by,0.94,(35,27,24),(190,145,119),frame%7 in (0,1,2),frame%61 in (0,1),int(math.sin(t*5)*2))
    if i>=3:
        d.ellipse((470,845,585,960),outline=(224,174,77),width=15)
        d.line((565,900,675,900),fill=(224,174,77),width=17)
        d.line((640,900,640,935),fill=(224,174,77),width=11)
    d.rounded_rectangle((32,48,688,140),radius=22,fill=(7,12,25))
    d.text((55,74),label,font=font(30,True),fill=(255,205,130))
    d.rounded_rectangle((28,1080,692,1235),radius=24,fill=(5,9,20))
    words=caption.split(); lines=[]; line=""
    for word in words:
        test=(line+" "+word).strip()
        if d.textbbox((0,0),test,font=font(26))[2]>590:
            lines.append(line); line=word
        else: line=test
    if line: lines.append(line)
    for n,ln in enumerate(lines[:3]): d.text((55,1105+n*39),ln,font=font(26),fill=(245,245,245))
    return im
async def make_voice(text,path):
    try:
        import edge_tts
        # One consistent adult male voice; lower pitch and slightly slower delivery.
        await edge_tts.Communicate(text,"ru-RU-DmitryNeural",rate="-7%",pitch="-14Hz",volume="+0%").save(str(path))
        if path.exists() and path.stat().st_size>1000: return
    except Exception as e: print("Neural voice unavailable; offline fallback:",e)
    wav=path.with_suffix(".wav")
    subprocess.run(["espeak-ng","-v","ru+m3","-s","132","-p","28","-w",str(wav),text],check=True)
    run(["ffmpeg","-y","-i",str(wav),"-codec:a","libmp3lame","-qscale:a","4",str(path)])
    wav.unlink(missing_ok=True)
async def main():
    clips=[]
    for i,(line,label,caption) in enumerate(SCENES):
        audio=WORK/f"voice_{i:02d}.mp3"; frames_dir=WORK/f"frames_{i:02d}"
        frames_dir.mkdir(exist_ok=True)
        await make_voice(line,audio)
        dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(audio)],text=True).strip())+0.5
        count=max(24,int(dur*FPS))
        for k in range(count):
            draw_frame(i,label,caption,k,count).save(frames_dir/f"frame_{k:04d}.png")
        video=WORK/f"clip_{i:02d}.mp4"
        run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(frames_dir/"frame_%04d.png"),"-i",str(audio),"-t",f"{dur:.3f}","-vf","scale=720:1280:flags=lanczos,format=yuv420p","-c:v","libx264","-preset","ultrafast","-crf","22","-c:a","aac","-b:a","160k","-shortest",str(video)])
        clips.append(video)
    listing=WORK/"concat.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips),encoding="utf-8")
    final=OUT/"za_zakrytoy_dveryu_ep01.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy","-movflags","+faststart",str(final)])
    print(f"CREATED {final} ({final.stat().st_size} bytes)")
if __name__=="__main__": asyncio.run(main())
