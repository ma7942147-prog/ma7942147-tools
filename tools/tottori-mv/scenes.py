# -*- coding: utf-8 -*-
"""鳥取県の名勝 16景 — 新海誠風。各シーンは 2560x1440 の一枚絵を返す。"""
import numpy as np
from art import *

def _sky(stops):
    return vgrad(stops)

# 01 東郷湖の夜明け前（藍の時間）
def s01_togo_lake_blue_hour():
    sky = _sky([(0.0,'#0b1030'),(0.32,'#16224f'),(0.6,'#33406e'),(0.82,'#6b6f92'),(1.0,'#9a90a6')])
    img = sky.copy()
    img = stars(img, density=0.00028, seed=101, ymax=0.55, twinkle=0.8)
    img, _ = clouds(img,'#1b2550','#8f9ccd',sun=(0.68,0.72),coverage=0.46,height=(0.18,0.66),
                    seed=102,softness=1.4,res=(3,5),tint='#3c4670')
    img = sun_disc(img,0.68,0.74,0.02,core='#ffe3c0',glow='#c98a7a',power=0.55,disc=False)
    img,_ = mountains(img,0.70,0.13,'#1a2140','#57608c',0.55,seed=103,res=4,sharp=1.1)
    img,_ = mountains(img,0.735,0.075,'#141a33','#3f4870',0.35,seed=104,res=7)
    sky_for_water = img.copy()
    img = water(img,0.745,sky_for_water,'#141b38',sun_x=0.68,sun_col='#e8b490',ripple=0.8,seed=105)
    img = grass(img,1.02,'#080b1c',n=380,seed=106,hmax=0.20,rim='#6d7aa8')
    return post(img,bloom=0.34,vig=0.38,warm=(0.97,0.99,1.06),contrast=1.05,seed=107,
                flare=(0.68,0.74,0.25,'#ffd2a8'))

# 02 浦富海岸・夜の波（山陰海岸ジオパーク）
def s02_uradome_night():
    sky = _sky([(0.0,'#070c24'),(0.35,'#101a40'),(0.62,'#22315e'),(1.0,'#465a86')])
    img = sky.copy()
    img = stars(img,density=0.00042,seed=201,ymax=0.5)
    img = sun_disc(img,0.24,0.20,0.028,core='#f2f6ff',glow='#8fa6d8',power=0.8)
    img,_ = clouds(img,'#0d1436','#7d90c8',sun=(0.24,0.20),coverage=0.40,height=(0.10,0.5),
                   seed=202,softness=1.3,tint='#2b3660')
    img,_ = mountains(img,0.60,0.10,'#0a1129','#2b3763',0.4,seed=203,res=5,sharp=1.3)
    sky_for_water = img.copy()
    img = water(img,0.62,sky_for_water,'#0a1430',sun_x=0.24,sun_col='#cfe0ff',ripple=1.4,seed=204)
    # 奇岩（rock stacks）
    rocks=[[(0.06,1.02),(0.09,0.60),(0.13,0.56),(0.17,0.63),(0.20,1.02)],
           [(0.74,1.02),(0.78,0.55),(0.83,0.52),(0.86,0.61),(0.90,1.02)],
           [(0.40,0.70),(0.43,0.585),(0.47,0.60),(0.49,0.70)]]
    m = silhouette_mask(rocks,feather=1.4)
    img = over(img,'#060a1c',m)
    img = screen(img,'#8fa6d8',blur(m,4)*0.16)
    # 白波
    foam = (fbm(H,W,res=(60,10),octaves=4,seed=205) > 0.66).astype(float)
    foam *= np.clip((NY-0.63)*4,0,1)*np.clip(1-(NY-0.63)*1.6,0,1)
    img = screen(img,'#dfe9ff',blur(foam,2.0)*0.55)
    return post(img,bloom=0.38,vig=0.42,warm=(0.95,0.99,1.10),contrast=1.08,seed=206)

# 03 鳥取砂丘・月夜の馬の背
def s03_dunes_night():
    sky = _sky([(0.0,'#080d26'),(0.4,'#131c45'),(0.72,'#2a3765'),(1.0,'#5b6390')])
    img = sky.copy()
    img = stars(img,density=0.0004,seed=301,ymax=0.6)
    img = sun_disc(img,0.72,0.18,0.022,core='#ffffff',glow='#9db4e6',power=0.9)
    img,_ = clouds(img,'#0e1638','#8ea3d8',sun=(0.72,0.18),coverage=0.34,height=(0.05,0.45),
                   seed=302,softness=1.4,tint='#28325c')
    img = dunes(img,[(0.72,0.10,4,303),(0.86,0.12,3,304),(1.06,0.16,2,305)],
                sand='#4a4f77',shade='#12162f',lit='#c6d4ff')
    ripple = fbm(H,W,res=(40,8),octaves=4,seed=306)
    m = np.clip((NY-0.72)*3,0,1)*np.clip((ripple-0.5)*2.2,0,1)
    img = screen(img,'#93a6d6',blur(m,2)*0.18)
    return post(img,bloom=0.36,vig=0.44,warm=(0.95,0.98,1.12),contrast=1.09,seed=307)

