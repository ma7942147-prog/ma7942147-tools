# -*- coding: utf-8 -*-
"""timings.json -> tools/tottori-mv/sync.html 的歌詞清單（LINES_PLACEHOLDER 替換）"""
import json, re, sys, io
cfg = json.load(open('timings.json', encoding='utf-8'))
SEC = {0,4,8,14,18,22,28,32}   # 段落起始行（Verse/Pre/Chorus/Bridge/Outro）
data = [[t, tx, (i in SEC)] for i,(t,tx) in enumerate(cfg['lines'])]
js = json.dumps(data, ensure_ascii=False)
p = sys.argv[1] if len(sys.argv)>1 else '../../../../../../home/user/ma7942147-tools/tools/tottori-mv/sync.html'
html = io.open(p, encoding='utf-8').read()
html = re.sub(r'const DEFAULT = .*?;\n', 'const DEFAULT = ' + js + ';\n', html, count=1, flags=re.S)
io.open(p,'w',encoding='utf-8').write(html)
print('sync.html updated:', len(data), 'lines')
