# -*- coding: utf-8 -*-
"""台湾のキャンパス 18 景 v2 — 中原大学を軸に。質感・奥行き・人の気配を入れる。"""
import numpy as np
from art import *
from PIL import ImageDraw
from scenes import windows, building, avenue, palm, road

def _sky(s): return vgrad(s)

def hills(img, y, amp, near, far, haze, seed, res=4, sharp=1.15, tex=0.10):
    img, top = mountains(img, y, amp, near, far, haze, seed=seed, res=res, sharp=sharp)
    m = (NY > top[None,:]).astype(float)
    return texture(img, blur(m,1.0), seed=seed+31, amount=tex, res=(9,7))

def lawn(img, y, col='#5f8a45', dark='#3d5c2c', seed=21, rim=None):
    m = np.clip((NY-y)*22,0,1)
    img = over(img, col, m*0.96)
    img = texture(img, m, seed=seed, amount=0.17, res=(7,11), tint=dark)
    img = grass(img, min(1.06, y+0.34), '#33501f', n=260, seed=seed+3, hmax=0.055, rim=rim)
    return img

def gate_arch(img, cx=0.5, y_top=0.30, y_bot=0.66, half=0.30, col='#8d8272',
              beam='#6f6556', sun=(0.5,0.3), seed=5, sign='#a83a32'):
    """角柱二本＋横長の看板梁。鳥居ではなく、台湾の大学の門のかたち。"""
    posts=[]
    for sgn in (-1,1):
        x = cx + sgn*half
        posts.append([(x-0.028, y_bot),(x-0.024, y_top-0.010),(x+0.024, y_top-0.010),(x+0.028, y_bot)])
    beam_poly=[(cx-half-0.030, y_top-0.010),(cx+half+0.030, y_top-0.010),
               (cx+half+0.030, y_top+0.062),(cx-half-0.030, y_top+0.062)]
    top_slab=[(cx-half-0.048, y_top-0.034),(cx+half+0.048, y_top-0.034),
              (cx+half+0.048, y_top-0.010),(cx-half-0.048, y_top-0.010)]
    mp=silhouette_mask(posts,0.7); mb=silhouette_mask([beam_poly],0.7); mt=silhouette_mask([top_slab],0.6)
    img=over(img,col,mp); img=over(img,beam,mb); img=over(img,'#4f4739',mt)
    m=np.clip(mp+mb+mt,0,1)
    img=texture(img,m,seed=seed,amount=0.15,res=(12,14))
    img=edge_light(img,m,sun=sun,col='#ffe6bc',strength=0.6)
    img=occlusion(img,m,strength=0.32)
    # 校名の板（字は読ませず、気配だけ）
    plate=silhouette_mask([[(cx-0.150,y_top+0.004),(cx+0.150,y_top+0.004),
                            (cx+0.150,y_top+0.050),(cx-0.150,y_top+0.050)]],0.5)
    img=over(img,sign,plate)
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    for i in range(4):
        x=cx-0.116+i*0.066
        d.rectangle([x*W,(y_top+0.013)*H,(x+0.034)*W,(y_top+0.042)*H],fill=255)
    a=blur(np.asarray(im).astype(np.float64)/255,1.2)
    img=screen(img,'#fff0cc',a*0.85)
    return img, m

# ---------------------------------------------------------------- 中原
def s01_cycu_gate_dawn():
    img=_sky([(0.0,'#20325f'),(0.18,'#4d5588'),(0.40,'#9b6f8e'),(0.60,'#e6926f'),(0.80,'#ffc98d'),(1.0,'#ffe9c8')])
    img,_=clouds(img,'#4a4b7c','#fff2d4',sun=(0.62,0.60),coverage=0.52,height=(0.02,0.50),
                 seed=101,softness=1.15,tint='#cf8a86')
    img=sun_disc(img,0.62,0.60,0.030,core='#fffbe8',glow='#ff9a4e',power=1.15)
    img=god_rays(img,0.62,0.60,'#ffdca8',strength=0.24,seed=102,length=1.5)
    img=hills(img,0.615,0.075,'#4a4870','#e8a888',0.46,seed=103,res=7)
    img,_=persp_building(img,0.02,0.30,0.40,0.66,vp=(0.55,0.60),depth=0.20,
                         face='#6d6480',side='#544d66',roof='#332f42',
                         win_cols=5,win_rows=4,win_p=0.45,seed=104,sun=(0.62,0.60))
    img,_=persp_building(img,0.74,0.99,0.44,0.66,vp=(0.45,0.60),depth=0.20,
                         face='#6a6178',side='#4f4960',roof='#332f42',
                         win_cols=4,win_rows=3,win_p=0.4,seed=105,sun=(0.62,0.60))
    img=trees(img,0.665,'#2b2b40',n=28,seed=106,scale=1.0,rim='#ffcf95',band=0.07)
    img,pm=paving(img,0.655,1.06,'#7d7468',line='#5f584e',centre=0.5,w0=0.10,w1=1.5,rows=14,seed=107)
    img,_=gate_arch(img,0.5,0.335,0.665,0.235,sun=(0.62,0.60),seed=108)
    img=people(img,[(0.40,0.80,0.081),(0.46,0.78,0.071),(0.62,0.85,0.096),(0.70,0.74,0.056)],
               col='#241f2e',seed=109,rim='#ffcf95')
    img=power_lines(img,y0=0.20,sag=0.035,n=4,col='#2a2436',seed=110)
    img=motes(img,n=150,seed=111,ymax=0.9)
    img=foreground_leaves(img,'left',col='#241a2a',seed=112,scale=1.05,blur_px=30,alpha=0.62)
    img=dof(img,far=0.62,amount=1.6)
    return post(img,bloom=0.52,vig=0.36,warm=(1.05,1.00,0.97),contrast=1.07,seed=113,
                flare=(0.62,0.60,0.5,'#ffd9a8'))

