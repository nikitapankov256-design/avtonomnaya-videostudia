import math, subprocess, wave, time, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS=720,1280,18
OUT=Path("render"); OUT.mkdir(exist_ok=True)
# Primary and backup Microsoft neural voices. Keep character voices distinct.
VOICE_POOLS={
 "car":["ru-RU-SvetlanaNeural","ru-RU-DariyaNeural"],
 "mech":["ru-RU-DmitryNeural","ru-RU-PavelNeural"]
}
SCENES=[
("Когда машину уводит","Мастер, почему машину тянет вправо? Я еду прямо, а меня всё время сносит!","road","car"),
("Первый осмотр","Так бывает, когда нарушены углы установки колёс. Но сначала проверяем подвеску и рулевые детали. Нельзя начинать регулировку, пока не убедились, что ходовая исправна.","road","mech"),
("Неровный руль","А если руль стоит криво, хотя дорога ровная?","road","car"),
("Неравномерный износ","Или протектор с одной стороны стирается быстрее?","tires","car"),
("Причины бывают разные","Это важные признаки. Но причина не всегда только в углах: возможны люфты, повреждения подвески или разное давление в шинах.","tires","mech"),
("Проверяем подвеску","Сначала осматриваем шаровые опоры, сайлентблоки, рулевые наконечники, амортизаторы и подшипники. Проверяем люфты и повреждения.","lift","mech"),
("Что такое развал","Хорошо. А что означает развал?","camber","car"),
("Развал простыми словами","Это наклон колеса относительно вертикали, если смотреть на автомобиль спереди. Слишком большой наклон может ускорять износ края шины.","camber","mech"),
("Что такое схождение","А схождение — это направление колёс, если смотреть сверху?","toe","car"),
("Схождение","Именно. Представь две стрелки: их передние края могут быть чуть ближе или дальше друг от друга. Неправильное схождение часто влияет на износ и устойчивость.","toe","mech"),
("И ещё кастер","Остался кастер. Он за что отвечает?","caster","car"),
("Кастер","Это продольный наклон оси поворота колеса. Он влияет на устойчивость автомобиля и на то, как руль возвращается после поворота.","caster","mech"),
("Измерение на 3D-стенде","Как узнать точные значения для моей машины?","stand","car"),
("Точные измерения","Устанавливаем автомобиль на 3D-стенд, фиксируем измерительные мишени и сравниваем показания с параметрами производителя именно для этой модели.","stand","mech"),
("Регулировка","И только после этого выполняете регулировку?","adjust","car"),
("Контроль результата","Да. Регулируем то, что предусмотрено конструкцией, повторно проверяем значения и оцениваем результат. Если машину уводит или шины изнашиваются неравномерно — начни с диагностики.","finish","mech")
]
def font(n,b=False):
 p="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if b else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
 return ImageFont.truetype(p,n)
def wrap(d,s,f,width):
 out=[]; line=""
 for word in s.split():
  test=(line+" "+word).strip()
  if d.textbbox((0,0),test,font=f)[2]<=width: line=test
  else:
   if line: out.append(line)
   line=word
 if line: out.append(line)
 return out
def text_center(d,s,y,f,fill,width=620,stroke=0):
 for ln in wrap(d,s,f,width):
  tw=d.textbbox((0,0),ln,font=f,stroke_width=stroke)[2]
  d.text(((W-tw)//2,y),ln,font=f,fill=fill,stroke_width=stroke,stroke_fill=(22,27,39))
  y+=f.size+10
 return y
def rounded(d,box,r,fill,outline=None,w=1):
 d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=w)
def gradient(im,top,bottom):
 strip=Image.new("RGB",(1,H)); p=strip.load()
 for y in range(H):
  q=y/(H-1); p[0,y]=tuple(int(top[k]*(1-q)+bottom[k]*q) for k in range(3))
 im.paste(strip.resize((W,H),Image.Resampling.BILINEAR),(0,0))
def ellipse_shadow(d,x,y,rx,ry,alpha=65):
 d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=(22,35,48))
