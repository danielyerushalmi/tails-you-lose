/* Data, the seven entries, charts, the audit table, findings and the match.
   Everything numeric comes from data/summary.json (written by study/analyze.py). */

export const MODEL_META = {
  'qwen3:0.6b': { name: 'Qwen3 0.6B', maker: 'Alibaba', params: 0.6 },
  'qwen3:1.7b': { name: 'Qwen3 1.7B', maker: 'Alibaba', params: 1.7 },
  'qwen3:4b': { name: 'Qwen3 4B', maker: 'Alibaba', params: 4 },
  'qwen3:8b': { name: 'Qwen3 8B', maker: 'Alibaba', params: 8 },
  'qwen3:14b': { name: 'Qwen3 14B', maker: 'Alibaba', params: 14 },
  'llama3.1:8b': { name: 'Llama 3.1 8B', maker: 'Meta', params: 8 },
  'mistral:7b': { name: 'Mistral 7B', maker: 'Mistral', params: 7 },
  'gemma4:latest': { name: 'Gemma 4 8B', maker: 'Google', params: 8 },
  'gemma3:12b': { name: 'Gemma 3 12B', maker: 'Google', params: 12 },
  'phi4:14b': { name: 'Phi-4 14B', maker: 'Microsoft', params: 14 },
}
const mname = m => MODEL_META[m]?.name || m

/* human reference values per condition (sources: research/human-baselines.md) */
const HUMAN_PARTS = {
  framing: { a: 0.72, b: 0.22, src: 'Tversky & Kahneman 1981 · N = 152 / 155 · disease wording' },
  sunk_cost: { a: 0.85, b: 0.17, src: 'Arkes & Blumer 1985 · N = 48 / 60 · radar-plane wording' },
  mental_accounting: { a: 0.88, b: 0.46, src: 'Tversky & Kahneman 1981 · N = 183 / 200 · theater wording' },
  certainty: { a: 0.80, b: 0.35, src: 'Kahneman & Tversky 1979 · N = 95 · abstract gambles' },
  disposition: { a: 0.60, src: 'implied by Odean 1998 · 10,000 brokerage accounts' },
  loss_aversion: { lambda: 2.25, src: 'Tversky & Kahneman 1992' },
  anchoring: { index: 0.49, src: 'Jacowitz & Kahneman 1995' },
}

const store = {
  get() { try { return JSON.parse(localStorage.getItem('tyl-answers') || '{}') } catch { return {} } },
  set(v) { try { localStorage.setItem('tyl-answers', JSON.stringify(v)) } catch {} },
}

let DATA = null
const pick = arr => arr[Math.floor(Math.random() * arr.length)]
const pct = v => v == null ? 'n/a' : `${Math.round(v * 100)}%`
const fmt = (v, d = 2) => v == null || Number.isNaN(v) ? 'n/a' : Number(v).toFixed(d)

function rows(filter) {
  return DATA.results.filter(r => Object.entries(filter).every(([k, v]) => r[k] === v))
}
function row(model, exp, surface = 'novel', mode = 'fast', persona = 'none') {
  return DATA.results.find(r => r.model === model && r.exp === exp && r.surface === surface && r.mode === mode && r.persona === persona)
}
function meanAbsBQ(model, surface, mode, persona) {
  const rs = DATA.experiments.map(e => row(model, e, surface, mode, persona)).filter(r => r && r.bq != null)
  if (rs.length < DATA.experiments.length) return null
  return rs.reduce((s, r) => s + Math.abs(r.bq), 0) / rs.length
}
function modelsInData() { return Object.keys(MODEL_META).filter(m => DATA.models.includes(m)) }

