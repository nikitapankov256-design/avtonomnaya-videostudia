import math, subprocess, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W,H,FPS=720,1280,12
OUT=Path("render"); OUT.mkdir(exist_ok=True)
MODEL="voices/ru_RU-irina-medium.onnx"
SCENES=[
("Машину уводит в сторону?","Вы едете прямо, а автомобиль постепенно тянет вправо или влево. Руль приходится постоянно поправлять. Иногда это связано с углами установки колёс, но причин может быть несколько. Не стоит гадать — важно начать с диагностики.", "road"),
("Сначала — осмотр ходовой","Я — механик, и сначала проверю подвеску и рулевые элементы. Нет ли люфтов, повреждений и изношенных деталей? Если есть неисправность, её нужно устранить до регулировки. Иначе измерения не дадут правильного результата.", "mechanic"),
("Что такое развал?","Развал — это наклон колеса, если смотреть на автомобиль спереди. Представьте две линии: колёса могут быть слегка наклонены внутрь или наружу. Важны точные значения, предусмотренные производителем именно для вашей машины.", "camber"),
("А схождение и кастер?","Схождение показывает, куда направлены колёса, если смотреть сверху: немного внутрь или наружу. Кастер — наклон оси поворота колеса сбоку. Он влияет на устойчивость автомобиля и возврат руля после поворота.", "angles"),
("Измеряем и регулируем","Когда ходовая исправна, автомобиль устанавливают на стенд 3D-развал-схождения. Специальные мишени помогают измерить положение колёс. Мастер сравнивает данные с заводскими параметрами и при необходимости выполняет регулировку.", "stand"),
("Проверяем результат","После настройки проверяют итоговые значения и поведение автомобиля в движении. Неравномерный износ шин, увод машины или криво стоящий руль — повод обратиться на диагностику. Берегите себя и не откладывайте проверку.", "finish")
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
 d.arc((x-18*scale,y-53*scale,x+20*scale,y-53*scale+mouth),0,180,fill=(70,15,25),width=4)
def mechanic(d,x,y,t):
 d.ellipse((x-48,y-55,x+48,y+42),fill=(235,185,145),outline="white",width=3)
 d.pieslice((x-52,y-75,x+52,y+20),180,360,fill=(30,48,65))
 d.rounded_rectangle((x-48,y+35,x+48,y+185),radius=22,fill=(35,95,145),outline="white",width=3)
 d.line((x+25,y+80,x+95,y+35+int(18*math.sin(t*4))),fill=(235,185,145),width=17)
 for ex in (x-25,x+10): d.ellipse((ex,y-10,ex+12,y+4),fill=(20,30,40))
 d.arc((x-15,y+5,x+15,y+25),0,180,fill=(100,30,35),width=3)
def make_frame(idx,title,caption,kind,t):
 im=Image.new("RGB",(W,H),(13,23,38)); d=ImageDraw.Draw(im)
 for xx in range(0,W,60): d.line((xx,0,xx,H),fill=(18,33,50))
 for yy in range(0,H,60): d.line((0,yy,W,yy),fill=(18,33,50))
 d.rounded_rectangle((22,22,W-22,H-22),radius=26,outline=(55,130,180),width=3)
 d.rounded_rectangle((45,42,W-45,92),radius=14,fill=(25,52,75))
 d.text((62,55),f"АВТОМОБИЛЬНАЯ АЗБУКА  •  {idx}/6",font=font(18,True),fill=(145,215,255))
 centered(d,title,130,font(34,True),(250,252,255),640,42)
 bob=int(9*math.sin(t*3))
 if kind=="road":
  d.polygon([(0,690),(720,690),(580,420),(140,420)],fill=(43,57,68))
  for k in range(5):
   yy=470+((k*100+int(t*100))%260)
   d.rounded_rectangle((350,yy,365,yy+42),radius=5,fill=(230,230,200))
  car(d,360,620+bob,t,.85)
  d.text((140,810),"СИМПТОМ: УВОД В СТОРОНУ",font=font(22,True),fill=(255,195,110))
 elif kind=="mechanic":
  car(d,230,620+bob,t,.58); mechanic(d,510,500+bob,t)
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
 else:
  car(d,360,650+bob,t,.82)
  d.ellipse((285,490,435,640),outline=(100,220,160),width=6)
  d.text((190,850),"КОНТРОЛЬ РЕЗУЛЬТАТА",font=font(24,True),fill=(110,225,165))
 d.rounded_rectangle((45,965,W-45,1195),radius=22,fill=(23,44,64),outline=(65,120,160),width=2)
 centered(d,caption,995,font(19),(230,239,247),590,29)
 d.text((55,1220),"ОБУЧАЮЩИЙ МУЛЬТФИЛЬМ",font=font(14,True),fill=(125,160,190))
 return im
def run(cmd,**kw): subprocess.run(cmd,check=True,**kw)
clips=[]
for i,(title,speech,kind) in enumerate(SCENES,1):
 wav=OUT/f"voice_{i:02d}.wav"
 run(["piper","--model",MODEL,"--output_file",str(wav)],input=speech.encode("utf-8"))
 with wave.open(str(wav),"rb") as w: seconds=w.getnframes()/w.getframerate()
 n=max(36,int((seconds+0.5)*FPS))
 frames=OUT/f"frames_{i:02d}"; frames.mkdir(exist_ok=True)
 for k in range(n):
  make_frame(i,title,speech,kind,k/FPS).save(frames/f"f_{k:05d}.png")
 clip=OUT/f"scene_{i:02d}.mp4"
 run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",str(frames/"f_%05d.png"),"-i",str(wav),"-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest",str(clip)])
 clips.append(clip)
lst=OUT/"concat.txt"; lst.write_text("".join(f"file '{p.resolve()}'\n" for p in clips),encoding="utf-8")
run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c","copy","-movflags","+faststart","autopromo_explainer.mp4"])
print("Created autopromo_explainer.mp4")