def background(kind,t):
 im=Image.new("RGB",(W,H)); gradient(im,(126,177,193),(229,219,194))
 d=ImageDraw.Draw(im)
 # warm illustrated workshop, with soft light panels and perspective floor
 d.rectangle((0,0,W,830),fill=(117,159,174))
 for x in range(3):
  xx=30+x*245
  rounded(d,(xx,100,xx+205,540),14,(165,199,201),(94,137,151),5)
  d.rectangle((xx+12,112,xx+193,520),fill=(190,216,210))
  for y in range(150,510,80):
   d.line((xx+12,y,xx+193,y),fill=(159,190,190),width=3)
 d.rectangle((0,565,W,840),fill=(71,104,119))
 # shelves, tool cabinets, tires, hanging lamps
 rounded(d,(22,620,170,818),16,(43,67,79),(28,48,60),5)
 for yy in (665,720,775): d.line((40,yy,152,yy),fill=(118,148,151),width=5)
 for i in range(3):
  xx=555+i*48
  d.ellipse((xx-25,665,xx+25,735),fill=(33,45,54),outline=(160,174,166),width=5)
  d.ellipse((xx-12,678,xx+12,722),fill=(91,111,116))
 # floor perspective
 d.polygon([(0,830),(720,830),(720,1280),(0,1280)],fill=(164,171,158))
 d.polygon([(0,830),(720,830),(720,880),(0,880)],fill=(198,193,168))
 for x in range(-500,1300,170):
  d.line((360,840,x,1280),fill=(143,153,145),width=2)
 for y in (960,1090,1210): d.line((0,y,720,y),fill=(145,154,145),width=2)
 # warm beams and motes
 overlay=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(overlay)
 od.polygon([(470,0),(610,0),(720,650),(570,650)],fill=(255,238,186,30))
 for i in range(34):
  x=(i*89+int(t*(9+i%5)*5))%W; y=(i*53+int(t*(5+i%4)*4))%800
  rr=1+i%3; od.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(255,244,208,80))
 im=Image.alpha_composite(im.convert("RGBA"),overlay).convert("RGB")
 d=ImageDraw.Draw(im)
 # top right scene label
 label={"road":"СИМПТОМЫ","tires":"ШИНЫ","lift":"ОСМОТР ХОДОВОЙ","camber":"РАЗВАЛ","toe":"СХОЖДЕНИЕ","caster":"КАСТЕР","stand":"3D-ДИАГНОСТИКА","adjust":"РЕГУЛИРОВКА","finish":"КОНТРОЛЬ"}[kind]
 rounded(d,(430,38,690,92),20,(38,52,66))
 d.text((452,51),label,font=font(19,True),fill=(255,240,207))
 return im
def draw_wheel(d,cx,cy,r,angle=0,tilt=0):
 # tire with sidewall, rim, spokes
 d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(28,34,39),outline=(12,18,23),width=5)
 d.ellipse((cx-r+9,cy-r+9,cx+r-9,cy+r-9),fill=(75,83,84),outline=(177,181,166),width=4)
 d.ellipse((cx-r*.52,cy-r*.52,cx+r*.52,cy+r*.52),fill=(186,196,185),outline=(50,65,70),width=5)
 for i in range(8):
  a=angle+i*math.pi/4
  x1=cx+math.cos(a)*r*.13; y1=cy+math.sin(a)*r*.13
  x2=cx+math.cos(a+tilt)*r*.46; y2=cy+math.sin(a+tilt)*r*.46
  d.line((x1,y1,x2,y2),fill=(83,111,119),width=5)
 d.ellipse((cx-r*.13,cy-r*.13,cx+r*.13,cy+r*.13),fill=(65,84,88),outline=(228,225,205),width=3)