def s02_cycu_avenue():
    img=_sky([(0.0,'#2f6ec9'),(0.22,'#68a0e2'),(0.5,'#accdec'),(0.74,'#e6effa'),(1.0,'#f8f0dd')])
    img,_=clouds(img,'#8fb4dd','#ffffff',sun=(0.40,0.24),coverage=0.5,height=(0.0,0.42),
                 seed=201,softness=1.05,res=(3,4),tint='#ffffff')
    img=sun_disc(img,0.40,0.24,0.026,core='#fffdf2',glow='#ffd08a',power=1.0)
    img=god_rays(img,0.40,0.24,'#ffeec8',strength=0.28,seed=202,length=1.6)
    img=hills(img,0.575,0.055,'#6d8a72','#cfdde8',0.55,seed=203,res=7)
    img,_=persp_building(img,0.60,0.98,0.28,0.60,vp=(0.42,0.56),depth=0.22,
                         face='#cfc6b2',side='#a79e8c',roof='#4a4550',
                         win_cols=8,win_rows=6,win_p=0.30,win_col='#cfe0f0',seed=204,sun=(0.40,0.24))
    img=lawn(img,0.585,'#6d9a4c','#446b2c',seed=205,rim='#dff0a8')
    img,_=paving(img,0.60,1.06,'#a8a094',line='#857e72',centre=0.44,w0=0.06,w1=1.1,rows=15,seed=206)
    # 楓香道の並木
    rows=[]
    n=8
    for i in range(n):
        t=(i/(n-1))**1.8
        rows.append((0.44-(0.055+t*0.52), 0.44+(0.055+t*0.52), 0.60+t*0.40, 0.10+t*0.46, 0.005+t*0.020))
    img,tm=avenue(img,rows,'#2a3a24',rim='#e6f4b0',seed=207)
    can=np.zeros((H,W))
    for i in range(n):
        t=(i/(n-1))**1.8
        for s in (-1,1):
            can+=radial(0.44+s*(0.055+t*0.52), 0.60+t*0.40-(0.10+t*0.46), 0.045+t*0.13, 1.4)
    tex=fbm(H,W,res=(9,14),octaves=6,seed=208)
    can=np.clip(can*(0.5+tex*1.1)-0.22,0,1)
    img=over(img,'#2f5127',blur(can,4))
    img=screen(img,'#cfe89a',blur(np.clip(can-blur(can,14),0,1),3)*0.6)
    img=people(img,[(0.30,0.86,0.099),(0.36,0.80,0.074),(0.58,0.92,0.124)],col='#1e2a1c',seed=209,rim='#dff0a8')
    img=motes(img,n=160,seed=210,ymax=0.85)
    img=dof(img,far=0.58,amount=1.5)
    return post(img,bloom=0.46,vig=0.30,warm=(1.02,1.02,0.99),contrast=1.06,seed=211,
                flare=(0.40,0.24,0.42,'#fff0cc'))