# 04 鳥取砂丘・砂嵐（風紋と舞い上がる砂）
def s04_dunes_sandstorm():
    sky = _sky([(0.0,'#3a2f3f'),(0.3,'#6b4f4a'),(0.58,'#a97a55'),(0.8,'#c9995f'),(1.0,'#8d6743')])
    img = sky.copy()
    img,_ = clouds(img,'#4a3a3c','#e8c489',sun=(0.4,0.3),coverage=0.68,height=(0.0,0.6),
                   seed=401,softness=1.6,density=1.2,tint='#7a5c47')
    img = sun_disc(img,0.40,0.30,0.03,core='#ffe6b8',glow='#d9853f',power=0.75,disc=False)
    img = dunes(img,[(0.66,0.09,4,402),(0.80,0.11,3,403),(1.05,0.17,2,404)],
                sand='#c0885a',shade='#4a2f22',lit='#ffdba2')
    # 舞う砂（横に流れる霞）
    dust = fbm(H,W,res=(5,26),octaves=5,gain=0.6,seed=405)
    dm = np.clip((dust-0.42)*1.8,0,1)*np.clip((NY-0.35)*1.6,0,1)
    img = over(img,'#d8ab74',blur(dm,14)*0.42)
    img = god_rays(img,0.40,0.30,'#ffdaa0',strength=0.30,seed=406)
    img = grass(img,1.04,'#3a2618',n=160,seed=407,hmax=0.13,rim='#e0a86a')
    return post(img,bloom=0.46,vig=0.36,warm=(1.06,1.00,0.93),contrast=1.07,seed=408,
                flare=(0.40,0.30,0.35,'#ffcf95'))

# 05 三徳山三仏寺投入堂・霧の峰々
def s05_nageiredo_mist():
    sky = _sky([(0.0,'#5a7280'),(0.28,'#8ea09e'),(0.6,'#bcc3b8'),(1.0,'#e0dbcb')])
    img = sky.copy()
    img,_ = clouds(img,'#6d787c','#ffffff',sun=(0.20,0.06),coverage=0.55,height=(0.0,0.34),
                   seed=501,softness=1.9,tint='#d2d6cd')
    img = god_rays(img,0.20,0.02,'#fff8e4',strength=0.42,seed=502,length=1.9)
    # 幾重にも重なる霧の峰
    img,_ = mountains(img,0.58,0.30,'#5a6d5c','#cfd4c8',0.74,seed=503,res=3,sharp=1.25)
    img,_ = mountains(img,0.68,0.26,'#485c4b','#c4cabd',0.62,seed=504,res=4,sharp=1.20)
    img,_ = mountains(img,0.80,0.24,'#374a3a','#b6bfae',0.46,seed=505,res=5,sharp=1.25)
    img,_ = mountains(img,0.94,0.22,'#26362a','#a3ad9c',0.28,seed=506,res=6,sharp=1.30)
    # 岩峰と投入堂（稜線にそっと乗せる／輪郭は羽根ぼかしで馴染ませる）
    crag = radial(0.663,0.612,0.115,1.5)
    crag = np.clip(crag*(0.55+fbm(H,W,res=(9,11),octaves=5,seed=507)*1.1)-0.30,0,1)
    crag = blur(crag,6)*np.clip((NY-0.47)*9,0,1)
    rockt = fbm(H,W,res=(20,16),octaves=7,gain=0.58,seed=508)
    rc = hexc('#2f3f2e')[None,None,:]*(0.40+1.5*rockt[...,None])
    img = img*(1-crag[...,None]) + np.clip(rc,0,1)*crag[...,None]
    img = screen(img,'#e6ecdc',blur(np.clip(crag-blur(crag,9),0,1),3)*0.9)
    hall=[[(0.640,0.598),(0.640,0.570),(0.688,0.570),(0.688,0.598)]]
    roof=[[(0.628,0.572),(0.664,0.549),(0.700,0.572)]]
    pil=[[(0.6445,0.628),(0.6485,0.628),(0.6485,0.598),(0.6445,0.598)],
         [(0.6620,0.636),(0.6660,0.636),(0.6660,0.598),(0.6620,0.598)],
         [(0.6795,0.631),(0.6835,0.631),(0.6835,0.598),(0.6795,0.598)]]
    hm=silhouette_mask(hall,0.4); rm2=silhouette_mask(roof,0.4); pm=silhouette_mask(pil,0.3)
    img = over(img,'#7d5530',hm); img = over(img,'#33251a',rm2); img = over(img,'#5c3e23',pm)
    img = screen(img,'#ffeccb',blur(hm+rm2,7)*0.35)
    # 谷を流れる霧
    for i,(y,st) in enumerate([(0.60,0.55),(0.73,0.62),(0.87,0.72)]):
        f = fbm(H,W,res=(2,10),octaves=5,seed=508+i)
        fm = np.clip((f-0.40)*2.0,0,1)*np.exp(-((NY-y)*7.5)**2)
        img = over(img,'#eaece5',blur(fm,22)*st)
    img = trees(img,1.05,'#1a271c',n=30,seed=511,scale=1.9,rim='#d2d8c8')
    return post(img,bloom=0.44,vig=0.34,warm=(1.00,1.01,1.00),contrast=1.06,seed=512)

