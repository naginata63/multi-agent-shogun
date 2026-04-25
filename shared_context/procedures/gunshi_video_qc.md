# 軍師 動画QC手順

軍師が動画系cmdのQCを実施する際の手順。`shared_context/qc_template.md` セクションE（動画タスクQC追加項目）の実践ガイド。

## 前提

- 動画系cmd = 視点切替MIX・4画面MIX・ハイライト等、動画成果物を含むタスク
- この手順は qc_template.md タイプ別チェック（A-D）に**追加**して実施する
- ffprobe/API確認のみでPASSを出してはならない（cmd_597/cmd_1464教訓）

## ステップ

### 1. 事前確認
- [ ] タスクYAMLの acceptance_criteria に視覚検証項目が含まれているか確認
- [ ] sync_record.yaml のパスが指定されているか確認
- [ ] `shared_context/procedures/multi_view_scene_switch.md` 鉄則3（視点切替）・鉄則4（テロップ）を把握

### 2. 視覚検証（mpv実視聴）
```bash
mpv --speed=2.0 <成果物動画.mp4>
```
- **全編視聴必須**。38分動画なら4-5分。ショートカット不可
- 以下を確認:
  - seg境界の transition（wipeleft等）が正しく適用されているか
  - 視点切替パターンが鉄則3に準拠（最初/最後=基準視点固定、中間=バリエーション）
  - 右上テロップが鉄則4に準拠（`<ボス名>(<戦闘番号>)` 形式）
  - 1戦目短seg（≤200秒）の場合、シンプルパターン（MEN→4画面→MEN）が適用されているか
  - 音声echo・途切れが無いか

### 3. sync_record.yaml 検証
- [ ] ファイルが存在し、multi_view_sync.md Step 7フォーマットに準拠しているか
- [ ] `visual_verification.result=pass` が記録されているか
- [ ] 各segの `view_switches` と実際のMIX結果が一致するか（冒頭・中盤・終盤3箇所サンプリング）

### 4. サンプル動画検証
- [ ] `verify_60s_*.mp4` が存在する場合、実再生してecho無し・視点切替正常を確認

### 5. 総合判定
- **PASS**: E-1〜E-3全項目クリア
- **CONDITIONAL PASS**: 軽微な問題のみ（理由必須明記）。視覚検証スキップは理由必須
- **FAIL**: 視覚検証で規格逸脱を発見した場合

## 報告フォーマット

QCレポートに以下セクションを追加:
```yaml
video_qc:
  mpv_visual_check: pass/fail
  mpv_checked_segments: [seg1sen, seg8sen]
  sync_record_exists: true/false
  sync_record_consistency: pass/fail
  findings:
    - "seg1sen: MEN→4grid→MEN パターン確認 OK"
    - "seg8sen: 右上テロップ 'エキドナ(8戦目)' 確認 OK"
  issues: []
```
