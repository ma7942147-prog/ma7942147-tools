# -*- coding: utf-8 -*-
"""新海誠風・鳥取県風景 procedural painter (numpy + Pillow)."""
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

W, H = 2560, 1440
rng_global = np.random.default_rng(20260821)

# ---------- noise ----------
def _lerp(a, b, t): return a + (b - a) * t
def _fade(t): return t * t * t * (t * (t * 6 - 15) + 10)

def value_noise(h, w, res, seed):
    r = np.random.default_rng(seed)
    gh, gw = res
    grid = r.random((gh + 1, gw + 1))
    y = np.linspace(0, gh, h, endpoint=False)
    x = np.linspace(0, gw, w, endpoint=False)
    y0 = y.astype(int); x0 = x.astype(int)
    ty = _fade(y - y0)[:, None]; tx = _fade(x - x0)[None, :]
    a = grid[y0][:, x0]; b = grid[y0][:, x0 + 1]
    c = grid[y0 + 1][:, x0]; d = grid[y0 + 1][:, x0 + 1]
    return _lerp(_lerp(a, b, tx), _lerp(c, d, tx), ty)

def fbm(h, w, res=(4, 6), octaves=6, gain=0.5, seed=0, lac=2.0):
    out = np.zeros((h, w)); amp = 1.0; norm = 0.0; ry, rx = res
    for o in range(octaves):
        out += amp * value_noise(h, w, (max(1, int(ry)), max(1, int(rx))), seed + o * 977)
        norm += amp; amp *= gain; ry *= lac; rx *= lac
    return out / norm

def fbm1d(w, res=6, octaves=6, gain=0.5, seed=0):
    r = np.zeros(w); amp = 1.0; norm = 0.0; res = float(res)
    for o in range(octaves):
        rr = np.random.default_rng(seed + o * 613)
        n = max(2, int(res))
        g = rr.random(n + 1)
        x = np.linspace(0, n, w, endpoint=False)
        i = x.astype(int); t = _fade(x - i)
        r += amp * _lerp(g[i], g[i + 1], t)
        norm += amp; amp *= gain; res *= 2
    return r / norm

# ---------- color helpers ----------
def hexc(s):
    s = s.lstrip('#')
    return np.array([int(s[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0

def vgrad(stops, h=H, w=W):
    """stops: [(pos0..1, '#hex'), ...] top->bottom"""
    ys = np.linspace(0, 1, h)
    pos = np.array([s[0] for s in stops])
    cols = np.array([hexc(s[1]) for s in stops])
    out = np.empty((h, 3))
    for c in range(3):
        out[:, c] = np.interp(ys, pos, cols[:, c])
    return np.repeat(out[:, None, :], w, axis=1)

YY, XX = np.mgrid[0:H, 0:W].astype(np.float64)
NY, NX = YY / H, XX / W

def radial(cx, cy, r, soft=1.0):
    d = np.sqrt(((NX - cx) * (W / H)) ** 2 + (NY - cy) ** 2)
    return np.clip(1 - d / r, 0, 1) ** soft

def screen(base, col, mask):
    c = hexc(col)[None, None, :]
    m = mask[..., None]
    return 1 - (1 - base) * (1 - c * m)

def over(base, col, mask):
    c = hexc(col)[None, None, :]
    return base * (1 - mask[..., None]) + c * mask[..., None]

def blur(a, r):
    if a.ndim == 2:
        im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), 'L')
        return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float64) / 255
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), 'RGB')
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float64) / 255

# ---------- elements ----------
def clouds(img, sky_top_col, lit_col, sun=(0.5, 0.35), coverage=0.5, height=(0.05, 0.55),
           seed=1, softness=1.0, density=1.0, res=(3, 5), tint='#ffffff'):
    h0, h1 = height
    n = fbm(H, W, res=res, octaves=7, gain=0.55, seed=seed)
    band = np.clip((NY - h0) / max(1e-6, (h1 - h0)), 0, 1)
    shape = np.sin(np.pi * np.clip(band, 0, 1)) ** 0.7
    m = np.clip((n * shape - (1 - coverage)) * 3.2 * density, 0, 1)
    m = blur(m, 6 * softness)
    # lighting: gradient of mask toward sun
    sx, sy = sun
    gy, gx = np.gradient(m)
    dirx = (sx - NX) * (W / H); diry = (sy - NY)
    ln = np.sqrt(dirx ** 2 + diry ** 2) + 1e-6
    lit = np.clip(-(gx * dirx / ln + gy * diry / ln) * 190, 0, 1) * m
    lit = blur(lit, 3)
    body = m * 0.9
    img = over(img, tint, body * 0.55)
    img = over(img, sky_top_col, body * 0.18)
    img = screen(img, lit_col, np.clip(lit * 1.5, 0, 1))
    return img, m