# 06 大山・暁の黄金（伯耆富士）
def s06_daisen_dawn_gold():
    sky = _sky([(0.0,'#1c2a58'),(0.22,'#4a4a83'),(0.44,'#a3628a'),(0.62,'#e08a63'),(0.78,'#ffbe72'),(1.0,'#ffe0a8')])
    img = sky.copy()
    img,_ = clouds(img,'#4a3f70','#fff0c8',sun=(0.62,0.80),coverage=0.52,height=(0.06,0.62),
                   seed=601,softness=1.2,tint='#c98aa0')
    img = sun_disc(img,0.62,0.795,0.030,core='#fffbe8',glow='#ff9d4d',power=1.15)
    img = god_rays(img,0.62,0.795,'#ffd79a',strength=0.30,seed=602,length=1.5)
    img,p = peak(img,0.36,0.86,0.44,0.19,'#3a3a63','#e2a184',0.42,snow='#fff4e2',snow_line=0.42,seed=603)
    img,_ = mountains(img,0.90,0.12,'#2b2a4e','#d59a86',0.30,seed=604,res=6)
    sky_for_water = img.copy()
    img = water(img,0.905,sky_for_water,'#3a2f4a',sun_x=0.62,sun_col='#ffd08a',ripple=0.9,seed=605)
    img = grass(img,1.03,'#241a2c',n=300,seed=606,hmax=0.15,rim='#ffc98a')
    return post(img,bloom=0.52,vig=0.32,warm=(1.05,1.00,0.97),contrast=1.07,seed=607,
                flare=(0.62,0.795,0.5,'#ffd9a0'))

# 07 白兎海岸・夕日の鳥居
def s07_hakuto_torii_sunset():
    sky = _sky([(0.0,'#2b2a63'),(0.2,'#5b3f78'),(0.42,'#b2547a'),(0.6,'#ee8055'),(0.76,'#ffb35f'),(1.0,'#ffd98f')])
    img = sky.copy()
    img,_ = clouds(img,'#5a3a64','#ffe9b4',sun=(0.34,0.70),coverage=0.55,height=(0.04,0.58),
                   seed=701,softness=1.15,tint='#d0748a')
    img = sun_disc(img,0.34,0.695,0.036,core='#fff4d2',glow='#ff7a3c',power=1.2)
    img,_ = mountains(img,0.70,0.08,'#3a2545','#e0906e',0.35,seed=702,res=6)
    sky_for_water = img.copy()
    img = water(img,0.705,sky_for_water,'#3d2a44',sun_x=0.34,sun_col='#ffcf87',ripple=1.2,seed=703)
    # 鳥居
    t=[[(0.60,1.00),(0.60,0.40),(0.635,0.40),(0.635,1.00)],
       [(0.80,1.00),(0.80,0.40),(0.835,0.40),(0.835,1.00)],
       [(0.565,0.40),(0.87,0.40),(0.87,0.435),(0.565,0.435)],
       [(0.585,0.475),(0.85,0.475),(0.85,0.505),(0.585,0.505)]]
    m = silhouette_mask(t,feather=0.9)
    img = over(img,'#2a1420',m)
    img = screen(img,'#ffc98a',blur(m,5)*0.22)
    rocks=[[(0.02,1.02),(0.05,0.66),(0.10,0.64),(0.14,1.02)]]
    rm = silhouette_mask(rocks,feather=1.2); img = over(img,'#2a1a24',rm)
    return post(img,bloom=0.55,vig=0.34,warm=(1.06,0.99,0.95),contrast=1.08,seed=704,
                flare=(0.34,0.695,0.55,'#ffd7a0'))

