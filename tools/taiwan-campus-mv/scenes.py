# -*- coding: utf-8 -*-
"""台湾の大学キャンパス 18 景 — 新海誠風。2560x1440。"""
import numpy as np
from art import *
from PIL import ImageDraw

def _sky(stops): return vgrad(stops)

def windows(rows, seed, warm='#ffd08a', glow='#ff9a48', p=0.6, blurpx=1.2):
    """rows: [(x0,x1,y0,y1,cols,rws)] 建物の窓明かり"""
    im = Image.new('L',(W,H),0); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    for (x0,x1,y0,y1,cols,rws) in rows:
        cw = (x1-x0)/cols; ch = (y1-y0)/rws
        for i in range(cols):
            for j in range(rws):
                if r.random() > p: continue
                wx = x0+i*cw+cw*0.22; wy = y0+j*ch+ch*0.22
                d.rectangle([wx*W, wy*H, (wx+cw*0.56)*W, (wy+ch*0.50)*H],
                            fill=int(140+r.random()*115))
    a = blur(np.asarray(im).astype(np.float64)/255, blurpx)
    return a

def building(img, poly, face, roof=None, edge=None, feather=0.8):
    m = silhouette_mask([poly], feather)
    img = over(img, face, m)
    if edge:
        gy,gx = np.gradient(m)
        img = screen(img, edge, blur(np.abs(gy)+np.abs(gx),2.2)*0.5)
    return img, m

def avenue(img, rows, col, rim=None, seed=3):
    """遠近のある並木／街灯。rows: [(t, x_left, x_right, y_base, h)]"""
    polys=[]
    for (xl, xr, yb, h, wdt) in rows:
        for x in (xl, xr):
            polys.append([(x-wdt, yb),(x-wdt*0.45, yb-h),(x+wdt*0.45, yb-h),(x+wdt, yb)])
    m = silhouette_mask(polys, 0.9)
    img = over(img, col, m)
    if rim: img = screen(img, rim, blur(m,3.5)*0.22)
    return img, m

def palm(img, base, seed=5, col='#22301f', rim='#ffe0a8', n=9):
    """椰林大道：手前ほど大きく、根元も下にくる。葉は垂れ下がる曲線。"""
    im = Image.new('L',(W,H),0); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    order = sorted(range(n), key=lambda i:i)      # 奥から描く
    for i in order:
        t = (i/(n-1))**1.9
        h  = 0.085 + t*0.58
        wd = 0.0028 + t*0.014
        yb = base + t*0.36
        for side in (-1, 1):
            x = 0.5 + side*(0.038 + t*0.60)
            top = yb - h
            # 幹：わずかに反る
            bend = side*0.010*t
            pts=[]
            for k in range(9):
                u=k/8
                px = x + bend*(u**2); py = yb - h*u
                w_ = wd*(1-0.45*u)
                pts.append((px-w_, py))
            for k in range(8,-1,-1):
                u=k/8
                px = x + bend*(u**2); py = yb - h*u
                w_ = wd*(1-0.45*u)
                pts.append((px+w_, py))
            d.polygon([(p[0]*W,p[1]*H) for p in pts], fill=255)
            # 冠：垂れ下がる葉
            tx = x + bend
            for k in range(9):
                ang = -3.05 + k*0.39 + (r.random()-0.5)*0.16
                L = (0.030 + t*0.115)*(0.75+0.5*r.random())
                seg=[]
                for m in range(7):
                    u=m/6
                    ex = tx + np.cos(ang)*L*u*0.66
                    ey = top + np.sin(ang)*L*u + (L*0.85)*(u**2.1)   # 重力で垂れる
                    seg.append((ex*W, ey*H))
                for m in range(6):
                    wdt = max(1, int((5+t*17)*(1-m/7)))
                    d.line([seg[m], seg[m+1]], fill=255, width=wdt)
    a = blur(np.asarray(im).astype(np.float64)/255, 1.0)
    img = over(img, col, np.clip(a*1.12,0,1))
    if rim: img = screen(img, rim, blur(a,4)*0.24)
    return img

def road(img, y0, y1, col, centre=0.5, w0=0.03, w1=0.95, line=None):
    poly=[(centre-w0/2, y0),(centre+w0/2, y0),(centre+w1/2, y1),(centre-w1/2, y1)]
    m = silhouette_mask([poly], 1.0)
    img = over(img, col, m*0.95)
    if line:
        lm = silhouette_mask([[(centre-0.002,y0),(centre+0.002,y0),(centre+0.012,y1),(centre-0.012,y1)]],1.0)
        img = over(img, line, lm*0.5)
    return img, m

# ---------------- 18 景 ----------------

# 01 学生宿舍の朝
def s01_dorm_morning():
    img = _sky([(0.0,'#2b3f74'),(0.22,'#5b6699'),(0.45,'#a97f92'),(0.66,'#f0a878'),(0.84,'#ffd39a'),(1.0,'#ffeccb')])
    img,_ = clouds(img,'#5a5a8c','#fff2d0',sun=(0.24,0.72),coverage=0.5,height=(0.02,0.55),
                   seed=101,softness=1.2,tint='#d38f86')
    img = sun_disc(img,0.24,0.72,0.030,core='#fffbe8',glow='#ff9a4e',power=1.15)
    img = god_rays(img,0.24,0.72,'#ffdca8',strength=0.26,seed=102,length=1.5)
    img,_ = mountains(img,0.72,0.10,'#4a4a72','#e0a888',0.45,seed=103,res=6)
    img,m = building(img,[(0.42,1.05),(0.42,0.30),(0.98,0.24),(0.98,1.05)],'#4e4a63',edge='#ffcf95')
    w = windows([(0.44,0.96,0.33,0.94,7,7)],104,p=0.55)
    img = screen(img,'#ffd9a0',w*0.95); img = screen(img,'#ff9c50',blur(w,18)*0.45)
    img,_ = building(img,[(0.0,1.05),(0.0,0.46),(0.30,0.42),(0.30,1.05)],'#3f3c55',edge='#ffbe86')
    w2 = windows([(0.02,0.28,0.48,0.92,4,5)],105,p=0.5)
    img = screen(img,'#ffcf90',w2*0.85)
    img = trees(img,1.02,'#20263a',n=26,seed=106,scale=1.3,rim='#ffcf95')
    return post(img,bloom=0.5,vig=0.34,warm=(1.05,1.00,0.97),contrast=1.06,seed=107,
                flare=(0.24,0.72,0.45,'#ffd9a8'))