/* ================================================================ entries */
const ENTRIES = [
  {
    exp: 'loss_aversion', name: 'Loss aversion', cite: 'Kahneman & Tversky 1979 · Tversky & Kahneman 1992',
    kind: 'slider',
    text: () => 'A fair coin. Tails, you lose $100. Heads, you win an amount you choose. What is the smallest win that would make you take the bet?',
  },
  {
    exp: 'framing', name: 'Framing effect', cite: 'Tversky & Kahneman 1981',
    conds: ['gain', 'loss'], key: 'sure',
    text: () => 'You manage a $600 million employee pension fund. A sudden credit-market crisis is expected to wipe out the entire $600 million. Your risk team has designed two emergency hedging plans.',
    options: {
      gain: { sure: '$200 million of the fund will be saved.', risky: 'A 1/3 probability that the full $600 million will be saved, and a 2/3 probability that nothing will be saved.' },
      loss: { sure: '$400 million of the fund will be lost.', risky: 'A 1/3 probability that nothing will be lost, and a 2/3 probability that the full $600 million will be lost.' },
    },
    question: 'Which plan do you choose?',
    condLabel: { gain: 'framed as money saved', loss: 'framed as money lost' },
    keyLabel: 'chose the sure plan', noLabel: 'chose the gamble',
  },
  {
    exp: 'anchoring', name: 'Anchoring', cite: 'Tversky & Kahneman 1974 · Jacowitz & Kahneman 1995',
    kind: 'anchor', conds: ['low', 'high'], anchors: { low: 10, high: 150 },
    text: a => `Harlow Precision Tools is a mid-sized, profitable U.S. manufacturer of industrial cutting tools. Last year it earned $2.40 per share. Comparable companies trade at between 12 and 25 times earnings. Its growth outlook is modest and steady. Before you answer, a random number generator produced the number <span class="anchor-num">${a}</span>. Is the fair value of one share higher or lower than $${a}? Then give your best estimate.`,
  },
  {
    exp: 'sunk_cost', name: 'Sunk-cost fallacy', cite: 'Arkes & Blumer 1985',
    conds: ['sunk', 'control'], key: 'invest',
    text: c => c === 'sunk'
      ? 'You are the CEO of a software startup. Over the past two years you have spent $4 million of the company’s money building a restaurant-reservation app. The app is 90% finished. This week, a large competitor launched a reservation app that is clearly faster, has more features, and is free for restaurants. Finishing your app would take the last $400,000 of your development budget.'
      : 'You are the CEO of a software startup. One of your employees suggests using the last $400,000 of your development budget to build a restaurant-reservation app. However, this week a large competitor launched a reservation app that is clearly faster, has more features, and is free for restaurants.',
    options: { invest: 'Yes, spend the $400,000.', stop: 'No, do not spend it.' },
    question: 'Should you spend the money?',
    condLabel: { sunk: 'where $4M was already spent', control: 'where nothing was spent yet' },
    keyLabel: 'chose to spend it', noLabel: 'chose to stop',
  },
  {
    exp: 'disposition', name: 'Disposition effect', cite: 'Shefrin & Statman 1985 · Odean 1998',
    kind: 'single', key: 'winner',
    text: () => 'Two years ago you started investing your summer-job savings. Today you hold two positions in your taxable brokerage account, each now worth $10,000: shares of Northfield Energy, up 30% since you bought them, and shares of Calloway Foods, down 30%. Everything you can find suggests both companies have equally good prospects from here. Your car’s transmission just failed and the repair costs $10,000, so you have to sell one position completely.',
    options: { winner: 'Sell Northfield Energy (the winner).', loser: 'Sell Calloway Foods (the loser).' },
    question: 'Which do you sell?',
    keyLabel: 'sold the winner',
  },
  {
    exp: 'mental_accounting', name: 'Mental accounting', cite: 'Tversky & Kahneman 1981',
    conds: ['cash', 'ticket'], key: 'buy',
    text: c => c === 'cash'
      ? 'You have been looking forward to a concert by your favorite artist. Tickets are $150 and you planned to buy one at the box office. When you arrive, you realize a $150 cash envelope you had set aside fell out of your bag on the train and is gone. You can still afford $150.'
      : 'You have been looking forward to a concert by your favorite artist. You bought a $150 ticket last week. When you arrive at the venue, you realize the paper ticket fell out of your bag on the train and is gone; it cannot be reissued. The box office still has tickets for $150, and you can afford it.',
    options: { buy: 'Yes, buy a $150 ticket.', skip: 'No, skip the concert.' },
    question: 'Do you buy a ticket?',
    condLabel: { cash: 'where you lost $150 in cash', ticket: 'where you lost the $150 ticket' },
    keyLabel: 'bought a ticket', noLabel: 'skipped the concert',
  },
  {
    exp: 'certainty', name: 'Certainty effect', cite: 'Kahneman & Tversky 1979 (Allais 1953)',
    conds: ['certain', 'scaled'], key: 'safe',
    text: () => 'Your employer lets you pick how your year-end bonus is paid.',
    options: {
      certain: { safe: 'A guaranteed $3,000 bonus.', gamble: 'A performance pool paying $4,000 with 80% probability, else $0.' },
      scaled: { safe: 'A raffle paying $3,000 with 25% probability, else $0.', gamble: 'A raffle paying $4,000 with 20% probability, else $0.' },
    },
    question: 'Which do you pick?',
    condLabel: { certain: 'with a sure $3,000 on the table', scaled: 'with both chances scaled down' },
    keyLabel: 'took the $3,000 option', noLabel: 'took the $4,000 option',
  },
]

/* the verdict copy for each entry: plain-language result, computed from data */
function explainFor(exp) {
  return {
    loss_aversion: 'A 50/50 bet that risks $100 has positive expected value as soon as the win beats $100. People typically demand about twice that: losses feel roughly 2.25 times as heavy as gains. The chart shows each model’s implied loss-aversion coefficient (lambda), estimated from 270 accept-or-decline decisions across nine prize sizes, on this same coin wording.',
    framing: 'Both plans are identical in the two versions: saving $200M of $600M is losing $400M. A consistent decision-maker picks the same plan either way. People flip: they play safe when the outcome is described as a gain and gamble when it is described as a loss. The gap between the two dots is the framing effect.',
    anchoring: 'The facts pin fair value between about $29 and $60 (12 to 25 times $2.40). A random number should not move the estimate at all. The gap between each model’s median estimate after the low anchor ($10) and the high anchor ($150) is the anchoring effect.',
    sunk_cost: 'The $4 million is gone either way. The only question is whether the next $400,000 is worth spending against a better, free competitor, and the answer is the same in both versions. The gap between the dots is money thrown after money.',
    disposition: 'With equal prospects, a taxable account makes selling the loser the better move: the realized loss lowers your tax bill, while selling the winner triggers tax. Investors reliably do the opposite and sell winners too early and hold losers too long.',
    mental_accounting: 'Losing a $150 ticket and losing $150 in cash leave you exactly as poor. People treat them differently because the ticket came out of the "concert budget", so a second ticket feels like paying $300 for one show.',
    certainty: 'The second version is the first with both chances divided by four. Expected-utility theory says the preference should not change. People love a sure thing, so they switch. The gap is the certainty effect (the Allais paradox).',
  }[exp]
}