# 08 雨滝・光の滝（日本の滝百選）
def s08_amedaki_falls():
    sky = _sky([(0.0,'#c9dca8'),(0.22,'#a3c489'),(0.5,'#6d9a68'),(0.78,'#456e4d'),(1.0,'#2e4f3c')])
    img = sky.copy()
    img,_ = mountains(img,0.62,0.22,'#4d7a55','#b7cfa4',0.55,seed=801,res=4,sharp=1.2)
    img = trees(img,0.70,'#2f5238',n=28,seed=802,scale=1.5,rim='#cfe8a8')
    img = god_rays(img,0.36,0.00,'#fff9d2',strength=0.62,seed=803,length=1.9)
    # 峡谷の岩壁
    lwall=[[(-0.03,1.06),(-0.03,-0.03),(0.20,-0.03),(0.31,0.30),(0.28,0.66),(0.36,1.06)]]
    rwall=[[(1.03,1.06),(1.03,-0.03),(0.78,-0.03),(0.635,0.26),(0.675,0.68),(0.60,1.06)]]
    rock = fbm(H,W,res=(18,14),octaves=7,gain=0.58,seed=804)
    strat = 0.5+0.5*np.sin(NY*60 + fbm(H,W,res=(4,4),octaves=3,seed=814)*8)
    for poly,tone in ((lwall,'#33472c'),(rwall,'#27391f')):
        m=silhouette_mask(poly,1.2)
        c=hexc(tone)[None,None,:]*(0.28+1.75*rock[...,None])*(0.84+0.28*strat[...,None])
        img = img*(1-m[...,None]) + np.clip(c,0,1)*m[...,None]
        gy,gx=np.gradient(m)
        img = screen(img,'#d6ecae',blur(np.abs(gx)+np.abs(gy),3)*0.35)
    # 滝
    fall = np.exp(-(((NX-0.462)/0.038)**2))*np.clip((NY-0.10)*6,0,1)*np.clip((0.88-NY)*8,0,1)
    strk = fbm(H,W,res=(110,3),octaves=4,seed=805)
    img = screen(img,'#f4fcff',blur(fall*(0.45+strk*1.05),2.0)*1.0)
    img = screen(img,'#d2ecff',blur(fall,18)*0.5)
    side = np.exp(-(((NX-0.532)/0.014)**2))*np.clip((NY-0.30)*6,0,1)*np.clip((0.86-NY)*8,0,1)
    img = screen(img,'#eaf7ff',blur(side*(0.4+strk),2)*0.6)
    # 滝壺
    mist = np.exp(-((NY-0.88)*7)**2)*np.exp(-(((NX-0.47)/0.22)**2))
    img = screen(img,'#e8f4ff',blur(mist,26)*0.9)
    pool = np.clip((NY-0.905)*9,0,1)
    img = over(img,'#22453a',pool*0.85)
    rip=(fbm(H,W,res=(70,10),octaves=3,seed=806)>0.58).astype(float)*pool
    img = screen(img,'#cdeae2',blur(rip,2)*0.45)
    img = grass(img,1.06,'#12211a',n=200,seed=807,hmax=0.11,rim='#cfe8a8')
    return post(img,bloom=0.52,vig=0.44,warm=(0.99,1.03,0.98),contrast=1.08,seed=808,
                flare=(0.36,0.02,0.42,'#fff2c8'))

# 09 大山・雪の朝（冬の荒野）
def s09_daisen_snow():
    sky = _sky([(0.0,'#3d4f77'),(0.3,'#6e7fa0'),(0.6,'#adb9cc'),(0.85,'#dfe3ea'),(1.0,'#f2f2f2')])
    img = sky.copy()
    img,_ = clouds(img,'#5a6a8c','#ffffff',sun=(0.72,0.22),coverage=0.6,height=(0.0,0.5),
                   seed=901,softness=1.6,tint='#c6cfdd')
    img = sun_disc(img,0.72,0.22,0.026,core='#ffffff',glow='#cfd9ea',power=0.7,disc=False)
    img,_ = peak(img,0.42,0.72,0.40,0.20,'#6a7a95','#d2dae6',0.38,snow='#f4f8ff',snow_line=0.30,seed=902)
    img,_ = mountains(img,0.78,0.09,'#a8b4c6','#e8edf4',0.55,seed=903,res=6)
    # 雪原
    fieldm = np.clip((NY-0.78)*8,0,1)
    tex = fbm(H,W,res=(6,12),octaves=5,seed=904)
    img = over(img,'#f4f7fb',fieldm*(0.85+0.15*tex))
    shade = np.clip((tex-0.55)*1.6,0,1)*fieldm
    img = over(img,'#b9c6d8',blur(shade,8)*0.5)
    img = trees(img,0.90,'#4a5568',n=14,seed=905,scale=1.1)
    img = snowfall(img,n=1600,seed=906)
    return post(img,bloom=0.44,vig=0.30,warm=(0.98,1.00,1.05),contrast=1.06,seed=907)