def s03_cycu_bikes():
    img=_sky([(0.0,'#3d7fd0'),(0.26,'#7fb0e8'),(0.56,'#bcd8f2'),(0.82,'#eaf2fb'),(1.0,'#fbf5e8')])
    img,_=clouds(img,'#8fb4dd','#ffffff',sun=(0.80,0.20),coverage=0.55,height=(0.0,0.42),
                 seed=301,softness=1.0,res=(3,4),tint='#ffffff')
    img=sun_disc(img,0.80,0.20,0.022,core='#ffffff',glow='#ffe1a8',power=0.85,disc=False)
    img,_=persp_building(img,0.0,0.42,0.16,0.62,vp=(0.62,0.58),depth=0.20,
                         face='#c3bcae',side='#9c9587',roof='#4a4550',
                         win_cols=6,win_rows=7,win_p=0.28,win_col='#cfe0f0',seed=302,sun=(0.80,0.20))
    img=trees(img,0.625,'#3f6136',n=26,seed=303,scale=1.0,rim='#dff0a8',band=0.075)
    img=lawn(img,0.63,'#75a052','#4a7030',seed=304)
    img,_=paving(img,0.655,1.06,'#a5a9a4',line='#83877f',centre=0.55,w0=0.10,w1=1.3,rows=13,seed=305)
    # 自転車の列（前後で大きさが変わる）
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    r=np.random.default_rng(306)
    for i in range(30):
        t=(i/29)**1.5
        x=0.16+t*0.80+r.random()*0.008; yb=0.70+t*0.28; s=0.020+t*0.070
        lw=max(2,int(2+t*9))
        d.ellipse([(x-s)*W,(yb-s*0.92)*H,(x-s*0.08)*W,(yb+s*0.92)*H],outline=255,width=lw)
        d.ellipse([(x+s*0.08)*W,(yb-s*0.92)*H,(x+s)*W,(yb+s*0.92)*H],outline=255,width=lw)
        d.line([(x-s*0.5)*W,yb*H,(x+s*0.5)*W,yb*H],fill=255,width=lw)
        d.line([(x-s*0.5)*W,yb*H,(x-s*0.1)*W,(yb-s*1.35)*H],fill=255,width=lw)
        d.line([(x+s*0.5)*W,yb*H,(x+s*0.15)*W,(yb-s*1.35)*H],fill=255,width=lw)
        d.line([(x-s*0.45)*W,(yb-s*1.35)*H,(x+s*0.15)*W,(yb-s*1.30)*H],fill=255,width=lw)
    a=blur(np.asarray(im).astype(np.float64)/255,1.0)
    img=over(img,'#2b3340',np.clip(a*1.2,0,1))
    img=screen(img,'#ffeec0',blur(a,4)*0.30)
    img=occlusion(img,np.clip(a,0,1),strength=0.28,r=10)
    img=people(img,[(0.30,0.80,0.087),(0.72,0.95,0.136)],col='#232b36',seed=307,rim='#ffeec0')
    img=motes(img,n=120,seed=308,ymax=0.8)
    img=foreground_leaves(img,'right',col='#1c2a18',seed=309,scale=0.95,blur_px=26,alpha=0.58)
    return post(img,bloom=0.42,vig=0.32,warm=(1.01,1.01,1.00),contrast=1.06,seed=310)

def s04_cycu_classroom():
    img=_sky([(0.0,'#4a86cf'),(0.3,'#8fbbe6'),(0.62,'#cfe2f2'),(0.88,'#f0eee2'),(1.0,'#f8f0d8')])
    img,_=clouds(img,'#93b7dd','#ffffff',sun=(0.16,0.18),coverage=0.46,height=(0.0,0.40),
                 seed=401,softness=1.1,tint='#ffffff')
    img=god_rays(img,0.14,0.10,'#fff6d0',strength=0.34,seed=402,length=1.7)
    img,_=persp_building(img,0.10,0.72,0.14,0.86,vp=(0.86,0.52),depth=0.26,
                         face='#cbbfa6',side='#a2967e',roof='#40404c',
                         win_cols=9,win_rows=8,win_p=0.34,win_col='#d8e8f6',seed=403,sun=(0.16,0.18))
    # 庇のライン
    bm=silhouette_mask([[(0.10,0.14),(0.72,0.14),(0.72,0.86),(0.10,0.86)]],0.8)
    slab=((np.sin(NY*H/52.0)>0.74)).astype(float)*bm
    img=over(img,'#8d8371',blur(slab,1.2)*0.42)
    img=trees(img,0.885,'#33512c',n=24,seed=404,scale=1.0,rim='#e6f4b0',band=0.07)
    img=lawn(img,0.89,'#6b9648','#456c2c',seed=405)
    img,_=paving(img,0.93,1.06,'#a8a294',line='#847e70',centre=0.5,w0=0.5,w1=1.6,rows=6,seed=406)
    img=people(img,[(0.80,0.99,0.118),(0.87,0.96,0.096),(0.24,0.95,0.074)],col='#232b22',seed=407,rim='#e6f4b0')
    img=motes(img,n=150,seed=408,ymax=0.8)
    img=foreground_leaves(img,'both',col='#1a2716',seed=409,scale=1.0,blur_px=30,alpha=0.62)
    return post(img,bloom=0.44,vig=0.32,warm=(1.01,1.01,1.00),contrast=1.06,seed=410,
                flare=(0.14,0.10,0.40,'#fff2cc'))

