| 實驗 | 任務 | 比較 | n | 成功率 | 成本中位數變化 | 95% CI（bootstrap） | 有把握？ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| calib_luna | T1 修分頁 bug | 無 AGENTS.md vs 有 AGENTS.md | 3 | 3/3 → 3/3 | +2.0% | -17.4% ~ +21.2% | 否 |
| calib_luna | T2 新增 endpoint | 無 AGENTS.md vs 有 AGENTS.md | 3 | 3/3 → 3/3 | -2.2% | -43.7% ~ +30.7% | 否 |
| calib_luna | T3 修 CI 檢查 | 無 AGENTS.md vs 有 AGENTS.md | 3 | 3/3 → 3/3 | +63.8% | -41.6% ~ +86.4% | 否 |
| calib_luna | T4 拆常數 | 無 AGENTS.md vs 有 AGENTS.md | 3 | 3/3 → 2/3 | -6.1% | -25.4% ~ +13.1% | 否 |
| calib_luna | T5 資料遷移 | 無 AGENTS.md vs 有 AGENTS.md | 3 | 3/3 → 3/3 | +31.6% | +3.4% ~ +56.5% | 是 |
| e09_agents_md | T1 修分頁 bug | 無 AGENTS.md vs 有 AGENTS.md | 5 | 5/5 → 5/5 | +15.0% | -34.7% ~ +32.7% | 否 |
| e09_agents_md | T2 新增 endpoint | 無 AGENTS.md vs 有 AGENTS.md | 5 | 5/5 → 5/5 | -13.2% | -38.8% ~ +29.0% | 否 |
| e09_agents_md | T3 修 CI 檢查 | 無 AGENTS.md vs 有 AGENTS.md | 5 | 5/5 → 5/5 | +28.7% | +16.5% ~ +79.6% | 是 |
| e11_skills | T5 資料遷移 | 有 Skill vs 無 Skill | 5 | 5/5 → 5/5 | -52.4% | -65.3% ~ -19.5% | 是 |
| e13_search_tools | T4 拆常數 | 加上 grep/find/ls vs 預設四個工具 | 5 | 5/5 → 5/5 | -15.4% | -43.2% ~ +22.8% | 否 |
| e15_system_prompt | T2 新增 endpoint | 規則灌進 system prompt vs 有 AGENTS.md | 5 | 5/5 → 5/5 | -16.6% | -40.8% ~ +4.0% | 否 |
| e15_system_prompt | T3 修 CI 檢查 | 規則灌進 system prompt vs 有 AGENTS.md | 5 | 5/5 → 5/5 | +37.4% | -21.8% ~ +70.1% | 否 |
| e17_thinking | T2 新增 endpoint | thinking low vs thinking off | 5 | 5/5 → 5/5 | +34.2% | -28.6% ~ +50.6% | 否 |
| e17_thinking | T2 新增 endpoint | thinking high vs thinking off | 5 | 5/5 → 5/5 | +51.7% | -14.9% ~ +59.1% | 否 |
| e17_thinking | T2 新增 endpoint | thinking high vs thinking low | 5 | 5/5 → 5/5 | +13.0% | -10.2% ~ +20.5% | 否 |
| e17_thinking | T5 資料遷移 | thinking low vs thinking off | 5 | 5/5 → 5/5 | -33.0% | -71.7% ~ -11.5% | 是 |
| e17_thinking | T5 資料遷移 | thinking high vs thinking off | 5 | 5/5 → 5/5 | +11.4% | -27.3% ~ +45.6% | 否 |
| e17_thinking | T5 資料遷移 | thinking high vs thinking low | 5 | 5/5 → 5/5 | +66.2% | +29.5% ~ +115.1% | 是 |
| e22_compaction | T5 資料遷移 | 強制觸發 compaction vs 不會觸發 compaction | 5 | 5/5 → 5/5 | +45.7% | +3.9% ~ +76.2% | 是 |
| e26_tool_gate | T7 清暫存檔 | 閘門 v1 vs 沒有閘門 | 5 | 5/5 → 2/5 | +41.9% | -5.3% ~ +80.8% | 否 |
| e28_sandbox | T2 新增 endpoint | docker vs host | 5 | 5/5 → 5/5 | +11.6% | -28.2% ~ +41.9% | 否 |

共 21 組比較，其中 6 組的區間不含 0。CI 為 10,000 次 percentile bootstrap；n 是每組的執行次數。