# 02 台大 椰林大道の朝
def s02_ntu_palm_avenue():
    img = _sky([(0.0,'#2f6ec9'),(0.22,'#5f9ae0'),(0.48,'#a8ccef'),(0.7,'#e2eefb'),(1.0,'#fdf3e2')])
    img,_ = clouds(img,'#8fb4dd','#ffffff',sun=(0.5,0.30),coverage=0.5,height=(0.0,0.45),
                   seed=201,softness=1.05,res=(3,4),tint='#ffffff')
    img = sun_disc(img,0.5,0.325,0.030,core='#fffdf2',glow='#ffd08a',power=1.15)
    img = god_rays(img,0.5,0.325,'#ffeec8',strength=0.32,seed=202,length=1.6)
    # 地面
    gm = np.clip((NY-0.585)*26,0,1)
    img = over(img,'#6f8a4e', gm*0.95)
    gtex = fbm(H,W,res=(6,12),octaves=5,seed=206)
    img = over(img,'#556f3a', gm*np.clip((gtex-0.45)*1.6,0,1)*0.5)
    # 遠景の校舎
    img,_ = building(img,[(0.0,0.605),(0.0,0.505),(0.30,0.500),(0.30,0.605)],'#8f95a4',edge='#ffffff')
    img,_ = building(img,[(0.72,0.605),(0.72,0.492),(1.0,0.498),(1.0,0.605)],'#949aa8',edge='#ffffff')
    img = trees(img,0.612,'#3f5c33',n=30,seed=207,scale=0.8,rim='#dff0a8')
    img,_ = road(img,0.60,1.05,'#a89c86',centre=0.5,w0=0.035,w1=0.78,line='#e2dcca')
    # 傅鐘（正面奥の鐘楼）
    img,_ = building(img,[(0.470,0.600),(0.470,0.487),(0.530,0.487),(0.530,0.600)],'#3d4a46',edge='#fff0c8')
    img,_ = building(img,[(0.458,0.489),(0.500,0.462),(0.542,0.489)],'#2b3532')
    img = palm(img, 0.60, seed=203, col='#22301f', rim='#ffe6b8')
    img = grass(img,1.03,'#2c3d24',n=200,seed=204,hmax=0.08,rim='#dff0a8')
    return post(img,bloom=0.46,vig=0.30,warm=(1.02,1.01,0.99),contrast=1.06,seed=205,
                flare=(0.5,0.325,0.45,'#fff0cc'))

# 03 校門前の自転車道
def s03_bike_lane():
    img = _sky([(0.0,'#3d7fd0'),(0.25,'#77aae6'),(0.55,'#b9d6f2'),(0.8,'#e8f1fb'),(1.0,'#fbf5e8')])
    img,_ = clouds(img,'#8fb4dd','#ffffff',sun=(0.76,0.22),coverage=0.55,height=(0.0,0.44),
                   seed=301,softness=1.0,res=(3,4),tint='#ffffff')
    img = sun_disc(img,0.76,0.22,0.024,core='#ffffff',glow='#ffe1a8',power=0.9,disc=False)
    img,_ = building(img,[(0.0,0.78),(0.0,0.34),(0.34,0.30),(0.34,0.78)],'#6b6f86',edge='#e8eef8')
    img = screen(img,'#ffd9a0',windows([(0.02,0.32,0.36,0.74,5,5)],302,p=0.35)*0.5)
    img = trees(img,0.655,'#3c5c3a',n=24,seed=304,scale=1.1,rim='#dff0a8',band=0.09)
    gm = np.clip((NY-0.645)*24,0,1)
    img = over(img,'#7f9a58', gm*0.9)
    img,_ = road(img,0.62,1.05,'#9aa4ab',centre=0.56,w0=0.05,w1=0.9)
    # 自転車の列（遠近）
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    r=np.random.default_rng(303)
    for i in range(26):
        t=(i/25)**1.6
        x=0.30+t*0.62+r.random()*0.01; yb=0.68+t*0.30; s=0.02+t*0.075
        d.ellipse([(x-s)*W,(yb-s*0.9)*H,(x-s*0.1)*W,(yb+s*0.9)*H],outline=255,width=max(2,int(2+t*8)))
        d.ellipse([(x+s*0.1)*W,(yb-s*0.9)*H,(x+s)*W,(yb+s*0.9)*H],outline=255,width=max(2,int(2+t*8)))
        d.line([(x-s*0.55)*W,yb*H,(x+s*0.55)*W,yb*H],fill=255,width=max(2,int(2+t*7)))
        d.line([(x)*W,yb*H,(x-s*0.15)*W,(yb-s*1.5)*H],fill=255,width=max(2,int(2+t*7)))
    a=blur(np.asarray(im).astype(np.float64)/255,1.0)
    img = over(img,'#242b38',np.clip(a*1.15,0,1))
    img = screen(img,'#ffe9b0',blur(a,4)*0.30)
    return post(img,bloom=0.42,vig=0.30,warm=(1.01,1.01,1.00),contrast=1.06,seed=305)

