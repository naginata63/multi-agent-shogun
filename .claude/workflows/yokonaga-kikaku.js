export const meta = {
  name: 'yokonaga-kikaku',
  description: '収益重視で次の横長動画の企画を、実績分析→多視点の発案→反証→採点→決定まで一気通貫で検討する',
  whenToUse: '殿が「横長なにつくればいい」「企画検討せよ」と言った時。args: {date:"YYYY-MM-DD"(materials の日付), background:"今回の経緯(任意)"}。手順書 shared_context/procedures/yokonaga_kikaku_meeting.md',
  phases: [
    { title: 'Understand', detail: '実績・他ch・素材・殿の掟・過去案の5方面を並行で調べる' },
    { title: 'Ideate', detail: '6つの視点で企画を発案(素材の実在を確かめて)' },
    { title: 'Merge', detail: '重複をまとめる' },
    { title: 'Verify', detail: '各案を3つの視点で反証' },
    { title: 'Judge', detail: '3人の審査で採点' },
    { title: 'Decide', detail: '1本に決め、作り方と見切り条件まで書く' },
    { title: 'Critic', detail: '抜けの点検' },
  ],
}

const P = '/home/murakami/multi-agent-shogun/projects/dozle_kirinuki'
const MEM = '/home/murakami/.claude/projects/-home-murakami-multi-agent-shogun/memory'
// 2026-10-22 の大会議(合流縦断の案A を出し、殿が即「あんa制作開始」)の台本を、日付と経緯を args で渡せる形にした物
const A = args || {}
const D = A.date   // 夜の自動の材料 work/autopilot/<D>/ の日付(必須)
if (!D) throw new Error('args.date (YYYY-MM-DD) が要る')
const SCR = A.scratch || `${P}/work/kikaku_scratch/${D}`

