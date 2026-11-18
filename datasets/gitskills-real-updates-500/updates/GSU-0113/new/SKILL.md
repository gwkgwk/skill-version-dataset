---
name: agent-master-recap
description: 使用復盤週報:結構統計 + 全庫語意深評(大材小用、prompt 重工),教練式直講
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/recap.sh:*), Bash(node ${CLAUDE_SKILL_DIR}/statusline/install.mjs:*)
---

先跑 `bash ${CLAUDE_SKILL_DIR}/recap.sh --rate-pct` 記下 BEFORE(格式 `used_percentage<TAB>resets_at<TAB>sampled_at`,`NA` 記為缺值),再跑:

!`bash ${CLAUDE_SKILL_DIR}/recap.sh $ARGUMENTS`

上面是結構性摘要與週報檔路徑(**注意:這一步已經覆寫了整份週報檔**,含之前 append 的第 5 章語意深評——這是 `recap.sh` 的既有行為,下面的流程要處理這個覆寫,不能假設舊內容還在)。接著做**語意深評**——對時間窗內每一個 session 判斷(全庫,不預篩):

1. 跑 `bash ${CLAUDE_SKILL_DIR}/recap.sh --list $ARGUMENTS`:首行 `CACHE<TAB><路徑>` 是深評 cache 的所在,其餘行是目前 session 清單(TSV:key、路徑、主要 model、output tokens、tool 數、時長分、429、標題)。
2. **讀取深評 cache**:路徑用上一步 `CACHE` 首行給的那個(固定的使用者層路徑,不受 `--out` 影響;用 Read 工具;不存在則視為 `{}`)。這個 JSON 是 `{ "<session key>": {tokens, tools, verdict, reason, suggestion} }`,存著上次深評每個 session 的結論。
3. 對每個 session:若 cache 沒有這個 key,或 cache 記錄的 tokens/tools 與這次 `--list` 讀到的不同(代表這個 session 有新內容)→ 需要重新深評;否則**直接複用 cache 裡的 verdict/reason/suggestion,不要派 subagent**(這是避免每次都重跑全部 19 個的關鍵——只對真正變化的 session 花 token)。
4. 對需要重新深評的 session 派出 subagent(單一訊息裡多個 Agent 呼叫,平行跑)。**每個 Agent 呼叫都固定帶 `model: "sonnet"`**(不論使用者當下 session 用什麼 model)——這是判斷「任務類型 vs model 是否合適」「prompt 哪裡含糊、怎麼改寫」的語意評分工作,需要穩定的理解與寫作能力,Haiku 對這種細膩判斷不夠可靠;而深評本身就是要抓大材小用,若拿使用者當下可能開著的旗艦 model 來做這件「檢查有沒有濫用旗艦 model」的工作也自相矛盾,故固定用 Sonnet,不隨使用者當下 session model 漂動。每個 subagent 的指示:
   - 先跑 `bash ${CLAUDE_SKILL_DIR}/recap.sh --dump <key>` 取得壓縮對話摘要(**不要讀 .jsonl 原檔,會爆 context**;若 session 之前深評過,只需比對/判讀新增的部分)。格式:`U 時間| user prompt`、`A 時間| model out=tokens txt≈可見文字B thk=thinking塊數 tools=[...]`、`ERR| tool 錯誤`。
   - 判斷 (a) **大材小用**:任務類型是什麼(蒐集資料/問答/寫程式/重構/除錯…)?所用 model 是否過強?out 大但 txt 小、又沒 tool,代表 token 多花在 thinking——輕任務出現這訊號=effort 開太大。若大材小用,給具體建議(如「Haiku + effort medium 就夠」)。
   - 判斷 (b) **prompt 品質**:有沒有因指令含糊導致重工、繞路、agent 多做不必要的事(訊號:ERR、使用者修正/重說、同檔反覆編輯、方向急轉)?若有,引用原句並示範怎麼改寫。
   - 回傳:`verdict: ok|降模型|prompt可改進` + 理由一句 + 具體建議(沒問題就說 ok,不要硬掰)。