# 04 教学棟の午後
def s04_lecture_hall():
    img = _sky([(0.0,'#4a86cf'),(0.28,'#86b3e2'),(0.6,'#c6dcf0'),(0.85,'#eef2f6'),(1.0,'#f6f2ea')])
    img,_ = clouds(img,'#93b7dd','#ffffff',sun=(0.2,0.2),coverage=0.45,height=(0.0,0.40),
                   seed=401,softness=1.1,tint='#ffffff')
    img,_ = building(img,[(0.06,1.05),(0.06,0.20),(0.94,0.20),(0.94,1.05)],'#c9c2b2',edge='#ffffff')
    # 水平の庇と縦のリブ
    slab = ((np.sin(NY*H/47.0)>0.72)).astype(float)*silhouette_mask([[(0.06,1.05),(0.06,0.20),(0.94,0.20),(0.94,1.05)]],0.8)
    img = over(img,'#8d8778',blur(slab,1.2)*0.45)
    w = windows([(0.09,0.91,0.24,0.96,9,8)],402,p=0.85,blurpx=0.9)
    img = over(img,'#2f3b4c',np.clip(w*1.1,0,1)*0.85)
    img = screen(img,'#cfe4ff',blur(w,4)*0.25)
    img = trees(img,1.04,'#2f4a2c',n=26,seed=403,scale=1.5,rim='#e6f2c0')
    img = grass(img,1.06,'#3a5730',n=200,seed=404,hmax=0.07)
    return post(img,bloom=0.38,vig=0.30,warm=(1.00,1.01,1.01),contrast=1.05,seed=405)

# 05 師大 紅樓
def s05_ntnu_red_house():
    img = _sky([(0.0,'#2c4f92'),(0.25,'#6d84b8'),(0.52,'#b98d9a'),(0.72,'#eaa67e'),(1.0,'#ffd9a8')])
    img,_ = clouds(img,'#6b6f9e','#ffe8c0',sun=(0.82,0.60),coverage=0.5,height=(0.02,0.5),
                   seed=501,softness=1.2,tint='#c98f96')
    img = sun_disc(img,0.82,0.60,0.026,core='#fff3d8',glow='#ff9a58',power=0.95)
    img,_ = building(img,[(0.10,1.05),(0.10,0.30),(0.90,0.30),(0.90,1.05)],'#8a4436',edge='#ffcf9a')
    # 尖った屋根
    img,_ = building(img,[(0.06,0.315),(0.20,0.20),(0.34,0.315)],'#4a2a24')
    img,_ = building(img,[(0.43,0.315),(0.50,0.16),(0.57,0.315)],'#4a2a24')
    img,_ = building(img,[(0.66,0.315),(0.80,0.20),(0.94,0.315)],'#4a2a24')
    bm = silhouette_mask([[(0.10,1.05),(0.10,0.30),(0.90,0.30),(0.90,1.05)]],0.8)
    brick = ((np.sin(NY*H/17.0)>0.80)).astype(float)*bm
    img = over(img,'#6b3228',blur(brick,1.0)*0.30)
    # アーチ窓
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    for i in range(9):
        x=0.145+i*0.079
        d.rounded_rectangle([x*W,0.44*H,(x+0.048)*W,0.62*H],radius=int(0.024*W),fill=210)
        d.rounded_rectangle([x*W,0.70*H,(x+0.048)*W,0.88*H],radius=int(0.024*W),fill=180)
    a=blur(np.asarray(im).astype(np.float64)/255,1.2)
    img = screen(img,'#ffd89a',a*0.85); img = screen(img,'#ff9c4a',blur(a,16)*0.4)
    img = trees(img,1.05,'#26331f',n=22,seed=502,scale=1.6,rim='#ffcf95')
    return post(img,bloom=0.48,vig=0.34,warm=(1.05,1.00,0.97),contrast=1.06,seed=503)

# 06 清華大学 成功湖
def s06_nthu_lake():
    img = _sky([(0.0,'#3a74c4'),(0.26,'#7fa8dc'),(0.55,'#c3d8ee'),(0.8,'#eef1ee'),(1.0,'#f6efdd')])
    img,_ = clouds(img,'#8fb0d6','#ffffff',sun=(0.68,0.28),coverage=0.5,height=(0.0,0.42),
                   seed=601,softness=1.1,tint='#ffffff')
    img = sun_disc(img,0.68,0.28,0.022,core='#ffffff',glow='#ffe4b0',power=0.85,disc=False)
    img,_ = mountains(img,0.56,0.13,'#5f7f5c','#bcd0dc',0.5,seed=602,res=5,sharp=1.2)
    img = trees(img,0.60,'#33512f',n=26,seed=603,scale=1.5,rim='#dff0a8')
    sky = img.copy()
    img = water(img,0.615,sky,'#2c4a44',sun_x=0.68,sun_col='#e8f4c8',ripple=0.7,seed=604)
    img = trees(img,1.04,'#1e3320',n=20,seed=605,scale=2.0,rim='#cfe8a0')
    img = grass(img,1.07,'#24421f',n=220,seed=606,hmax=0.10,rim='#dff0a8')
    return post(img,bloom=0.42,vig=0.32,warm=(1.00,1.02,1.00),contrast=1.06,seed=607)

