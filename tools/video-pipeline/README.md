# video-pipeline — AI 影片製作流程

把「分鏡 → 角色定妝 → 提示詞 → 生成 → 品檢 → 紀錄」固定成一套流程。
流程本體是 Claude Skill：`.claude/skills/video-pipeline/SKILL.md`。
在這個 repo 裡對 Claude 說「用紫璃做一支 XX 主題的短片」就會照著跑。

## 檔案
| 路徑 | 用途 |
|---|---|
| `characters/zili.json` | 紫璃的角色卡（長相、服裝、負面詞、影片提示詞模板） |
| `projects/<日期>-<主題>/` | 每支影片的分鏡、提示詞、品檢紀錄 |
| `prompt-log.md` | 成功提示詞與失敗原因的累積紀錄 |

## 更新角色卡
1. 打開紫璃工坊，選好服裝與氛圍、生出滿意的定妝圖
2. 按「🎬 匯出角色卡」→ 下載 `zili-card.json`（同時複製到剪貼簿）
3. 改名為 `zili.json` 覆蓋 `characters/zili.json`，commit

## 串接 Google Flow（尚未安裝，待評估）
Flow 沒有官方 API，以下都是社群做的工具，靠「操作你已登入的 Chrome」運作：

| 工具 | 特點 | 注意 |
|---|---|---|
| [GTAI-1/flow-mcp](https://github.com/GTAI-1/flow-mcp/wiki) | 支援 Claude Code、Codex；用 Flow 方案內的點數 | 執行中電腦不能睡眠，Chrome 視窗要開著 |
| [ffroliva/gflow-cli](https://mcpservers.org/servers/ffroliva/gflow-cli) | MIT 授權，有 Claude Code plugin；可用 `--no-spend` 先只裝不花點數的工具 | 標示 alpha、非 Google 官方 |
| [kodelyx/flow-agent](https://github.com/kodelyx/flow-agent) | CLI + MCP + Chrome 擴充 | 要先啟動背景服務 |

共同風險：
- 非官方，Flow 改版就可能失效；也可能不符合 Google 服務條款
- 會用到你的 Google 帳號登入狀態，只在自己的電腦上裝
- 必須裝在**你自己的電腦**（有 Chrome、有登入），雲端 Claude 工作階段無法替你執行

建議順序：先裝 gflow-cli 並用 `--no-spend` 模式，確認讀得到專案和素材，再開放生成功能。