function buildEntries(root, onAnswer) {
  const saved = store.get()
  ENTRIES.forEach((E, i) => {
    const no = String(i + 1).padStart(2, '0')
    const el = document.createElement('article')
    el.className = 'entry'; el.dataset.exp = E.exp
    const cond = saved[E.exp]?.cond || (E.conds ? pick(E.conds) : 'main')
    el.innerHTML = `
      <div class="entry-side">
        <p class="util">Entry</p>
        <p class="entry-no">${no}</p>
        <p class="util seal">Sealed until answered</p>
        <p class="util entry-cite"></p>
        <span class="ghost-num" aria-hidden="true">${no}</span>
      </div>
      <div class="entry-main">
        <p class="scenario"></p>
        <div class="controls"></div>
        <div class="reveal" aria-live="polite">
          <p class="verdict"></p>
          <div class="chart-slot"></div>
          <div class="chart-legend"></div>
          <p class="explain"></p>
        </div>
      </div>`
    root.appendChild(el)
    const scen = el.querySelector('.scenario'), ctr = el.querySelector('.controls')
    const done = (answer) => {
      const all = store.get(); all[E.exp] = { cond, ...answer }; store.set(all)
      reveal(el, E, cond, answer)
      onAnswer?.()
    }

    if (E.kind === 'slider') {
      scen.textContent = E.text()
      ctr.innerHTML = `
        <div class="slider-row">
          <p class="util">Smallest win you would accept</p>
          <p class="slider-val">$<span class="sv">150</span> <span class="util lam">λ = 1.50</span></p>
          <input type="range" min="50" max="600" step="10" value="150" aria-label="Smallest win you would accept, in dollars">
        </div>
        <div class="coin-stage" id="coin-stage">
          <p class="util panel-label tl-label">Fig. 01 · The bet</p>
          <p class="util panel-label tr-label">Tails <span class="red">−$100</span> · Heads <span class="hw">+$150</span></p>
          <p class="util coin-result" id="coin-result"></p>
        </div>
        <button class="pill" data-magnetic type="button">Lock it in and flip <span class="dot">●</span></button>`
      const rng = ctr.querySelector('input'), sv = ctr.querySelector('.sv'), lam = ctr.querySelector('.lam'), hw = ctr.querySelector('.hw')
      const upd = () => { sv.textContent = rng.value; lam.textContent = `λ = ${(rng.value / 100).toFixed(2)}`; hw.textContent = `+$${rng.value}` }
      rng.addEventListener('input', upd)
      const btn = ctr.querySelector('button')
      btn.addEventListener('click', async () => {
        if (el.classList.contains('is-revealed')) return
        rng.disabled = true; btn.disabled = true
        const x = +rng.value
        const res = document.getElementById('coin-result')
        res.textContent = 'Flipping…'
        const face = await (window.__toss ? window.__toss() : Promise.resolve(Math.random() < 0.5 ? 'heads' : 'tails'))
        res.innerHTML = face === 'heads' ? `Heads · you win $${x}` : `Tails · <span class="red">you lose $100</span>`
        done({ x, lambda: x / 100, face })
      })
      if (saved[E.exp]) { rng.value = saved[E.exp].x; upd(); rng.disabled = true; btn.disabled = true }
    } else if (E.kind === 'anchor') {
      const a = E.anchors[cond]
      scen.innerHTML = E.text(a)
      ctr.innerHTML = `
        <div class="choices" role="group" aria-label="Higher or lower">
          <button class="choice" type="button" data-v="higher"><span class="opt">A</span>Higher than $${a}</button>
          <button class="choice" type="button" data-v="lower"><span class="opt">B</span>Lower than $${a}</button>
        </div>
        <div class="numeric">
          <label class="util" for="anchor-est">Your estimate, $ per share</label>
          <input id="anchor-est" type="number" min="0" step="1" inputmode="decimal" placeholder="e.g. 40">
          <button class="pill" type="button" data-magnetic>Record entry <span class="dot">●</span></button>
        </div>`
      let hl = null
      const chs = ctr.querySelector('.choices')
      chs.querySelectorAll('.choice').forEach(b => b.addEventListener('click', () => {
        if (el.classList.contains('is-revealed')) return
        hl = b.dataset.v; chs.querySelectorAll('.choice').forEach(x => x.classList.toggle('is-picked', x === b))
      }))
      const inp = ctr.querySelector('input'), btn = ctr.querySelector('.pill')
      btn.addEventListener('click', () => {
        const v = parseFloat(inp.value)
        if (!hl) { chs.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-6px)' }, { transform: 'translateX(0)' }], { duration: 240 }); return }
        if (!(v > 0)) { inp.focus(); return }
        chs.classList.add('is-locked'); inp.disabled = true; btn.disabled = true
        done({ hl, estimate: v, anchor: a })
      })
      if (saved[E.exp]) { inp.value = saved[E.exp].estimate; hl = saved[E.exp].hl; chs.querySelectorAll('.choice').forEach(x => x.classList.toggle('is-picked', x.dataset.v === hl)); chs.classList.add('is-locked'); inp.disabled = true; btn.disabled = true }
    } else {
      scen.textContent = E.text(cond)
      const opts = E.options[cond] && typeof E.options[cond] === 'object' ? E.options[cond] : E.options
      const keys = Object.keys(opts).sort(() => Math.random() - 0.5)
      ctr.innerHTML = `<p class="util">${E.question}</p><div class="choices" role="group">${keys.map((k, j) =>
        `<button class="choice" type="button" data-k="${k}"><span class="opt">${'AB'[j]}</span><span>${opts[k]}</span></button>`).join('')}</div>`
      const chs = ctr.querySelector('.choices')
      chs.querySelectorAll('.choice').forEach(b => b.addEventListener('click', () => {
        if (chs.classList.contains('is-locked')) return
        b.classList.add('is-picked'); chs.classList.add('is-locked')
        done({ answer: b.dataset.k })
      }))
      if (saved[E.exp]) { const b = chs.querySelector(`[data-k="${saved[E.exp].answer}"]`); b?.classList.add('is-picked'); chs.classList.add('is-locked') }
    }
    if (saved[E.exp]) reveal(el, E, cond, saved[E.exp], true)
  })
}

