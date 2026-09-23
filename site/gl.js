/* One fixed full-viewport canvas renders two "views" (scissored into DOM rects):
   the hero coin pile (Rapier physics, cursor shoves, click flips) and a single coin
   in the loss-aversion entry that is tossed for real when the visitor places a bet.
   The coin is this study's own mint (heads: lambda, tails: -$100), so it is drawn
   procedurally: canvas height maps -> normal maps, brass PBR, reeded edge. */
import * as THREE from 'three'
import RAPIER from '@dimforge/rapier3d-compat'

const canvas = document.getElementById('gl')
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true })
renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
renderer.toneMapping = THREE.ACESFilmicToneMapping
renderer.toneMappingExposure = 1.0
renderer.setScissorTest(true)
renderer.setClearColor(0x000000, 0)

const isSmall = matchMedia('(max-width: 700px)').matches
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches

/* ---------------- environment: structured studio bands (metal needs contrast) ---------------- */
function makeEnv() {
  const W = 512, H = 256, data = new Float32Array(W * H * 4)
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    // DataTexture row 0 is the BOTTOM of the equirect (down); v measures from the top (zenith) here
    const i = (y * W + x) * 4, v = 1 - y / H, u = x / W
    // dark green room
    let r = 0.02, g = 0.035, b = 0.03
    // big softbox where flat faces reflect into for this camera (u~0.25 is -z, v~0.25 is 45deg up)
    const soft = Math.exp(-Math.pow((v - 0.24) / 0.1, 2)) * Math.exp(-Math.pow((u - 0.25) / 0.09, 2))
    r += soft * 2.4; g += soft * 2.25; b += soft * 1.9
    // a smaller, harder card near the zenith for rim glints
    const top = Math.exp(-Math.pow((v - 0.06) / 0.04, 2)) * Math.exp(-Math.pow((u - 0.6) / 0.2, 2))
    r += top * 1.6; g += top * 1.6; b += top * 1.45
    // two vertical strip lights with dark gaps between them (edge highlights)
    const s1 = Math.exp(-Math.pow((u - 0.72) / 0.012, 2)) * (v > 0.1 && v < 0.62 ? 1 : 0)
    const s2 = Math.exp(-Math.pow((u - 0.08) / 0.02, 2)) * (v > 0.2 && v < 0.55 ? 1 : 0)
    r += (s1 * 5 + s2 * 2.2); g += (s1 * 5 + s2 * 2.3); b += (s1 * 4.6 + s2 * 2.2)
    // faint paper-green floor bounce
    const floor = Math.max(0, v - 0.6) * 0.5
    r += floor * 0.25; g += floor * 0.32; b += floor * 0.27
    data[i] = r; data[i + 1] = g; data[i + 2] = b; data[i + 3] = 1
  }
  const tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat, THREE.FloatType)
  tex.mapping = THREE.EquirectangularReflectionMapping
  tex.needsUpdate = true
  const pmrem = new THREE.PMREMGenerator(renderer)
  const env = pmrem.fromEquirectangular(tex).texture
  tex.dispose(); pmrem.dispose()
  return env
}
const ENV = makeEnv()