def sun_disc(img, cx, cy, r, core='#fff6df', glow='#ffb56b', power=1.0, disc=True):
    g = radial(cx, cy, r * 7.0, 1.6) * 0.55 * power
    img = screen(img, glow, g)
    g2 = radial(cx, cy, r * 2.4, 2.2) * 0.85 * power
    img = screen(img, core, g2)
    if disc:
        d = np.sqrt(((NX - cx) * (W / H)) ** 2 + (NY - cy) ** 2)
        img = screen(img, core, blur((d < r * 0.42).astype(float), 8) * power)
    return img

def god_rays(img, cx, cy, col='#ffe9c0', strength=0.35, n=90, seed=5, length=1.4):
    ang = np.arctan2(NY - cy, (NX - cx) * (W / H))
    d = np.sqrt(((NX - cx) * (W / H)) ** 2 + (NY - cy) ** 2)
    r = np.random.default_rng(seed)
    ph = r.random(4) * 6.28
    m = np.zeros_like(ang)
    for k, f in enumerate([7, 13, 23, 41]):
        m += (0.5 + 0.5 * np.sin(ang * f + ph[k])) / (k + 1.3)
    m = (m / 2.2) ** 2.2
    m *= np.clip(1 - d / length, 0, 1) ** 1.5
    m = blur(m, 10)
    return screen(img, col, np.clip(m * strength, 0, 1))

def stars(img, density=0.00035, seed=3, ymax=0.75, twinkle=1.0):
    r = np.random.default_rng(seed)
    n = int(H * W * density)
    ys = r.random(n) ** 1.4 * ymax
    xs = r.random(n)
    br = r.random(n) ** 3
    layer = np.zeros((H, W))
    yi = (ys * H).astype(int); xi = (xs * W).astype(int)
    np.add.at(layer, (yi, xi), br * twinkle)
    layer = blur(layer, 1.0) * 3.0
    return screen(img, '#eaf2ff', np.clip(layer, 0, 1))

def milky_way(img, seed=9):
    a = -0.55
    d = np.abs((NY - 0.42) - a * (NX - 0.5)) 
    band = np.exp(-(d / 0.17) ** 2)
    n = fbm(H, W, res=(3, 6), octaves=7, gain=0.6, seed=seed)
    m = np.clip(band * (0.35 + n * 0.9) - 0.18, 0, 1)
    img = screen(img, '#9fb8ff', blur(m, 18) * 0.45)
    img = screen(img, '#f0e6ff', blur(m, 6) * 0.22)
    r = np.random.default_rng(seed)
    n2 = (r.random((H, W)) < (band * 0.0022)).astype(float) * r.random((H, W))
    img = screen(img, '#ffffff', blur(n2, 0.8) * 2.2)
    return img

def mountains(img, base_y, amp, col, haze_col, haze, seed=1, res=5, rough=0.5, sharp=1.0):
    prof = fbm1d(W, res=res, octaves=6, gain=rough, seed=seed)
    prof = (prof - prof.min()) / (np.ptp(prof) + 1e-9)
    prof = prof ** sharp
    top = base_y - prof * amp
    m = (NY > top[None, :]).astype(float)
    m = blur(m, 1.2)
    c = hexc(col) * (1 - haze) + hexc(haze_col) * haze
    return img * (1 - m[..., None]) + c[None, None, :] * m[..., None], top

def peak(img, cx, base_y, height, width, col, haze_col, haze, snow=None, snow_line=0.45, seed=7):
    xs = np.linspace(0, 1, W)
    d = np.abs(xs - cx)
    shape = np.exp(-(d / width) ** 1.7)
    jag = (fbm1d(W, res=14, octaves=5, gain=0.55, seed=seed) - 0.5) * 0.035
    top = base_y - height * shape + jag * shape
    m = (NY > top[None, :]).astype(float)
    m = blur(m, 1.2)
    c = hexc(col) * (1 - haze) + hexc(haze_col) * haze
    img = img * (1 - m[..., None]) + c[None, None, :] * m[..., None]
    if snow:
        sm = m * np.clip((base_y - snow_line * height - NY) * 14, 0, 1)
        tex = fbm(H, W, res=(6, 10), octaves=5, seed=seed + 3)
        sm = np.clip(sm * (0.55 + tex * 0.75), 0, 1)
        img = over(img, snow, blur(sm, 2) * 0.92)
    return img, top

