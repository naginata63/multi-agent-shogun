# 総点検の目付け(Sonnet)への下知の雛形

`yokonaga_total_qc.md` の手順4で使う。{ } の欄を差し替え、範囲ごとに3通り書き出して `Agent(model=sonnet)` に渡す。
英語で書くのは、目付けが英語の指示のほうが手順を落とさぬため(返す台帳は日本語でも英語でもよい)。

---

You are visual QC inspector {EYE} for version {VER} (out_{VER}) of the landscape YouTube compilation 「{TITLE}」 (Dozle-sha Minecraft clips; Japanese). Read-only on the video and project; write only your result file.

B=/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/{WORK}
- Final: B/out_{VER}/{VIDEO} (get the length with ffprobe). Timeline B/out_{VER}/marks.json ([start_sec, kind, file]). Card PNGs B/out_{VER}/png/. Script B/plan.json. Cuts (lo/hi per source clip, editor "why"): /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/editor/{WORK}.json. Source word-level STT: /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/qwen_stt/merged_<videoid>.json. Fact ledger: {LEDGER}.
- Rules: /home/murakami/multi-agent-shogun/shared_context/procedures/yokonaga_cards_quiz_build.md §2 and §5 only.
- Previous version's ledger: B/qc_{PREV}/raw_eye1.json, raw_eye2.json, raw_eye3.json. Times there are {PREV} seconds — map by part name or source cut id, not by time.
- What changed in {VER} (check these first): {CHANGES}
- Known and accepted by the director (do not report again unless it got worse): {ACCEPTED}
- Machine check results for this version (sound levels, word cuts, flashes, banned words — already measured, do NOT re-measure; use them as a list of places to look): B/qc_{VER}/machine.json.

YOUR RANGE: {VER} {A} s to {Bs} s.

COST AND MEMORY RULES (a previous run of this inspection crashed the PC by running 5 copies of a speech model at once and burned the usage limit — follow these strictly):
- Do NOT load any ASR / speech / vision model. Do NOT redo sound or card-text measurements: those are finished (see B/qc_{VER}/machine.json).
- Look at pictures through the contact sheets first: B/qc_{VER}/tiles/t_NNN.jpg. Sheet N covers {VER} seconds (N-1)*30 to N*30, 1 frame per second, in reading order, timestamp in the corner. Read only the sheets for your range.
- Grab a full-size frame (ffmpeg -nostdin -v error -ss T -i B/out_{VER}/{VIDEO} -frames:v 1 -y out.png, then Read) only where a sheet shows something to check. At most 40 full-size frames in total. Never run more than 2 ffmpeg at once.
- Any python that might use more than 1 GB must be run as: /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/scripts/heavy.sh -m 4G python3 ...
- Keep tool output short (head/tail, jq filters). Do not cat big JSON files whole.
- Scratch dir: {SCRATCH}/{VER}_{EYE}/

DO:
1. Regression: for every {PREV} finding in B/qc_{PREV}/raw_eye*.json whose part lies in your range, answer fixed / unfixed / n/a with measured evidence. Skip findings whose insp is S, T or machine (sound and card text are re-measured by machine).
2. Fresh visual checks in your range only:
   a. Overlays (source tag top-left, chips, ※ notes, any added caption) must not cover faces, moving name tags, the top name band, the bottom 140 px (本家 telop / hotbar) or top-right y≈20-130. Check every overlay while it is on screen.
   b. Added ※ notes: by the director's rule there should be none. Report every ※ or added caption that is not burned into the source (compare with the source frame).
   c. Cut context: for every clip, read the source STT around lo and hi (±5 s). Does the clip keep its setup (前フリ) and its punchline / reaction? Does a sentence get cut off, or does the next sentence start before hi?
   d. Picture continuity at every clip boundary on the sheets: stray 1-4 frames of another view, debug screens, black/white flashes, a clip ending on a confusing frame.
   e. Facts on cards vs what the clips show (who did what, who won), honorifics: guests get 「さん」; Dozle-sha members and ドズル社 never do; progress/death messages are 「ログ」 not チャット.
   f. Each chapter shows the cheat / handicap actually working on screen at least once (not only announced). Report a chapter where it is never shown.
3. Write B/qc_{VER}/raw_{EYE}.json as soon as you have your first result and rewrite it as you go: {"scope", "regression":[{"prev_id","status","evidence"}], "findings":[{"id":"{EYE}-01","severity":"重い|中|軽","t":<{VER} sec>,"part","problem","evidence","fix"}]}. 重い = viewer clearly notices / wrong fact / flash / cut word; 中 = noticeable on careful watch; 軽 = polish. Every finding and every "OK" needs measured evidence.

Final reply: only counts per severity, the regression tally and the path. No long summary.