5. **重寫**(不是 append 增量片段)一份**完整**的「## 5. 語意深評」章節,涵蓋這次「新跑的 + 複用的」全部 19 個 session 的結論,**教練式風格**——直接講壞習慣、不打圓場、不堆砌禮貌詞。內容:
   - 只挑目前**最嚴重的幾個**(依當下 output token 排序,或訊號最明顯的 3~6 個,不是全部逐一列),每個講清楚「現在這樣做浪費在哪」+「換成哪個 model(Haiku/Sonnet/保留原model)」。
   - prompt 改進:只挑造成實際重工/多輪來回的案例,原句 → 改寫,不挑無傷大雅的小事。
   - 一句總評:目前的核心壞習慣是什麼、下一步具體改哪一件事。
   - 用 Read 週報檔案確認有沒有既有「## 5. 語意深評」標題;有就用 Edit **整段取代**(從該標題到檔尾),沒有就用 Edit append 到檔尾。**絕不產生 5.1/5.2 這種碎片化的追加小節**——每次都是一份自成一體、當下最新狀態的完整第 5 章。
6. **更新 cache**:把這次全部 session(新跑的用新結論、複用的維持原結論)的 `{tokens, tools, verdict, reason, suggestion}` 寫回第 1 步 `CACHE` 首行給的同一個路徑(用 Write 工具整份覆寫),供下次 `/agent-master-recap` 比對。
7. 用**教練口吻**(直接、具體、不含糊其辭)向使用者摘要重點,**不要逐條複誦本週全部 session**——只講上面挑出的那幾個最嚴重的。
8. **回報這次 /agent-master-recap 深評的實際消耗**:
   - **Token**:對這次(只計新跑的 subagent,複用 cache 的不算)每一個 subagent 呼叫回傳的 usage,分別加總 `input_tokens`、`output_tokens`、`cache_creation_input_tokens`、`cache_read_input_tokens` 四個欄位(不要只報一個籠統總和)。回報格式固定為:「這次深評 M 個 session 新跑(N 個沿用 cache 未重跑):output X tokens・cache_read Y tokens(便宜,多為重複讀取已建好的 cache,非新運算)・input+cache_creation Z tokens」。**不要把四項相加成單一總數講給使用者聽**——cache_read 常佔絕大多數但成本遠低於 output,混在一起會讓這個 skill 的花費看起來遠比實際貴(容易被誤讀成跟旗艦 model 開發同等級的消耗)。
   - **5h 額度真實占用**:全部深評與寫檔都做完後,再跑一次 `bash ${CLAUDE_SKILL_DIR}/recap.sh --rate-pct` 記下 AFTER。若 BEFORE/AFTER 兩次都不是 NA 且 resets_at 相同(代表期間沒有跨過重置點),回報 `AFTER - BEFORE` 個百分點,即為這次深評真實吃掉的 5h 配額;若 resets_at 不同,說明「期間跨過額度重置,無法算差值」;若任一為 NA,說明「本機 statusline 快取不夠新(可能未安裝 statusline 或剛開機),無法算佔比」——**這三種情況都不要編一個數字出來湊。** statusline 模組隨本 skill 附帶(`statusline/`):若 NA 是因為沒安裝,可以問使用者要不要現在裝,同意後跑 `node ${CLAUDE_SKILL_DIR}/statusline/install.mjs`(會合併寫入 `~/.claude/settings.json`,原設定自動備份;移除加 `--uninstall`),重啟 session 後生效。
   - **寫回週報檔**:把上面兩項算出來的結果,用 Edit 接在週報檔「## 5. 語意深評」章節總評段落之後,新增一行 `> 本次深評消耗:{token 說明} ・ 5h 配額 {百分點或無法算的說明}`。這一步是紀錄這次深評本身的成本,不要開新的 ## 6 章節,也不要只停留在對話裡沒寫進檔案。