def s05_cycu_library_day():
    img=_sky([(0.0,'#3f79c8'),(0.28,'#82abe0'),(0.6,'#c6dbee'),(0.86,'#eef0ea'),(1.0,'#f6eedc')])
    img,_=clouds(img,'#8fb0d6','#ffffff',sun=(0.72,0.22),coverage=0.5,height=(0.0,0.42),
                 seed=501,softness=1.1,tint='#ffffff')
    img=sun_disc(img,0.72,0.22,0.024,core='#ffffff',glow='#ffe4b0',power=0.9,disc=False)
    img,_=persp_building(img,0.18,0.86,0.20,0.80,vp=(0.10,0.52),depth=0.22,
                         face='#c8b79a',side='#a08f76',roof='#3d3a44',
                         win_cols=7,win_rows=6,win_p=0.30,win_col='#cfe4f4',seed=502,sun=(0.72,0.22))
    # 縦のリブ（図書館らしい柱列）
    bm=silhouette_mask([[(0.18,0.20),(0.86,0.20),(0.86,0.80),(0.18,0.80)]],0.8)
    rib=((np.sin(NX*W/38.0)>0.55)).astype(float)*bm
    img=over(img,'#8f8168',blur(rib,1.2)*0.30)
    img=edge_light(img,bm,sun=(0.72,0.22),col='#fff2d4',strength=0.45)
    img=trees(img,0.815,'#37552f',n=24,seed=503,scale=1.0,rim='#e6f4b0',band=0.07)
    img=lawn(img,0.82,'#6d9a4c','#456c2c',seed=504)
    img,_=paving(img,0.90,1.06,'#aaa496',line='#85806f',centre=0.5,w0=0.6,w1=1.7,rows=6,seed=505)
    img=people(img,[(0.34,0.99,0.105),(0.42,0.97,0.090),(0.66,1.00,0.115)],col='#26301f',seed=506,rim='#e6f4b0')
    img=motes(img,n=130,seed=507,ymax=0.8)
    img=foreground_leaves(img,'left',col='#1c2a17',seed=508,scale=1.0,blur_px=28,alpha=0.60)
    return post(img,bloom=0.44,vig=0.32,warm=(1.01,1.01,1.00),contrast=1.06,seed=509)

def s09_cycu_lawn():
    img=_sky([(0.0,'#2a68c4'),(0.24,'#6fa2de'),(0.52,'#aecfec'),(0.78,'#e8f0f8'),(1.0,'#faf2df')])
    img,_=clouds(img,'#82a8d2','#ffffff',sun=(0.30,0.18),coverage=0.60,height=(0.0,0.48),
                 seed=901,softness=0.95,res=(3,4),tint='#ffffff')
    img=sun_disc(img,0.30,0.18,0.024,core='#ffffff',glow='#ffe8bc',power=0.95,disc=False)
    img=hills(img,0.545,0.05,'#6d8a72','#cfdde8',0.6,seed=902,res=8)
    img,_=persp_building(img,0.62,1.0,0.34,0.56,vp=(0.3,0.52),depth=0.16,
                         face='#c6bda8',side='#a1977f',roof='#464350',
                         win_cols=7,win_rows=3,win_p=0.25,win_col='#cfe0f0',seed=903,sun=(0.30,0.18))
    img=trees(img,0.565,'#3d6134',n=30,seed=904,scale=0.9,rim='#dff0a8',band=0.06)
    img=lawn(img,0.57,'#71a04e','#48702e',seed=905,rim='#e8f8b8')
    img=people(img,[(0.22,0.78,0.062),(0.27,0.79,0.059),(0.52,0.86,0.081),(0.75,0.95,0.112),(0.80,0.93,0.099)],
               col='#243020',seed=906,rim='#e8f8b8')
    img=motes(img,n=170,seed=907,ymax=0.9)
    img=foreground_leaves(img,'both',col='#20301a',seed=908,scale=1.1,blur_px=32,alpha=0.58)
    img=dof(img,far=0.55,amount=1.4)
    return post(img,bloom=0.46,vig=0.28,warm=(1.02,1.02,0.99),contrast=1.06,seed=909,
                flare=(0.30,0.18,0.35,'#fff2cc'))