# 07 中央大学 中大湖と松林
def s07_ncu_lake():
    img = _sky([(0.0,'#27427e'),(0.22,'#5b6ba4'),(0.48,'#a97d9c'),(0.68,'#eda078'),(0.86,'#ffcf92'),(1.0,'#ffe9c4')])
    img,_ = clouds(img,'#5a5a90','#fff0cc',sun=(0.30,0.66),coverage=0.52,height=(0.02,0.52),
                   seed=701,softness=1.15,tint='#cf8b92')
    img = sun_disc(img,0.30,0.66,0.032,core='#fffbe8',glow='#ff9448',power=1.2)
    img,_ = mountains(img,0.64,0.10,'#4a4870','#e8a888',0.42,seed=702,res=6)
    img = trees(img,0.665,'#2c2f42',n=22,seed=703,scale=1.7,rim='#ffcf95')
    sky = img.copy()
    img = water(img,0.675,sky,'#3a3450',sun_x=0.30,sun_col='#ffd79a',ripple=0.8,seed=704)
    img = trees(img,1.05,'#1c1e2c',n=16,seed=705,scale=2.3,rim='#ffcf95')
    img = grass(img,1.07,'#242030',n=200,seed=706,hmax=0.10,rim='#ffcf95')
    return post(img,bloom=0.52,vig=0.34,warm=(1.05,1.00,0.97),contrast=1.07,seed=707,
                flare=(0.30,0.66,0.5,'#ffd9a8'))

# 08 中興大学 中興湖の夕
def s08_nchu_lake():
    img = _sky([(0.0,'#243a6e'),(0.2,'#535f96'),(0.44,'#a8708f'),(0.64,'#f09a6c'),(0.82,'#ffc98a'),(1.0,'#ffe8c8')])
    img,_ = clouds(img,'#4e5288','#fff0cc',sun=(0.62,0.68),coverage=0.55,height=(0.02,0.55),
                   seed=801,softness=1.2,tint='#d18b8e')
    img = sun_disc(img,0.62,0.68,0.030,core='#fff8e0',glow='#ff8f3e',power=1.15)
    img = god_rays(img,0.62,0.68,'#ffdba0',strength=0.24,seed=802,length=1.4)
    img,_ = building(img,[(0.02,0.70),(0.02,0.50),(0.24,0.48),(0.24,0.70)],'#3a3552',edge='#ffcf95')
    img = trees(img,0.705,'#2e2b45',n=24,seed=803,scale=1.5,rim='#ffcf95')
    sky = img.copy()
    img = water(img,0.715,sky,'#3d3050',sun_x=0.62,sun_col='#ffd79a',ripple=0.9,seed=804)
    # 湖心の島
    isl = silhouette_mask([[(0.40,0.735),(0.44,0.700),(0.52,0.696),(0.57,0.735)]],1.0)
    img = over(img,'#241f36',isl)
    img = screen(img,'#ffc98a',blur(isl,5)*0.18)
    img = grass(img,1.06,'#221d33',n=230,seed=805,hmax=0.11,rim='#ffcf95')
    return post(img,bloom=0.54,vig=0.34,warm=(1.06,1.00,0.96),contrast=1.07,seed=806,
                flare=(0.62,0.68,0.55,'#ffd9a8'))

# 09 東海大学 路思義教堂
def s09_thu_luce_chapel():
    img = _sky([(0.0,'#2b62b8'),(0.24,'#6f9bd8'),(0.52,'#b5cfe8'),(0.76,'#eddfc8'),(1.0,'#f8e6c0')])
    img,_ = clouds(img,'#87abd4','#ffffff',sun=(0.78,0.34),coverage=0.48,height=(0.0,0.44),
                   seed=901,softness=1.05,tint='#ffffff')
    img = sun_disc(img,0.78,0.34,0.026,core='#fffdf0',glow='#ffcf8a',power=1.0)
    img = god_rays(img,0.78,0.34,'#ffeec8',strength=0.26,seed=902,length=1.5)
    # 双曲面シェル：内側にくびれた輪郭のテント形
    APEX_Y, BASE_Y = 0.235, 0.905
    def side_curve(sign, halfw):
        pts=[]
        for k in range(46):
            u=k/45
            x = 0.5 + sign*halfw*(u**1.42)      # 下ほど急に広がる＝凹んだ稜線
            y = APEX_Y + (BASE_Y-APEX_Y)*u
            pts.append((x,y))
        return pts
    L = side_curve(-1, 0.300); R = side_curve(1, 0.300)
    shell_l = [(0.5-0.008, APEX_Y)] + L + [(0.5-0.008, BASE_Y)]
    shell_r = [(0.5+0.008, APEX_Y)] + R[::-1] + [(0.5+0.008, BASE_Y)][::-1]
    shell_r = [(0.5+0.008, APEX_Y)] + R + [(0.5+0.008, BASE_Y)]
    ml = silhouette_mask([shell_l],0.9); mr = silhouette_mask([shell_r],0.9)
    img = over(img,'#b3a894', ml)                 # 陽の当たる面
    img = over(img,'#7f7565', mr)                 # 陰の面
    # 屋根の菱形タイル
    u = (NX-0.5); v = (NY-APEX_Y)
    tile = ((np.sin((u*46+v*26))>0.75)|(np.sin((-u*46+v*26))>0.75)).astype(float)*(ml+mr)
    img = over(img,'#5f5648', blur(tile,1.0)*0.28)
    # 中央のトップライト
    ridge = silhouette_mask([[(0.5-0.010,APEX_Y),(0.5+0.010,APEX_Y),(0.5+0.016,BASE_Y),(0.5-0.016,BASE_Y)]],0.7)
    img = screen(img,'#fff6dc', blur(ridge,3)*0.75)
    # 軒下の影
    eave = np.clip((NY-0.86)*16,0,1)*(ml+mr)
    img = over(img,'#4a4236', blur(eave,4)*0.5)
    img = grass(img,1.03,'#3f6030',n=240,seed=903,hmax=0.09,rim='#e6f4b0')
    img = trees(img,0.92,'#33512c',n=20,seed=904,scale=1.1,rim='#e6f4b0')
    return post(img,bloom=0.46,vig=0.30,warm=(1.02,1.01,0.99),contrast=1.06,seed=905,
                flare=(0.78,0.34,0.4,'#fff0cc'))

