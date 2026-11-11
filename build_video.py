import math, subprocess, wave, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

W,H,FPS=720,1280,12
OUT=Path("render"); OUT.mkdir(exist_ok=True)

VOICES={"car":"ru-RU-SvetlanaNeural","mech":"ru-RU-DmitryNeural"}
SCENES=[
("Увод в сторону","Мастер, помогите! Машину тянет вправо, а руль стоит криво!","road","car"),
("С чего начать","Такое бывает при нарушении углов установки колёс, но сначала проверим подвеску и рулевые детали.","road","mech"),
("Износ шин","А если шины стираются неравномерно — это тоже сигнал?","mechanic","car"),
("Износ шин","Да. Если одна сторона протектора изнашивается быстрее, нужна диагностика. Но причин бывает несколько.","mechanic","mech"),
("Проверка ходовой","Что вы проверяете до стенда?","mechanic","car"),
("Проверка ходовой","Сайлентблоки, шаровые опоры, рулевые наконечники и другие элементы. Люфты и повреждения сначала устраняют.","mechanic","mech"),
("Что такое развал","Теперь объясните развал. Это наклон колёс?","camber","car"),
("Что такое развал","Верно. Развал — наклон колеса относительно вертикали, если смотреть на автомобиль спереди.","camber","mech"),
("Что такое схождение","А схождение — это когда колёса смотрят в разные стороны?","angles","car"),
("Что такое схождение","Почти. Это угол направления колёс относительно продольной оси автомобиля. Даже небольшие отклонения влияют на износ шин.","angles","mech"),
("Что такое кастер","И что за загадочный кастер?","angles","car"),
("Что такое кастер","Кастер — продольный наклон оси поворота. Он влияет на возврат руля и устойчивость движения.","angles","mech"),
("3D-измерение","Как понять, какие значения правильные?","stand","car"),
("3D-измерение","Измеряем углы на 3D-стенде и сравниваем с данными производителя для конкретной модели и комплектации.","stand","mech"),
("Регулировка","А после измерения сразу крутите регулировки?","finish","car"),
("Регулировка","Сначала учитываем состояние подвески, затем выполняем допустимые регулировки и проверяем результат. Если машину уводит или шины стираются неравномерно — начните с диагностики.","finish","mech")
]
def font(n,b=False):
 p="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if b else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
 return ImageFont.truetype(p,n)
def wrap(draw,s,f,width):
 out=[]; line=""
 for word in s.split():
  test=(line+" "+word).strip()
  if draw.textbbox((0,0),test,font=f)[2] <= width: line=test
  else:
   if line: out.append(line)
   line=word
 if line: out.append(line)
 return out