const CTX = `
【背景】YouTube チャンネル「毎日ドズル社切り抜き」(ドズル社のマイクラ動画の切り抜き。YPP収益化済み)。殿(チャンネル主)の問い: 「次の横長(長尺)動画は何を作ればいいのか。収益重視で」。
${A.background || '夜の横長決定会議の結論(work/autopilot/_yokonaga/decision.json)はあるが、それに縛られず、ゼロから一番稼げる案を探す。'}

【収益の事実】(2026-10-22 時点。調査:own で最新値に置き換えて読め)1000再生あたり収益: 長尺 ¥317.63 / ショート ¥14.03(約22.6倍)。期間収益の42.7%が長尺で、長尺の再生は全体の3.2%。新作の横長を出した直後に日別収益が上がり、新作が無い期間に下がる。

【主な資料(読むだけ。書き換え禁止。計算用の一時ファイルは ${SCR} に置け)】
- ${P}/work/autopilot/${D}/materials_meeting.md : 自ch横長25本の公開後1/3/7日の初速表・維持率の所感・収益の所感・流行り検知・企画ストック・提案台帳(殿の返事)。最重要
- ${P}/work/autopilot/${D}/yokonaga_a.json / yokonaga_b.json / yokonaga_decision.json : 今日の決定会議の提案者・反証者・決裁役
- ${P}/work/autopilot/${D}/yokonaga_candidates.md : 過去5夜の横長案と検分結果
- ${P}/analytics/${D}_raw.json : per_video_analytics(全動画の尺・平均視聴秒・維持率%・再生・視聴分)、revenue(by_video・by_video_period・daily・by_content_type)、traffic_sources、retention_top5。日別は ${P}/analytics/YYYY-MM-DD_raw.json(3月〜)と _snapshot.md
- ${P}/context/kikaku_yokonaga_*.md(0821/0829_2/0902/0903/0926/1017)・kikaku_stock.md・kikaku100_ideas_20260904.json・kikaku_chouhen_20260829.md・kirinuki_method.md : 過去の企画会議と殿の判断
- ${P}/work/trend/long/latest.json と snap_*.json : 他chの横長で伸びている元動画(再生/日・他ch数・題)。${P}/work/trend/latest.json はショート版
- 殿の掟(memory): ${MEM}/index_ranking_thumb.md(横長・ランキング・サムネの索引。そこから各ファイルを読む)、${MEM}/feedback_judge_format_by_first_days_trend.md、feedback_kikaku_viewer_question_first.md、feedback_kikaku_seasonality_and_negative_labels.md、feedback_no_copying_past_formats.md、feedback_yokonaga_thumbnail_before_upload.md、feedback_dozle_no_honorific.md、feedback_ai_zero_detection_needs_human_recall_check.md、feedback_count_check_against_known_total.md
- 素材: 本家の語単位の文字起こし ${P}/work/qwen_stt/merged_<動画ID>.json(213本)、コメント全件 ${P}/work/comment_db/raw_full/<動画ID>.json(904本・title/comments[text,likes])。
  検索道具: cd ${P} && python3 scripts/autopilot/scene_tools.py videos(文字起こしのある回の一覧) / grep <正規表現>(全回の文字起こしを検索) / window <ID> <秒> --before 20 --after 25 / comments <ID> --top 15(同じ秒に集まったコメント) / hot --days 4000 --top 40(全回で同じ秒に人が集まった場面)
- ドズル社メンバー: ドズル・ぼんじゅうる・おんりー・おらふくん・おおはらMEN(+ネコおじ)。「ドズル社さん」「ドズルさん」等の敬称を足すな。

【殿の掟(破れば即却下)】
1. 視聴者が知りたい問いを一言で書け、答えを聞いて「へえ」となること。測れる・競合空白というだけで選ぶな。
2. 暦: 大賞・総決算系は年末(12月)。いま ${D}。季節の行事(ハロウィン10/31 等)を暦で確かめよ。
3. メンバーへの腐すラベル(ポンコツ等)はファンが実際に使う呼び名以外禁止。
4. 過去の自ch作品の型の使い回し禁止。構成か見せ方に新しい工夫を1つ入れる。
5. 型の強さは累計ではなく、同じ型の直近3本の公開後1日/7日の初速の推移で判断する(殿「なのは誰だっていう形式 最近伸びてない」: 7日後 40,139→33,354→24,637→15,096→7,516)。
6. 1時間を超える回は維持率11.9〜17.7%(例外: 一本の問いで引っ張った未払い決算27.1%)。集計の仕組みが主役の回(音量・笑い声・1位回数)は14〜18%。編集済み映像で測れぬ量(実時間など)は測れない。
7. 素材は本家の横長本編のみ(ショート・他chの切り抜きは不可)。ゲスト回は解禁済み。他chと場面が重なっても外さず注記のみ。
8. AIが勝手に場面を選ばない: 候補を並べて殿が選ぶ。順位ものはサムネで1位をネタバレしない。非公開アップはサムネまで一式。
9. 推測の数字を書くな。数字は資料の引用か、自分で数えた物(数え方を書く)だけ。
`

const FACTS = { type: 'object', properties: {
  facts: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, number: { type: 'string' }, source: { type: 'string' } }, required: ['claim', 'source'] } },
  insights: { type: 'array', items: { type: 'string' } },
  gaps: { type: 'array', items: { type: 'string' } },
}, required: ['facts', 'insights'] }