def s10_cycu_rooftop():
    img=_sky([(0.0,'#04060f'),(0.28,'#080e22'),(0.58,'#101a38'),(0.82,'#24325c'),(1.0,'#4e4a74')])
    img=milky_way(img,seed=1001)
    img=stars(img,density=0.00090,seed=1002,ymax=0.78)
    glow=np.exp(-((NY-0.845)*7)**2)
    img=screen(img,'#ffb877',glow*0.34)
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    r=np.random.default_rng(1003); x=0.0
    while x<1.0:
        w_=0.028+r.random()*0.055; h_=0.03+r.random()*0.10
        d.rectangle([x*W,(0.875-h_)*H,(x+w_)*W,0.895*H],fill=255)
        x+=w_+0.004
    city=blur(np.asarray(im).astype(np.float64)/255,1.0)
    img=over(img,'#0a1024',city)
    cw=windows([(0.0,1.0,0.79,0.892,36,3)],1004,p=0.42,blurpx=0.8)*city
    img=screen(img,'#ffcf8a',cw*0.9); img=screen(img,'#ff9a48',blur(cw,20)*0.45)
    img=over(img,'#070a16',np.clip((NY-0.895)*12,0,1))
    floor=np.clip((NY-0.895)*12,0,1)
    img=texture(img,floor,seed=1005,amount=0.18,res=(6,9))
    rail=[[(0.0,0.900),(1.0,0.900),(1.0,0.914),(0.0,0.914)]]
    for i in range(28):
        x=i/27
        rail.append([(x-0.0032,0.900),(x+0.0032,0.900),(x+0.0032,1.0),(x-0.0032,1.0)])
    rm=silhouette_mask(rail,0.7)
    img=over(img,'#04060e',rm)
    img=screen(img,'#7284bc',blur(rm,3)*0.22)
    # 座って話す二人＋ギター
    img=people(img,[(0.30,0.985,0.071),(0.38,0.985,0.068)],col='#04060e',seed=1006,rim='#5f74ac')
    gm=silhouette_mask([[(0.425,0.985),(0.437,0.940),(0.452,0.940),(0.462,0.985)]],0.8)
    img=over(img,'#04060e',gm)
    img=motes(img,n=90,seed=1007,ymax=0.85,col='#cfe0ff')
    return post(img,bloom=0.42,vig=0.48,warm=(0.97,0.99,1.08),contrast=1.10,seed=1008,grain=0.015)

def s12_cycu_corridor():
    img=_sky([(0.0,'#2b3d78'),(0.2,'#5d5c93'),(0.44,'#a9718c'),(0.64,'#ef9b6c'),(0.84,'#ffc98a'),(1.0,'#ffe8c6')])
    img,_=clouds(img,'#5a5590','#fff0cc',sun=(0.86,0.56),coverage=0.5,height=(0.02,0.5),
                 seed=1201,softness=1.15,tint='#cf8b90')
    img=sun_disc(img,0.86,0.56,0.030,core='#fff8e0',glow='#ff9040',power=1.15)
    # 柱廊：手前ほど大きい柱と、その間から差す夕日
    cols=[]
    n=8
    for i in range(n):
        t=(i/(n-1))**1.75
        x=0.62-t*0.72; wd=0.010+t*0.052
        cols.append([(x-wd,0.06+ -t*0.06),(x+wd,0.06-t*0.06),(x+wd,1.0),(x-wd,1.0)])
    cm=silhouette_mask(cols,0.9)
    img=over(img,'#4a3546',cm)
    img=texture(img,cm,seed=1202,amount=0.16,res=(10,13))
    img=edge_light(img,cm,sun=(0.86,0.56),col='#ffd9a0',strength=0.75,width=4)
    # 天井と床
    ceil=np.clip((0.10-NY)*14,0,1)
    img=over(img,'#3d2c3e',ceil)
    fl=np.clip((NY-0.80)*7,0,1)
    img=over(img,'#5f4750',fl*0.9)
    img=texture(img,fl,seed=1203,amount=0.14,res=(6,10))
    band=np.zeros((H,W))
    for i in range(n):
        t=(i/(n-1))**1.75
        x=0.62-t*0.72
        band+=np.exp(-(((NX-(x+0.05+t*0.06))*(16-t*9))**2))
    band=np.clip(band,0,1)*np.clip((NY-0.78)*6,0,1)
    img=screen(img,'#ffd08a',blur(band,7)*0.75)
    img=people(img,[(0.30,0.96,0.124),(0.40,0.93,0.102)],col='#2a1e2c',seed=1204,rim='#ffcf95')
    img=motes(img,n=180,seed=1205,ymax=0.95)
    img=god_rays(img,0.90,0.55,'#ffdca8',strength=0.30,seed=1206,length=1.4)
    return post(img,bloom=0.56,vig=0.42,warm=(1.06,1.00,0.96),contrast=1.08,seed=1207,
                flare=(0.86,0.56,0.55,'#ffd9a8'))