# 10 成功大学 榕園の大榕樹
def s10_ncku_banyan():
    img = _sky([(0.0,'#4f8fd6'),(0.28,'#8fbbe6'),(0.6,'#cfe2f2'),(0.85,'#f0eee2'),(1.0,'#f8f0d8')])
    img,_ = clouds(img,'#8fb4dd','#ffffff',sun=(0.18,0.16),coverage=0.42,height=(0.0,0.40),
                   seed=1001,softness=1.1,tint='#ffffff')
    img = god_rays(img,0.18,0.10,'#fff6d0',strength=0.40,seed=1002,length=1.7)
    # 大榕樹
    r = np.random.default_rng(1003)
    # 樹冠：多数の塊を重ねて、陽の側だけ明るく
    canopy = np.zeros((H,W))
    blobs = [(0.50,0.46,0.34),(0.24,0.52,0.24),(0.76,0.51,0.25),(0.36,0.37,0.20),
             (0.65,0.37,0.19),(0.13,0.58,0.16),(0.87,0.57,0.16),(0.50,0.31,0.17),
             (0.38,0.56,0.18),(0.63,0.56,0.18),(0.50,0.60,0.20)]
    for cx,cy,rr in blobs:
        canopy += radial(cx,cy,rr,1.35)
    tex = fbm(H,W,res=(10,16),octaves=6,gain=0.55,seed=1004)
    canopy = np.clip(canopy*(0.40+tex*1.25)-0.20,0,1)
    canopy = blur(canopy,4)
    # 枝：太い主枝から細い枝へ
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    def branch(x,y,ang,L,w_,depth):
        if depth==0 or w_<2: return
        x2 = x+np.cos(ang)*L; y2 = y+np.sin(ang)*L
        d.line([(x*W,y*H),(x2*W,y2*H)],fill=255,width=int(w_))
        for s in (-1,1):
            branch(x2,y2,ang+s*(0.42+r.random()*0.3),L*0.62,w_*0.58,depth-1)
    # 幹（板根つき）
    d.polygon([(0.436*W,1.00*H),(0.462*W,0.66*H),(0.492*W,0.585*H),
               (0.532*W,0.585*H),(0.560*W,0.66*H),(0.588*W,1.00*H)],fill=255)
    for k in range(7):
        a0 = -2.75 + k*0.42 + (r.random()-0.5)*0.14
        branch(0.512, 0.62, a0, 0.085, 22, 3)
    trunk = blur(np.asarray(im).astype(np.float64)/255,1.1)
    # 気根：樹冠から垂れる細い線
    im2=Image.new('L',(W,H),0); d2=ImageDraw.Draw(im2)
    for k in range(52):
        x = 0.20+r.random()*0.62
        y0 = 0.46+r.random()*0.12
        ln = 0.10+r.random()*0.26
        d2.line([(x*W,y0*H),((x+(r.random()-0.5)*0.012)*W,(y0+ln)*H)],
                fill=int(120+r.random()*90),width=int(1+r.random()*3))
    roots = blur(np.asarray(im2).astype(np.float64)/255,0.9)
    img = over(img,'#33261b', roots*0.60)
    img = over(img,'#3d2c1e', np.clip(trunk*1.1,0,1))
    img = over(img,'#1d3317', np.clip(canopy,0,1))
    lit = np.clip(canopy-blur(canopy,16),0,1)*np.clip(1-(NX-0.30)*1.1,0,1)
    img = screen(img,'#d4ec9c', blur(lit,3)*0.75)
    img = over(img,'#0f1f0c', np.clip(canopy*np.clip((NY-0.34)*2.2,0,1),0,1)*0.35)
    img = grass(img,1.02,'#3f6030',n=260,seed=1005,hmax=0.08,rim='#e6f4b0')
    return post(img,bloom=0.48,vig=0.34,warm=(1.01,1.02,0.98),contrast=1.06,seed=1006,
                flare=(0.18,0.10,0.42,'#fff2cc'))

# 11 中正大学 寧靜湖
def s11_ccu_lake():
    img = _sky([(0.0,'#1f3468'),(0.2,'#4b5a90'),(0.45,'#9d7396'),(0.66,'#e79b78'),(0.85,'#ffcb92'),(1.0,'#ffe9c8')])
    img,_ = clouds(img,'#4e5288','#fff0cc',sun=(0.44,0.70),coverage=0.5,height=(0.02,0.52),
                   seed=1101,softness=1.2,tint='#cf8b95')
    img = sun_disc(img,0.44,0.70,0.028,core='#fff8e4',glow='#ff9448',power=1.1)
    img,_ = building(img,[(0.62,0.72),(0.62,0.44),(0.72,0.42),(0.80,0.44),(0.80,0.72)],'#3a3454',edge='#ffcf95')
    img = screen(img,'#ffd08a',windows([(0.64,0.78,0.48,0.70,4,4)],1102,p=0.6)*0.9)
    img = trees(img,0.725,'#2c2942',n=24,seed=1103,scale=1.4,rim='#ffcf95')
    sky = img.copy()
    img = water(img,0.735,sky,'#3a3050',sun_x=0.44,sun_col='#ffd79a',ripple=0.7,seed=1104)
    img = grass(img,1.05,'#221e32',n=220,seed=1105,hmax=0.10,rim='#ffcf95')
    return post(img,bloom=0.52,vig=0.34,warm=(1.05,1.00,0.97),contrast=1.07,seed=1106,
                flare=(0.44,0.70,0.5,'#ffd9a8'))