def draw_car(d,x,y,t,scale=1,turn=0,blink=False):
 # animated anthropomorphic compact car, suspension bob + wheel rotation
 bob=5*math.sin(t*3.2)
 y+=bob
 ellipse_shadow(d,x,y+100*scale,185*scale,25*scale)
 # body silhouette
 d.polygon([(x-180*scale,y+35*scale),(x-166*scale,y-28*scale),(x-105*scale,y-65*scale),(x-66*scale,y-130*scale),(x+83*scale,y-130*scale),(x+142*scale,y-60*scale),(x+177*scale,y-28*scale),(x+188*scale,y+40*scale),(x+150*scale,y+70*scale),(x-145*scale,y+70*scale)],fill=(210,93,62),outline=(104,52,47))
 d.polygon([(x-105*scale,y-65*scale),(x-59*scale,y-119*scale),(x+76*scale,y-119*scale),(x+124*scale,y-62*scale)],fill=(137,191,196),outline=(244,215,175))
 d.line((x+5*scale,y-115*scale,x+5*scale,y-65*scale),fill=(245,224,186),width=max(2,int(4*scale)))
 d.line((x-160*scale,y-12*scale,x+158*scale,y-12*scale),fill=(247,167,112),width=max(2,int(4*scale)))
 # bumper and lamps
 rounded(d,(x-168*scale,y+24*scale,x+174*scale,y+63*scale),18,(166,69,52),(255,194,145),max(2,int(3*scale)))
 for xx in (x-146*scale,x+135*scale):
  d.ellipse((xx-19*scale,y-4*scale,xx+19*scale,y+20*scale),fill=(255,231,170),outline=(255,249,215),width=2)
 # eyes on windshield, blinking
 for ex in (x-47*scale,x+37*scale):
  if blink:
   d.arc((ex-11*scale,y-103*scale,ex+11*scale,y-78*scale),0,180,fill=(32,47,52),width=max(2,int(4*scale)))
  else:
   d.ellipse((ex-10*scale,y-105*scale,ex+10*scale,y-80*scale),fill=(255,249,222))
   d.ellipse((ex-4*scale,y-100*scale,ex+6*scale,y-83*scale),fill=(32,46,53))
 # expressive mouth
 if int(t*6)%3==0:
  d.ellipse((x-14*scale,y-61*scale,x+18*scale,y-42*scale),fill=(77,35,39))
 else:
  d.arc((x-16*scale,y-64*scale,x+18*scale,y-43*scale),5,175,fill=(77,35,39),width=max(2,int(3*scale)))
 # wheels rotate, tilt indicates steering angle
 for wx in (x-112*scale,x+112*scale):
  draw_wheel(d,wx,y+64*scale,40*scale,t*2.7,turn)
def draw_person(d,x,y,t,talking=False,gesture=0,scale=1):
 bob=4*math.sin(t*3)
 y+=bob
 # legs and boots
 d.line((x-18*scale,y+145*scale,x-31*scale,y+235*scale),fill=(48,58,65),width=max(8,int(22*scale)))
 d.line((x+18*scale,y+145*scale,x+33*scale,y+235*scale),fill=(48,58,65),width=max(8,int(22*scale)))
 rounded(d,(x-55*scale,y+218*scale,x-12*scale,y+247*scale),10,(91,68,52))
 rounded(d,(x+12*scale,y+218*scale,x+58*scale,y+247*scale),10,(91,68,52))
 # body coat, folds
 d.polygon([(x-46*scale,y+38*scale),(x+45*scale,y+38*scale),(x+62*scale,y+160*scale),(x-59*scale,y+160*scale)],fill=(47,112,142),outline=(26,65,88))
 d.line((x,y+46*scale,x+4*scale,y+147*scale),fill=(180,213,210),width=max(2,int(3*scale)))
 d.line((x-30*scale,y+72*scale,x-44*scale,y+145*scale),fill=(90,159,178),width=max(2,int(4*scale)))
 # head, hair, ears
 d.ellipse((x-40*scale,y-48*scale,x+40*scale,y+42*scale),fill=(226,177,143),outline=(103,68,59),width=max(2,int(3*scale)))
 d.pieslice((x-43*scale,y-62*scale,x+43*scale,y+26*scale),180,360,fill=(63,50,45))
 for ex in (x-22*scale,x+12*scale):
  d.ellipse((ex,y-8*scale,ex+11*scale,y+5*scale),fill=(36,43,44))
 d.line((x-5*scale,y+18*scale,x+9*scale,y+19*scale),fill=(119,63,55),width=max(2,int(3*scale)))
 if talking and int(t*6)%2==0:
  d.ellipse((x-8*scale,y+23*scale,x+11*scale,y+39*scale),fill=(110,42,45))
 else: d.arc((x-10*scale,y+20*scale,x+12*scale,y+37*scale),0,180,fill=(110,42,45),width=2)
 # arms articulate at shoulder and elbow
 swing=math.sin(t*4+gesture)*14
 if gesture%2==0:
  d.line((x-38*scale,y+62*scale,x-72*scale,y+112*scale,x-85*scale,y+85*scale),fill=(226,177,143),width=max(8,int(18*scale)),joint="curve")
  d.ellipse((x-96*scale,y+72*scale,x-75*scale,y+96*scale),fill=(226,177,143))
  d.line((x+38*scale,y+62*scale,x+72*scale,y+108*scale,x+102*scale,y+95*scale+swing),fill=(226,177,143),width=max(8,int(18*scale)),joint="curve")
  d.ellipse((x+91*scale,y+84*scale+swing,x+113*scale,y+106*scale+swing),fill=(226,177,143))
 else:
  d.line((x-38*scale,y+62*scale,x-72*scale,y+110*scale,x-99*scale,y+98*scale),fill=(226,177,143),width=max(8,int(18*scale)),joint="curve")
  d.line((x+38*scale,y+62*scale,x+72*scale,y+110*scale,x+88*scale,y+78*scale),fill=(226,177,143),width=max(8,int(18*scale)),joint="curve")
  d.ellipse((x+78*scale,y+66*scale,x+99*scale,y+90*scale),fill=(226,177,143))