def s13_cycu_library_night():
    img=_sky([(0.0,'#070c22'),(0.32,'#101a3c'),(0.66,'#1e2a50'),(1.0,'#2f375f')])
    img=stars(img,density=0.00020,seed=1301,ymax=0.40,twinkle=0.7)
    img,_=clouds(img,'#121a3c','#7a88c0',sun=(0.5,0.9),coverage=0.30,height=(0.0,0.32),
                 seed=1302,softness=1.5,tint='#212a52')
    img,bm=persp_building(img,0.14,0.80,0.22,0.86,vp=(0.94,0.55),depth=0.20,
                          face='#1e2748',side='#161d38',roof='#0f1428',
                          win_cols=8,win_rows=7,win_p=0.72,win_col='#ffd08a',seed=1303,
                          sun=(0.5,0.9),lit='#6d7cb8',frame='#2b3559')
    ent=silhouette_mask([[(0.40,0.90),(0.40,0.72),(0.54,0.72),(0.54,0.90)]],0.8)
    img=screen(img,'#ffe0b0',ent*0.6)
    img=trees(img,0.885,'#0c1226',n=22,seed=1304,scale=1.1,rim='#4a5c94',band=0.07)
    img,pm=paving(img,0.89,1.06,'#101638',line='#0a0f2a',centre=0.5,w0=0.6,w1=1.7,rows=6,seed=1305)
    wet=np.exp(-(((NX-0.47)*2.2)**2))*np.clip((NY-0.89)*7,0,1)
    img=screen(img,'#ffc178',blur(wet*(0.4+fbm(H,W,res=(80,4),octaves=3,seed=1306)),6)*0.65)
    img=people(img,[(0.36,1.00,0.093),(0.62,0.98,0.084)],col='#080d20',seed=1307,rim='#ffc178')
    img=power_lines(img,y0=0.16,sag=0.030,n=4,col='#0a0f22',seed=1308)
    img=foreground_leaves(img,'right',col='#060a18',seed=1309,scale=1.0,blur_px=28,alpha=0.62)
    return post(img,bloom=0.52,vig=0.46,warm=(1.02,0.99,1.03),contrast=1.08,seed=1310)

def s16_cycu_night_market():
    img=_sky([(0.0,'#090e26'),(0.30,'#151c40'),(0.60,'#282d56'),(1.0,'#3d3a66')])
    img=stars(img,density=0.00010,seed=1601,ymax=0.24,twinkle=0.6)
    left=[[(-0.02,1.06),(-0.02,0.02),(0.38,0.38),(0.38,1.06)]]
    right=[[(1.02,1.06),(1.02,0.0),(0.62,0.37),(0.62,1.06)]]
    lm=silhouette_mask(left,1.0); rm=silhouette_mask(right,1.0)
    img=over(img,'#1e2550',lm); img=over(img,'#1a2044',rm)
    img=texture(img,lm,seed=1602,amount=0.16,res=(9,12))
    img=texture(img,rm,seed=1603,amount=0.16,res=(9,12))
    # 看板：縦の帯を色違いで
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    im2=Image.new('L',(W,H),0); d2=ImageDraw.Draw(im2)
    r=np.random.default_rng(1604)
    for side in (0,1):
        for k in range(15):
            t=k/15+r.random()*0.03
            if side==0: x=-0.02+t*0.40; ytop=0.02+t*0.36
            else: x=1.02-t*0.40; ytop=0.00+t*0.37
            for row in range(3):
                y=ytop+0.05+row*0.115+r.random()*0.02
                w_=0.013+0.022*t; h_=0.032+0.050*t
                tgt = d if r.random()<0.6 else d2
                tgt.rectangle([x*W,y*H,(x+w_)*W,(y+h_)*H],fill=int(165+r.random()*90))
    s1=blur(np.asarray(im).astype(np.float64)/255,1.0)
    s2=blur(np.asarray(im2).astype(np.float64)/255,1.0)
    img=over(img,'#c2321f',s1*0.55)
    img=screen(img,'#ff6a2a',s1*1.0); img=screen(img,'#ff3a14',blur(s1,26)*0.6)
    img=over(img,'#b8860a',s2*0.5)
    img=screen(img,'#ffd84a',s2*1.0); img=screen(img,'#ff9c10',blur(s2,26)*0.55)
    # 屋台の裸電球
    lamp=np.zeros((H,W))
    for k in range(11):
        t=k/10
        for side in (-1,1):
            x=0.5+side*(0.05+t*0.46); y=0.26+t*0.26
            lamp+=radial(x,y,0.013+t*0.030,1.5)
    lamp=np.clip(lamp,0,1)
    img=screen(img,'#ffe4b0',lamp*1.0)
    img=screen(img,'#ff7a3c',blur(lamp,32)*0.6)
    # 湯気
    st=fbm(H,W,res=(4,9),octaves=5,seed=1605)
    sm=np.clip((st-0.46)*2.2,0,1)*np.exp(-((NY-0.56)*5.5)**2)
    img=screen(img,'#ffd9b0',blur(sm,22)*0.40)
    road_m=np.clip((NY-0.40)*3.0,0,1)*np.clip(1-np.abs(NX-0.5)*0.95,0,1)
    img=over(img,'#0d1230',road_m*0.9)
    img=texture(img,road_m,seed=1606,amount=0.15,res=(7,10))
    refl=np.zeros((H,W))
    for k in range(11):
        t=k/10
        for side in (-1,1):
            x=0.5+side*(0.05+t*0.46); y=0.26+t*0.26
            refl+=np.exp(-(((NX-x)*22)**2))*np.clip((NY-y-0.22)*2.0,0,1)
    streak=fbm(H,W,res=(90,4),octaves=3,seed=1607)
    img=screen(img,'#ffb066',blur(refl*(0.3+streak*1.2),6)*0.72)
    img=people(img,[(0.42,0.72,0.065),(0.50,0.76,0.077),(0.57,0.74,0.071),
                    (0.33,0.85,0.102),(0.68,0.90,0.115),(0.25,0.68,0.053)],
               col='#090c1e',seed=1608,rim='#ffb877')
    img=power_lines(img,y0=0.12,sag=0.028,n=5,col='#0a0e20',seed=1609)
    return post(img,bloom=0.58,vig=0.44,warm=(1.05,0.99,1.00),contrast=1.08,seed=1610)

