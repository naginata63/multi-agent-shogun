# 📊 戦況報告
最終更新: 2026-04-29 07:28

## 🎌 YPP戦略確定 (2026-04-28 殿御裁断)

**選択肢①確定**: 21日再審査は諦め・30日後再申請(約5/27〜)に向け編集独自性強化
- 既存動画は削除せず据え置き・新規DoZ切り抜き独自編集要素必須
- 漫画ショート = **主力素材** ・MCN返答受領後は併用検討

## 🚨 要対応

### clip2 start_sec順序問題 (cmd_1509)
- panels_tono_clip2.json の start_sec が時系列逆転している箇所あり
- 殿のレビューと判断が必要・Phase2着手前に確認要

## 🔄 進行中

### cmd_1509 (high) — tono_clip1/clip2 漫画パネル化
- ✅ subtask_1509a2: panels_tono_clip1.json (7パネル) 完了
- ✅ subtask_1509b2: panels_tono_clip2.json (7パネル) CONDITIONAL_PASS
- 🚨 **殿レビュー待ち**: clip2 start_sec順序問題あり

### cmd_1545 (high) — litestream @reboot cron削除 (race condition根治)
- 🔄 subtask_1545a → 足軽3号: crontab @reboot行削除 (実行中)

### cmd_1544 (medium) — gacha2_old_v1 P2パネル再生成
- 🔄 subtask_1544a → 足軽2号: p2_success.png 単発再生成 (実行中)

## ⏸ 待機中

### cmd_1542 (low) — bun daemon systemd user unit化
- cmd_1539/1540/1541完遂後 → 着手可能

## ✅ 最近の完了

### cmd_1543 (medium) — litestream_keepalive.sh 再診断 (2026-04-29) 軍師判断A
- **keepalive.sh は正常**
- 真因: **@reboot sleep 30 と user systemd のrace condition**
  - is-enabled チェック時に DBus 未初期化 → false → nohup fallback
  - 直後に systemd が litestream を別経路起動 → 二重起動 (pid=2621 + pid=2623)
- 修正: @reboot cron 削除 → cmd_1545 で実施

### cmd_1541 — haiku SDK MAX_CONCURRENT=5 + Idle timeout=60s (2026-04-29)
### cmd_1539 — bun daemon pgrep guard + HOME統一 (2026-04-29) CONDITIONAL_PASS
### cmd_1538 — litestream LTX残骸クリーン (2026-04-29) QC PASS
### cmd_1540 — chroma-mcp健全性監視 cron (2026-04-29) QC PASS
### cmd_1537 — chroma-mcp根因解析 (2026-04-29)

## 🔧 技術負債

- **hooks.json patch追跡**: plugin更新時に消失リスク → claude_mem_hooks_patch.md 作成推奨
- **worker.pid書込なし**: worker-service.cjs内部問題 → daemon再起動必要・慎重判断
- **systemd_cron_design_rule**: 軍師推奨 — user systemd auto-start で十分な unit には @reboot cron を入れない原則を文書化せよ
- **git push**: 家老paneでGitHub認証なし → 殿のpaneで `git push origin main` 必要