def water(img, horizon, sky_img, tint, sun_x=None, sun_col='#ffd9a0', ripple=1.0, seed=4):
    """mirror the sky above horizon into water below, add shimmer."""
    hy = int(horizon * H)
    if hy >= H - 4: return img
    src = sky_img[:hy][::-1]
    need = H - hy
    if src.shape[0] < need:
        src = np.concatenate([src, np.repeat(src[-1:], need - src.shape[0], axis=0)], axis=0)
    refl = src[:need]
    # wavy distortion
    yy = np.arange(need)[:, None]
    off = (np.sin(yy / 9.0 + np.linspace(0, 30, W)[None, :]) * (1.5 + yy / 40) * ripple).astype(int)
    idx = np.clip(np.arange(W)[None, :] + off, 0, W - 1)
    refl = np.take_along_axis(refl, idx[..., None].repeat(3, axis=2), axis=1)
    t = hexc(tint)[None, None, :]
    fade = np.clip(np.linspace(0, 1, need), 0, 1)[:, None, None]
    wat = refl * (0.55 - 0.25 * fade) + t * (0.45 + 0.25 * fade)
    img = img.copy(); img[hy:] = wat
    # shimmer
    band = np.zeros((H, W))
    if sun_x is not None:
        colm = np.exp(-(((NX - sun_x) * 3.4) ** 2))
        spark = (fbm(H, W, res=(120, 6), octaves=3, gain=0.6, seed=seed) > 0.62).astype(float)
        band = spark * colm
        band[:hy] = 0
        band *= np.clip((NY - horizon) * 3.5, 0, 1)
        img = screen(img, sun_col, blur(band, 1.2) * 0.85)
    # horizon glow line
    line = np.exp(-((NY - horizon) * 220) ** 2)
    img = screen(img, sun_col, line * 0.18)
    return img

def dunes(img, ridges, light=(0.75, 0.2), sand='#d9a86a', shade='#6b4a35', lit='#ffdca8', seed=11):
    """ridges: list of (base_y, amp, res, seed) — 遠→近"""
    for (by, amp, res, sd) in ridges:
        prof = fbm1d(W, res=res, octaves=3, gain=0.42, seed=sd)
        prof = (prof - prof.min()) / (np.ptp(prof) + 1e-9)
        k = 121
        prof = np.convolve(np.pad(prof, k, mode='edge'), np.hanning(k) / np.hanning(k).sum(), 'same')[k:-k]
        top = by - prof * amp
        m = blur((NY > top[None, :]).astype(float), 1.0)
        slope = np.gradient(top) * W
        ks = 201
        slope = np.convolve(np.pad(slope, ks, mode='edge'), np.hanning(ks) / np.hanning(ks).sum(), 'same')[ks:-ks]
        shading = np.clip(0.5 - slope * 0.55, 0.12, 1.0)[None, :]
        depth = np.clip((NY - top[None, :]) * 1.9, 0, 1)
        # 風紋：沿著稜線走的橫向細波
        d_rel = (NY - top[None, :])
        ripple = 0.5 + 0.5 * np.sin(d_rel * 210 + fbm(H, W, res=(3, 5), octaves=3, seed=sd + 9) * 9)
        ripple = np.clip(ripple, 0, 1) * np.clip(1 - d_rel * 2.6, 0, 1)
        base = hexc(sand)[None, None, :] * (0.72 + 0.40 * shading[..., None])
        base = base * (1 - 0.5 * depth[..., None]) + hexc(shade)[None, None, :] * (0.5 * depth[..., None])
        base = base * (0.96 + 0.09 * ripple[..., None])
        img = img * (1 - m[..., None]) + np.clip(base, 0, 1) * m[..., None]
        rim = np.clip(np.exp(-((NY - top[None, :]) * 230) ** 2), 0, 1) * m
        img = screen(img, lit, rim * 0.5)
    return img

