/* Page copy that depends on the results. Every number is computed from the data;
   the sentences around them are written after reading the results. */
const f2 = v => v == null ? 'n/a' : v.toFixed(2)

export const COPY = {
  v: 1,
  headline(D, h) {
    const ms = h.modelsInData()
    const scores = ms.map(m => ({ m, v: h.meanAbsBQ(m, 'novel', 'fast', 'none') })).filter(s => s.v != null)
    const avg = scores.reduce((s, x) => s + x.v, 0) / Math.max(1, scores.length)
    const best = scores.slice().sort((a, b) => a.v - b.v)[0]
    return `Across ten models, the average bias quotient is <em>${f2(avg)}</em>, where 1.00 means exactly as biased as people. The most consistent model, ${best ? h.mname(best.m) : 'n/a'}, scores ${best ? f2(best.v) : 'n/a'}.`
  },
  findings(D, h) {
    return [
      { title: 'Bigger is not automatically more rational.', body: 'Same family, same training recipe, five sizes. The line tracks the mean bias quotient as the model grows.' },
      { title: 'Textbook wording flatters the models.', body: 'Each test ran twice: the famous wording and a new financial version with the same structure.' },
      { title: 'Thinking first changes the answers.', body: 'The same models, asked to write their reasoning before choosing.' },
      { title: 'Telling a model it is a financial advisor does little.', body: 'The same models, prompted as a disciplined, CFA-certified advisor.' },
    ]
  },
}