# 10 倉吉・白壁土蔵群の冬夕
def s10_kurayoshi_storehouses():
    sky = _sky([(0.0,'#1e2b50'),(0.26,'#45426f'),(0.52,'#8a5872'),(0.72,'#cd8264'),(1.0,'#f2bd8a')])
    img = sky.copy()
    img,_ = clouds(img,'#3a3663','#ffdcac',sun=(0.5,0.60),coverage=0.48,height=(0.03,0.46),
                   seed=1001,softness=1.3,tint='#9d6478')
    img = sun_disc(img,0.50,0.60,0.018,core='#ffeccb',glow='#ff9350',power=0.6,disc=False)
    from PIL import ImageDraw
    body=[]; roof=[]; eave=[]
    xs=-0.02; r=np.random.default_rng(1002)
    while xs<1.02:
        w_=0.10+r.random()*0.08; top=0.50+r.random()*0.08
        body.append([(xs,0.90),(xs,top),(xs+w_,top),(xs+w_,0.90)])
        roof.append([(xs-0.016,top+0.012),(xs+w_/2,top-0.052),(xs+w_+0.016,top+0.012)])
        eave.append([(xs-0.016,top+0.012),(xs+w_+0.016,top+0.012),(xs+w_+0.016,top+0.024),(xs-0.016,top+0.024)])
        xs+=w_+0.006
    bm=silhouette_mask(body,0.6); rm=silhouette_mask(roof,0.6); em=silhouette_mask(eave,0.5)
    img,_ = mountains(img,0.62,0.10,'#3b3550','#8a6a78',0.45,seed=1008,res=6)
    img = over(img,'#e6d7ba',bm*0.95)
    shadetex = fbm(H,W,res=(3,9),octaves=4,seed=1007)
    img = over(img,'#9d8a6e',bm*np.clip((shadetex-0.42)*1.4,0,1)*0.30)
    img = over(img,'#5a4a3c',bm*np.clip((NY-0.755)*9,0,1)*0.88)     # 黒い腰板
    img = over(img,'#9a8464',bm*np.clip((NY-0.63)*4,0,1)*0.30)      # 壁の陰
    img = over(img,'#1b1d29',rm); img = over(img,'#14161f',em)
    # なまこ壁の格子（下半分だけ・控えめ）
    grid=((np.abs(np.sin(NX*W/34))>0.93)|(np.abs(np.sin(NY*H/34))>0.93)).astype(float)
    grid*=bm*np.clip((NY-0.60)*4,0,1)
    img = over(img,'#7d6a55',blur(grid,1.4)*0.14)
    # 窓明かり
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im); r2=np.random.default_rng(1003)
    for b in body:
        if r2.random()<0.7:
            x0=b[0][0]+0.028; y0=b[1][1]+0.075
            d.rectangle([x0*W,y0*H,(x0+0.030)*W,(y0+0.042)*H],fill=255)
    win=blur(np.asarray(im).astype(np.float64)/255,1.2)
    img = screen(img,'#ffc276',win*0.95)
    img = screen(img,'#ff8f3c',blur(win,18)*0.45)
    # 玉川と石橋
    sky_for_water=img.copy()
    img = water(img,0.90,sky_for_water,'#2a2740',sun_x=0.5,sun_col='#ffbe80',ripple=0.6,seed=1004)
    img = snowfall(img,n=800,seed=1005,col='#ffe9d0')
    return post(img,bloom=0.46,vig=0.38,warm=(1.04,1.00,0.98),contrast=1.07,seed=1006)

# 11 中海・雷鳴の海（米子）
def s11_nakaumi_storm():
    sky = _sky([(0.0,'#161a2e'),(0.3,'#2a2f4d'),(0.55,'#4a4a68'),(0.78,'#7a6f7d'),(1.0,'#a08f8a')])
    img = sky.copy()
    img,_ = clouds(img,'#1b2038','#dfe4ff',sun=(0.62,0.30),coverage=0.74,height=(0.0,0.55),
                   seed=1101,softness=1.7,density=1.25,tint='#3d4460')
    # 稲妻
    from PIL import ImageDraw
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    r=np.random.default_rng(1102); x,y=0.62,0.06
    while y<0.56:
        nx_,ny_=x+(r.random()-0.5)*0.07, y+0.03+r.random()*0.045
        d.line([(x*W,y*H),(nx_*W,ny_*H)],fill=255,width=5)
        if r.random()<0.3:
            d.line([(nx_*W,ny_*H),((nx_+(r.random()-0.5)*0.1)*W,(ny_+0.06)*H)],fill=200,width=3)
        x,y=nx_,ny_
    bolt=np.asarray(im).astype(np.float64)/255
    img = screen(img,'#ffffff',blur(bolt,1.5))
    img = screen(img,'#b9c8ff',blur(bolt,30)*0.55)
    img,_ = mountains(img,0.60,0.09,'#171b30','#4a5068',0.4,seed=1103,res=5)
    sky_for_water=img.copy()
    img = water(img,0.615,sky_for_water,'#141a2e',sun_x=0.62,sun_col='#c9d6ff',ripple=1.8,seed=1104)
    foam=(fbm(H,W,res=(70,9),octaves=4,seed=1105)>0.60).astype(float)
    foam*=np.clip((NY-0.62)*3.2,0,1)
    img = screen(img,'#dbe6ff',blur(foam,2.2)*0.6)
    img = rain(img,n=700,seed=1106)
    return post(img,bloom=0.42,vig=0.46,warm=(0.96,0.99,1.08),contrast=1.10,seed=1107)

# 12 皆生温泉・荒波の海岸
def s12_kaike_waves():
    sky = _sky([(0.0,'#233156'),(0.3,'#3f4d74'),(0.58,'#7d7c93'),(0.8,'#c99a86'),(1.0,'#f0c295')])
    img = sky.copy()
    img,_ = clouds(img,'#2c3a60','#ffe2bd',sun=(0.78,0.60),coverage=0.58,height=(0.02,0.55),
                   seed=1201,softness=1.4,tint='#6a6c8a')
    img = sun_disc(img,0.78,0.60,0.024,core='#fff0d4',glow='#ff9a5e',power=0.85,disc=False)
    img,p = peak(img,0.22,0.64,0.26,0.15,'#2f3a5c','#9aa0b4',0.55,snow='#e8eef6',snow_line=0.45,seed=1202)
    sky_for_water=img.copy()
    img = water(img,0.645,sky_for_water,'#26314e',sun_x=0.78,sun_col='#ffcf95',ripple=1.6,seed=1203)
    # 打ち寄せる白波（横に長い帯）
    for yb,st,fr in [(0.70,0.35,26),(0.755,0.45,18),(0.83,0.60,12),(0.94,0.75,8)]:
        wob = fbm1d(W,res=fr,octaves=4,gain=0.5,seed=int(yb*1000))
        wob = (wob-wob.min())/(np.ptp(wob)+1e-9)
        yline = yb + (wob[None,:]-0.5)*0.016
        band = np.exp(-((NY-yline)*(190-yb*90))**2)
        det = fbm(H,W,res=(30,40),octaves=3,seed=int(yb*777))
        img = screen(img,'#eef5ff',blur(band*(0.55+det*0.8),2.0)*st)
        img = screen(img,'#cfe0f5',blur(band,14)*st*0.35)
    sand=np.clip((NY-0.965)*22,0,1)
    img = over(img,'#6a5a52',sand*0.8)
    return post(img,bloom=0.46,vig=0.36,warm=(1.03,1.00,0.99),contrast=1.07,seed=1204,
               flare=(0.78,0.60,0.35,'#ffd6a8'))

