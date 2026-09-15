# my_first_pi_agent_project

iThome 鐵人賽 2026《Harness Engineering × Pi Agent 實戰：打造可觀測、可評估的 AI Coding Agent》的實作與實驗資料。

這個 repo 回答一個問題：**模型不變的前提下，harness 的每個元件（AGENTS.md、Skills、搜尋工具、thinking level…）到底讓 coding agent 的成功率、成本、工具呼叫次數變了多少？** 所有數字都能用這裡的程式碼重跑。

## 目錄

```
bench/
  fixtures/taskapp/     受測專案：一個埋了五個慣例的小型 Python API（約 60 個檔案）
  tasks/<task_id>/      任務定義：prompt、setup（把專案弄成待修狀態）、solution（參考解）、hidden（隱藏驗收測試）
  skills/               Skills 實驗用的 SKILL.md
  runner/               harness 無關的 runner：workspace 準備、驗收、session 解析、去識別化
    adapters/           每個 harness 一個 adapter（目前是 Pi）
experiments/
  configs/              每個實驗的設定（任務 × 條件 × 重複次數）
  results/<exp>/        runs.jsonl（每次執行一行）、summary.csv/md、sessions/、diffs/
  figures/              文章用的圖
analysis/summarize.py   從 runs.jsonl 產生表格與圖
```

## 受測專案埋的五個慣例

慣例的設計原則是「**找得到，但要付出成本**」：沒有 AGENTS.md 的 agent 讀了 README／docs 也能發現，但很容易漏掉。

| 慣例 | 怎麼被強制 |
| --- | --- |
| 真正的驗收是 `python scripts/check.py`，`python -m pytest` 只跑單元測試 | contract 測試需要 `-p taskapp_testing.plugin` 才跑得起來 |
| 新增 endpoint 要改三處：route、`schemas/__init__.py` 匯出、`ROUTE_REGISTRY` | dispatcher 找不到 schema 會回 500，check 也會檢查 registry 一致性 |
| 預期錯誤一律 raise `AppError` 子類 | 裸 `ValueError` 會變 500；check 用 AST 掃描 |
| `models_generated.py` 禁止手改 | check 比對 `schema/models.lock` 的 hash |
| routes／services 不能出現 0、1、-1 以外的數字常值 | check 用 AST 掃描 |

## 任務

| 任務 | 綁定的元件 | 內容 |
| --- | --- | --- |
| `t1_fix_pagination` | baseline | 修一個分頁邊界 bug |
| `t2_add_endpoint` | AGENTS.md | 新增 `GET /projects/{id}/stats`（要改三處） |
| `t3_fix_check` | AGENTS.md | 「CI 沒過」，但 `pytest` 是綠的，問題只有 `check.py` 看得到 |
| `t4_split_constant` | 搜尋工具 | 把散在 6 個檔案的 `DEFAULT_PAGE_SIZE` 拆成兩個常數 |
| `t5_migration` | Skills | 依專案的六步驟遷移流程新增 `Task.due_date` |

每個任務都通過 `selfcheck`：原始狀態驗收**必須失敗**、套上參考解**必須成功**。

## 怎麼判定成功

1. 先比對 agent 有沒有改到受保護的檔案（`scripts/check.py`、`tests/`、`pyproject.toml`…），有就記錄下來，然後**還原**。
2. 跑 `python scripts/check.py --json`。
3. 把該任務的隱藏測試複製進去跑。
4. 兩者都通過才算成功。判定只看 exit code，不用 LLM 當裁判。

## 重跑

需求：Node 24、Pi 0.84.3、Python 3.11+、已登入的 Pi provider。

```bash
# 1. 受測專案用的乾淨 Python 環境（放在 repo 外面，agent 看不到）
uv venv D:/pi-bench-runs/_env/venv --python 3.13
uv pip install --python D:/pi-bench-runs/_env/venv/Scripts/python.exe pytest==8.3.4 ruff==0.15.5

# 2. 不花 token 的自我檢查
python -m bench.runner.cli selfcheck

# 3. 跑實驗（可中斷，重跑會從沒做完的地方接續）
python -m bench.runner.cli run experiments/configs/e09_agents_md.json

# 4. 產生表格與圖
python -m analysis.summarize e09_agents_md
```

路徑可用環境變數改：`BENCH_RUNS_ROOT`（每次執行的工作目錄）、`BENCH_PYTHON`（受測專案用的 python）、`PI_CLI_JS`。

每次執行都在 `BENCH_RUNS_ROOT` 底下的獨立目錄進行，而且是獨立的 git repo，確保 Pi 往上層找 `AGENTS.md`、往上找 `.agents/skills` 時不會撿到別的東西。Pi 一律帶 `--no-extensions --no-skills --no-prompt-templates --no-themes`，只有實驗條件明確指定的東西會被載入。

## 換成別的 harness

runner 只依賴 `bench/runner/adapters/base.py` 的 `HarnessAdapter` 介面：給一個工作目錄、prompt、條件，回傳 exit code 與 session 檔。任務、條件、驗收都跟 harness 無關，寫一個 Claude Code 或 Codex 的 adapter 就能跑同一組任務。

## 資料與隱私

`experiments/results/` 裡的 session 與 diff 在寫出前會把本機家目錄、使用者名稱、電腦名稱、工作目錄換成 `<HOME>`、`<user>`、`<host>`、`<RUNS>`。session 中的 reasoning 是 provider 回傳的加密內容，無法還原。
