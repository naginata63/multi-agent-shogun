# panel_review.html ステータス表示+characters修正手順（cmd_1355）

## 修正1: panel_review_gen.py — showStatus自動消去削除+スピナー追加

### showStatus関数の修正
- `setTimeout`（自動消去）を削除
- 生成中は `⏳ 生成中...` を表示し続け、完了/失敗で上書き
- CSSアニメーションでローディングスピナーを追加:
  ```css
  .spinner { display: inline-block; animation: spin 1s linear infinite; }
  @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  ```
- 生成中メッセージ: `<span class="spinner">⏳</span> 生成中...`
- 完了メッセージ: `✅ パネル候補生成完了！`
- 失敗メッセージ: `❌ 生成失敗: {エラー内容}`

## 修正2: server.py — characters空問題修正

### プロンプト強化
`/api/generate_panels_llm` のプロンプトに以下を追加:
```
【重要】各パネルの "characters" フィールドには必ずメンバーキーを入れること。
使用可能なキー: dozle, bon, qnly, orafu, oo_men, nekooji
セリフがないパネルも含め、全パネルに characters を設定すること。
```

### バリデーション補完（Claude出力後）
```python
for i, panel in enumerate(panels):
    if not panel.get('characters'):
        # 対応するrowsのspeakerから補完
        if i < len(rows):
            speaker = rows[i].get('speaker', '不明')
            if speaker != '不明':
                panel['characters'] = [speaker]
```

## テスト
1. `grep -c 'showStatus\|setTimeout' panel_review.html` でsetTimeout削除確認
2. `grep -c 'characters' scripts/dashboard/server.py` でプロンプト強化確認
3. git commit & push

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽1号、subtask_1355a完了。ステータス表示修正+characters補完修正報告。" \
  report_completed ashigaru1
```