const STUDIES = [
  { key: 'own', title: '自chの横長の収益構造', prompt: `自chの横長(尺3分以上)全本について、analytics の per_video_analytics と revenue.by_video / by_video_period、materials の初速表を突き合わせ、「1本あたりの収益」を決めている要因を数字で明らかにせよ。少なくとも: 横長ごとの累計収益・収益/日の推移(公開直後と現在)・尺・維持率・平均視聴分・再生。型(ファン投票/〜は誰だ/全部数えた/総集編/エピソード集 等)ごとに並べ、収益で勝つのはどの要素(再生数か視聴分か尺か)かを示せ。8分以上(ミッドロール)・20〜35分・1時間超で収益/再生の差も出せ。日別ファイルで公開直後の収益の跳ねも確かめよ。` },
  { key: 'rival', title: '他chの横長の勝ち筋', prompt: `${P}/work/trend/long/ の全スナップと latest.json、${P}/analytics/competitor_comparison_2026-03-18.json、materials の流行り検知を読み、ドズル社切り抜き界隈で今「横長」で再生/日を稼いでいる題・型・元動画を洗い出せ。自chがまだやっていない型、自chより他chが強い型、伸び率(accel)が高い元動画を数字で並べよ。他chの題の付け方の傾向(何を題の頭に置くか)も拾え。` },
  { key: 'stock', title: '本家の素材の在庫と旬', prompt: `本家の素材を調べよ。(a) scene_tools.py videos で文字起こしのある回を並べ、直近60日の新しい本編とその題・企画名を一覧に。(b) コメント台帳(raw_full)で直近60日の回ごとのコメント数と、同じ秒に人が集まった場面(hot --days 60 --top 40)を出す。(c) 直近の本家で続いているシリーズ・流行っている言葉(コメントに繰り返し出る言い回し)を数えて上位を出す。(d) 暦: 10/31ハロウィン、11月、年末に向けて使える材料。横長の素材として今いちばん厚い所はどこかを数字で示せ。` },
  { key: 'rules', title: '殿の掟と退けた理由の全目録', prompt: `${MEM}/index_ranking_thumb.md から辿れる memory を全部読み、さらに ${P}/context/kikaku_yokonaga_*.md・kikaku_chouhen_20260829.md・kikaku_stock.md・materials の提案台帳を読んで、横長の企画に関する殿の掟・殿が退けた案とその理由・殿が褒めた/採った案とその理由を、漏れなく一覧にせよ(出典つき)。これから出る案を機械的に照らせる「却下条件のチェックリスト」にまとめよ。` },
  { key: 'pool', title: '過去の案の在庫', prompt: `${P}/context/kikaku100_ideas_20260904.json、kikaku_stock.md、kikaku_yokonaga_*.md、${P}/work/autopilot/*/proposals.json と review.json、今日の yokonaga_*.json を全部読み、これまでに出た横長の案を全件並べ、状態(作った/殿が退けた/検分で落ちた/未回答/温存)と理由を付けよ。作ったものは公開日と7日後の再生を materials の初速表から引け。まだ試していない有望な案を、根拠つきで上位10件に絞れ。` },
]

phase('Understand')
log('5方面の調査を並行で開始')
const studies = await parallel(STUDIES.map(s => () =>
  agent(`${CTX}\n\n【あなたの調査】${s.title}\n${s.prompt}\n数字は必ず出所(ファイルとキー)を書け。推測は insights に「仮説:」と付けて分けよ。`,
    { label: `調査:${s.key}`, phase: 'Understand', schema: FACTS })))
const brief = STUDIES.map((s, i) => {
  const r = studies[i]
  if (!r) return `## ${s.title}\n(調査失敗)`
  return `## ${s.title}\n` + r.facts.map(f => `- ${f.claim}${f.number ? ' [' + f.number + ']' : ''} (${f.source})`).join('\n') +
    '\n所見:\n' + r.insights.map(x => `- ${x}`).join('\n') + (r.gaps && r.gaps.length ? '\n欠け:\n' + r.gaps.map(x => `- ${x}`).join('\n') : '')
}).join('\n\n')
log(`調査 ${studies.filter(Boolean).length}/5 完了`)

const IDEAS = { type: 'object', properties: { ideas: { type: 'array', items: { type: 'object', properties: {
  title: { type: 'string' }, question: { type: 'string' }, format: { type: 'string' },
  why_revenue: { type: 'string' }, evidence: { type: 'array', items: { type: 'string' } },
  novelty: { type: 'string' }, materials_check: { type: 'string' }, length: { type: 'string' },
  thumbnail: { type: 'string' }, risk: { type: 'string' } },
  required: ['title', 'question', 'format', 'why_revenue', 'evidence', 'novelty', 'materials_check', 'length', 'risk'] } } }, required: ['ideas'] }

