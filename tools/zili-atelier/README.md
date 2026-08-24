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

## 支援的 API
| 供應商 | 預設模型 | 預設端點 |
|--------|----------|----------|
| xAI（Grok） | `grok-2-image-1212` | `https://api.x.ai/v1/images/generations` |
| OpenAI | `gpt-image-1` | `https://api.openai.com/v1/images/generations` |
| Google Gemini | `gemini-2.5-flash-image` | `https://generativelanguage.googleapis.com/v1beta/models` |
| 自訂 | 自填 | 任何 OpenAI 相容的 `images/generations` 端點 |

⚠️ **CORS**：瀏覽器直接打這些 API 有機會被 CORS 擋掉（錯誤訊息會是 `Failed to fetch`）。
若遇到，就架一個代理（這個 repo 的 `functions/` 可以放），再把「端點 URL」指向代理。

## 要改人設或加選項？
- **換人設**：設定頁的「角色鎖定字串」直接改，按儲存即可（有「還原預設人設」）
- **加衣服／場景**：編輯 `index.html` 的 `GROUPS` 陣列，每項是 `["中文標籤", "english prompt fragment"]`
- 預設人設常數在 `DEFAULT_LOCK`／`DEFAULT_NEG`

## 檔案
- `index.html` — 全部功能（單檔）
- `refs/` — 13 張角色參考圖
