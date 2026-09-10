# -*- coding: utf-8 -*-
"""把 MV 包成一頁可線上看、可下載的 HTML（發佈成 Artifact 用）。

Artifact 檢視器不給網頁自己觸發下載，必須走 downloads 能力：
  claude.use("downloads") → downloads.save({filename, data})
所以下載鈕會把內嵌的影片解回二進位再交給檢視器。
"""
import base64
import os
import sys

import project

ROOT = os.path.dirname(os.path.abspath(__file__))

PAGE = """<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,400&display=swap">
<style>
  :root{
    --ink:#1b1524; --dim:#6d6480; --line:#e4dced; --bg:#faf7fc;
    --card:#ffffff; --accent:#7b4bb8; --glow:#efe4ff;
  }
  :root:not([data-theme="light"]){}
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]){
      --ink:#f2ecf8; --dim:#a79cba; --line:#332b40; --bg:#100c16;
      --card:#1a1522; --accent:#c9a2ff; --glow:#2a1f3a;
    }
  }
  :root[data-theme="dark"]{
    --ink:#f2ecf8; --dim:#a79cba; --line:#332b40; --bg:#100c16;
    --card:#1a1522; --accent:#c9a2ff; --glow:#2a1f3a;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:16px/1.7 "PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif}
  .wrap{max-width:940px;margin:0 auto;padding:40px 22px 64px;
        display:flex;flex-direction:column;gap:26px}
  header{text-align:center;display:flex;flex-direction:column;gap:6px}
  h1{font-family:"Cormorant Garamond",Georgia,serif;font-weight:500;
     font-size:clamp(34px,6vw,52px);margin:0;letter-spacing:.01em;text-wrap:balance}
  .sub{color:var(--dim);font-size:14px;letter-spacing:.22em}
  video{width:100%;display:block;border-radius:14px;background:#000;
        box-shadow:0 18px 50px -22px rgba(60,20,110,.5)}
  .bar{display:flex;gap:12px;align-items:center;justify-content:center;flex-wrap:wrap}
  button{font:inherit;font-size:15px;padding:11px 22px;border-radius:999px;cursor:pointer;
         border:1px solid var(--accent);background:var(--accent);color:var(--bg);font-weight:600}
  button:hover{filter:brightness(1.08)}
  button:disabled{opacity:.55;cursor:default}
  button.ghost{background:transparent;color:var(--accent)}
  :focus-visible{outline:2px solid var(--accent);outline-offset:3px}
  .note{color:var(--dim);font-size:13.5px;text-align:center;max-width:620px;margin:0 auto}
  .facts{border:1px solid var(--line);border-radius:14px;background:var(--card);
         padding:6px 20px;display:grid;grid-template-columns:auto 1fr;gap:0 22px}
  .facts dt{color:var(--dim);font-size:13px;padding:9px 0;border-bottom:1px solid var(--line)}
  .facts dd{margin:0;font-size:14px;padding:9px 0;border-bottom:1px solid var(--line)}
  .facts dt:last-of-type,.facts dd:last-of-type{border-bottom:0}
  @media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap">
  <header>
    <h1>__TITLE__</h1>
    <p class="sub">__SUB__</p>
  </header>

  <video id="v" controls playsinline preload="auto"></video>

  <div class="bar">
    <button id="dl">下載 MV</button>
    <button class="ghost" id="cc">下載字幕時間碼</button>
  </div>
  <p class="note" id="msg">__NOTE__</p>

  <dl class="facts">__FACTS__</dl>
</div>

<script type="application/base64" id="mp4">__SRC__</script>
<script>
const B64 = document.getElementById('mp4').textContent.trim();
function bytes(b64){
  const bin = atob(b64), u = new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) u[i] = bin.charCodeAt(i);
  return u;
}
// 大檔用 data: URI 餵 <video> 在不少瀏覽器會載不起來，改成 Blob URL
const VID = bytes(B64);
document.getElementById('v').src =
  URL.createObjectURL(new Blob([VID], {type:'video/mp4'}));
const msg = document.getElementById('msg'), dl = document.getElementById('dl');
let downloads = null;
(async () => {
  downloads = window.claude && claude.use ? await claude.use('downloads') : null;
  if(!downloads){ dl.disabled = true; dl.textContent = '這個檢視器不支援下載'; }
})();
dl.onclick = async () => {
  if(!downloads) return;
  dl.disabled = true; dl.textContent = '準備中…';
  try{
    await downloads.save({filename:'__FILENAME__', data: VID.slice(0)});
    dl.textContent = '已儲存 ✓';
  }catch(e){
    dl.disabled = false; dl.textContent = '下載 MV';
    const m = {declined:'取消了，隨時可以再按一次。',
               too_large:'檔案超過檢視器允許的大小。',
               rate_limited:'剛剛已經有一個下載視窗，稍等一下再按。'};
    msg.textContent = m[e && e.code] || ('下載沒有成功：' + ((e && e.message) || '未知原因'));
  }
};
const ASS = __ASS__;
document.getElementById('cc').onclick = async () => {
  if(!downloads){ msg.textContent = '這個檢視器不支援下載。'; return; }
  try{
    await downloads.save({filename:'lyrics.txt', data: ASS});
    msg.textContent = '已存成 lyrics.txt —— 副檔名改成 .ass 就能直接掛在播放器上。';
  }catch(e){
    if(e && e.code === 'declined') return;
    msg.textContent = '字幕檔沒有存成功：' + ((e && e.code) || '');
  }
};
</script>
"""


def build(video, ass, dst, title="MV", sub="", facts=(), note="", download=False):
    b64 = base64.b64encode(open(video, "rb").read()).decode()
    html = PAGE.replace("__SRC__", b64)
    html = html.replace("__ASS__", __import__("json").dumps(
        open(ass, encoding="utf-8").read()))
    html = html.replace("__TITLE__", title).replace("__SUB__", sub)
    html = html.replace("__NOTE__", note)
    html = html.replace("__FILENAME__", f"{project.NAME}_MV.mp4")
    html = html.replace("__FACTS__", "".join(
        f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts))
    open(dst, "w", encoding="utf-8").write(html)
    mb = os.path.getsize(dst) / 1e6
    print(f"wrote {dst}  ({mb:.2f} MB)" + ("  ⚠ 超過 16 MB" if mb > 16 else "  OK"))


if __name__ == "__main__":
    build(os.path.join(project.BUILD, "MV_web.mp4"),
          os.path.join(project.BUILD, "lyrics.ass"),
          [a for a in sys.argv[1:] if not a.startswith("-")][0]
          if [a for a in sys.argv[1:] if not a.startswith("-")]
          else os.path.join(project.BUILD, "watch.html"))
