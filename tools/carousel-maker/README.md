# carousel-maker · 輪播圖產生器

教學型輪播卡產生器（Threads / IG 直式，**1080×1350**）。
就是「小白開 AI」那種每日輪播圖的做法：**改文字 → 一鍵匯出 PNG**，不用會排版、不用裝任何東西。

## 怎麼用

1. 打開 `index.html`（雙擊，用瀏覽器開；建議 Chrome / Edge）。
2. 展開「✏️ 編輯內容（JSON）」，把文字改成你要的。
3. 按 **更新預覽** → 每張卡右下角 **下載 PNG**，或最上面 **⬇ 下載全部 PNG**。
4. 把 PNG 依序上傳到 Threads / IG 就是一組輪播。

> 字體用系統的中文黑體（PingFang / 微軟正黑），所見即所得。
> 若某些瀏覽器擋了自動匯出，改用截圖即可。

## 內容格式（JSON）

最外層是一個陣列，一個物件 = 一張卡：

```jsonc
{
  "kind": "cover",                 // 選填，封面卡用
  "tag": "小白開 AI · EP1",         // 選填，左上深色小標籤
  "eyebrow": "01 · What is it",    // 英文小標（· 會自動變紅點）
  "title": "到底什麼是 Claude Code？",
  "subtitle": "真的能取代工程師嗎？", // 選填，紅色副標
  "blocks": [ /* 見下方 */ ],
  "footer": { "note": "最後一頁：…", "brand": "HK AI DAILY", "page": "01/05" }
}
```

**行內強調**：文字用 `**兩個星號**` 包起來 → 變紅色重點；`\n` → 換行。

### 可用的 blocks

| type | 長相 | 欄位 |
|------|------|------|
| `lead` | 一段引言 | `text` |
| `dark` | 深色重點框 | `text`、`note`（選填小字） |
| `list` | 三行條列（左標籤＋右說明） | `items: [{label, tone, text}]` |
| `compare` | 左右兩欄對比 | `left / right: {tag, tone, title, text}` |
| `take` | 紅色「帶走句」框 | `text` |

`tone` 可用：`blue`、`red`、`orange`、`green`、`muted`。

## 設計說明

- 米白卡面 + 深色頁尾條 + 紅色重點，對齊參考帳號的視覺。
- 卡片樣式集中在 `index.html` 的 `<style id="cardcss">`，這段會被打包進匯出的 PNG。
- 匯出用純瀏覽器技術（SVG `foreignObject` → canvas → PNG），**不依賴任何外部程式庫**，離線可用。

## 之後可以加

- 換品牌色 / 換 logo 文字（改 `--red`、`footer.brand`）。
- 接 Firebase：每天用一份 JSON 自動產圖。