const LENSES = [
  { key: 'revenue', t: '収益の最大化(1本あたりの収益・視聴分・尺・ミッドロール・公開直後の跳ね)' },
  { key: 'discover', t: '見つけてもらう(検索・おすすめ・関連動画・題とサムネのクリック・他chの勝ち題)' },
  { key: 'fan', t: 'ファンの需要(コメントに書かれている欲求・同じ秒に集まる場面・推しメンバー・おんりーを出すと伸びる傾向)' },
  { key: 'new', t: '新しい型の開拓(自chも他chもまだやっていない見せ方。ただし問いが一言で立つこと)' },
  { key: 'season', t: '旬と暦(ハロウィン・11月・直近の本家の新シリーズ・流行り言葉)' },
  { key: 'series', t: '続けて作れる柱(毎週・毎月出せる型で、収益の谷を埋める。総集編の上り坂の理由も踏まえる)' },
]

phase('Ideate')
const ideaSets = await parallel(LENSES.map(l => () =>
  agent(`${CTX}\n\n【調査結果のまとめ】\n${brief}\n\n【あなたの視点】${l.t}\nこの視点で、次の横長の企画を4件出せ。各案は:
- 問いを一言で(掟1)。過去作の型との違い(掟4)を具体的に。
- 収益の見込みを、調査結果の数字(同じ要素を持つ自chの回の初速・収益・維持率)で根拠づける。
- materials_check: 実際に scene_tools.py grep/hot/comments 等を走らせ、素材が何件・どの回の何秒にあるかを確かめた結果を書く(走らせた命令も書く)。確かめられない案は出すな。
- 尺(20〜35分を基本)、サムネの案(1位をネタバレしない)、弱み。`,
    { label: `発案:${l.key}`, phase: 'Ideate', schema: IDEAS })))
let pool = []
ideaSets.forEach((s, i) => { if (s) s.ideas.forEach(x => pool.push({ ...x, lens: LENSES[i].key })) })
log(`案 ${pool.length}件`)

phase('Merge')
const MERGED = { type: 'object', properties: { ideas: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, title: { type: 'string' }, question: { type: 'string' }, format: { type: 'string' },
  why_revenue: { type: 'string' }, evidence: { type: 'array', items: { type: 'string' } }, novelty: { type: 'string' },
  materials_check: { type: 'string' }, length: { type: 'string' }, thumbnail: { type: 'string' }, risk: { type: 'string' },
  merged_from: { type: 'array', items: { type: 'string' } } },
  required: ['id', 'title', 'question', 'format', 'why_revenue', 'evidence', 'novelty', 'materials_check', 'length', 'risk'] } },
  dropped: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, reason: { type: 'string' } } } } }, required: ['ideas'] }
const merged = await agent(`${CTX}\n\n次の企画案 ${pool.length}件から、同じ中身の案を1つにまとめよ(根拠と素材確認は合わせて残す)。掟に明らかに触れる案(殿が既に退けた形・年末の大賞系を今出す・1時間超前提・測れぬ量)は dropped に理由つきで落とせ。残す案には I01, I02… の id を振れ。中身は書き換えず、まとめるだけにせよ。\n\n${JSON.stringify(pool)}`,
  { label: 'まとめ', phase: 'Merge', schema: MERGED })
const ideas = (merged && merged.ideas) || []
log(`まとめ後 ${ideas.length}件 / 落とした ${merged && merged.dropped ? merged.dropped.length : 0}件`)

