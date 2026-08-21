# 人聲分離（vocal-remover）

demucs 的權重來源（dl.fbaipublicfiles.com）和 torch hub（download.pytorch.org）、
zenodo 都被這個環境的網路政策擋掉，但 **github.com 的 release 資產可以下載**，
所以改用 tsurumeso/vocal-remover（純 PyTorch 的 U-Net，權重放在 GitHub Releases）。

```bash
pip install torch librosa soundfile resampy opencv-python-headless tqdm
git clone --depth 1 https://github.com/tsurumeso/vocal-remover.git
curl -L -o vr.zip https://github.com/tsurumeso/vocal-remover/releases/download/v6.0.0b4/vocal-remover-v6.0.0b4.zip
unzip vr.zip                      # models/baseline.pth（59MB）在裡面
cd vocal-remover
python3 inference.py --input ../song.mp3 --pretrained_model models/baseline.pth --gpu -1 --output_dir ../vrout
# CPU 4 核跑 4:49 的曲子約 8 分鐘，產出 song_Vocals.wav / song_Instruments.wav
```

分離完之後：

- `vocal_onsets.py` — 從人聲軌抓發聲區間
- `vad.py` — 算「人聲軌 / (人聲軌+伴奏軌)」的能量比，也就是**模型自己的把握度**，
  比單看音量可靠得多
- `vad_seg.py` — 用把握度切句

## 這首歌實測到的東西

| 區間 | 人聲軌音量 | 模型把握度 | 判讀 |
|---|---|---|---|
| 0:08–0:13 | 0.38–0.64 | 0.90–0.97 | 前奏，人聲質感的成分 |
| 0:23–0:30 | 0.5–1.47 | 0.85–0.92 | 短促的吟唱，非歌詞 |
| 0:30.25–0:35.5 | **0.00** | — | 完全靜音 |
| 0:36–0:47 | 0.67–1.02 | **0.61–0.78** | 有聲但模型不確定 |
| 0:48 之後 | 0.44–1.08 | **0.94–0.98** | 確定是主唱 |

0:36–0:47 這一段兩邊證據打架（音量夠大但模型把握度低），自動判斷分不出來。
最後採用實際聽的人的回報（比 0:36.1 晚約 5–6 秒），設 `lyric_offset = 6.0`。

**還是對不準就只改 `timings.json` 的 `lyric_offset` 一個數字**，
或用 `OFFSET=7.5 python3 render.py out.mp4` 試不同值，不必重畫圖。

## 對拍還是對不準的時候

自動偵測在這首歌上連續三次抓錯（0:04 → 0:36.10 → 0:42.10 都還是太早），
問題出在 0:23-0:47 之間有數段「人聲質感但不是主唱」的成分，
分離模型的把握度在那裡只有 0.61-0.78，判斷不了。

最後把第一句錨在把握度 0.94-0.98 才穩定的 0:48.46（`lyric_offset = 12.36`），
並做了 `tap.html`：一頁式的對拍器，歌曲用 base64 內嵌在 HTML 裡，
手機打開就能邊聽邊按，41 下打完把 JSON 複製出來貼回 `timings.json` 的 `lines`。
這是唯一 100% 準的方法 —— 用人的耳朵。