def arrow(d,a,b,color=(255,224,147),w=5):
 d.line((a[0],a[1],b[0],b[1]),fill=color,width=w)
 ang=math.atan2(b[1]-a[1],b[0]-a[0])
 for off in (2.5,-2.5):
  d.line((b[0],b[1],b[0]-18*math.cos(ang+off),b[1]-18*math.sin(ang+off)),fill=color,width=w)
def diagram(d,kind,t):
 # large explanatory floating board with animated wheel geometry
 rounded(d,(65,310,655,790),32,(43,67,78),(222,205,165),6)
 if kind=="camber":
  d.text((105,340),"ВИД СПЕРЕДИ",font=font(22,True),fill=(255,233,194))
  d.line((360,430,360,735),fill=(228,232,216),width=4)
  tilt=math.sin(t*1.4)*.08+.15
  for cx,sgn in ((260,-1),(460,1)):
   dx=math.sin(tilt)*145
   x2=cx+dx*sgn
   d.line((cx,460,x2,700),fill=(34,40,43),width=58)
   d.line((cx-4,465,x2-4,695),fill=(137,157,154),width=6)
   arrow(d,(cx+sgn*55,500),(cx+sgn*55,650),(128,220,180),4)
  d.text((205,735),"НАКЛОН КОЛЕСА",font=font(19,True),fill=(155,229,199))
 elif kind=="toe":
  d.text((105,340),"ВИД СВЕРХУ",font=font(22,True),fill=(255,233,194))
  d.rounded_rectangle((180,430,540,710),radius=50,outline=(180,202,190),width=5)
  z=math.sin(t*1.6)*25
  d.polygon([(240,500),(470-z,500),(470-z,565),(240,565)],fill=(33,40,43),outline=(237,198,151))
  d.polygon([(240,620),(470+z,620),(470+z,685),(240,685)],fill=(33,40,43),outline=(237,198,151))
  arrow(d,(220,595),(500,595),(128,220,180),5)
  d.text((218,735),"НАПРАВЛЕНИЕ КОЛЁС",font=font(19,True),fill=(155,229,199))
 elif kind=="caster":
  d.text((105,340),"ВИД СБОКУ",font=font(22,True),fill=(255,233,194))
  d.line((360,420,360,730),fill=(210,222,211),width=4)
  d.line((300,680,405,455),fill=(32,40,43),width=62)
  d.line((300,680,405,455),fill=(132,153,153),width=6)
  d.arc((245,420,475,740),250,305,fill=(126,221,184),width=7)
  arrow(d,(410,480),(450,430),(255,220,144),5)
  d.text((205,735),"НАКЛОН ОСИ ПОВОРОТА",font=font(18,True),fill=(155,229,199))