def s17_cycu_chapel_night():
    img=_sky([(0.0,'#070c26'),(0.3,'#121a44'),(0.6,'#26305c'),(0.85,'#4a4270'),(1.0,'#6b4f64')])
    img=stars(img,density=0.00030,seed=1701,ymax=0.44,twinkle=0.8)
    img,_=clouds(img,'#141c44','#8a92cc',sun=(0.5,0.7),coverage=0.34,height=(0.0,0.36),
                 seed=1702,softness=1.4,tint='#242c58')
    # 尖った切妻の礼拝堂
    body=[(0.34,0.86),(0.34,0.46),(0.50,0.24),(0.66,0.46),(0.66,0.86)]
    bm=silhouette_mask([body],0.9)
    img=over(img,'#2a2a48',bm)
    img=texture(img,bm,seed=1703,amount=0.15,res=(11,13))
    # 大きなステンドグラス
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    d.polygon([(0.44*W,0.80*H),(0.44*W,0.50*H),(0.50*W,0.38*H),(0.56*W,0.50*H),(0.56*W,0.80*H)],fill=255)
    a=blur(np.asarray(im).astype(np.float64)/255,1.2)
    img=screen(img,'#ffd08a',a*0.95)
    img=screen(img,'#ff9a48',blur(a,26)*0.6)
    grid=((np.sin(NX*W/22.0)>0.6)|(np.sin(NY*H/22.0)>0.6)).astype(float)*a
    img=over(img,'#3a2a1e',blur(grid,1.0)*0.45)
    # 十字架
    cr=silhouette_mask([[(0.494,0.235),(0.506,0.235),(0.506,0.135),(0.494,0.135)],
                        [(0.470,0.180),(0.530,0.180),(0.530,0.192),(0.470,0.192)]],0.6)
    img=over(img,'#1a1a30',cr)
    img=screen(img,'#ffe0a8',blur(cr,7)*0.55)
    img=edge_light(img,bm,sun=(0.5,0.62),col='#ffd9a0',strength=0.4)
    img=trees(img,0.875,'#0d1128',n=22,seed=1704,scale=1.2,rim='#5f6ea8',band=0.08)
    img,_=paving(img,0.88,1.06,'#161c3c',line='#0e132e',centre=0.5,w0=0.5,w1=1.6,rows=6,seed=1705)
    wet=np.exp(-(((NX-0.5)*2.4)**2))*np.clip((NY-0.88)*7,0,1)
    img=screen(img,'#ffb877',blur(wet*(0.4+fbm(H,W,res=(80,4),octaves=3,seed=1706)),6)*0.6)
    img=people(img,[(0.28,0.99,0.087),(0.72,0.97,0.081)],col='#070b1c',seed=1707,rim='#ffb877')
    img=motes(img,n=110,seed=1708,ymax=0.9,col='#ffe0b8')
    return post(img,bloom=0.54,vig=0.46,warm=(1.03,0.99,1.02),contrast=1.08,seed=1709)

