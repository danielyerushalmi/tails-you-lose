import { initStudy } from './study.js?v=3'
import { COPY } from './copy.js?v=1'

const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
const hasGsap = typeof window.gsap !== 'undefined'

/* ---------- smooth scroll bridge ---------- */
let lenis = null
let glState = null
if (hasGsap) {
  gsap.registerPlugin(ScrollTrigger, SplitText)
  if (!reduced && typeof window.Lenis !== 'undefined') {
    lenis = new Lenis({ lerp: 0.1, smoothWheel: true })
    lenis.on('scroll', ScrollTrigger.update)
    gsap.ticker.add(t => lenis.raf(t * 1000))
    gsap.ticker.lagSmoothing(0)
    lenis.on('scroll', e => { if (glState) glState.scrollVel = e.velocity })
    document.querySelectorAll('a[href^="#"]').forEach(a => a.addEventListener('click', e => {
      const id = a.getAttribute('href'); if (id.length < 2) return
      e.preventDefault(); lenis.scrollTo(id, { offset: -70 })
    }))
  }
}

/* ---------- WebGL layer (lazy; the page works without it) ---------- */
const glReady = import('./gl.js?v=9').then(m => {
  glState = m.glState
  window.__toss = () => m.tossCoin()
  return m
}).catch(err => { console.warn('WebGL layer unavailable:', err); return null })

/* ---------- data + entries ---------- */
initStudy(COPY).then(async () => {
  if (hasGsap) { ScrollTrigger.refresh(); setupMotion() }
  // the coin stage lives inside an entry, which only exists once the data has loaded
  const m = await glReady
  const stage = document.getElementById('coin-stage')
  if (m && stage) m.registerTossStage(stage)
}).catch(err => {
  console.error(err)
  document.getElementById('finding-text').textContent = 'The ledger failed to load. Refresh to try again.'
})

function setupMotion() {
  /* masked headline reveals */
  if (!reduced) document.querySelectorAll('[data-split]').forEach(el => {
    const split = new SplitText(el, { type: 'lines', linesClass: 'split-line-inner' })
    split.lines.forEach(line => {
      const wrap = document.createElement('div'); wrap.className = 'split-line'
      line.parentNode.insertBefore(wrap, line); wrap.appendChild(line)
    })
    gsap.from(split.lines, { yPercent: 110, duration: 1, ease: 'power4.out', stagger: 0.08, scrollTrigger: { trigger: el, start: 'top 85%' } })
  })
  /* entries and findings rise in */
  if (!reduced) gsap.utils.toArray('.entry, .finding, .figure').forEach(el => {
    gsap.from(el, { y: 40, opacity: 0, duration: 1, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 88%' } })
  })
  /* figures count up */
  document.querySelectorAll('.big-num[data-count]').forEach(el => {
    const target = parseInt(el.textContent.replace(/,/g, ''), 10)
    if (!target || reduced) return
    const o = { v: 0 }
    gsap.to(o, { v: target, duration: 1.6, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 85%' },
      onUpdate: () => { el.textContent = Math.round(o.v).toLocaleString('en-US') } })
  })
  /* velocity skew on the ledger figures and audit table (2D chapters stay alive) */
  if (!reduced && lenis) {
    const skewEls = gsap.utils.toArray('.figures, .audit-table-wrap, .finding-list')
    const setters = skewEls.map(el => gsap.quickTo(el, 'skewY', { duration: 0.5, ease: 'power3.out' }))
    lenis.on('scroll', e => { const v = gsap.utils.clamp(-3, 3, e.velocity * 0.08); setters.forEach(s => s(v)) })
  }
  /* nav active state */
  const links = [...document.querySelectorAll('[data-nav]')]
  links.forEach(a => {
    const sec = document.getElementById(a.dataset.nav)
    if (sec) ScrollTrigger.create({ trigger: sec, start: 'top 50%', end: 'bottom 50%',
      onToggle: s => { if (s.isActive) links.forEach(l => l.classList.toggle('is-active', l === a)) } })
  })
  magnetic(); tilt(); lamp()
}

/* ---------- desk lamp on the reconciliation card ---------- */
function lamp() {
  const card = document.querySelector('.match-card')
  if (!card || reduced) return
  const pos = { x: 70, y: 30 }
  const setX = gsap.quickTo(pos, 'x', { duration: 0.6, ease: 'power3.out', onUpdate: () => card.style.setProperty('--lx', pos.x + '%') })
  const setY = gsap.quickTo(pos, 'y', { duration: 0.6, ease: 'power3.out', onUpdate: () => card.style.setProperty('--ly', pos.y + '%') })
  card.addEventListener('pointermove', e => {
    const r = card.getBoundingClientRect()
    setX((e.clientX - r.left) / r.width * 100); setY((e.clientY - r.top) / r.height * 100)
    card.style.setProperty('--lo', 1)
  })
  card.addEventListener('pointerleave', () => card.style.setProperty('--lo', 0.55))
}

/* ---------- magnetic buttons ---------- */
function magnetic() {
  if (reduced) return
  document.querySelectorAll('[data-magnetic]').forEach(el => {
    el.addEventListener('pointermove', e => {
      const r = el.getBoundingClientRect()
      gsap.to(el, { x: (e.clientX - r.left - r.width / 2) * 0.25, y: (e.clientY - r.top - r.height / 2) * 0.3, duration: 0.3, ease: 'power2.out' })
    })
    el.addEventListener('pointerleave', () => gsap.to(el, { x: 0, y: 0, duration: 0.7, ease: 'power4.out' }))
  })
}
/* ---------- hover tilt (paper card, entry cards) ---------- */
function tilt() {
  if (reduced) return
  document.querySelectorAll('[data-tilt], .entry').forEach(el => {
    const max = el.matches('.entry') ? 1.2 : 5
    el.style.transformPerspective = '1200px'
    el.addEventListener('pointermove', e => {
      const r = el.getBoundingClientRect()
      const px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5
      gsap.to(el, { rotateY: px * max * 2, rotateX: -py * max * 2, transformPerspective: 1200, duration: 0.5, ease: 'power3.out' })
    })
    el.addEventListener('pointerleave', () => gsap.to(el, { rotateY: 0, rotateX: 0, duration: 0.8, ease: 'power4.out' }))
  })
}