# 13 鳥取砂丘・黄金の日の出（再生）
def s13_dunes_sunrise_gold():
    sky = _sky([(0.0,'#2a3f7a'),(0.18,'#6b5f9a'),(0.38,'#c9738a'),(0.55,'#f79a5c'),(0.72,'#ffc978'),(1.0,'#ffeec4')])
    img = sky.copy()
    img,_ = clouds(img,'#5c4a86','#fff3cf',sun=(0.55,0.60),coverage=0.5,height=(0.02,0.55),
                   seed=1301,softness=1.1,tint='#e0879a')
    img = sun_disc(img,0.55,0.60,0.042,core='#fffbe6',glow='#ff8f36',power=1.35)
    img = god_rays(img,0.55,0.60,'#ffdba0',strength=0.34,seed=1302,length=1.6)
    sky_for_water=img.copy()
    img = water(img,0.615,sky_for_water,'#5a4a5e',sun_x=0.55,sun_col='#ffd79a',ripple=1.1,seed=1303)
    img = dunes(img,[(0.70,0.075,4,1304),(0.83,0.11,3,1305),(1.06,0.17,2,1306)],
                sand='#e0a86a',shade='#7a4a30',lit='#fff0c0')
    img = grass(img,1.05,'#5a3520',n=220,seed=1307,hmax=0.13,rim='#ffd79a')
    return post(img,bloom=0.60,vig=0.30,warm=(1.07,1.01,0.95),contrast=1.08,seed=1308,
                flare=(0.55,0.60,0.7,'#ffe0ac'))

# 14 若桜鉄道・夏雲の田園
def s14_wakasa_railway():
    sky = _sky([(0.0,'#2a6fd6'),(0.25,'#5b9ae8'),(0.5,'#9fc9f5'),(0.72,'#d8ecfb'),(1.0,'#eef7fd')])
    img = sky.copy()
    img,_ = clouds(img,'#8fb4dd','#ffffff',sun=(0.30,0.14),coverage=0.60,height=(0.02,0.52),
                   seed=1401,softness=1.0,res=(3,4),tint='#ffffff')
    img = sun_disc(img,0.30,0.14,0.02,core='#ffffff',glow='#fff0c0',power=0.75,disc=False)
    img,_ = mountains(img,0.66,0.16,'#4a6f4e','#bcd4e6',0.5,seed=1402,res=4,sharp=1.2)
    img,_ = mountains(img,0.72,0.09,'#3c5c40','#a8c4d8',0.3,seed=1403,res=7)
    # 田んぼ
    fieldm=np.clip((NY-0.72)*8,0,1)
    tex=fbm(H,W,res=(8,14),octaves=5,seed=1404)
    img = over(img,'#7fae4e',fieldm*(0.85+0.2*tex))
    rows=(np.sin((NY-0.72)*H/9.0)>0.4).astype(float)*fieldm*np.clip((NY-0.78)*4,0,1)
    img = over(img,'#5d8a38',blur(rows,1.2)*0.35)
    # 築堤と列車
    emb=[[(0.0,0.80),(1.0,0.735),(1.0,0.80),(0.0,0.855)]]
    em=silhouette_mask(emb,1.0); img = over(img,'#6a6350',em*0.9)
    tr=[[(0.40,0.752),(0.40,0.700),(0.42,0.688),(0.62,0.679),(0.64,0.690),(0.64,0.742)]]
    tm=silhouette_mask(tr,0.8)
    img = over(img,'#c0392b',tm)
    win=[[(0.43,0.706),(0.61,0.699),(0.61,0.718),(0.43,0.725)]]
    wm=silhouette_mask(win,0.6); img = over(img,'#f6e7c8',wm*0.9)
    img = screen(img,'#ffe9b8',blur(tm+wm,10)*0.18)
    img = grass(img,1.04,'#3f5c2c',n=340,seed=1405,hmax=0.16,rim='#dff0a0')
    return post(img,bloom=0.40,vig=0.28,warm=(1.00,1.02,1.02),contrast=1.06,seed=1406,
                flare=(0.30,0.14,0.3,'#ffffff'))