def s18_cycu_graduation():
    img=_sky([(0.0,'#2c4a90'),(0.16,'#6a6aa8'),(0.36,'#c47a92'),(0.55,'#f79a5c'),(0.74,'#ffc978'),(1.0,'#fff2d6')])
    img,_=clouds(img,'#5c4a86','#fff8dc',sun=(0.5,0.58),coverage=0.5,height=(0.02,0.54),
                 seed=1801,softness=1.1,tint='#e0879a')
    img=sun_disc(img,0.5,0.58,0.046,core='#fffdf0',glow='#ff8f36',power=1.45)
    img=god_rays(img,0.5,0.58,'#ffe4b0',strength=0.36,seed=1802,length=1.7)
    img=hills(img,0.60,0.05,'#5a4a70','#f0b48e',0.5,seed=1803,res=8)
    img=trees(img,0.615,'#3f3040',n=28,seed=1804,scale=0.9,rim='#ffd79a',band=0.06)
    img,_=paving(img,0.62,1.06,'#a89a84',line='#857a68',centre=0.5,w0=0.08,w1=1.4,rows=14,seed=1805)
    img,_=gate_arch(img,0.5,0.355,0.640,0.245,col='#9a8d79',beam='#7a6f5c',sun=(0.5,0.58),seed=1806)
    img=people(img,[(0.30,0.86,0.096),(0.36,0.88,0.102),(0.42,0.90,0.108),
                    (0.60,0.92,0.115),(0.67,0.89,0.105),(0.74,0.85,0.093)],
               col='#3a2a30',seed=1807,rim='#ffd79a')
    # 舞い上がる角帽
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    r=np.random.default_rng(1808)
    for k in range(9):
        x=0.22+r.random()*0.58; y=0.20+r.random()*0.22; s=0.016+r.random()*0.014
        d.polygon([(x*W,(y-s*0.5)*H),((x+s)*W,y*H),(x*W,(y+s*0.5)*H),((x-s)*W,y*H)],fill=255)
    cap=blur(np.asarray(im).astype(np.float64)/255,1.0)
    img=over(img,'#2e2230',np.clip(cap*1.15,0,1))
    img=screen(img,'#ffd79a',blur(cap,6)*0.35)
    img=motes(img,n=200,seed=1809,ymax=0.95)
    img=foreground_leaves(img,'left',col='#3a2a2c',seed=1810,scale=1.0,blur_px=32,alpha=0.52)
    return post(img,bloom=0.62,vig=0.28,warm=(1.07,1.01,0.95),contrast=1.07,seed=1811,
                flare=(0.5,0.58,0.75,'#ffe4b4'))

CYCU=[('01_cycu_gate_dawn','中原大學 校門・清晨',s01_cycu_gate_dawn),
      ('02_cycu_avenue','中原大學 校園大道',s02_cycu_avenue),
      ('03_cycu_bikes','中原大學 腳踏車停車場',s03_cycu_bikes),
      ('04_cycu_classroom','中原大學 教學大樓',s04_cycu_classroom),
      ('05_cycu_library_day','中原大學 圖書館',s05_cycu_library_day),
      ('09_cycu_lawn','中原大學 大草坪',s09_cycu_lawn),
      ('10_cycu_rooftop','中原大學 宿舍頂樓',s10_cycu_rooftop),
      ('12_cycu_corridor','中原大學 長廊的黃昏',s12_cycu_corridor),
      ('13_cycu_library_night','中原大學 圖書館的通宵',s13_cycu_library_night),
      ('16_cycu_night_market','中原夜市',s16_cycu_night_market),
      ('17_cycu_chapel_night','中原大學 教堂之夜',s17_cycu_chapel_night),
      ('18_cycu_graduation','中原大學 畢業的早晨',s18_cycu_graduation)]

if __name__=='__main__':
    import sys,os,time
    os.makedirs('frames2',exist_ok=True)
    only=sys.argv[1:]
    for key,name,fn in CYCU:
        if only and not any(o in key for o in only): continue
        t0=time.time(); to_image(fn()).save(f'frames2/{key}.jpg',quality=93)
        print(f"{key} {name} {time.time()-t0:.1f}s",flush=True)
