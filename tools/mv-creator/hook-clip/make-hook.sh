#!/usr/bin/env bash
# 把 16:9 的 MV 剪成直式 9:16 短影音片段（例如 Suno 短影音 hook）
#
# 用法：
#   ./make-hook.sh <來源.mp4> <起點秒數> <長度秒數> <輸出.mp4> [模式]
#
# 模式：
#   full   （預設）保留歌曲＋原片字幕，中間 4:3 畫面、上下模糊背景
#   silent 無聲、裁掉原片燒進去的字幕（裁掉畫面底部約 17%）
#
# 例：停損 MV 的 45 秒純影片版
#   ./make-hook.sh 停損_MV_字幕版.mp4 97.9 45 停損_45s_9x16_純影片.mp4 silent
set -euo pipefail

SRC="$1"; START="$2"; DUR="$3"; OUT="$4"; MODE="${5:-full}"
FADE_OUT_AT=$(python3 -c "print(max(0, $DUR - 1.5))")

if [ "$MODE" = "silent" ]; then
  # 原片字幕位於 1080p 畫面 y≈910–985，只取上方 896 像素
  ffmpeg -y -ss "$START" -i "$SRC" -t "$DUR" -an -filter_complex "
    [0:v]crop=iw:896:0:0,split[a][b];
    [a]crop=504:896,scale=1080:1920,boxblur=30:3,eq=brightness=-0.15[bg];
    [b]crop=1194:896,scale=1080:810[fg];
    [bg][fg]overlay=0:(H-h)/2,fade=t=in:st=0:d=0.3,fade=t=out:st=$FADE_OUT_AT:d=1.5,format=yuv420p[v]" \
    -map "[v]" -c:v libx264 -preset medium -crf 20 -r 24 -movflags +faststart "$OUT"
else
  ffmpeg -y -ss "$START" -i "$SRC" -t "$DUR" -filter_complex "
    [0:v]split[a][b];
    [a]scale=-2:1920,crop=1080:1920,boxblur=30:3,eq=brightness=-0.15[bg];
    [b]crop=1440:1080,scale=1080:810[fg];
    [bg][fg]overlay=0:(H-h)/2,fade=t=in:st=0:d=0.3,fade=t=out:st=$FADE_OUT_AT:d=1.5,format=yuv420p[v];
    [0:a]afade=t=in:st=0:d=0.25,afade=t=out:st=$FADE_OUT_AT:d=1.5[au]" \
    -map "[v]" -map "[au]" -c:v libx264 -preset medium -crf 20 -r 24 \
    -c:a aac -b:a 192k -movflags +faststart "$OUT"
fi