const VERDICT = { type: 'object', properties: { refuted: { type: 'boolean' }, reasons: { type: 'array', items: { type: 'string' } }, fix: { type: 'string' } }, required: ['refuted', 'reasons'] }
const VLENS = [
  { key: 'numbers', t: '数字の裏付け: 根拠の数字を資料で1つずつ確かめ、都合のよい切り取り(新しい数字を伏せる・型の最低の回を伏せる・累計で型を読む)を探せ。同じ要素を持つ自chの直近3本の初速が下り坂なら反証。' },
  { key: 'rules', t: '殿の掟: 掟1〜9と、調査「殿の掟と退けた理由の全目録」に照らし、触れていれば反証。特に過去作の型の使い回し(新しい工夫が見せ方の小手先だけなら使い回し)と、殿が退けた形との類似。' },
  { key: 'make', t: '作れるか: 素材確認を自分で再実行し(scene_tools.py 等)、案の数・場面が本当に揃うか、20〜35分を埋められるか、1位の答えに「へえ」があるかを確かめよ。素材が足りぬ・答えが平凡なら反証。' },
]
phase('Verify')
const verified = await pipeline(ideas,
  idea => parallel(VLENS.map(v => () =>
    agent(`${CTX}\n\n【調査結果のまとめ】\n${brief}\n\n【反証する案】${JSON.stringify(idea)}\n\n【あなたの視点】${v.t}\nこの案を崩しにかかれ。確かな根拠で崩せた時だけ refuted=true。崩せないが直せば良くなる所は fix に書け。`,
      { label: `反証:${idea.id}:${v.key}`, phase: 'Verify', schema: VERDICT }))),
  (votes, idea) => {
    const vs = (votes || []).filter(Boolean)
    const ref = vs.filter(v => v.refuted).length
    return { ...idea, votes: vs.map((v, i) => ({ lens: VLENS[i] ? VLENS[i].key : '?', refuted: v.refuted, reasons: v.reasons, fix: v.fix || '' })), survives: vs.length >= 2 && ref < 2 }
  })
const all = verified.filter(Boolean)
const survivors = all.filter(x => x.survives)
log(`反証を通った案 ${survivors.length}/${all.length}`)

phase('Judge')
const SCORES = { type: 'object', properties: { scores: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, revenue: { type: 'number' }, discover: { type: 'number' }, novelty: { type: 'number' }, feasibility: { type: 'number' },
  expected_7day_views: { type: 'string' }, rationale: { type: 'string' } }, required: ['id', 'revenue', 'discover', 'novelty', 'feasibility', 'rationale'] } } }, required: ['scores'] }
const JUDGES = ['収益の見込み(1本あたりの収益・公開直後の跳ね・長く稼ぐか)を最重視する審査員', '視聴者が押したくなるか(題・サムネ・問いの強さ・初速)を最重視する審査員', '殿の掟と作りやすさ(素材の確かさ・使い回しでないこと・殿の手数)を最重視する審査員']
const target = survivors.length ? survivors : all
const judged = await parallel(JUDGES.map((j, k) => () =>
  agent(`${CTX}\n\n【調査結果のまとめ】\n${brief}\n\n【審査する案と反証の記録】\n${JSON.stringify(target.map(x => ({ id: x.id, title: x.title, question: x.question, format: x.format, why_revenue: x.why_revenue, evidence: x.evidence, novelty: x.novelty, materials_check: x.materials_check, length: x.length, risk: x.risk, votes: x.votes })))}\n\nあなたは${j}。各案を revenue / discover / novelty / feasibility の4項目で1〜10点で採点し、7日後の再生の見込みを、似た自chの回の実数を物差しに幅で書け(根拠の回の名を書く)。`,
    { label: `審査${k + 1}`, phase: 'Judge', schema: SCORES })))
const tally = {}
judged.filter(Boolean).forEach(j => j.scores.forEach(s => {
  const t = tally[s.id] || (tally[s.id] = { sum: 0, n: 0, notes: [] })
  t.sum += 2 * s.revenue + s.discover + s.novelty + s.feasibility; t.n++
  t.notes.push(`${s.rationale} / 7日後見込み:${s.expected_7day_views || '-'}`)
}))
const ranked = target.map(x => ({ ...x, score: tally[x.id] ? +(tally[x.id].sum / tally[x.id].n).toFixed(2) : 0, judge_notes: tally[x.id] ? tally[x.id].notes : [] }))
  .sort((a, b) => b.score - a.score)
