import math, subprocess, wave, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

W,H,FPS=720,1280,15
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
  if draw.textbbox((0,0),test,font=f)[2]<=width: line=test
  else:
   if line: out.append(line)
   line=word
 if line: out.append(line)
 return out
def centered(d,s,y,f,fill,width=620,step=None):
 step=step or f.size+9
 for ln in wrap(d,s,f,width):
  tw=d.textbbox((0,0),ln,font=f)[2]
  d.text(((W-tw)//2,y),ln,font=f,fill=fill,stroke_width=2,stroke_fill=(10,18,28)); y+=step
 return y
def gradient(im,top,bottom):
 strip=Image.new("RGB",(1,H)); p=strip.load()
 for y in range(H):
  q=y/(H-1); p[0,y]=tuple(int(top[k]*(1-q)+bottom[k]*q) for k in range(3))
 im.paste(strip.resize((W,H),Image.Resampling.BILINEAR),(0,0))
def workshop(d,t):
 d.polygon([(0,0),(720,0),(720,800),(0,800)],fill=(30,48,66))
 d.polygon([(0,780),(720,780),(720,1280),(0,1280)],fill=(43,58,70))
 for x in (75,360,645):
  d.polygon([(x-10,0),(x+10,0),(x+70,760),(x-70,760)],fill=(39,61,78))
  d.rounded_rectangle((x-65,60,x+65,79),radius=8,fill=(111,195,222))
  d.ellipse((x-30,48,x+30,91),fill=(67,126,154))
 for y in (180,330,480,630): d.line((0,y,720,y),fill=(53,78,94),width=3)
 d.rounded_rectangle((18,500,145,790),radius=14,fill=(23,39,52),outline=(91,125,143),width=4)
 d.rounded_rectangle((570,490,700,790),radius=14,fill=(23,39,52),outline=(91,125,143),width=4)
 for y in (550,615,680,745): d.line((38,y,125,y),fill=(85,111,128),width=4)
 for x in range(-400,1200,160): d.line((360,790,x,1280),fill=(61,81,93),width=2)
 for y in (900,1030,1160): d.line((0,y,720,y),fill=(58,77,89),width=2)
 # floating dust motes give the frame a little life
 for i in range(24):
  x=(i*97+int(t*(12+i%4)*7))%720; y=(i*71+int(t*(8+i%3)*5))%880; r=2+i%3
  d.ellipse((x-r,y-r,x+r,y+r),fill=(105,159,178) if i%2 else (217,173,113))
def draw_car(d,x,y,t,scale=1):
 y+=int(7*math.sin(t*3))
 d.ellipse((x-200*scale,y+66*scale,x+200*scale,y+110*scale),fill=(19,28,37))
 d.rounded_rectangle((x-190*scale,y-45*scale,x+190*scale,y+65*scale),radius=int(42*scale),fill=(194,72,48),outline=(255,205,160),width=max(2,int(5*scale)))
 d.polygon([(x-120*scale,y-42*scale),(x-62*scale,y-112*scale),(x+80*scale,y-112*scale),(x+142*scale,y-42*scale)],fill=(225,111,70),outline=(255,216,177))
 d.polygon([(x-88*scale,y-52*scale),(x-48*scale,y-99*scale),(x+2*scale,y-99*scale),(x+2*scale,y-52*scale)],fill=(91,157,178))
 d.polygon([(x+12*scale,y-99*scale),(x+72*scale,y-99*scale),(x+112*scale,y-52*scale),(x+12*scale,y-52*scale)],fill=(91,157,178))
 for wx in (x-112*scale,x+112*scale):
  d.ellipse((wx-39*scale,y+28*scale,wx+39*scale,y+106*scale),fill=(15,22,29),outline=(215,220,217),width=max(2,int(5*scale)))
  d.ellipse((wx-20*scale,y+48*scale,wx+20*scale,y+88*scale),fill=(123,149,157))
  for q in range(4):
   an=q*math.pi/2+t*2
   xx=wx+int(13*scale*math.cos(an)); yy=y+68*scale+int(13*scale*math.sin(an))
   d.ellipse((xx-3,yy-3,xx+3,yy+3),fill=(239,242,235))
 for ex in (x-42*scale,x+27*scale):
  d.ellipse((ex,y-86*scale,ex+27*scale,y-55*scale),fill=(255,255,240))
  d.ellipse((ex+9*scale,y-78*scale,ex+20*scale,y-59*scale),fill=(19,30,40))
 if int(t*7)%2==0: d.ellipse((x-18*scale,y-39*scale,x+22*scale,y-23*scale),fill=(70,22,29))
 else: d.arc((x-18*scale,y-42*scale,x+22*scale,y-22*scale),0,180,fill=(70,22,29),width=3)
 d.ellipse((x+145*scale,y-12*scale,x+180*scale,y+12*scale),fill=(255,221,145))
def draw_mechanic(d,x,y,t,talking=False,gesture=0):
 y+=int(5*math.sin(t*3))
 d.ellipse((x-48,y-66,x+48,y+32),fill=(229,177,143),outline=(255,220,188),width=3)
 d.pieslice((x-52,y-83,x+52,y+20),180,360,fill=(34,49,62),outline=(12,22,31),width=3)
 d.rounded_rectangle((x-55,y-57,x+55,y-39),radius=8,fill=(40,62,77))
 for ex in (x-27,x+10): d.ellipse((ex,y-20,ex+13,y-5),fill=(23,31,39))
 if talking and int(t*7)%2==0: d.ellipse((x-12,y+2,x+14,y+22),fill=(104,34,41))
 else: d.arc((x-14,y+2,x+14,y+22),0,180,fill=(104,34,41),width=3)
 d.rounded_rectangle((x-57,y+26,x+57,y+190),radius=22,fill=(40,103,137),outline=(159,208,220),width=4)
 d.line((x-34,y+60,x+34,y+60),fill=(220,229,220),width=3)
 ay=y+94+int(18*math.sin(t*4))
 if gesture%2==0:
  d.line((x+38,y+65,x+82,ay,x+120,ay-24),fill=(229,177,143),width=17)
  d.ellipse((x+108,ay-39,x+136,ay-11),fill=(229,177,143))
 else:
  d.line((x-38,y+65,x-76,ay,x-100,ay-18),fill=(229,177,143),width=17)
  d.ellipse((x-115,ay-33,x-87,ay-5),fill=(229,177,143))
def title_card(d,title,t):
 f=font(36,True); yy=125
 for line in wrap(d,title,f,640):
  tw=d.textbbox((0,0),line,font=f,stroke_width=2)[2]; xx=(W-tw)//2
  d.text((xx+3,yy+5),line,font=f,fill=(7,14,21),stroke_width=5,stroke_fill=(7,14,21))
  d.text((xx,yy),line,font=f,fill=(255,248,230),stroke_width=2,stroke_fill=(30,42,54)); yy+=47
def make_frame(idx,title,caption,kind,t,speaker):
 im=Image.new("RGB",(W,H)); gradient(im,(28,47,65),(66,87,98)); d=ImageDraw.Draw(im)
 workshop(d,t)
 bob=int(7*math.sin(t*3))
 if kind=="road":
  d.polygon([(0,820),(720,820),(720,970),(0,970)],fill=(35,49,60))
  for k in range(5):
   xx=(k*190+int(t*100))%850-60; d.line((xx,835,xx+75,835),fill=(240,189,103),width=5)
  draw_car(d,250,660+bob,t,.72); draw_mechanic(d,555,520+bob,t,speaker=="mech",0)
  centered(d,"МАШИНУ УВОДИТ В СТОРОНУ",865,font(20,True),(255,205,135),540,26)
 elif kind=="mechanic":
  draw_car(d,235,650+bob,t,.64); draw_mechanic(d,525,520+bob,t,speaker=="mech",int(t*2)%2)
  centered(d,"СНАЧАЛА — ПРОВЕРКА ХОДОВОЙ",865,font(19,True),(170,224,244),560,25)
 elif kind in ("camber","angles"):
  names=["РАЗВАЛ","СХОЖДЕНИЕ","КАСТЕР"] if kind=="angles" else ["РАЗВАЛ"]
  for j,label in enumerate(names):
   cx=120+j*240 if kind=="angles" else 360
   d.rounded_rectangle((cx-100,405,cx+100,805),radius=22,fill=(30,55,73),outline=(119,177,198),width=4)
   f=font(17,True); tw=d.textbbox((0,0),label,font=f)[2]; d.text((cx-tw/2,425),label,font=f,fill=(255,215,154))
   d.line((cx,500,cx,735),fill=(225,239,239),width=4)
   if label=="РАЗВАЛ":
    z=18*math.sin(t*1.8); d.line((cx-35+z,535,cx-55+z,720),fill=(255,167,103),width=28); d.line((cx+35-z,535,cx+55-z,720),fill=(255,167,103),width=28)
    d.arc((cx-92,560,cx+92,740),260,350,fill=(116,223,181),width=5)
   elif label=="СХОЖДЕНИЕ":
    z=18*math.sin(t*2); d.line((cx-48+z,520,cx-65+z,730),fill=(255,167,103),width=25); d.line((cx+48-z,520,cx+65-z,730),fill=(255,167,103),width=25)
    d.line((cx-78,515,cx+78,515),fill=(116,223,181),width=4)
   else:
    d.line((cx-45,715,cx+32,525),fill=(255,167,103),width=26); d.arc((cx-80,620,cx+82,790),205,300,fill=(116,223,181),width=6)
  centered(d,"СХЕМА УГЛОВ УСТАНОВКИ КОЛЁС",850,font(18,True),(170,224,244),570,25)
 elif kind=="stand":
  d.rounded_rectangle((78,750,642,815),radius=18,fill=(28,41,51),outline=(112,156,177),width=3)
  draw_car(d,360,655+bob,t,.72)
  for x in (205,515):
   d.rounded_rectangle((x-34,490,x+34,755),radius=12,fill=(35,83,110),outline=(170,218,230),width=4)
   d.rounded_rectangle((x-24,555,x+24,620),radius=8,fill=(211,231,231),outline=(67,126,155),width=3)
  for k in range(4):
   yy=470+k*55+int(8*math.sin(t*3+k)); d.line((165,yy,555,yy),fill=(76,192,237),width=3)
  draw_mechanic(d,600,510+bob,t,speaker=="mech",0)
  centered(d,"3D-ИЗМЕРЕНИЕ И СРАВНЕНИЕ С НОРМОЙ",865,font(17,True),(170,224,244),560,24)
 else:
  draw_car(d,360,660+bob,t,.82)
  d.ellipse((270,475,450,655),outline=(104,223,165),width=7)
  if int(t*2)%2==0: d.line((315,560,350,595,410,525),fill=(104,223,165),width=12)
  draw_mechanic(d,570,525+bob,t,speaker=="mech",1)
  centered(d,"ПРОВЕРКА РЕЗУЛЬТАТА",865,font(21,True),(151,239,185),450,26)
 title_card(d,title,t)
 d.rounded_rectangle((38,970,W-38,1195),radius=24,fill=(17,31,44),outline=(95,143,166),width=3)
 label="АВТОМОБИЛЬ" if speaker=="car" else "МЕХАНИК"
 col=(255,198,124) if speaker=="car" else (144,220,245)
 d.rounded_rectangle((58,945,265,980),radius=12,fill=(39,65,83)); d.text((75,952),label,font=font(16,True),fill=col)
 centered(d,caption,1000,font(19),(246,247,239),580,31)
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