/* ---------------- coin textures ---------------- */
function heightToNormal(hc, strength) {
  const w = hc.width, h = hc.height
  const src = hc.getContext('2d').getImageData(0, 0, w, h).data
  const out = document.createElement('canvas'); out.width = w; out.height = h
  const ctx = out.getContext('2d'), img = ctx.createImageData(w, h), d = img.data
  const H = (x, y) => src[((Math.min(h - 1, Math.max(0, y)) * w) + Math.min(w - 1, Math.max(0, x))) * 4] / 255
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const dx = (H(x + 1, y) - H(x - 1, y)) * strength, dy = (H(x, y + 1) - H(x, y - 1)) * strength
    const len = Math.hypot(dx, dy, 1), i = (y * w + x) * 4
    d[i] = (-dx / len * 0.5 + 0.5) * 255; d[i + 1] = (dy / len * 0.5 + 0.5) * 255; d[i + 2] = (1 / len * 0.5 + 0.5) * 255; d[i + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
  return out
}
function ringText(ctx, text, r, size, start) {
  ctx.save()
  ctx.font = `500 ${size}px "Geist Mono", monospace`
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  const chars = [...text], step = (Math.PI * 1.62) / chars.length
  let a = start
  for (const ch of chars) {
    ctx.save(); ctx.rotate(a); ctx.translate(0, -r); ctx.fillText(ch, 0, 0); ctx.restore()
    a += step
  }
  ctx.restore()
}
function faceHeight(kind) {
  const c = document.createElement('canvas'); c.width = c.height = 512
  const x = c.getContext('2d')
  x.fillStyle = '#6a6a6a'; x.fillRect(0, 0, 512, 512)
  x.translate(256, 256)
  // raised rim
  x.lineWidth = 22; x.strokeStyle = '#fff'; x.beginPath(); x.arc(0, 0, 238, 0, Math.PI * 2); x.stroke()
  // bead ring
  x.fillStyle = '#e0e0e0'
  for (let i = 0; i < 72; i++) { const a = i / 72 * Math.PI * 2; x.beginPath(); x.arc(Math.cos(a) * 214, Math.sin(a) * 214, 3.4, 0, Math.PI * 2); x.fill() }
  x.fillStyle = '#f2f2f2'
  if (kind === 'heads') {
    ringText(x, 'IN EXPECTED VALUE WE TRUST', 180, 25, -Math.PI * 0.81)
    x.font = '400 250px "Schibsted Grotesk", serif'; x.textAlign = 'center'; x.textBaseline = 'middle'
    x.fillText('λ', 0, 6)
    x.font = '500 22px "Geist Mono", monospace'; x.fillText('MMXXVI', 0, 150)
  } else {
    ringText(x, 'TAILS · YOU LOSE · TAILS', 180, 25, -Math.PI * 0.81)
    x.font = '500 124px "Schibsted Grotesk", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'
    x.fillText('−100', 0, 4)
    x.font = '500 22px "Geist Mono", monospace'; x.fillText('ONE LEDGER DOLLAR', 0, 110)
  }
  return c
}
function edgeHeight() {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 32
  const x = c.getContext('2d')
  for (let i = 0; i < 1024; i++) { const v = 0.5 + 0.5 * Math.sin(i / 1024 * Math.PI * 2 * 140); x.fillStyle = `rgb(${v * 255},${v * 255},${v * 255})`; x.fillRect(i, 0, 1, 32) }
  return c
}
function makeCoinMaterials() {
  const mk = (kind) => {
    const hc = faceHeight(kind)
    const n = new THREE.CanvasTexture(heightToNormal(hc, 3.2)); n.colorSpace = THREE.NoColorSpace
    n.anisotropy = 4
    return new THREE.MeshPhysicalMaterial({
      color: kind === 'heads' ? 0xc49a45 : 0xb58c40, metalness: 1, roughness: 0.34,
      normalMap: n, normalScale: new THREE.Vector2(0.9, 0.9), envMap: ENV, envMapIntensity: 1.25,
      clearcoat: 0.25, clearcoatRoughness: 0.35,
    })
  }
  const en = new THREE.CanvasTexture(heightToNormal(edgeHeight(), 2)); en.colorSpace = THREE.NoColorSpace
  const edge = new THREE.MeshPhysicalMaterial({ color: 0xa8843c, metalness: 1, roughness: 0.38, normalMap: en, envMap: ENV, envMapIntensity: 1.1 })
  return [edge, mk('heads'), mk('tails')]
}

/* fonts must be ready before textures rasterize the glyphs */
await document.fonts.ready.catch(() => {})
const COIN_MATS = makeCoinMaterials()
const R = 0.62, T = 0.1
const COIN_GEO = new THREE.CylinderGeometry(R, R, T, 64, 1)
// caps map (u,v) as a disc: rotate the bottom cap so tails text is not mirrored
;(function fixBottomUV() {
  const uv = COIN_GEO.attributes.uv, pos = COIN_GEO.attributes.position, nrm = COIN_GEO.attributes.normal
  for (let i = 0; i < uv.count; i++) if (nrm.getY(i) < -0.99) {   // bottom-cap vertices only (side verts share positions)
    // bottom cap: planar map from x/z (reads unmirrored when the coin lands tails-up)
    uv.setXY(i, 0.5 + pos.getX(i) / (2 * R), 0.5 - pos.getZ(i) / (2 * R))
  }
  uv.needsUpdate = true
})()
function coinMesh() { const m = new THREE.Mesh(COIN_GEO, COIN_MATS); return m }

/* ---------------- views ---------------- */
function makeView(el, fov, camPos, lookAt) {
  const scene = new THREE.Scene()
  scene.environment = ENV
  const key = new THREE.DirectionalLight(0xfff4e0, 1.2); key.position.set(3, 6, 4); scene.add(key)
  const camera = new THREE.PerspectiveCamera(fov, 1, 0.1, 80)
  camera.position.copy(camPos); camera.lookAt(lookAt)
  return { el, scene, camera, rect: null, visible: false }
}

await RAPIER.init()

/* ===== hero: coin pile on the blotter ===== */
const heroEl = document.getElementById('hero-panel')
const hero = makeView(heroEl, 32, new THREE.Vector3(0, 11.5, 12.5), new THREE.Vector3(0, 0, 0.4))
const heroWorld = new RAPIER.World({ x: 0, y: -14, z: 0 })
const coins = []
let halfW = 6, halfD = 3.6
const walls = []
function buildHeroWalls() {
  for (const w of walls) heroWorld.removeCollider(w, false)
  walls.length = 0
  // visible table extent on the y=0 plane, from the camera frustum
  const cam = hero.camera
  const ray = new THREE.Raycaster(), plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), p = new THREE.Vector3()
  const hit = (x, y) => { ray.setFromCamera(new THREE.Vector2(x, y), cam); return ray.ray.intersectPlane(plane, p) ? p.clone() : null }
  const tl = hit(-0.92, 0.86), br = hit(0.92, -0.86), bl = hit(-0.92, -0.86)
  halfW = Math.max(2, Math.min(Math.abs(bl.x), Math.abs(br.x)) * 0.98)
  const zFar = tl ? tl.z : -4, zNear = br.z
  const add = (hx, hy, hz, x, y, z) => walls.push(heroWorld.createCollider(RAPIER.ColliderDesc.cuboid(hx, hy, hz).setTranslation(x, y, z).setFriction(0.6).setRestitution(0.2)))
  add(40, 0.5, 40, 0, -0.5, 0)                       // table
  add(0.5, 10, 20, -halfW - 0.5, 10, 0)               // left
  add(0.5, 10, 20, halfW + 0.5, 10, 0)                // right
  add(40, 10, 0.5, 0, 10, zFar - 0.5)                 // back
  add(40, 10, 0.5, 0, 10, zNear + 0.5)                // front
  add(40, 0.5, 40, 0, 20.5, 0)                       // ceiling
  halfD = (zNear - zFar) / 2
  hero.zc = (zNear + zFar) / 2
}
function spawnCoin(i, n) {
  const mesh = coinMesh()
  hero.scene.add(mesh)
  const body = heroWorld.createRigidBody(
    RAPIER.RigidBodyDesc.dynamic()
      .setTranslation((Math.random() - 0.5) * halfW * 1.6, 4 + i * 0.55, (hero.zc || 0) + (Math.random() - 0.5) * halfD)
      .setRotation(new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.random() * 6, Math.random() * 6, Math.random() * 6)))
      .setLinearDamping(0.25).setAngularDamping(0.35).setCcdEnabled(true)
  )
  heroWorld.createCollider(RAPIER.ColliderDesc.cylinder(T / 2, R).setRestitution(0.3).setFriction(0.55).setDensity(8), body)
  coins.push({ mesh, body, lastFace: null, settled: false })
}
const mouseBody = heroWorld.createRigidBody(RAPIER.RigidBodyDesc.kinematicPositionBased().setTranslation(0, -50, 0))
heroWorld.createCollider(RAPIER.ColliderDesc.ball(0.75), mouseBody)