def silhouette_mask(polys, feather=1.0):
    from PIL import ImageDraw
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    for p in polys:
        d.polygon([(x * W, y * H) for x, y in p], fill=255)
    a = np.asarray(im).astype(np.float64) / 255
    return blur(a, feather)

def grass(img, base_y, col, n=520, seed=12, hmax=0.16, rim=None):
    from PIL import ImageDraw
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    for i in range(n):
        x = r.random() * 1.06 - 0.03
        hgt = (0.35 + r.random() ** 2) * hmax
        lean = (r.random() - 0.5) * 0.05
        wdt = max(1.2, r.random() * 4.5)
        d.line([(x * W, base_y * H), ((x + lean) * W, (base_y - hgt) * H)], fill=255, width=int(wdt))
    a = blur(np.asarray(im).astype(np.float64) / 255, 1.0)
    img = over(img, col, np.clip(a * 1.2, 0, 1))
    if rim:
        img = screen(img, rim, blur(a, 2.5) * 0.25)
    return img

def trees(img, base_y, col, n=26, seed=13, scale=1.0, rim=None, band=None):
    """不規則な樹林のシルエット帯。"""
    h_prof = fbm1d(W, res=max(6, int(n)), octaves=5, gain=0.55, seed=seed)
    h_prof = (h_prof - h_prof.min()) / (np.ptp(h_prof) + 1e-9)
    spike = fbm1d(W, res=max(20, int(n * 3)), octaves=3, gain=0.4, seed=seed + 41)
    hgt = (0.35 + 0.65 * h_prof) * 0.075 * scale + spike * 0.022 * scale
    top = base_y - hgt
    m = (NY > top[None, :])
    if band is not None:                    # 帯だけ描く（手前の物を隠さない）
        m = m & (NY < (top[None, :] + band))
    m = blur(m.astype(float), 0.8)
    img = over(img, col, np.clip(m * 1.05, 0, 1))
    if rim:
        edge = np.clip(np.exp(-((NY - top[None, :]) * 150) ** 2), 0, 1) * m
        img = screen(img, rim, blur(edge, 2.5) * 0.30)
    return img

def snowfall(img, n=1400, seed=21, col='#ffffff'):
    r = np.random.default_rng(seed)
    layer = np.zeros((H, W))
    ys = (r.random(n) * H).astype(int); xs = (r.random(n) * W).astype(int)
    np.add.at(layer, (ys, xs), r.random(n) ** 1.5)
    return screen(img, col, blur(layer, 1.6) * 2.0)

def petals(img, n=260, seed=22, col='#ffd7e6'):
    from PIL import ImageDraw
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    for i in range(n):
        x, y = r.random() * W, r.random() * H
        s = 2 + r.random() * 7
        d.ellipse([x, y, x + s * 1.7, y + s], fill=int(120 + r.random() * 135))
    a = blur(np.asarray(im).astype(np.float64) / 255, 1.1)
    return over(img, col, a * 0.8)

def embers(img, n=420, seed=23, col='#ffb361'):
    r = np.random.default_rng(seed)
    layer = np.zeros((H, W))
    ys = (r.random(n) ** 0.7 * H).astype(int); xs = (r.random(n) * W).astype(int)
    np.add.at(layer, (ys, xs), r.random(n))
    return screen(img, col, blur(layer, 2.2) * 2.6)

def rain(img, n=520, seed=24, col='#cfe0ff', slant=0.02, length=0.05):
    from PIL import ImageDraw
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    for i in range(n):
        x, y = r.random(), r.random()
        d.line([(x*W, y*H), ((x+slant)*W, (y+length)*H)], fill=int(60+r.random()*120), width=1)
    a = blur(np.asarray(im).astype(np.float64)/255, 0.8)
    return screen(img, col, a * 0.5)