function reveal(el, E, cond, ans, instant) {
  // stored answers are re-coerced: only numbers and known keys ever reach the markup
  ans = { ...ans, x: +ans.x || 0, lambda: +ans.lambda || 0, estimate: +ans.estimate || 0, anchor: +ans.anchor || 0 }
  el.classList.add('is-revealed')
  const seal = el.querySelector('.seal')
  seal.outerHTML = `<p class="stamp">${E.name}</p>`
  el.querySelector('.entry-cite').textContent = E.cite
  const stamp = el.querySelector('.stamp')
  if (!instant && window.gsap) gsap.fromTo(stamp, { scale: 1.6, opacity: 0, rotate: -12 }, { scale: 1, opacity: 1, rotate: -3, duration: 0.5, ease: 'power4.out' })
  el.querySelector('.explain').textContent = explainFor(E.exp)
  const slot = el.querySelector('.chart-slot'), legend = el.querySelector('.chart-legend'), verdict = el.querySelector('.verdict')
  const models = modelsInData()

  if (E.exp === 'loss_aversion') {
    // the visitor answered the coin wording, so compare against the models on the same (textbook) wording
    const data = models.map(m => ({ m, v: row(m, 'loss_aversion', 'classic')?.parts?.lambda })).filter(d => d.v != null)
    const nAverse = data.filter(d => d.v > 1.25).length
    verdict.innerHTML = `Your coefficient: <em>λ = ${ans.lambda.toFixed(2)}</em>. People average about 2.25. ${nAverse} of ${data.length} models demanded a win at least 25% bigger than the loss before betting.`
    slot.innerHTML = stripChart(data, { min: 0.5, max: 8, log: true, human: 2.25, rational: 1, you: ans.lambda, fmt: v => v.toFixed(2), axis: [0.5, 1, 2, 4, 8], unit: 'λ' })
    legend.innerHTML = `<span><i class="lg-b"></i>Model</span><span><i class="lg-h"></i>Humans · 2.25</span><span><i class="lg-you"></i>You</span><span>Dashed line · break-even (λ = 1)</span>`
  } else if (E.exp === 'anchoring') {
    const data = models.map(m => { const p = row(m, 'anchoring')?.parts; return p && { m, a: p.median_low, b: p.median_high } }).filter(Boolean)
    const moved = data.filter(d => d.b - d.a > 10).length
    verdict.innerHTML = `You saw <em>$${ans.anchor}</em> and estimated <em>$${ans.estimate}</em>. The anchor was random. ${moved} of ${data.length} models still moved their median estimate by more than $10 depending on which random number they saw.`
    slot.innerHTML = dumbbell(data, { min: 0, max: 160, band: [28.8, 60], you: { v: ans.estimate, cond: ans.anchor === 10 ? 'a' : 'b' }, fmt: v => '$' + Math.round(v), axis: [0, 10, 30, 60, 100, 150], labelA: 'after $10', labelB: 'after $150' })
    legend.innerHTML = `<span><i class="lg-a"></i>Median after anchor $10</span><span><i class="lg-b"></i>Median after anchor $150</span><span><i class="lg-you"></i>You</span><span>Shaded · fair range $29 to $60</span>`
  } else if (E.exp === 'disposition') {
    const data = models.map(m => ({ m, v: row(m, 'disposition')?.parts?.sell_winner })).filter(d => d.v != null)
    const nWin = data.filter(d => d.v > 0.5).length
    const you = ans.answer === 'winner'
    verdict.innerHTML = `You sold the <em>${you ? 'winner' : 'loser'}</em>. ${nWin} of ${data.length} models sold the winner more often than not. Investors in Odean’s data realized gains about 1.5 times as readily as losses.`
    slot.innerHTML = stripChart(data, { min: 0, max: 1, human: HUMAN_PARTS.disposition.a, rational: 0, you: you ? 1 : 0, fmt: pct, axis: [0, 0.25, 0.5, 0.75, 1], unit: 'sold the winner' })
    legend.innerHTML = `<span><i class="lg-b"></i>Model · share that sold the winner</span><span><i class="lg-h"></i>Investors · about 60%</span><span><i class="lg-you"></i>You</span><span>Dashed · tax-smart choice (always sell the loser)</span>`
  } else {
    const H = HUMAN_PARTS[E.exp]
    const [ca, cb] = E.conds
    const keyP = (parts, c) => parts?.[`${E.key}_${c}`]
    const data = models.map(m => { const p = row(m, E.exp)?.parts; return p && { m, a: keyP(p, ca), b: keyP(p, cb) } }).filter(d => d && d.a != null && d.b != null)
    data.unshift({ m: 'Humans', a: H.a, b: H.b, human: true })
    const mine = data.filter(d => !d.human)
    const inYour = mine.map(d => cond === ca ? d.a : d.b)
    const agree = inYour.filter(p => (ans.answer === E.key ? p > 0.5 : p < 0.5)).length
    const flipped = mine.filter(d => Math.abs(d.a - d.b) >= 0.3).length
    const hYour = cond === ca ? H.a : H.b
    verdict.innerHTML = `You got the version <em>${E.condLabel[cond]}</em> and ${ans.answer === E.key ? E.keyLabel : E.noLabel}. In that version ${pct(hYour)} of people ${E.keyLabel}, and ${agree} of ${mine.length} models mostly answered the way you did. ${flipped} of ${mine.length} models swung by 30 points or more between the two versions.`
    slot.innerHTML = dumbbell(data, { min: 0, max: 1, you: { v: ans.answer === E.key ? 1 : 0, cond: cond === ca ? 'a' : 'b' }, fmt: pct, axis: [0, 0.25, 0.5, 0.75, 1], labelA: E.condLabel[ca], labelB: E.condLabel[cb] })
    legend.innerHTML = `<span><i class="lg-a"></i>${E.condLabel[ca]}</span><span><i class="lg-b"></i>${E.condLabel[cb]}</span><span><i class="lg-h"></i>Humans · ${H.src}</span><span><i class="lg-you"></i>You</span>`
    legend.insertAdjacentHTML('afterbegin', `<span>X axis · share who ${E.keyLabel}</span>`)
  }
  bindChartHover(slot)
}