def draw_lift(d,t):
 # car on hydraulic lift, suspension and wheel components visible
 rounded(d,(70,750,650,810),15,(55,68,71),(206,187,146),4)
 for x in (130,590):
  d.rectangle((x-16,530,x+16,780),fill=(61,112,132),outline=(201,220,208),width=3)
  d.rectangle((x-32,520,x+32,545),fill=(217,174,106))
 draw_car(d,360,640,t,.68)
 # suspension strut and control arm shown beside car
 for x in (220,500):
  draw_wheel(d,x,650,55,t*2)
  d.line((x,580,x+10,490),fill=(187,204,195),width=12)
  d.line((x,700,x+70,740),fill=(205,166,119),width=10)
  d.ellipse((x+57,728,x+80,751),fill=(91,104,103))
  d.line((x+5,590,x-35,630),fill=(212,174,123),width=7)
def make_frame(title,caption,kind,t,speaker,idx):
 im=background(kind,t); d=ImageDraw.Draw(im)
 if kind in ("road","tires"):
  # floor lane / tire tread demonstration
  if kind=="road":
   d.polygon([(0,820),(720,820),(720,1000),(0,1000)],fill=(65,79,79))
   for k in range(5):
    xx=(k*180+int(t*110))%850-70
    d.line((xx,910,xx+80,910),fill=(241,208,153),width=7)
   draw_car(d,235,680,t,.75,turn=.18*math.sin(t*2),blink=int(t*4)%13==0)
   draw_person(d,550,565,t,speaker=="mech",int(t*1.5)%2,.82)
   # curved drift arrow
   arrow(d,(95,770),(165+int(15*math.sin(t*2)),735),(255,222,149),5)
  else:
   draw_car(d,215,680,t,.67)
   draw_person(d,550,570,t,speaker=="mech",1,.82)
   # magnified tire wear cross-section
   rounded(d,(340,480,500,750),22,(44,62,70),(226,201,160),4)
   d.ellipse((370,515,470,680),fill=(30,36,39),outline=(181,187,172),width=7)
   for yy in range(535,665,26): d.line((378,yy,460,yy+8),fill=(117,132,128),width=7)
   d.text((350,710),"ИЗНОС",font=font(18,True),fill=(255,224,160))
 elif kind=="lift":
  draw_lift(d,t); draw_person(d,585,545,t,speaker=="mech",1,.78)
 elif kind in ("camber","toe","caster"):
  diagram(d,kind,t)
  draw_person(d,570,810,t,speaker=="mech",idx%2,.65)
 elif kind=="stand":
  # measurement arch and 3D target markers, scanning beams
  rounded(d,(75,770,645,825),16,(45,61,66),(220,193,151),4)
  draw_car(d,360,660,t,.72)
  for x in (205,515):
   rounded(d,(x-42,470,x+42,755),18,(49,91,109),(202,222,208),4)
   rounded(d,(x-25,540,x+25,610),8,(221,231,208),(76,123,143),3)
   for a in range(3):
    d.ellipse((x-14+a*12,560,x-6+a*12,568),fill=(70,150,177))
  # animated laser scan
  yy=500+int((t*95)%210)
  d.line((140,yy,580,yy),fill=(107,232,220),width=4)
  d.line((140,yy+5,580,yy+5),fill=(107,232,220),width=1)
  draw_person(d,600,540,t,speaker=="mech",1,.76)
 elif kind=="adjust":
  draw_car(d,355,675,t,.73)
  # mechanic adjusts wheel with wrench; arm follows rotation
  draw_person(d,570,545,t,speaker=="mech",int(t*2)%2,.8)
  wx=250+int(5*math.sin(t*3)); wy=740
  d.line((wx,wy,wx+75,wy-65),fill=(217,215,193),width=12)
  d.ellipse((wx+56,wy-80,wx+88,wy-50),outline=(218,215,193),width=8)
  for j in range(4):
   d.arc((wx-12-j*4,wy-15-j*4,wx+12+j*4,wy+15+j*4),0,300,fill=(255,213,140),width=2)
 else:
  draw_car(d,350,680,t,.8,turn=.02*math.sin(t))
  draw_person(d,575,555,t,speaker=="mech",1,.82)
  rounded(d,(95,400,625,500),26,(39,65,76),(138,206,177),4)
  d.text((150,425),"ПОВТОРНЫЙ ЗАМЕР",font=font(28,True),fill=(180,239,201))
  # checkmark animates into place
  if t>1:
   d.line((530,450,548,468,585,425),fill=(133,235,174),width=10)
 # scene title
 titlefont=font(31,True); y=130
 for ln in wrap(d,title,titlefont,620):
  tw=d.textbbox((0,0),ln,font=titlefont,stroke_width=2)[2]
  d.text(((W-tw)//2+3,y+4),ln,font=titlefont,fill=(23,32,39),stroke_width=5,stroke_fill=(23,32,39))
  d.text(((W-tw)//2,y),ln,font=titlefont,fill=(255,246,222),stroke_width=2,stroke_fill=(53,66,72))
  y+=43
 # subtitles: clean, outlined, readable, bottom safe area
 rounded(d,(32,1000,688,1215),26,(27,39,48),(126,154,153),3)
 name="АВТОМОБИЛЬ" if speaker=="car" else "МЕХАНИК"
 col=(255,207,143) if speaker=="car" else (151,224,224)
 rounded(d,(55,976,245,1015),12,(55,76,83))
 d.text((72,983),name,font=font(16,True),fill=col)
 text_center(d,caption,1035,font(20,True),(255,250,237),580,2)
 return im
def run(cmd): subprocess.run(cmd,check=True)
clips=[]
for i,(title,speech,kind,speaker) in enumerate(SCENES,1):
 mp3=OUT/f"voice_{i:02d}.mp3"; wav=OUT/f"voice_{i:02d}.wav"
 rate="+1%" if speaker=="car" else "-2%"
 pitch="+1Hz" if speaker=="car" else "-1Hz"
 # Neural Microsoft Edge voices only. Rotate natural neural alternatives on transient service failures.
 voice_pool=VOICE_POOLS[speaker]
 last=None
 if not (mp3.exists() and mp3.stat().st_size>5000):
  for round_no in range(4):
   for voice_no,voice in enumerate(voice_pool):
    p=subprocess.run(["edge-tts","--voice",voice,f"--rate={rate}",f"--pitch={pitch}","--text",speech,"--write-media",str(mp3)],capture_output=True,text=True,timeout=150)
    if p.returncode==0 and mp3.exists() and mp3.stat().st_size>5000:
     last=None
     break
    last=(p.stderr or p.stdout or "TTS returned no audio")
    if mp3.exists(): mp3.unlink()
    time.sleep(min(25,5*(round_no+1)+voice_no*2))
   if last is None: break
   time.sleep(min(40,8*(round_no+1)))
 if last: raise RuntimeError(f"Natural neural voice generation failed for scene {i} after retries with {voice_pool}: {last}")
 run(["ffmpeg","-y","-loglevel","error","-i",str(mp3),"-af","loudnorm=I=-17:TP=-2:LRA=7","-ar","24000","-ac","1",str(wav)])
 with wave.open(str(wav),"rb") as w: secs=w.getnframes()/w.getframerate()
 n=max(50,int((secs+0.8)*FPS))
 frames=OUT/f"frames_{i:02d}"; frames.mkdir(exist_ok=True)
 for k in range(n):
  t=k/FPS
  make_frame(title,speech,kind,t,speaker,i).save(frames/f"f_{k:05d}.jpg",quality=92)
 clip=OUT/f"scene_{i:02d}.mp4"
 run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",str(frames/"f_%05d.jpg"),"-i",str(wav),"-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-shortest",str(clip)])
 clips.append(clip)
lst=OUT/"concat.txt"; lst.write_text("".join(f"file '{p.resolve()}'\n" for p in clips),encoding="utf-8")
run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c","copy","-movflags","+faststart","autopromo_explainer.mp4"])
probe=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=width,height","-of","json","autopromo_explainer.mp4"],text=True)
print("FINAL VIDEO VERIFIED:",probe)