# ---------- post ----------
def post(img, bloom=0.42, grain=0.012, vig=0.32, warm=(1.0, 1.0, 1.0), contrast=1.06, seed=31,
         flare=None, ca=1.0):
    img = np.clip(img, 0, 1)
    lum = img.mean(2)
    hi = np.clip((lum - 0.62) / 0.38, 0, 1)[..., None] * img
    img = 1 - (1 - img) * (1 - blur(hi, 26) * bloom)
    img = 1 - (1 - img) * (1 - blur(hi, 90) * bloom * 0.5)
    if flare:
        cx, cy, st, col = flare
        for k, (o, r_, a) in enumerate([(0.0, 0.30, 0.5), (0.35, 0.10, 0.28), (0.7, 0.16, 0.2), (1.25, 0.07, 0.24), (1.6, 0.13, 0.15)]):
            fx = cx + (0.5 - cx) * 2 * o; fy = cy + (0.5 - cy) * 2 * o
            img = screen(img, col, radial(fx, fy, r_, 2.0) * a * st)
    v = 1 - vig * (((NX - 0.5) * 1.25) ** 2 + ((NY - 0.5) * 1.25) ** 2)
    img = img * np.clip(v, 0, 1)[..., None]
    img = np.clip((img - 0.5) * contrast + 0.5, 0, 1)
    img = img * np.array(warm)[None, None, :]
    if ca != 1.0 and ca > 0:
        # subtle chromatic aberration via per-channel scale
        out = img.copy()
        for ch, s in ((0, 1.0 + 0.0016 * ca), (2, 1.0 - 0.0016 * ca)):
            im = Image.fromarray((np.clip(img[..., ch], 0, 1) * 255).astype(np.uint8), 'L')
            nw, nh = int(W * s), int(H * s)
            im = im.resize((nw, nh), Image.LANCZOS)
            ox, oy = (nw - W) // 2, (nh - H) // 2
            out[..., ch] = np.asarray(im).astype(np.float64)[oy:oy + H, ox:ox + W] / 255
        img = out
    r = np.random.default_rng(seed)
    img = img + (r.random((H, W, 1)) - 0.5) * grain
    return np.clip(img, 0, 1)

def to_image(img):
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), 'RGB')

# ============================================================
#  v2: 「平ら過ぎる」を直すための道具立て
#  - マスクの中に質感を入れる／陽の当たる縁を光らせる
#  - 消失点を持つ建築（正面と側面の二面）
#  - 手前のボケた葉、電線、人影、被写界深度、光の粒
# ============================================================

def texture(img, mask, seed=0, amount=0.16, res=(14,20), tint=None):
    """マスクの内側にムラを入れる。単色のベタ塗りを避ける。"""
    n = fbm(H, W, res=res, octaves=6, gain=0.55, seed=seed)
    v = (n - 0.5) * 2 * amount
    out = img * (1 + v[..., None] * mask[..., None])
    if tint is not None:
        out = over(out, tint, np.clip((n-0.58)*1.8,0,1) * mask * 0.28)
    return np.clip(out, 0, 1)

def edge_light(img, mask, sun=(0.5,0.3), col='#ffe6bc', strength=0.55, width=3.0):
    """陽の側の輪郭だけを光らせる。立体感はほぼこれで出る。"""
    gy, gx = np.gradient(blur(mask, 1.5))
    sx, sy = sun
    dx = (sx - NX) * (W/H); dy = (sy - NY)
    L = np.sqrt(dx**2 + dy**2) + 1e-6
    lit = np.clip(-(gx*dx/L + gy*dy/L) * 240, 0, 1)
    return screen(img, col, blur(lit, width) * strength)

def occlusion(img, mask, col='#1a1a22', strength=0.35, r=18):
    """接地部の影。物が浮かなくなる。"""
    sh = np.clip(blur(mask, r) - mask, 0, 1)
    return over(img, col, sh * strength)

