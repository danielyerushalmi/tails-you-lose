/* Page copy that depends on the results. Every number is computed from the data at load time;
   the sentences around them were written after reading the final results. */
const f2 = v => v == null ? 'n/a' : v.toFixed(2)
const pc = v => v == null ? 'n/a' : `${Math.round(v * 100)}%`
const avg = xs => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null

export const COPY = {
  v: 3,
  headline(D, h) {
    const ms = h.modelsInData()
    const nf = avg(ms.map(m => h.meanAbsBQ(m, 'novel', 'fast', 'none')).filter(v => v != null))
    const anch = ms.filter(m => (h.row(m, 'anchoring')?.bq ?? 0) > 1).length
    const sunk = ms.filter(m => { const p = h.row(m, 'sunk_cost')?.parts; return p && p.invest_sunk <= 0.05 && p.invest_control <= 0.05 }).length
    return `On new financial problems the models averaged a bias quotient of <em>${f2(nf)}</em>, a bit less biased than people. The average hides the story: ${sunk} of ${ms.length} never fell for sunk costs, yet ${anch} of ${ms.length} were more anchored than people by a random number.`
  },
  findings(D, h) {
    const ms = h.modelsInData()
    const m = (s, mo, p = 'none') => avg(ms.map(x => h.meanAbsBQ(x, s, mo, p)).filter(v => v != null))
    const t = D.tests || {}, pe = D.per_exp_tests || {}
    const fd = pe.fast_vs_deliberate_novel || {}, tn = pe.textbook_vs_novel || {}, ad = pe.none_vs_advisor || {}
    const q = ['qwen3:0.6b', 'qwen3:1.7b', 'qwen3:14b'].map(x => h.meanAbsBQ(x, 'novel', 'fast', 'none'))
    const acq = D.acquiescence_x50 || {}
    const acc = k => avg(ms.map(x => acq[x]?.[k]).filter(v => v != null))
    return [
      { title: 'Size helped, but not in a straight line.',
        body: `Same family, five sizes. The 14B model was the most consistent decision-maker in the study (<span class="stat">${f2(q[2])}</span>), but the 1.7B model (<span class="stat">${f2(q[1])}</span>) did worse than the 0.6B (<span class="stat">${f2(q[0])}</span>). Small models are erratic: the 0.6B simply repeats the random anchor back.` },
      { title: 'Familiar wording changes the answers, both ways.',
        body: `Overall, textbook and new wordings scored about the same (<span class="stat">${f2(m('classic', 'fast'))}</span> vs <span class="stat">${f2(m('novel', 'fast'))}</span>). But anchoring nearly vanished on the famous question (<span class="stat">${f2(tn.anchoring?.mean_a)}</span> vs <span class="stat">${f2(tn.anchoring?.mean_b)}</span>), while on the famous theater-ticket problem the models echoed the human bias far more (<span class="stat">${f2(tn.mental_accounting?.mean_a)}</span> vs <span class="stat">${f2(tn.mental_accounting?.mean_b)}</span>). Famous test problems are a poor guide.` },
      { title: 'Thinking first fixes one bias and feeds another.',
        body: `Writing out reasoning before answering cut anchoring from <span class="stat">${f2(fd.anchoring?.mean_a)}</span> to <span class="stat">${f2(fd.anchoring?.mean_b)}</span>: models that did the price-to-earnings math stopped copying the random number. The same step raised the certainty effect from <span class="stat">${f2(fd.certainty?.mean_a)}</span> to <span class="stat">${f2(fd.certainty?.mean_b)}</span>, the classic Allais pattern.` },
      { title: 'Telling a model it is a financial advisor made it worse.',
        body: `Prompted as a "disciplined, CFA-certified advisor", the models averaged <span class="stat">${f2(m('novel', 'fast', 'advisor'))}</span>, against <span class="stat">${f2(m('novel', 'fast'))}</span> without the persona${t.none_vs_advisor ? `, and ${t.none_vs_advisor.n_increase} of ${t.none_vs_advisor.n_models} got worse` : ''}. The "disciplined" advisor mostly turned too cautious, refusing profitable bets (loss aversion <span class="stat">${f2(ad.loss_aversion?.mean_a)}</span> to <span class="stat">${f2(ad.loss_aversion?.mean_b)}</span>).` },
      { title: 'Call it a trade, not a gamble, and they take the losing bet.',
        body: `Stake $100 on a coin flip to win $50: a bad deal. As a coin flip, the models took it <span class="stat">${pc(acc('classic_fast'))}</span> of the time. Offered as a one-time trade in a brokerage app, with identical odds, <span class="stat">${pc(acc('novel_fast'))}</span>. We first suspected a social effect: framed as a friend's business it was <span class="stat">${pc(acc('friend_fast'))}</span>, so the friend adds little. The word "trade" does the work.` },
    ]
  },
}