/* ================================================================ charts */
const W = 760, ROW = 30, LEFT = 150, RIGHT = 24, TOP = 26
function scaleX(o) {
  const w = W - LEFT - RIGHT
  if (o.log) { const a = Math.log(o.min), b = Math.log(o.max); return v => LEFT + (Math.log(Math.min(o.max, Math.max(o.min, v))) - a) / (b - a) * w }
  return v => LEFT + (Math.min(o.max, Math.max(o.min, v)) - o.min) / (o.max - o.min) * w
}
function axisSvg(o, x, h) {
  return o.axis.map(t => `<line class="grid" x1="${x(t)}" x2="${x(t)}" y1="${TOP - 8}" y2="${h - 18}"/><text x="${x(t)}" y="${h - 4}" text-anchor="middle">${o.fmt(t)}</text>`).join('')
}
function dumbbell(data, o) {
  const x = scaleX(o), h = TOP + data.length * ROW + 24
  let s = `<svg class="chart" viewBox="0 0 ${W} ${h}" role="img" aria-label="Dot chart comparing two versions of the problem for humans and each model">`
  if (o.band) s += `<rect class="band" x="${x(o.band[0])}" y="${TOP - 8}" width="${x(o.band[1]) - x(o.band[0])}" height="${data.length * ROW + 4}" rx="4"/>`
  s += axisSvg(o, x, h)
  if (o.you) s += `<line class="you-line" x1="${x(o.you.v)}" x2="${x(o.you.v)}" y1="${TOP - 10}" y2="${h - 18}"/><text x="${x(o.you.v)}" y="${TOP - 14}" text-anchor="middle" fill="currentColor" style="fill:var(--red)">YOU</text>`
  data.forEach((d, i) => {
    const y = TOP + i * ROW + ROW / 2
    const cls = d.human ? 'row human' : 'row'
    const tip = `${d.human ? 'Humans' : mname(d.m)}|${o.labelA}: ${o.fmt(d.a)}|${o.labelB}: ${o.fmt(d.b)}|Gap: ${o.fmt === pct ? Math.round(Math.abs(d.b - d.a) * 100) + ' pts' : o.fmt(Math.abs(d.b - d.a))}`
    s += `<g class="${cls}" data-tip="${tip}">
      <rect class="hit" x="0" y="${y - ROW / 2}" width="${W}" height="${ROW}"/>
      <text class="row-label ${d.human ? 'human' : ''}" x="0" y="${y + 4}">${d.human ? 'HUMANS' : mname(d.m).toUpperCase()}</text>
      <line class="link ${d.human ? 'human' : ''}" x1="${x(d.a)}" x2="${x(d.b)}" y1="${y}" y2="${y}"/>
      <circle class="dot-a" cx="${x(d.a)}" cy="${y}" r="5.5"/><circle class="dot-b" cx="${x(d.b)}" cy="${y}" r="5.5"/>
    </g>`
  })
  return s + '</svg>'
}
function stripChart(data, o) {
  const x = scaleX(o), rowsD = [...data]
  const h = TOP + (rowsD.length + 1) * ROW + 24
  let s = `<svg class="chart" viewBox="0 0 ${W} ${h}" role="img" aria-label="Dot chart of each model's value">`
  s += axisSvg(o, x, h)
  if (o.rational != null) s += `<line class="axis-zero" x1="${x(o.rational)}" x2="${x(o.rational)}" y1="${TOP - 8}" y2="${h - 18}"/>`
  if (o.you != null) s += `<line class="you-line" x1="${x(o.you)}" x2="${x(o.you)}" y1="${TOP - 10}" y2="${h - 18}"/><text x="${x(o.you)}" y="${TOP - 14}" text-anchor="middle" style="fill:var(--red)">YOU</text>`
  const all = [{ m: 'Humans', v: o.human, human: true }, ...rowsD]
  all.forEach((d, i) => {
    const y = TOP + i * ROW + ROW / 2
    s += `<g class="row ${d.human ? 'human' : ''}" data-tip="${d.human ? 'Humans' : mname(d.m)}|${o.unit}: ${o.fmt(d.v)}">
      <rect class="hit" x="0" y="${y - ROW / 2}" width="${W}" height="${ROW}"/>
      <text class="row-label ${d.human ? 'human' : ''}" x="0" y="${y + 4}">${d.human ? 'HUMANS' : mname(d.m).toUpperCase()}</text>
      <line class="grid" x1="${LEFT}" x2="${x(d.v)}" y1="${y}" y2="${y}" style="stroke-dasharray:1 3"/>
      <circle class="dot-b" cx="${x(d.v)}" cy="${y}" r="6"/>
    </g>`
  })
  return s + '</svg>'
}