def persp_building(img, x0, x1, y_top, y_bot, vp=(0.5, 0.55), depth=0.16,
                   face='#c8c2b4', side='#8f897c', roof='#3a3a44',
                   win_cols=6, win_rows=5, win_col='#ffd9a0', win_p=0.5,
                   seed=1, sun=(0.5,0.3), lit='#fff0cc', frame='#6b6455'):
    """正面＋側面の二面を持つ建物。消失点に向かって側面が縮む。"""
    vx, vy = vp
    def to_vp(x, y, t):
        return (x + (vx - x)*t, y + (vy - y)*t)
    # 側面（消失点側）
    if x1 < vx: sx0, sx1 = x1, x1     # 右へ伸びる
    else:       sx0, sx1 = x0, x0
    p_top = to_vp(sx0, y_top, depth); p_bot = to_vp(sx1, y_bot, depth)
    side_poly = [(sx0, y_top), (p_top[0], p_top[1]), (p_bot[0], p_bot[1]), (sx1, y_bot)]
    ms = silhouette_mask([side_poly], 0.8)
    img = over(img, side, ms)
    img = texture(img, ms, seed=seed+7, amount=0.13, res=(10,8))
    # 正面
    front = [(x0, y_top), (x1, y_top), (x1, y_bot), (x0, y_bot)]
    mf = silhouette_mask([front], 0.8)
    img = over(img, face, mf)
    img = texture(img, mf, seed=seed, amount=0.15, res=(12,16))
    # 屋根の縁
    rf = silhouette_mask([[(x0-0.006, y_top-0.012),(x1+0.006, y_top-0.012),
                           (x1+0.006, y_top+0.006),(x0-0.006, y_top+0.006)]], 0.6)
    img = over(img, roof, rf)
    # 窓：枠つき・奥行きのある窓
    im = Image.new('L',(W,H),0); d = ImageDraw.Draw(im)
    imf = Image.new('L',(W,H),0); df = ImageDraw.Draw(imf)
    r = np.random.default_rng(seed)
    cw = (x1-x0)/win_cols; ch = (y_bot-y_top)/win_rows
    for i in range(win_cols):
        for j in range(win_rows):
            wx = x0 + i*cw + cw*0.18; wy = y_top + j*ch + ch*0.20
            ww = cw*0.64; wh = ch*0.52
            df.rectangle([(wx-cw*0.05)*W,(wy-ch*0.05)*H,(wx+ww+cw*0.05)*W,(wy+wh+ch*0.05)*H],fill=255)
            if r.random() < win_p:
                d.rectangle([wx*W, wy*H, (wx+ww)*W, (wy+wh)*H], fill=int(150+r.random()*105))
    wf = blur(np.asarray(imf).astype(np.float64)/255, 1.0) * mf
    wl = blur(np.asarray(im).astype(np.float64)/255, 0.9) * mf
    img = over(img, frame, np.clip(wf-wl,0,1)*0.55)
    img = over(img, '#2b3444', wl*0.35)
    img = screen(img, win_col, wl*0.85)
    img = screen(img, win_col, blur(wl, 16)*0.30)
    m_all = np.clip(mf+ms+rf, 0, 1)
    img = edge_light(img, m_all, sun=sun, col=lit, strength=0.5)
    img = occlusion(img, m_all, strength=0.30)
    return img, m_all

def foreground_leaves(img, side='both', col='#0e1a10', seed=9, scale=1.0, blur_px=26, alpha=0.92):
    """画面の隅に、ピントの合っていない葉。新海誠の定番。"""
    im = Image.new('L',(W,H),0); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    corners = {'both':[(0.0,0.0),(1.0,0.0)],'left':[(0.0,0.0)],'right':[(1.0,0.0)],
               'bottom':[(0.0,1.0),(1.0,1.0)],'tl':[(0.0,0.0)]}[side]
    for (cx, cy) in corners:
        for k in range(26):
            bx = cx + (r.random()-0.5)*0.42*scale
            by = cy + (r.random()-0.5)*0.36*scale
            L = (0.06+r.random()*0.16)*scale
            ang = r.random()*6.28
            pts=[]
            for m in range(9):
                u=m/8
                px = bx+np.cos(ang)*L*u
                py = by+np.sin(ang)*L*u
                wdt = L*0.30*np.sin(np.pi*u)
                pts.append((px, py, wdt))
            poly=[(p[0]-p[2]*0.5, p[1]) for p in pts]+[(p[0]+p[2]*0.5, p[1]) for p in pts[::-1]]
            d.polygon([(p[0]*W,p[1]*H) for p in poly], fill=255)
    a = blur(np.asarray(im).astype(np.float64)/255, blur_px)
    return over(img, col, np.clip(a*1.25,0,1)*alpha)

def power_lines(img, y0=0.20, sag=0.045, n=5, col='#161a22', seed=11, poles=True):
    """電柱と電線。台湾の街並みにはこれがある。"""
    im = Image.new('L',(W,H),0); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    for k in range(n):
        yy = y0 + k*0.022
        pts=[(x, yy + sag*np.sin(np.pi*x)) for x in np.linspace(-0.02,1.02,60)]
        for i in range(len(pts)-1):
            d.line([(pts[i][0]*W,pts[i][1]*H),(pts[i+1][0]*W,pts[i+1][1]*H)],fill=190,width=2)
    if poles:
        for px in (0.14, 0.78):
            d.rectangle([(px-0.0022)*W, (y0-0.06)*H, (px+0.0022)*W, 0.72*H], fill=210)
            d.rectangle([(px-0.026)*W,(y0-0.045)*H,(px+0.026)*W,(y0-0.038)*H],fill=210)
    a = blur(np.asarray(im).astype(np.float64)/255, 1.0)
    return over(img, col, np.clip(a*0.85,0,1))