# 12 中山大学 西子灣の夕陽
def s12_nsysu_sunset():
    img = _sky([(0.0,'#2a2f70'),(0.18,'#5b4384'),(0.4,'#b0537c'),(0.6,'#f07d52'),(0.78,'#ffb35f'),(1.0,'#ffdc96')])
    img,_ = clouds(img,'#5c3d6c','#ffe9b4',sun=(0.42,0.66),coverage=0.55,height=(0.02,0.56),
                   seed=1201,softness=1.15,tint='#d0748a')
    img = sun_disc(img,0.42,0.66,0.040,core='#fff6d6',glow='#ff7433',power=1.3)
    img,_ = mountains(img,0.62,0.14,'#3a2545','#e0906e',0.38,seed=1202,res=5,sharp=1.25)
    # 丘の上の校舎
    img,_ = building(img,[(0.70,0.66),(0.70,0.52),(0.88,0.50),(0.88,0.66)],'#2f1e34',edge='#ffc07a')
    img = screen(img,'#ffd9a0',windows([(0.72,0.86,0.545,0.645,4,3)],1203,p=0.7)*0.8)
    sky = img.copy()
    img = water(img,0.665,sky,'#3d2a44',sun_x=0.42,sun_col='#ffcf87',ripple=1.3,seed=1204)
    bw = silhouette_mask([[(0.0,0.735),(0.30,0.700),(0.30,0.726),(0.0,0.775)]],0.9)
    img = over(img,'#2a1a24',bw)
    img = trees(img,1.04,'#241521',n=18,seed=1205,scale=1.8,rim='#ffc98a')
    return post(img,bloom=0.58,vig=0.34,warm=(1.06,0.99,0.95),contrast=1.08,seed=1206,
                flare=(0.42,0.66,0.6,'#ffd7a0'))

# 13 淡江大学 宮燈大道と淡水の夕照
def s13_tku_lanterns():
    img = _sky([(0.0,'#0d1338'),(0.18,'#22224f'),(0.42,'#443159'),(0.64,'#7a4560'),(0.82,'#b35c5c'),(1.0,'#d98a5e')])
    img = stars(img,density=0.00020,seed=1300,ymax=0.34,twinkle=0.7)
    img,_ = clouds(img,'#221a44','#a2708c',sun=(0.5,0.62),coverage=0.42,height=(0.02,0.44),
                   seed=1301,softness=1.3,tint='#3a2b52')
    img = sun_disc(img,0.5,0.62,0.020,core='#ffd9b0',glow='#c9603c',power=0.55,disc=False)
    img,_ = mountains(img,0.60,0.07,'#1b1430','#6b3d52',0.35,seed=1302,res=7)
    img,_ = road(img,0.60,1.05,'#2e2740',centre=0.5,w0=0.03,w1=0.66)
    # 宮燈（提灯の柱）
    rows=[]
    n=8
    for i in range(n):
        t=(i/(n-1))**1.7
        h=0.055+t*0.30; wd=0.004+t*0.011; yb=0.605+t*0.34
        rows.append((0.5-(0.045+t*0.42), 0.5+(0.045+t*0.42), yb, h, wd))
    img,lm = avenue(img,rows,'#171029',rim='#ffd9a0',seed=1303)
    lamp=np.zeros((H,W))
    for i in range(n):
        t=(i/(n-1))**1.7
        h=0.055+t*0.30; yb=0.605+t*0.34
        for side in (-1,1):
            x=0.5+side*(0.045+t*0.42)
            lamp+=radial(x,yb-h,0.020+t*0.055,1.4)
    lamp=np.clip(lamp,0,1)
    img = screen(img,'#ffe6b8',np.clip(lamp*1.4,0,1))
    img = screen(img,'#ff9a48',blur(lamp,40)*0.95)
    img = trees(img,0.548,'#150f26',n=22,seed=1304,scale=0.9,rim='#c98a6a',band=0.05)
    # 濡れた路面の映り込み
    refl=np.zeros((H,W))
    for i in range(n):
        t=(i/(n-1))**1.7; h=0.055+t*0.30; yb=0.605+t*0.34
        for side in (-1,1):
            x=0.5+side*(0.045+t*0.42)
            refl+=np.exp(-(((NX-x)*26)**2))*np.clip((NY-yb)*3.0,0,1)
    img = screen(img,'#ffb877',blur(refl*(0.35+fbm(H,W,res=(90,4),octaves=3,seed=1306)),6)*0.65)
    return post(img,bloom=0.56,vig=0.42,warm=(1.04,0.99,0.99),contrast=1.08,seed=1305)

# 14 図書館の徹夜
def s14_library_night():
    img = _sky([(0.0,'#080d24'),(0.35,'#111a3e'),(0.68,'#1f2a52'),(1.0,'#30375f')])
    img = stars(img,density=0.00022,seed=1401,ymax=0.42,twinkle=0.7)
    img,_ = clouds(img,'#121a3c','#7a88c0',sun=(0.5,0.9),coverage=0.32,height=(0.0,0.34),
                   seed=1402,softness=1.5,tint='#212a52')
    img,_ = building(img,[(0.12,1.05),(0.12,0.22),(0.88,0.18),(0.88,1.05)],'#1b2444',edge='#5f6ea8')
    w = windows([(0.15,0.85,0.24,0.92,8,7)],1403,p=0.72,blurpx=1.0)
    img = screen(img,'#ffd28e',w)
    img = screen(img,'#ff9a48',blur(w,22)*0.5)
    ent = silhouette_mask([[(0.44,1.05),(0.44,0.80),(0.56,0.80),(0.56,1.05)]],0.8)
    img = screen(img,'#ffe0b0',ent*0.55)
    img = over(img,'#0d1230',np.clip((NY-0.93)*14,0,1)*0.85)
    refl = np.exp(-(((NX-0.5)*2.4)**2))*np.clip((NY-0.93)*8,0,1)
    img = screen(img,'#ffc178',blur(refl*(0.4+fbm(H,W,res=(80,4),octaves=3,seed=1404)),5)*0.6)
    img = trees(img,1.02,'#0c1226',n=20,seed=1405,scale=1.5,rim='#4a5c94')
    return post(img,bloom=0.50,vig=0.44,warm=(1.02,0.99,1.03),contrast=1.08,seed=1406)