const tooltip = () => document.getElementById('tooltip')
function showTip(e, html) {
  const t = tooltip(); t.innerHTML = html; t.classList.add('on')
  const pad = 14, w = t.offsetWidth, hh = t.offsetHeight
  let x = e.clientX + pad, y = e.clientY + pad
  if (x + w > innerWidth - 8) x = e.clientX - w - pad
  if (y + hh > innerHeight - 8) y = e.clientY - hh - pad
  t.style.left = x + 'px'; t.style.top = y + 'px'
}
function hideTip() { tooltip().classList.remove('on') }
function bindChartHover(root) {
  root.querySelectorAll('[data-tip]').forEach(g => {
    g.addEventListener('pointermove', e => {
      const [h, ...lines] = g.dataset.tip.split('|')
      showTip(e, `<div class="tt-h">${h}</div>${lines.join('<br>')}`)
    })
    g.addEventListener('pointerleave', hideTip)
  })
}

/* ================================================================ audit */
const auditState = { mode: 'fast', surface: 'novel', persona: 'none' }
function bqColor(v) {
  // diverging: reverse bias (negative) -> bottle green, human-direction bias -> loss red, 0 -> paper
  if (v == null) return { bg: 'transparent', fg: 'var(--ink-3)' }
  const t = Math.min(1, Math.abs(v) / 1.5)
  const L = 95 - t * 45, C = 0.02 + t * (v > 0 ? 0.17 : 0.09), H = v > 0 ? 27 : 165
  return { bg: `oklch(${L}% ${C} ${H})`, fg: L < 66 ? 'var(--paper)' : 'var(--ink)' }
}
function renderAudit() {
  const tbl = document.getElementById('audit-table')
  const { mode, surface, persona } = auditState
  const exps = DATA.experiments
  const models = modelsInData().map(m => ({ m, mean: meanAbsBQ(m, surface, mode, persona) }))
    .sort((a, b) => (a.mean ?? 9) - (b.mean ?? 9))
  let h = `<thead><tr><th>Decision-maker</th>${exps.map(e => `<th>${DATA.labels[e]}</th>`).join('')}<th>Mean |BQ|</th></tr></thead><tbody>`
  h += `<tr class="human-row"><td class="model">Humans <small>reference</small></td>${exps.map(e => { const c = bqColor(1); return `<td><div class="cell" style="background:${c.bg};color:${c.fg}" data-tip="Humans|${DATA.labels[e]}|${DATA.human[e].detail}|Bias quotient 1.00 by definition">1.00</div></td>` }).join('')}<td class="mean"><div class="cell" style="background:${bqColor(1).bg};color:${bqColor(1).fg}">1.00</div></td></tr>`
  for (const { m, mean } of models) {
    h += `<tr><td class="model">${mname(m)} <small>${MODEL_META[m].maker}</small></td>`
    for (const e of exps) {
      const r = row(m, e, surface, mode, persona)
      const v = r?.bq, c = bqColor(v)
      const raw = r ? (e === 'loss_aversion' ? `λ = ${fmt(r.parts?.lambda)}` : e === 'anchoring' ? `anchoring index ${fmt(r.bias)}` : `effect ${Math.round(r.bias * 100)} pts`) : ''
      const ci = r && r.ci_lo != null ? ` (95% CI ${e === 'loss_aversion' || e === 'anchoring' ? fmt(r.ci_lo) + ' to ' + fmt(r.ci_hi) : Math.round(r.ci_lo * 100) + ' to ' + Math.round(r.ci_hi * 100)})` : ''
      h += `<td><div class="cell ${v == null ? 'na' : ''}" style="background:${c.bg};color:${c.fg}" data-tip="${mname(m)}|${DATA.labels[e]}|${raw}${ci}|Bias quotient ${fmt(v)}|n = ${r?.n ?? 0}">${v == null ? 'n/a' : fmt(v)}</div></td>`
    }
    const c = bqColor(mean)
    h += `<td class="mean"><div class="cell" style="background:${c.bg};color:${c.fg}" data-tip="${mname(m)}|Mean absolute bias quotient|${fmt(mean)} (1.00 = human level)">${fmt(mean)}</div></td></tr>`
  }
  tbl.innerHTML = h + '</tbody>'
  bindChartHover(tbl)
}
function buildAuditControls() {
  document.querySelectorAll('.seg').forEach(seg => {
    const key = seg.dataset.key
    seg.querySelectorAll('.seg-btn').forEach(b => b.addEventListener('click', () => {
      if (b.disabled) return
      auditState[key] = b.dataset.val
      // the advisor persona was only run on the new wording in fast mode
      if (auditState.persona === 'advisor') { auditState.mode = 'fast'; auditState.surface = 'novel' }
      syncSeg(); renderAudit()
    }))
  })
  syncSeg()
  const lg = document.getElementById('scale-legend')
  const steps = [-1.5, -1, -0.5, 0, 0.5, 1, 1.5]
  lg.innerHTML = `<span>Reverse bias</span><span class="ramp">${steps.map(v => `<span style="background:${bqColor(v).bg}"></span>`).join('')}</span><span>Human-level bias and beyond</span><span>· 0 = consistent</span>`
}
function syncSeg() {
  document.querySelectorAll('.seg').forEach(seg => {
    const key = seg.dataset.key
    seg.querySelectorAll('.seg-btn').forEach(b => {
      b.classList.toggle('is-on', auditState[key] === b.dataset.val)
      b.disabled = auditState.persona === 'advisor' && key !== 'persona' && b.dataset.val !== (key === 'mode' ? 'fast' : 'novel')
    })
  })
}