def people(img, spec, col='#161822', seed=13, rim=None):
    """spec: [(x, y_base, height)]。x は W、y は H で正規化されているので、
    円を円に見せるには x 半径に H/W を掛ける必要がある（ここを間違えると頭が横に潰れる）。"""
    AR = H / W
    im = Image.new('L',(W,H),0); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    for (x, yb, h) in spec:
        hr = 0.062*h                      # 頭の半径（y 単位）
        hx = hr*AR*1.0
        head_cy = yb - h + hr
        d.ellipse([(x-hx)*W,(head_cy-hr)*H,(x+hx)*W,(head_cy+hr)*H],fill=255)
        d.rectangle([(x-hx*0.30)*W,(head_cy+hr*0.7)*H,(x+hx*0.30)*W,(yb-h*0.80)*H],fill=255)  # 首
        sw = 0.115*h*AR                   # 肩幅
        wa = 0.085*h*AR                   # 腰幅
        d.polygon([((x-sw)*W,(yb-h*0.80)*H),((x+sw)*W,(yb-h*0.80)*H),
                   ((x+wa)*W,(yb-h*0.44)*H),((x-wa)*W,(yb-h*0.44)*H)],fill=255)
        for s in (-1,1):                  # 腕
            d.line([((x+s*sw*0.86)*W,(yb-h*0.78)*H),((x+s*wa*1.15)*W,(yb-h*0.42)*H)],
                   fill=255,width=max(2,int(h*H*0.045)))
        for s in (-1,1):                  # 脚
            jitter=(r.random()-0.5)*0.012*h
            d.line([((x+s*wa*0.55)*W,(yb-h*0.45)*H),((x+s*wa*0.62+jitter)*W, yb*H)],
                   fill=255,width=max(2,int(h*H*0.058)))
    a_ = blur(np.asarray(im).astype(np.float64)/255, 0.9)
    img = over(img, col, np.clip(a_*1.2,0,1))
    if rim: img = screen(img, rim, blur(a_,4)*0.28)
    return img

def dof(img, near_mask=None, far=0.0, amount=2.0):
    """遠景をわずかにぼかす。空気感が出る。"""
    if far <= 0: return img
    b = blur(img, amount)
    w = np.clip((far - NY)/max(1e-6,far), 0, 1)[..., None]
    return img*(1-w) + b*w

def motes(img, n=180, seed=15, col='#fff2cc', ymax=1.0):
    """空気中の光の粒。"""
    r = np.random.default_rng(seed)
    layer = np.zeros((H,W))
    xs=(r.random(n)*W).astype(int); ys=(r.random(n)**0.8*H*ymax).astype(int)
    np.add.at(layer,(ys,xs), 0.4+r.random(n)*0.6)
    layer = blur(layer, 3.0)*4.0
    return screen(img, col, np.clip(layer,0,1)*0.5)

def paving(img, y0, y1, col='#9a9488', line='#7d786c', centre=0.5, w0=0.05, w1=1.4, rows=13, seed=17):
    """遠近のあるタイル舗装。"""
    poly=[(centre-w0/2,y0),(centre+w0/2,y0),(centre+w1/2,y1),(centre-w1/2,y1)]
    m = silhouette_mask([poly],1.0)
    img = over(img, col, m*0.96)
    img = texture(img, m, seed=seed, amount=0.10, res=(8,10))
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    for k in range(rows):
        u=(k/rows)**1.9
        y=y0+(y1-y0)*u
        hw=(w0+(w1-w0)*u)/2
        d.line([((centre-hw)*W,y*H),((centre+hw)*W,y*H)],fill=255,width=max(1,int(1+u*4)))
    for s in np.linspace(-0.5,0.5,9):
        d.line([((centre+s*w0)*W,y0*H),((centre+s*w1)*W,y1*H)],fill=160,width=2)
    a=blur(np.asarray(im).astype(np.float64)/255,1.0)*m
    return over(img, line, a*0.35), m
