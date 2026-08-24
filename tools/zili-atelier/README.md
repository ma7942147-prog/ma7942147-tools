# 紫璃工坊（Zili Atelier）

單頁 HTML 工具：固定的角色模板（紫璃），選場景／姿勢／服裝／氛圍／比例後
**直接呼叫 AI 繪圖 API 生成圖片**，生成過的圖自動存進相簿。

## 用法
用瀏覽器打開 `index.html`（不需伺服器）。

### 三個分頁
| 分頁 | 做什麼 |
|------|--------|
| 🖼 **工坊** | 選搭配 →「生成紫璃」→ 看圖、下載、再生成一張 |
| 📖 **設定** | 填 API Key、選供應商／模型、每日上限、改角色鎖定字串 |
| 🖼 **相簿** | 看所有生成過的圖，點圖放大，可下載／複製當時提示詞／刪除 |

### 第一次使用
1. 到「設定」選 API 供應商（xAI Grok／OpenAI／Gemini／自訂端點）
2. 貼上 API Key，確認模型名稱與端點 → 按「儲存設定」
3. 回「工坊」選搭配 → 按「生成紫璃」

API Key 只存在這台裝置的瀏覽器 localStorage，**不會進 git、不會傳給第三方**，
只會直接送到你設定的那個 API。

## 功能
- 頂端角色參考圖：外觀鎖定基準（臉、髮、髮箍不變）
- 七組選項：場景 14／姿勢 12／上身 12／下身 10／鞋子 6／氛圍 6／畫面比例 6
- 額外指示自由輸入欄
- 每日生成次數上限（預設 10 次，設定可改，可手動重設）
- 🎲 隨機搭配、☆ 收藏搭配、⧉ 複製提示詞
- 相簿存在瀏覽器 IndexedDB，換裝置不會跟著走

## 部署到 Firebase Hosting（推薦：Key 不放瀏覽器）

在你自己的電腦上跑（這個 repo 已經接 `my-teaching-tools-77014`）：

```bash
# 1. 裝 CLI 並登入（只要做一次）
npm install -g firebase-tools
firebase login

# 2. 設定兩個 secret
#    IMAGE_API_KEY     = 你的 xAI / OpenAI / Gemini API Key
#    ZILI_ACCESS_TOKEN = 你自己想一組通行碼，等下要填進網站設定頁
firebase functions:secrets:set IMAGE_API_KEY
firebase functions:secrets:set ZILI_ACCESS_TOKEN

# 3. 部署（網站 + 代理 function）
cd functions && npm install && cd ..
firebase deploy --only hosting,functions
```

部署完會看到兩個網址：

| 東西 | 網址長相 |
|------|----------|
| 網站 | `https://my-teaching-tools-77014.web.app/tools/zili-atelier/` |
| 代理 function | `https://generateimage-xxxxx-uc.a.run.app`（deploy 訊息裡的 `generateImage`） |

最後打開網站 → 設定頁：
1. API 供應商選 **Firebase 代理**
2. 「端點 URL」貼上代理 function 的網址
3. 「通行碼」填剛剛設的 `ZILI_ACCESS_TOKEN`
4. 「代理背後用哪家」選 xAI／OpenAI／Gemini，模型留空就用該家預設
5. 按儲存 → 回工坊按「生成紫璃」

**為什麼要通行碼**：function 網址是公開的，沒有這道檢查的話任何人都能拿去燒你的 API 點數。
通行碼不對就回 401，不會打到上游。

## 支援的 API
| 供應商 | 預設模型 | 預設端點 |
|--------|----------|----------|
| xAI（Grok） | `grok-2-image-1212` | `https://api.x.ai/v1/images/generations` |
| OpenAI | `gpt-image-1` | `https://api.openai.com/v1/images/generations` |
| Google Gemini | `gemini-2.5-flash-image` | `https://generativelanguage.googleapis.com/v1beta/models` |
| 自訂 | 自填 | 任何 OpenAI 相容的 `images/generations` 端點 |
| **Firebase 代理** | 由代理決定 | 你部署的 `generateImage` function |

⚠️ **直連模式的 CORS 問題**：瀏覽器直接打 x.ai／OpenAI／Gemini 常會被 CORS 擋掉
（錯誤訊息是 `Failed to fetch`），而且 API Key 得放在瀏覽器裡。
所以正式使用請走上面的 **Firebase 代理**，直連模式當本機測試用就好。

## 要改人設或加選項？
- **換人設**：設定頁的「角色鎖定字串」直接改，按儲存即可（有「還原預設人設」）
- **加衣服／場景**：編輯 `index.html` 的 `GROUPS` 陣列，每項是 `["中文標籤", "english prompt fragment"]`
- 預設人設常數在 `DEFAULT_LOCK`／`DEFAULT_NEG`

## 檔案
- `index.html` — 全部功能（單檔）
- `refs/` — 13 張角色參考圖