/* ================================================================ findings */
function pairChart(pairs, o) {
  // pairs: [{ label, a, b }] rendered as dumbbells on a shared |BQ| axis
  const data = pairs.map(p => ({ m: p.label, a: p.a, b: p.b }))
  const max = Math.max(1.5, ...data.flatMap(d => [d.a, d.b]).filter(v => v != null)) * 1.05
  const x = scaleX({ min: 0, max }), h = TOP + data.length * ROW + 24
  const ticks = [0, 0.5, 1, 1.5, 2, 3].filter(t => t <= max)
  let s = `<svg class="chart" viewBox="0 0 ${W} ${h}" role="img" aria-label="${o.aria}">`
  s += ticks.map(t => `<line class="${t === 1 ? 'axis-zero' : 'grid'}" x1="${x(t)}" x2="${x(t)}" y1="${TOP - 8}" y2="${h - 18}"/><text x="${x(t)}" y="${h - 4}" text-anchor="middle">${t === 1 ? '1 · HUMAN' : t}</text>`).join('')
  data.forEach((d, i) => {
    if (d.a == null || d.b == null) return
    const y = TOP + i * ROW + ROW / 2
    s += `<g class="row" data-tip="${d.m}|${o.labelA}: ${fmt(d.a)}|${o.labelB}: ${fmt(d.b)}|Change: ${d.b - d.a > 0 ? '+' : ''}${fmt(d.b - d.a)}">
      <rect class="hit" x="0" y="${y - ROW / 2}" width="${W}" height="${ROW}"/>
      <text class="row-label" x="0" y="${y + 4}">${d.m.toUpperCase()}</text>
      <line class="link" x1="${x(d.a)}" x2="${x(d.b)}" y1="${y}" y2="${y}"/>
      <circle class="dot-a" cx="${x(d.a)}" cy="${y}" r="5.5"/><circle class="dot-b" cx="${x(d.b)}" cy="${y}" r="5.5"/>
    </g>`
  })
  return s + '</svg>'
}
function lineChart(points, o) {
  const w = W, h = 260, L = 50, Rr = 24, T = 20, B = 36
  const xs = points.map(p => Math.log(p.x)), x0 = Math.min(...xs), x1 = Math.max(...xs)
  const ymax = Math.max(1.2, ...points.flatMap(p => [p.a, p.b]).filter(v => v != null)) * 1.1
  const X = v => L + (Math.log(v) - x0) / (x1 - x0) * (w - L - Rr), Y = v => T + (1 - v / ymax) * (h - T - B)
  let s = `<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${o.aria}">`
  for (const t of [0, 0.5, 1, 1.5, 2].filter(t => t <= ymax)) s += `<line class="${t === 1 ? 'axis-zero' : 'grid'}" x1="${L}" x2="${w - Rr}" y1="${Y(t)}" y2="${Y(t)}"/><text x="${L - 8}" y="${Y(t) + 4}" text-anchor="end">${t === 1 ? 'HUMAN 1' : t}</text>`
  for (const p of points) s += `<text x="${X(p.x)}" y="${h - 12}" text-anchor="middle">${p.x}B</text>`
  const path = key => points.filter(p => p[key] != null).map((p, i) => `${i ? 'L' : 'M'}${X(p.x)},${Y(p[key])}`).join('')
  s += `<path d="${path('a')}" fill="none" stroke="var(--model)" stroke-width="2" stroke-dasharray="4 4"/>`
  s += `<path d="${path('b')}" fill="none" stroke="var(--ink)" stroke-width="2"/>`
  for (const p of points) {
    s += `<g class="row" data-tip="Qwen3 ${p.x}B|${o.labelA}: ${fmt(p.a)}|${o.labelB}: ${fmt(p.b)}"><rect class="hit" x="${X(p.x) - 24}" y="${T}" width="48" height="${h - T - B}"/>`
    if (p.a != null) s += `<circle class="dot-a" cx="${X(p.x)}" cy="${Y(p.a)}" r="5"/>`
    if (p.b != null) s += `<circle cx="${X(p.x)}" cy="${Y(p.b)}" r="5" fill="var(--ink)" stroke="var(--paper)" stroke-width="2"/>`
    s += `</g>`
  }
  return s + '</svg>'
}
export const FINDING_COPY = {}   // filled by findings.js text (written after the data is in)
function renderFindings(copy) {
  const root = document.getElementById('finding-list')
  const models = modelsInData()
  const qwen = ['qwen3:0.6b', 'qwen3:1.7b', 'qwen3:4b', 'qwen3:8b', 'qwen3:14b'].filter(m => models.includes(m))
  const F = [
    {
      chart: lineChart(qwen.map(m => ({ x: MODEL_META[m].params, a: meanAbsBQ(m, 'novel', 'fast', 'none'), b: meanAbsBQ(m, 'novel', 'deliberate', 'none') })),
        { aria: 'Mean bias quotient by Qwen3 model size', labelA: 'Fast', labelB: 'Thinks first' }),
      legend: `<span><i class="lg-a"></i>Fast answers</span><span><i class="lg-h"></i>Thinks first</span><span>Same model family, five sizes</span>`,
    },
    {
      chart: pairChart(models.map(m => ({ label: mname(m), a: meanAbsBQ(m, 'classic', 'fast', 'none'), b: meanAbsBQ(m, 'novel', 'fast', 'none') })),
        { aria: 'Bias quotient on textbook versus new wording', labelA: 'Textbook wording', labelB: 'New financial wording' }),
      legend: `<span><i class="lg-a"></i>Textbook wording</span><span><i class="lg-b"></i>New financial wording</span>`,
    },
    {
      chart: pairChart(models.map(m => ({ label: mname(m), a: meanAbsBQ(m, 'novel', 'fast', 'none'), b: meanAbsBQ(m, 'novel', 'deliberate', 'none') })),
        { aria: 'Bias quotient answering fast versus thinking first', labelA: 'Fast', labelB: 'Thinks first' }),
      legend: `<span><i class="lg-a"></i>Fast</span><span><i class="lg-b"></i>Thinks first</span>`,
    },
    {
      chart: pairChart(models.map(m => ({ label: mname(m), a: meanAbsBQ(m, 'novel', 'fast', 'none'), b: meanAbsBQ(m, 'novel', 'fast', 'advisor') })),
        { aria: 'Bias quotient with and without a financial advisor persona', labelA: 'No persona', labelB: 'Financial advisor persona' }),
      legend: `<span><i class="lg-a"></i>No persona</span><span><i class="lg-b"></i>"CFA-certified advisor" persona</span>`,
    },
  ]
  root.innerHTML = F.map((f, i) => `
    <article class="finding">
      <p class="finding-no">0${i + 1}</p>
      <div><h3>${copy[i].title}</h3><p>${copy[i].body}</p></div>
      <div><div class="chart-slot">${f.chart}</div><div class="chart-legend" style="margin-top:8px">${f.legend}</div></div>
    </article>`).join('')
  bindChartHover(root)
}