/* ===== entry view: one coin, tossed on demand ===== */
const tossEls = []   // registered by study.js (the entry's coin stage)
const toss = { view: null, world: null, coin: null, pending: null }
function initToss(el) {
  const v = makeView(el, 30, new THREE.Vector3(0, 4.4, 2.9), new THREE.Vector3(0, 0.25, 0))
  const w = new RAPIER.World({ x: 0, y: -18, z: 0 })
  w.createCollider(RAPIER.ColliderDesc.cuboid(20, 0.5, 20).setTranslation(0, -0.5, 0).setFriction(0.7).setRestitution(0.35))
  for (const [hx, hz, x, z] of [[0.5, 6, -2.4, 0], [0.5, 6, 2.4, 0], [6, 0.5, 0, -1.6], [6, 0.5, 0, 1.6]])
    w.createCollider(RAPIER.ColliderDesc.cuboid(hx, 6, hz).setTranslation(x, 6, z))
  const mesh = coinMesh(); v.scene.add(mesh)
  const body = w.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(0, 0.2, 0).setAngularDamping(0.2).setCcdEnabled(true))
  w.createCollider(RAPIER.ColliderDesc.cylinder(T / 2, R).setRestitution(0.35).setFriction(0.6).setDensity(8), body)
  Object.assign(toss, { view: v, world: w, coin: { mesh, body } })
}