# 15 宿舍頂樓の星空
def s15_rooftop_stars():
    img = _sky([(0.0,'#04060f'),(0.3,'#080e22'),(0.62,'#101a38'),(0.85,'#22305a'),(1.0,'#4a4a72')])
    img = milky_way(img,seed=1501)
    img = stars(img,density=0.00085,seed=1502,ymax=0.80)
    # 街の灯り（地平線のグロー）
    glow = np.exp(-((NY-0.86)*7)**2)
    img = screen(img,'#ffb877',glow*0.30)
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    r=np.random.default_rng(1503)
    x=0.0
    while x<1.0:
        w_=0.03+r.random()*0.05; h_=0.03+r.random()*0.09
        d.rectangle([x*W,(0.88-h_)*H,(x+w_)*W,0.90*H],fill=255)
        x+=w_+0.004
    city = blur(np.asarray(im).astype(np.float64)/255,1.0)
    img = over(img,'#0a1024',city)
    cw = windows([(0.0,1.0,0.80,0.895,34,3)],1504,p=0.4,blurpx=0.8)*city
    img = screen(img,'#ffcf8a',cw*0.9)
    img = screen(img,'#ff9a48',blur(cw,20)*0.45)
    # 手すりと床
    img = over(img,'#080b18',np.clip((NY-0.90)*12,0,1))
    rail=[]
    rail.append([(0.0,0.905),(1.0,0.905),(1.0,0.918),(0.0,0.918)])
    for i in range(26):
        x=i/25
        rail.append([(x-0.0035,0.905),(x+0.0035,0.905),(x+0.0035,1.0),(x-0.0035,1.0)])
    rm = silhouette_mask(rail,0.7)
    img = over(img,'#05070f',rm)
    img = screen(img,'#6d7cb4',blur(rm,3)*0.20)
    return post(img,bloom=0.40,vig=0.48,warm=(0.97,0.99,1.08),contrast=1.10,seed=1505,grain=0.015)

# 16 宵夜街
def s16_night_market():
    img = _sky([(0.0,'#0a0f28'),(0.32,'#161d42'),(0.62,'#2a2f58'),(1.0,'#3f3a66')])
    img = stars(img,density=0.00012,seed=1601,ymax=0.30,twinkle=0.6)
    left=[[(-0.02,1.05),(-0.02,0.06),(0.40,0.40),(0.40,1.05)]]
    right=[[(1.02,1.05),(1.02,0.04),(0.60,0.39),(0.60,1.05)]]
    lm=silhouette_mask(left,1.0); rm=silhouette_mask(right,1.0)
    img = over(img,'#1d2448',lm); img = over(img,'#191f3e',rm)
    # 看板の帯（縦に並ぶネオン）
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    r=np.random.default_rng(1602)
    for side in (0,1):
        for k in range(14):
            t=k/14+r.random()*0.03
            if side==0: x=-0.02+t*0.42; ytop=0.06+t*0.34
            else: x=1.02-t*0.42; ytop=0.04+t*0.35
            for row in range(3):
                y=ytop+0.05+row*0.11+r.random()*0.02
                w_=0.012+0.020*t; h_=0.030+0.045*t
                d.rectangle([x*W,y*H,(x+w_)*W,(y+h_)*H],fill=int(160+r.random()*95))
    sign=blur(np.asarray(im).astype(np.float64)/255,1.0)
    for col,mult in (('#ff8f5a',1.0),('#ffd66e',0.7),('#7fd8ff',0.35)):
        img = screen(img,col,sign*mult*0.6)
    img = screen(img,'#ff7a3c',blur(sign,26)*0.55)
    # 提灯の列
    lamp=np.zeros((H,W))
    for k in range(9):
        t=k/8
        for side in (-1,1):
            x=0.5+side*(0.06+t*0.44); y=0.30+t*0.22
            lamp+=radial(x,y,0.012+t*0.026,1.6)
    lamp=np.clip(lamp,0,1)
    img = screen(img,'#ffd08a',lamp*0.95)
    img = screen(img,'#ff6f3a',blur(lamp,30)*0.55)
    road_m=np.clip((NY-0.42)*3.0,0,1)*np.clip(1-np.abs(NX-0.5)*1.0,0,1)
    img = over(img,'#0d1230',road_m*0.9)
    refl=np.zeros((H,W))
    for k in range(9):
        t=k/8
        for side in (-1,1):
            x=0.5+side*(0.06+t*0.44); y=0.30+t*0.22
            refl+=np.exp(-(((NX-x)*22)**2))*np.clip((NY-y-0.20)*2.0,0,1)
    streak=fbm(H,W,res=(90,4),octaves=3,seed=1603)
    img = screen(img,'#ffb066',blur(refl*(0.3+streak*1.2),6)*0.7)
    # 人影
    ppl=[]
    r2=np.random.default_rng(1604)
    for k in range(9):
        t=0.15+r2.random()*0.85; x=0.5+(r2.random()-0.5)*0.55*t; yb=0.55+t*0.45; h=0.06+t*0.20
        ppl.append([(x-h*0.10,yb),(x-h*0.09,yb-h),(x+h*0.09,yb-h),(x+h*0.10,yb)])
    pm=silhouette_mask(ppl,1.0)
    img = over(img,'#0a0d20',pm*0.9)
    return post(img,bloom=0.56,vig=0.44,warm=(1.05,0.99,1.00),contrast=1.08,seed=1605)