# 15 境港・水木しげるロードの夜
def s15_mizuki_road_night():
    sky = _sky([(0.0,'#0a1130'),(0.32,'#151e46'),(0.6,'#28315e'),(1.0,'#3d3f70')])
    img = sky.copy()
    img = stars(img,density=0.00020,seed=1501,ymax=0.36,twinkle=0.7)
    img,_ = clouds(img,'#141b3e','#8b98d0',sun=(0.5,0.9),coverage=0.34,height=(0.0,0.30),
                   seed=1502,softness=1.5,tint='#28315c')
    from PIL import ImageDraw
    # 両側の町並み（軒の高さを1軒ずつ変える）
    r=np.random.default_rng(1503)
    facades=[]; roofs=[]
    for side in (0,1):
        x = -0.03 if side==0 else 1.03
        step = 0.075 if side==0 else -0.075
        for k in range(7):
            t0 = k/7.0; t1 = (k+1)/7.0
            if side==0:
                x0,x1 = -0.03+t0*0.45, -0.03+t1*0.45
                y0,y1 = 0.13+t0*0.30, 0.13+t1*0.30
            else:
                x0,x1 = 1.03-t0*0.45, 1.03-t1*0.45
                y0,y1 = 0.11+t0*0.31, 0.11+t1*0.31
            j = r.random()*0.045
            facades.append([(x0,1.06),(x0,y0+j),(x1,y1+j),(x1,1.06)])
            roofs.append([(x0-0.012,y0+j+0.012),(x0,y0+j-0.030),(x1,y1+j-0.030),(x1+0.012,y1+j+0.012)])
    fm=silhouette_mask(facades,0.9); rmk=silhouette_mask(roofs,0.8)
    img = over(img,'#20294f',fm)
    img = over(img,'#0f1430',rmk)
    # 軒下に落ちる暖色の照り返し
    warmspill = fm*np.clip((NY-0.34)*2.2,0,1)
    img = screen(img,'#ff9c4e',blur(warmspill,26)*0.30)
    gy,gx=np.gradient(rmk)
    img = screen(img,'#6d7cc0',blur(np.abs(gy)+np.abs(gx),2.5)*0.55)
    # 店の灯り
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    for side in (0,1):
        for k in range(18):
            t=k/18 + r.random()*0.04
            if side==0: x=-0.02+t*0.44; ytop=0.13+t*0.30
            else: x=1.02-t*0.44; ytop=0.11+t*0.31
            for row in range(2):
                y=ytop+0.055+row*0.085+r.random()*0.015
                w_=0.009+0.013*t; h_=0.014+0.018*t
                d.rectangle([x*W,y*H,(x+w_)*W,(y+h_)*H],fill=int(150+r.random()*105))
    lights=blur(np.asarray(im).astype(np.float64)/255,1.0)
    img = screen(img,'#ffd28e',lights)
    img = screen(img,'#ff9a48',blur(lights,20)*0.6)
    # 街灯
    lamp=np.zeros((H,W))
    for lx,ly,rr in [(0.08,0.62,0.050),(0.28,0.50,0.032),(0.72,0.49,0.032),(0.92,0.61,0.050)]:
        lamp+=radial(lx,ly,rr,2.0)
    lamp=np.clip(lamp,0,1)
    img = screen(img,'#ffe6b4',lamp*0.95)
    img = screen(img,'#ffb066',blur(lamp,40)*0.55)
    # 濡れた石畳
    road=np.clip((NY-0.42)*3.0,0,1)
    img = over(img,'#0c1132',road*np.clip(1-np.abs(NX-0.5)*0.9,0,1)*0.9)
    refl=np.zeros((H,W))
    for lx,ly in [(0.08,0.62),(0.28,0.50),(0.72,0.49),(0.92,0.61)]:
        refl+=np.exp(-(((NX-lx)*24)**2))*np.clip((NY-ly-0.05)*2.0,0,1)
    refl+=np.clip((NY-0.55)*1.6,0,1)*np.exp(-(((NX-0.5)*3.2)**2))*0.5
    streak=fbm(H,W,res=(90,4),octaves=3,seed=1504)
    img = screen(img,'#ffc178',blur(refl*(0.32+streak*1.15),5)*0.75)
    return post(img,bloom=0.52,vig=0.46,warm=(1.03,0.99,1.02),contrast=1.08,seed=1505)

# 16 大山・天の川（桝水高原の星空）
def s16_daisen_milkyway():
    sky = _sky([(0.0,'#050a18'),(0.35,'#0a1228'),(0.68,'#121d3f'),(1.0,'#223057')])
    img = sky.copy()
    img = milky_way(img,seed=1601)
    img = milky_way(img,seed=1611)
    img = stars(img,density=0.00110,seed=1602,ymax=0.86,twinkle=1.3)
    img = sun_disc(img,0.18,0.16,0.006,core='#ffffff',glow='#8ea6e0',power=0.5)
    img,_ = peak(img,0.62,0.92,0.34,0.22,'#0d1329','#2c3859',0.35,snow='#7b89ae',snow_line=0.42,seed=1603)
    img,_ = mountains(img,0.96,0.10,'#070a14','#182042',0.25,seed=1604,res=6)
    img = over(img,'#090d1c',np.clip((NY-0.955)*14,0,1))
    img = grass(img,1.03,'#05070f',n=300,seed=1605,hmax=0.14,rim='#5d719f')
    img = screen(img,'#93a9dd',radial(0.62,0.60,0.40,2.0)*0.13)
    return post(img,bloom=0.40,vig=0.48,warm=(0.96,0.98,1.10),contrast=1.12,seed=1606,grain=0.016)