/* ---------------- pointer ---------------- */
const ndc = new THREE.Vector2(-9, -9)
let pointerInHero = false, pointerClient = { x: 0, y: 0 }
addEventListener('pointermove', e => {
  pointerClient = { x: e.clientX, y: e.clientY }
  if (cursorAway && Math.hypot(e.clientX - cursorAway.x, e.clientY - cursorAway.y) > 24) cursorAway = null
  const r = heroEl.getBoundingClientRect()
  pointerInHero = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom
  ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1)
}, { passive: true })
const ray = new THREE.Raycaster()
const table = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.35)
const mouseWorld = new THREE.Vector3()
const tally = { heads: 0, tails: 0 }
let flips = 0, mouseParked = true, cursorAway = null   // {x,y} of the click while the cursor collider is parked
heroEl.addEventListener('pointerdown', e => {
  ray.setFromCamera(ndc, hero.camera)
  const hits = ray.intersectObjects(coins.map(c => c.mesh))
  if (hits.length) {
    const c = coins.find(c => c.mesh === hits[0].object)
    flipBody(c.body, 1)
    c.counted = false; c.still = 0; flips++
    // lift the cursor collider away briefly so it does not bat the coin on its way down
    cursorAway = { x: e.clientX, y: e.clientY }
  } else if (ray.ray.intersectPlane(table, mouseWorld)) {
    // click on the felt: radial puff
    for (const { body } of coins) {
      const p = body.translation(), d = new THREE.Vector3(p.x - mouseWorld.x, 0, p.z - mouseWorld.z)
      const dist = Math.max(d.length(), 0.5)
      if (dist < 2.6) body.applyImpulse({ x: d.x / dist * 0.9, y: 1.4 / dist, z: d.z / dist * 0.9 }, true)
    }
  }
})
function flipBody(body, scale) {
  // set velocities directly: a real flip needs ~15-25 rad/s of spin, far more than a gentle impulse gives
  const sgn = Math.random() < 0.5 ? -1 : 1
  body.setLinvel({ x: (Math.random() - 0.5) * 0.8, y: (5.8 + Math.random() * 1.6) * scale, z: (Math.random() - 0.5) * 0.6 }, true)
  body.setAngvel({ x: sgn * (15 + Math.random() * 9) * scale, y: (Math.random() - 0.5) * 2, z: (Math.random() - 0.5) * 3 }, true)
}
const up = new THREE.Vector3(), tmpQ = new THREE.Quaternion()
function faceUp(body) {
  const q = body.rotation(); tmpQ.set(q.x, q.y, q.z, q.w)
  up.set(0, 1, 0).applyQuaternion(tmpQ)
  return up.y > 0.8 ? 'heads' : up.y < -0.8 ? 'tails' : null
}