# 17 政治大学 山あいのキャンパス、雨あがり
def s17_nccu_hill():
    img = _sky([(0.0,'#57708a'),(0.3,'#8fa3ad'),(0.6,'#bcc7c2'),(0.85,'#e2ddcd'),(1.0,'#f2e9d4')])
    img,_ = clouds(img,'#75879a','#ffffff',sun=(0.72,0.14),coverage=0.6,height=(0.0,0.40),
                   seed=1701,softness=1.8,tint='#ccd3cf')
    img = god_rays(img,0.74,0.06,'#fff6e0',strength=0.36,seed=1702,length=1.8)
    img,_ = mountains(img,0.66,0.30,'#4e6a54','#c6cdc2',0.66,seed=1703,res=3,sharp=1.2)
    img,_ = mountains(img,0.78,0.22,'#3a5440','#b2bcae',0.42,seed=1704,res=5,sharp=1.25)
    img,_ = building(img,[(0.16,0.86),(0.16,0.60),(0.40,0.58),(0.40,0.86)],'#c8c0ae',edge='#ffffff')
    img,_ = building(img,[(0.44,0.86),(0.44,0.66),(0.62,0.65),(0.62,0.86)],'#b8b0a0',edge='#ffffff')
    img,_ = building(img,[(0.66,0.86),(0.66,0.62),(0.86,0.60),(0.86,0.86)],'#c0b8a8',edge='#ffffff')
    img = screen(img,'#ffe0a8',windows([(0.18,0.38,0.62,0.84,4,4),(0.68,0.84,0.64,0.84,4,4)],1705,p=0.35)*0.5)
    for i,(y,st) in enumerate([(0.60,0.42),(0.72,0.52)]):
        f = fbm(H,W,res=(2,10),octaves=5,seed=1706+i)
        fm = np.clip((f-0.42)*2.0,0,1)*np.exp(-((NY-y)*8.0)**2)
        img = over(img,'#eceee7',blur(fm,22)*st)
    sky = img.copy()
    img = water(img,0.875,sky,'#3f4a44',sun_x=0.74,sun_col='#e8eedc',ripple=0.6,seed=1708)
    img = trees(img,1.03,'#22331f',n=26,seed=1709,scale=1.7,rim='#d8e4c0')
    return post(img,bloom=0.42,vig=0.32,warm=(1.00,1.01,1.00),contrast=1.05,seed=1710)

# 18 卒業の朝 — 椰林大道の日の出
def s18_campus_sunrise():
    img = _sky([(0.0,'#2c4a90'),(0.18,'#6a6aa8'),(0.38,'#c47a92'),(0.56,'#f79a5c'),(0.74,'#ffc978'),(1.0,'#fff0d2')])
    img,_ = clouds(img,'#5c4a86','#fff6d8',sun=(0.5,0.60),coverage=0.48,height=(0.02,0.54),
                   seed=1801,softness=1.1,tint='#e0879a')
    img = sun_disc(img,0.5,0.60,0.046,core='#fffdf0',glow='#ff8f36',power=1.45)
    img = god_rays(img,0.5,0.60,'#ffe4b0',strength=0.38,seed=1802,length=1.7)
    img,_ = road(img,0.615,1.05,'#a08e78',centre=0.5,w0=0.03,w1=0.70,line='#e8dcc4')
    img = palm(img, 0.615, seed=1803, col='#3a2f2a', rim='#ffe0a8')
    img = grass(img,1.04,'#5a4630',n=220,seed=1804,hmax=0.09,rim='#ffd79a')
    return post(img,bloom=0.62,vig=0.28,warm=(1.07,1.01,0.95),contrast=1.07,seed=1805,
                flare=(0.5,0.60,0.75,'#ffe4b4'))

SCENES=[
 ('01_dorm_morning','学生宿舍の朝',s01_dorm_morning),
 ('02_ntu_palm_avenue','台大 椰林大道',s02_ntu_palm_avenue),
 ('03_bike_lane','校門前の自転車道',s03_bike_lane),
 ('04_lecture_hall','教学棟の午後',s04_lecture_hall),
 ('05_ntnu_red_house','師大 紅樓',s05_ntnu_red_house),
 ('06_nthu_lake','清大 成功湖',s06_nthu_lake),
 ('07_ncu_lake','中央大 中大湖',s07_ncu_lake),
 ('08_nchu_lake','中興大 中興湖',s08_nchu_lake),
 ('09_thu_luce_chapel','東海大 路思義教堂',s09_thu_luce_chapel),
 ('10_ncku_banyan','成大 榕園',s10_ncku_banyan),
 ('11_ccu_lake','中正大 寧靜湖',s11_ccu_lake),
 ('12_nsysu_sunset','中山大 西子灣',s12_nsysu_sunset),
 ('13_tku_lanterns','淡江大 宮燈大道',s13_tku_lanterns),
 ('14_library_night','図書館の徹夜',s14_library_night),
 ('15_rooftop_stars','宿舍頂樓の星空',s15_rooftop_stars),
 ('16_night_market','宵夜街',s16_night_market),
 ('17_nccu_hill','政大 山あいの校園',s17_nccu_hill),
 ('18_campus_sunrise','卒業の朝',s18_campus_sunrise),
]

if __name__=='__main__':
    import sys,os,time
    os.makedirs('frames',exist_ok=True)
    only=sys.argv[1:]
    for key,name,fn in SCENES:
        if only and not any(o in key for o in only): continue
        t0=time.time(); to_image(fn()).save(f'frames/{key}.jpg',quality=92)
        print(f"{key} {name} {time.time()-t0:.1f}s", flush=True)