/* ================================================================ match */
function renderMatch() {
  const ans = store.get()
  const done = ENTRIES.filter(E => ans[E.exp])
  const title = document.getElementById('match-title'), rowsEl = document.getElementById('match-rows')
  if (done.length < 3) { title.innerHTML = `Answer at least three entries to see who you decide like. <span class="util" style="opacity:.7">(${done.length} of 7 so far)</span>`; rowsEl.innerHTML = ''; return }
  const sim = {}
  const cands = [...modelsInData(), 'Humans']
  for (const c of cands) {
    let s = 0, k = 0
    for (const E of done) {
      const a = ans[E.exp]
      let v = null
      if (E.exp === 'loss_aversion') {
        const lam = c === 'Humans' ? 2.25 : row(c, E.exp, 'classic')?.parts?.lambda
        if (lam != null) v = Math.exp(-Math.abs(Math.log(a.lambda / lam)))
      } else if (E.exp === 'anchoring') {
        if (c === 'Humans') continue
        const p = row(c, E.exp)?.parts
        const med = p && (a.anchor === 10 ? p.median_low : p.median_high)
        if (med) v = Math.exp(-Math.abs(Math.log(a.estimate / med)))
      } else if (E.exp === 'disposition') {
        const pw = c === 'Humans' ? 0.6 : row(c, E.exp)?.parts?.sell_winner
        if (pw != null) v = a.answer === 'winner' ? pw : 1 - pw
      } else {
        const H = HUMAN_PARTS[E.exp]
        const pk = c === 'Humans' ? (a.cond === E.conds[0] ? H.a : H.b) : row(c, E.exp)?.parts?.[`${E.key}_${a.cond}`]
        if (pk != null) v = a.answer === E.key ? pk : 1 - pk
      }
      if (v != null) { s += v; k++ }
    }
    if (k) sim[c] = s / k
  }
  const ranked = Object.entries(sim).sort((a, b) => b[1] - a[1])
  const [top] = ranked[0]
  title.innerHTML = `You decide most like <em>${top === 'Humans' ? 'a typical human' : mname(top)}</em>.`
  rowsEl.innerHTML = ranked.map(([c, v], i) => `<div class="match-row ${i === 0 ? 'top' : ''}"><span>${c === 'Humans' ? 'HUMANS' : mname(c).toUpperCase()}</span><span class="match-bar"><i style="width:${Math.round(v * 100)}%"></i></span><span>${Math.round(v * 100)}%</span></div>`).join('')
    + `<p class="util" style="opacity:.6;margin-top:12px">Agreement = the chance each decision-maker gives your answer in your version, averaged over the ${done.length} entries you completed.</p>`
}

/* ================================================================ boot */
export async function initStudy(copy) {
  const res = await fetch('data/summary.json?v=' + (copy.v || 1))
  DATA = await res.json()
  document.querySelectorAll('[data-count="models"]').forEach(el => el.textContent = DATA.models.length)
  document.querySelectorAll('[data-count="trials"]').forEach(el => el.textContent = DATA.n_trials.toLocaleString('en-US'))
  document.getElementById('finding-text').innerHTML = copy.headline(DATA, { meanAbsBQ, modelsInData, row, mname })
  buildEntries(document.getElementById('entries'), renderMatch)
  buildAuditControls(); renderAudit()
  renderFindings(copy.findings(DATA, { meanAbsBQ, modelsInData, row, mname }))
  renderMatch()
  return DATA
}
export { ENTRIES, meanAbsBQ, modelsInData }