/* ---------------- scroll velocity (fed by app.js) ---------------- */
export const glState = { scrollVel: 0 }

/* ---------------- sizing ---------------- */
function resize() {
  renderer.setSize(innerWidth, innerHeight, false)
}
addEventListener('resize', () => { resize(); layoutHero() })
resize()
function layoutHero() {
  const r = heroEl.getBoundingClientRect()
  hero.camera.aspect = r.width / r.height
  // keep the table width constant-ish: pull back on narrow panels
  const narrow = hero.camera.aspect < 1.2
  hero.camera.position.set(0, narrow ? 15 : 11.5, narrow ? 15 : 12.5)
  hero.camera.lookAt(0, 0, 0.4)
  hero.camera.updateProjectionMatrix()
  buildHeroWalls()
}
layoutHero()
const N = isSmall ? 16 : 30
for (let i = 0; i < N; i++) spawnCoin(i, N)
document.getElementById('coin-count').textContent = String(N)

/* ---------------- render ---------------- */
function viewRect(el) {
  const r = el.getBoundingClientRect()
  const vis = r.bottom > 0 && r.top < innerHeight && r.width > 0
  return { r, vis }
}
function drawView(v) {
  const { r, vis } = viewRect(v.el)
  v.visible = vis
  if (!vis) return
  const x = r.left, y = innerHeight - r.bottom
  renderer.setViewport(x, y, r.width, r.height)
  renderer.setScissor(x, y, r.width, r.height)
  if (Math.abs(v.camera.aspect - r.width / r.height) > 1e-3) { v.camera.aspect = r.width / r.height; v.camera.updateProjectionMatrix() }
  renderer.render(v.scene, v.camera)
}
const clock = new THREE.Clock()
let frame = 0
const pile = new THREE.Vector3()
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 1 / 30)
  frame++
  renderer.setScissor(0, 0, innerWidth, innerHeight); renderer.setViewport(0, 0, innerWidth, innerHeight)
  renderer.clear()

  // hero physics only while visible (the pile sleeps otherwise)
  const hv = viewRect(heroEl).vis
  if (hv) {
    ray.setFromCamera(ndc, hero.camera)
    if (pointerInHero && !cursorAway && ray.ray.intersectPlane(table, mouseWorld)) {
      const t = { x: mouseWorld.x, y: 0.35, z: mouseWorld.z }
      // entering from the parked spot must TELEPORT (setTranslation): a kinematic move of 50 units
      // in one step gives the collider ~1500 m/s and launches every coin it touches
      if (mouseParked) { mouseBody.setTranslation(t, true); mouseParked = false }
      else mouseBody.setNextKinematicTranslation(t)
    } else if (!mouseParked) { mouseBody.setTranslation({ x: 0, y: -50, z: 0 }, true); mouseParked = true }
    const sv = glState.scrollVel
    if (Math.abs(sv) > 3 && !reduced) for (const { body } of coins) {
      if (Math.random() < 0.08) body.applyImpulse({ x: 0, y: Math.min(Math.abs(sv), 40) * 0.0035 * body.mass(), z: 0 }, true)
    }
    heroWorld.timestep = dt
    heroWorld.step()
    for (const c of coins) {
      const p = c.body.translation()
      if (p.y < -3 || p.y > 25 || Math.abs(p.x) > halfW + 3 || Math.abs(p.z) > 30) { c.body.setTranslation({ x: 0, y: 5, z: hero.zc || 0 }, true); c.body.setLinvel({ x: 0, y: 0, z: 0 }, true) }
      c.mesh.position.set(p.x, p.y, p.z)
      c.mesh.quaternion.copy(c.body.rotation())
      // tally a flip once the coin comes to rest after a click
      if (c.counted === false) {
        const v = c.body.linvel(), w = c.body.angvel()
        const still = Math.hypot(v.x, v.y, v.z) < 0.08 && Math.hypot(w.x, w.y, w.z) < 0.15
        c.still = still ? (c.still || 0) + 1 : 0
        if (c.still > 12) {   // at rest for a dozen frames (on the table or on another coin)
          const f = faceUp(c.body)
          if (f) { tally[f]++; c.counted = true; updateTally() }
          else if (c.still > 90) c.counted = true   // leaning on its edge against another coin: no call
        }
      }
    }
  }
  drawView(hero)

  if (toss.view) {
    const tv = viewRect(toss.view.el).vis
    if (tv) {
      toss.world.timestep = dt
      toss.world.step()
      const b = toss.coin.body, p = b.translation()
      toss.coin.mesh.position.set(p.x, p.y, p.z)
      toss.coin.mesh.quaternion.copy(b.rotation())
      if (toss.pending) {
        const v = b.linvel(), w = b.angvel()
        toss.pending.t += dt
        if (toss.pending.t > 0.6 && Math.hypot(v.x, v.y, v.z) < 0.04 && Math.hypot(w.x, w.y, w.z) < 0.06) {
          const f = faceUp(b)
          if (f) { const cb = toss.pending.cb; toss.pending = null; cb(f) }
          else if (toss.pending.t > 4) { flipBody(b, 0.6) }   // landed on its edge: nudge
        }
      }
    }
    drawView(toss.view)
  }
})
function updateTally() {
  document.getElementById('t-heads').textContent = tally.heads
  document.getElementById('t-tails').textContent = tally.tails
}