def centered(d,s,y,f,fill,width=620,step=None):
 step=step or f.size+9
 for ln in wrap(d,s,f,width):
  tw=d.textbbox((0,0),ln,font=f)[2]
  d.text(((W-tw)//2,y),ln,font=f,fill=fill); y+=step
 return y
def car(d,x,y,t,scale=1):
 # body, windows, wheels and expressive face
 d.rounded_rectangle((x-175*scale,y-42*scale,x+175*scale,y+52*scale),radius=int(38*scale),fill=(40,145,210),outline=(225,245,255),width=4)
 d.polygon([(x-105*scale,y-40*scale),(x-58*scale,y-105*scale),(x+70*scale,y-105*scale),(x+120*scale,y-40*scale)],fill=(90,195,225),outline=(240,250,255))
 for wx in (x-112*scale,x+112*scale):
  d.ellipse((wx-34*scale,y+22*scale,wx+34*scale,y+90*scale),fill=(12,18,28),outline=(220,230,240),width=4)
  d.ellipse((wx-13*scale,y+44*scale,wx+13*scale,y+70*scale),fill=(150,190,210))
 for ex in (x-38*scale,x+18*scale):
  d.ellipse((ex,y-82*scale,ex+25*scale,y-55*scale),fill="white")
  d.ellipse((ex+8*scale,y-75*scale,ex+18*scale,y-59*scale),fill=(15,25,40))
 mouth=8+10*abs(math.sin(t*7))
 if int(t*7)%2==0: d.ellipse((x-18*scale,y-53*scale,x+20*scale,y-53*scale+mouth),fill=(70,15,25))
 else: d.arc((x-18*scale,y-53*scale,x+20*scale,y-53*scale+mouth),0,180,fill=(70,15,25),width=4)
def mechanic(d,x,y,t,talking=False):
 d.ellipse((x-48,y-55,x+48,y+42),fill=(235,185,145),outline="white",width=3)
 d.pieslice((x-52,y-75,x+52,y+20),180,360,fill=(30,48,65))
 d.rounded_rectangle((x-48,y+35,x+48,y+185),radius=22,fill=(35,95,145),outline="white",width=3)
 d.line((x+25,y+80,x+95,y+35+int(18*math.sin(t*4))),fill=(235,185,145),width=17)
 for ex in (x-25,x+10): d.ellipse((ex,y-10,ex+12,y+4),fill=(20,30,40))
 if talking and int(t*7)%2==0: d.ellipse((x-13,y+5,x+15,y+28),fill=(100,25,35))
 else: d.arc((x-15,y+5,x+15,y+25),0,180,fill=(100,30,35),width=3)
def make_frame(idx,title,caption,kind,t,speaker):
 im=Image.new("RGB",(W,H),(13,23,38)); d=ImageDraw.Draw(im)
 for xx in range(0,W,60): d.line((xx,0,xx,H),fill=(18,33,50))
 for yy in range(0,H,60): d.line((0,yy,W,yy),fill=(18,33,50))
 d.rounded_rectangle((22,22,W-22,H-22),radius=26,outline=(55,130,180),width=3)
 d.rounded_rectangle((45,42,W-45,92),radius=14,fill=(25,52,75))
 d.text((62,55),f"АВТОМОБИЛЬНАЯ АЗБУКА  •  {idx}/16",font=font(18,True),fill=(145,215,255))
 centered(d,title,130,font(34,True),(250,252,255),640,42)
 bob=int(9*math.sin(t*3))
 if kind=="road":
  d.polygon([(0,690),(720,690),(580,420),(140,420)],fill=(43,57,68))
  for k in range(5):
   yy=470+((k*100+int(t*100))%260)
   d.rounded_rectangle((350,yy,365,yy+42),radius=5,fill=(230,230,200))
  car(d,245,620+bob,t,.65)
  mechanic(d,555,510+bob,t,speaker=="mech")
  d.text((140,810),"СИМПТОМ: УВОД В СТОРОНУ",font=font(22,True),fill=(255,195,110))
 elif kind=="mechanic":
  car(d,230,620+bob,t,.58); mechanic(d,510,500+bob,t,speaker=="mech")
  d.text((115,820),"ОСМОТР ПОДВЕСКИ И РУЛЕВЫХ ДЕТАЛЕЙ",font=font(18,True),fill=(145,215,255))
 elif kind in ("camber","angles"):
  labels=["РАЗВАЛ","СХОЖДЕНИЕ","КАСТЕР"] if kind=="angles" else ["НАКЛОН КОЛЕСА"]
  for j,label in enumerate(labels):
   cx=120+j*240 if kind=="angles" else 360
   d.rounded_rectangle((cx-92,410,cx+92,800),radius=18,fill=(22,44,65),outline=(75,150,195),width=3)
   tw=d.textbbox((0,0),label,font=font(17,True))[2]
   d.text((cx-tw/2,430),label,font=font(17,True),fill=(145,215,255))
   if j==0:
    d.line((cx,510,cx,735),fill="white",width=3)
    d.line((cx-35,545,cx-65,700),fill=(255,185,100),width=18)
    d.line((cx+35,545,cx+65,700),fill=(255,185,100),width=18)
   elif j==1:
    d.line((cx-48,520,cx-48,735),fill=(255,185,100),width=18); d.line((cx+48,520,cx+48,735),fill=(255,185,100),width=18)
    d.line((cx-70,520,cx+70,520),fill="white",width=3)
   else:
    d.line((cx,515,cx,735),fill="white",width=3); d.line((cx-48,715,cx+30,525),fill=(255,185,100),width=18)
    d.arc((cx-65,630,cx+70,780),205,300,fill=(100,220,160),width=6)
 elif kind=="stand":
  car(d,360,670+bob,t,.68)
  for x in (220,500):
   d.rounded_rectangle((x-32,520,x+32,745),radius=10,fill=(35,78,105),outline=(140,220,255),width=5)
   d.ellipse((x-18,575,x+18,611),outline=(255,195,100),width=5)
  for k in range(4):
   yy=470+k*55+int(8*math.sin(t*3+k))
   d.line((145,yy,575,yy),fill=(70,185,255),width=3)
  d.text((185,845),"ИЗМЕРЕНИЕ  →  СРАВНЕНИЕ  →  НАСТРОЙКА",font=font(18,True),fill=(145,215,255))
  mechanic(d,585,500+bob,t,speaker=="mech")
 else:
  car(d,360,650+bob,t,.82)
  d.ellipse((285,490,435,640),outline=(100,220,160),width=6)
  d.text((190,850),"КОНТРОЛЬ РЕЗУЛЬТАТА",font=font(24,True),fill=(110,225,165))
 d.rounded_rectangle((45,965,W-45,1195),radius=22,fill=(23,44,64),outline=(65,120,160),width=2)
 centered(d,caption,995,font(19),(230,239,247),590,29)
 speaker_label="МАШИНА ГОВОРИТ" if speaker=="car" else "МАСТЕР ОБЪЯСНЯЕТ"
 d.rounded_rectangle((45,915,675,950),radius=12,fill=(35,65,88))
 d.text((65,922),speaker_label,font=font(17,True),fill=(255,205,120) if speaker=="car" else (145,215,255))
 d.text((55,1220),"ДИАЛОГОВЫЙ ОБУЧАЮЩИЙ МУЛЬТФИЛЬМ",font=font(14,True),fill=(125,160,190))
 return im
def run(cmd,**kw): subprocess.run(cmd,check=True,**kw)
clips=[]
for i,(title,speech,kind,speaker) in enumerate(SCENES,1):
 mp3=OUT/f"voice_{i:02d}.mp3"
 wav=OUT/f"voice_{i:02d}.wav"
 rate="--rate=+5%" if speaker=="car" else "--rate=-4%"
 pitch="--pitch=+3Hz" if speaker=="car" else "--pitch=-2Hz"
 last_error=None
 for attempt in range(4):
  result=subprocess.run(["edge-tts","--voice",VOICES[speaker],rate,pitch,"--text",speech,"--write-media",str(mp3)],capture_output=True,text=True)
  if result.returncode==0 and mp3.exists() and mp3.stat().st_size>3000:
   last_error=None
   break
  last_error=result.stderr or result.stdout or "No audio returned"
  time.sleep(2+attempt*2)
 if last_error:
  print(f"Edge neural voice unavailable for {speaker}; switching to free Google TTS fallback")
  gTTS(text=speech,lang="ru",slow=(speaker=="mech")).save(str(mp3))
 if speaker=="mech" and last_error is not None:
  run(["ffmpeg","-y","-loglevel","error","-i",str(mp3),"-af","asetrate=21600,aresample=24000,atempo=1.111","-ar","24000","-ac","1",str(wav)])
 else:
  run(["ffmpeg","-y","-loglevel","error","-i",str(mp3),"-ar","24000","-ac","1",str(wav)])
 with wave.open(str(wav),"rb") as w: seconds=w.getnframes()/w.getframerate()
 n=max(42,int((seconds+0.9)*FPS))
 frames=OUT/f"frames_{i:02d}"; frames.mkdir(exist_ok=True)
 for k in range(n):
  make_frame(i,title,speech,kind,k/FPS,speaker).save(frames/f"f_{k:05d}.png")
 clip=OUT/f"scene_{i:02d}.mp4"
 run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",str(frames/"f_%05d.png"),"-i",str(wav),"-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest",str(clip)])
 clips.append(clip)
lst=OUT/"concat.txt"; lst.write_text("".join(f"file '{p.resolve()}'\n" for p in clips),encoding="utf-8")
run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c","copy","-movflags","+faststart","autopromo_explainer.mp4"])
print("Created autopromo_explainer.mp4")