# 17 賀露港の朝・金蓮の光（終曲）
def s17_karo_port_dawn():
    sky = _sky([(0.0,'#3a4f8c'),(0.2,'#7d6fa8'),(0.4,'#d68f8a'),(0.58,'#ffb877'),(0.75,'#ffdca0'),(1.0,'#fff2d6')])
    img = sky.copy()
    img,_ = clouds(img,'#6a5a96','#fffbe8',sun=(0.48,0.62),coverage=0.46,height=(0.02,0.55),
                   seed=1701,softness=1.15,tint='#e8a394')
    img = sun_disc(img,0.48,0.62,0.05,core='#ffffff',glow='#ffa851',power=1.5)
    img = god_rays(img,0.48,0.62,'#ffeec4',strength=0.40,seed=1702,length=1.8)
    img,_ = mountains(img,0.655,0.055,'#5a4a70','#f0b48e',0.45,seed=1703,res=7)
    sky_for_water=img.copy()
    img = water(img,0.66,sky_for_water,'#6a5570',sun_x=0.48,sun_col='#ffe2ae',ripple=0.9,seed=1704)
    # 防波堤と灯台、漁船
    bw=[[(0.0,0.70),(0.34,0.685),(0.34,0.715),(0.0,0.735)]]
    bm=silhouette_mask(bw,0.9); img = over(img,'#4a3a4e',bm)
    lh=[[(0.30,0.688),(0.305,0.60),(0.325,0.60),(0.33,0.688)],
        [(0.298,0.60),(0.332,0.60),(0.332,0.578),(0.298,0.578)]]
    lm=silhouette_mask(lh,0.6); img = over(img,'#f2f2ee',lm*0.85)
    img = screen(img,'#ff6f4a',radial(0.315,0.586,0.03,2.0)*0.8)
    boats=[[(0.70,0.70),(0.78,0.70),(0.77,0.72),(0.71,0.72)],
           [(0.735,0.70),(0.745,0.655),(0.752,0.70)]]
    bo=silhouette_mask(boats,0.6); img = over(img,'#3f3050',bo)
    # 金の蓮（光の花）
    lot=np.zeros((H,W))
    ang=np.arctan2(NY-0.60,(NX-0.48)*(W/H)); d0=np.sqrt(((NX-0.48)*(W/H))**2+(NY-0.60)**2)
    lot=np.clip(1-d0/(0.16*(0.6+0.4*np.abs(np.cos(ang*8)))),0,1)**2
    img = screen(img,'#ffe6a8',blur(lot,10)*0.32)
    return post(img,bloom=0.62,vig=0.28,warm=(1.06,1.01,0.96),contrast=1.06,seed=1705,
                flare=(0.48,0.62,0.8,'#ffe4b4'))

SCENES = [
    ('01_togo_lake_blue_hour','東郷湖の夜明け前', s01_togo_lake_blue_hour),
    ('02_uradome_night','浦富海岸の夜', s02_uradome_night),
    ('03_dunes_night','鳥取砂丘 月夜の馬の背', s03_dunes_night),
    ('04_dunes_sandstorm','鳥取砂丘 砂嵐', s04_dunes_sandstorm),
    ('05_nageiredo_mist','三徳山三仏寺 投入堂', s05_nageiredo_mist),
    ('06_daisen_dawn_gold','大山 暁の黄金', s06_daisen_dawn_gold),
    ('07_hakuto_torii_sunset','白兎海岸 夕日の鳥居', s07_hakuto_torii_sunset),
    ('08_amedaki_falls','雨滝', s08_amedaki_falls),
    ('09_daisen_snow','大山 雪の朝', s09_daisen_snow),
    ('10_kurayoshi_storehouses','倉吉 白壁土蔵群', s10_kurayoshi_storehouses),
    ('11_nakaumi_storm','中海 雷鳴', s11_nakaumi_storm),
    ('12_kaike_waves','皆生温泉 荒波', s12_kaike_waves),
    ('13_dunes_sunrise_gold','鳥取砂丘 黄金の日の出', s13_dunes_sunrise_gold),
    ('14_wakasa_railway','若桜鉄道 夏雲', s14_wakasa_railway),
    ('15_mizuki_road_night','境港 水木しげるロード', s15_mizuki_road_night),
    ('16_daisen_milkyway','大山 天の川', s16_daisen_milkyway),
    ('17_karo_port_dawn','賀露港の朝', s17_karo_port_dawn),
]

if __name__ == '__main__':
    import sys, os, time
    os.makedirs('frames', exist_ok=True)
    only = sys.argv[1:] 
    for key, name, fn in SCENES:
        if only and not any(o in key for o in only): continue
        t0=time.time(); img = fn(); to_image(img).save(f'frames/{key}.jpg', quality=93)
        print(f"{key} {name} {time.time()-t0:.1f}s")