/* ---------------- API for study.js ---------------- */
export function registerTossStage(el) { initToss(el) }
export function tossCoin() {
  return new Promise(res => {
    if (!toss.coin) return res(Math.random() < 0.5 ? 'heads' : 'tails')
    const b = toss.coin.body
    b.setTranslation({ x: 0, y: 0.3, z: 0 }, true)
    b.setLinvel({ x: 0, y: 0, z: 0 }, true); b.setAngvel({ x: 0, y: 0, z: 0 }, true)
    b.setRotation({ x: 0, y: 0, z: 0, w: 1 }, true)
    const sgn = Math.random() < 0.5 ? -1 : 1
    b.setLinvel({ x: (Math.random() - 0.5) * 0.4, y: 6.4, z: (Math.random() - 0.5) * 0.2 }, true)
    b.setAngvel({ x: sgn * (19 + Math.random() * 8), y: 0, z: (Math.random() - 0.5) * 2 }, true)
    toss.pending = { t: 0, cb: res }
  })
}

window.__dbg = Object.assign(window.__dbg || {}, {
  gl: () => ({
    frame, coins: coins.length, tally: { ...tally }, flips, halfW,
    ys: coins.map(c => +c.body.translation().y.toFixed(2)),
    pointerInHero, mouse: mouseBody.translation(),
    toss: toss.coin ? { pos: toss.coin.body.translation(), pending: !!toss.pending } : null,
    coinState: () => coins.filter(c => c.counted !== undefined).map(c => { const v = c.body.linvel(), w = c.body.angvel(), q = c.body.rotation(); tmpQ.set(q.x, q.y, q.z, q.w); return { counted: c.counted, still: c.still, upY: +new THREE.Vector3(0, 1, 0).applyQuaternion(tmpQ).y.toFixed(2), v: +Math.hypot(v.x, v.y, v.z).toFixed(3), w: +Math.hypot(w.x, w.y, w.z).toFixed(3), y: +c.body.translation().y.toFixed(2), sleeping: c.body.isSleeping() } }),
  }),
})