log('上位: ' + ranked.slice(0, 5).map(x => `${x.id} ${x.title}(${x.score})`).join(' / '))

phase('Decide')
const FINAL = { type: 'object', properties: {
  decision: { type: 'object', properties: { id: { type: 'string' }, title: { type: 'string' }, question: { type: 'string' }, length: { type: 'string' }, thumbnail: { type: 'string' }, structure: { type: 'array', items: { type: 'string' } }, new_twist: { type: 'string' } }, required: ['id', 'title', 'question', 'length', 'structure', 'new_twist'] },
  why: { type: 'string' }, expected: { type: 'string' },
  alternates: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, title: { type: 'string' }, when: { type: 'string' } } } },
  pillar: { type: 'string' },
  production_plan: { type: 'array', items: { type: 'string' } },
  stop_if: { type: 'string' }, risks: { type: 'array', items: { type: 'string' } },
  ask_lord: { type: 'string' }, vs_today_decision: { type: 'string' } },
  required: ['decision', 'why', 'expected', 'alternates', 'production_plan', 'stop_if', 'ask_lord', 'vs_today_decision'] }
const final = await agent(`${CTX}\n\n【調査結果のまとめ】\n${brief}\n\n【採点順の案(反証の記録と審査の所見つき)】\n${JSON.stringify(ranked.slice(0, 8))}\n\n【反証で落ちた案】${JSON.stringify(all.filter(x => !x.survives).map(x => ({ id: x.id, title: x.title, why: x.votes.filter(v => v.refuted).map(v => v.reasons.join(' / ')) })))}\n\nあなたは決裁役。収益重視で、次に作る横長を1本に決めよ(「両方」「様子見」は禁止)。採点1位を機械的に選ぶ必要はないが、変えるなら理由を数字で書け。
- decision.structure: 冒頭〜締めの構成を章立てで(何分に何を置くか)。new_twist: 過去作と違う新しい工夫。
- expected: 7日後の再生と収益の見込みを、似た自chの回の実数を物差しに幅で。
- alternates: 次点2本と、それに切り替える時機。pillar: 毎週出せる柱にするならどの型か(収益の谷を埋める案)。
- production_plan: 素材集め→殿の選定(編集アプリで全カットoffで並べる)→組み→サムネ→非公開アップまでの段取り。
- stop_if: 作る前・公開後に見切る条件(何日目の何の数字がいくら)。
- vs_today_decision: 夜の決定会議の結論(work/autopilot/_yokonaga/decision.json)と比べてどうか。
- ask_lord: 殿に決めてほしいことを1つだけ。`, { label: '決裁', phase: 'Decide', schema: FINAL })

phase('Critic')
const CRIT = { type: 'object', properties: { missing: { type: 'array', items: { type: 'string' } }, unverified_claims: { type: 'array', items: { type: 'string' } }, verdict: { type: 'string' } }, required: ['missing', 'verdict'] }
const critic = await agent(`${CTX}\n\n次の企画検討の結論を点検せよ。抜けている調査(読んでいない資料・走らせていない検索)、裏の取れていない数字、殿の掟の見落としを挙げ、結論がそれで揺らぐかを verdict に一言で。\n\n【結論】${JSON.stringify(final)}\n\n【調査結果のまとめ】\n${brief}`,
  { label: '点検', phase: 'Critic', schema: CRIT })

return { brief, pool_count: pool.length, dropped: merged ? merged.dropped : [], all: all.map(x => ({ id: x.id, title: x.title, question: x.question, format: x.format, novelty: x.novelty, length: x.length, thumbnail: x.thumbnail, materials_check: x.materials_check, evidence: x.evidence, risk: x.risk, survives: x.survives, votes: x.votes })), ranked: ranked.map(x => ({ id: x.id, title: x.title, score: x.score, judge_notes: x.judge_notes })), final, critic }
