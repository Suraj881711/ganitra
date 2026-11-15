/* ============================================================================
   Wave 62B — the OLD Logo Jungle, performed by the eagle alone.

   History: Wave 62 restored the pre-61 scene system (Waves
   23-28) with the four real 3D friends performing it. Suraj's
   FINAL spec followed within the hour (15 Nov 2026,
   15:57-16:15 IST) and this module implements exactly that:

   1. "abhi saare 3d model chodo bs eagle kaa rakho" — the 3D
      scene keeps ONLY THE EAGLE. The tiger, lion and boy
      models are NOT loaded and never appear; their .glb files
      stay in /static/models/ (parked, not deleted) with the
      walk clips Wave 62 authored in them. On activation
      this module marks tiger/boy/lion "broken" with the
      director, so their scenes leave the performed rotation;
      the director's eagle-only fallback in pickSceneName
      (window.__sceneEagleOnly3D) keeps the rotation alive on
      the one remaining scene. In a pure-2D visit nothing here
      runs and the rotation is exactly the pre-62 one.
   2. "aise board mai nhi karana, pahale ki tarah same karana
      hai" — NO wooden plaque/board. Like the old 2D scene,
      the LOGO ITSELF is the play object: the eagle perches
      directly on the G, grips the G itself for the carry and
      kisses the G itself.
   3. "jo ganitra kaa logo hai G bas wahi hona chahiye" — the
      object is ONLY the "G" of the logo (the "Ganitra" name
      is not part of it): /static/logo-g-t.png, a crop of
      Suraj's frozen original artwork limited to the G glyph
      (RGB pixels byte-identical to the original; only the
      paper background was keyed to alpha so the mark stands
      alone, the same treatment as the app's own logo-full-t).
      The full frozen logo everywhere else is untouched.
   4. The boy writer is the pre-61 2D sprite again: this
      module never defines the 3D boy-writer hook, so Teach
      / thinking use scene-boy.webp exactly as before.

   The director (templates/index.html) remains the single
   scheduler — first scene ~2-4s after every load, later gaps
   ~25-75s, tap-the-stage plays now, scenes stop when the
   student starts working, hidden tab freezes, none under
   prefers-reduced-motion. It speaks in .playing-* classes;
   this module watches them (MutationObserver) and performs.
   The eagle scene slot is the old 4.4s; inside it, three
   eagle performances rotate (never the same one twice in a
   row): the classic PERCH (swoop in, perch on the G, bob,
   fly off), the CARRY (grip the G with the talons, lift off
   carrying it, fly it across, set it back down gently from
   the other side, re-perch) and the KISS (perch, lean down,
   a gentle beak-touch kiss on the G with a small heart pop,
   a soft nuzzle, then off).

   The stage: a FIXED camera (no orbit, no zoom), a
   transparent backdrop (the page itself, like the 2D scene),
   the G standing at centre, a shadow-catcher floor. The
   eagle is visible only while his scene plays. The canvas
   is pointer-events:none, so taps land on the stage and
   page scroll is never touched.

   The eagle is a static museum scan (wings folded, no rig):
   he cannot flap — his flight legs are kept SHORT (in from
   just off-frame, act, out), never long glides. A rigged
   flapping eagle is a separate, already-agreed swap.

   NON-BLOCKING CONTRACT (kept from Waves 61/62): lazy import
   long after first paint; the 2D scene runs until the eagle
   model has loaded; any failure (no WebGL, a model error,
   the 30s watchdog) leaves the 2D jungle running untouched,
   silently; rendering pauses when the tab is hidden or the
   stage is off screen; the canvas is absolutely positioned
   inside the stage box and can never shift the composer or
   the answer cards.
   ========================================================================== */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const MODEL_V = '62';   // model URL pin — eagle.glb is unchanged since
                        // Wave 62 (the parked cats keep their own files;
                        // they are simply never requested now)
const modelURL = (name) => `/static/models/${name}.glb?v=${MODEL_V}`;
const LOAD_WATCHDOG_MS = 30000;

/* ------------------------- stage geometry -------------------------
   World units on the stage plane (z = 0). The G stands at
   centre on the ground, like the hero logo of the 2D stage. */
const LOGO_SCALE = 1.45;
const LOGO_W = 0.9196, LOGO_H = 0.835;      // the G crop's aspect (696x632)
const LOGO_REST_Y = (LOGO_H / 2) * LOGO_SCALE;   // G's feet on the ground
/* The glyph's top edge inside the crop (row 30 of 632),
   measured from the logo group's centre, in world units. */
const GLYPH_TOP_OFFSET = (0.5 - 30 / 632) * LOGO_H * LOGO_SCALE;
const G_TOP_Y = LOGO_REST_Y + GLYPH_TOP_OFFSET;
const EAGLE_FOOT_DROP = 0.054;   // fit origin is the tail tip; talons rest higher
const PERCH_Y = G_TOP_Y - EAGLE_FOOT_DROP;

const EAGLE_CFG = {
  label: 'Eagle',
  file: modelURL('eagle'),
  // The web eagle is KHR_mesh_quantization-encoded, so three.js
  // cannot measure it with Box3. The fit below was computed
  // offline from the float original (Wave 61) and reproduces
  // the prototype's fitByHeight result exactly.
  fitScale: 0.82919,
  fitPos: new THREE.Vector3(0.03496, -0.02661, 0.06267),
  faceOffset: 0            // museum scan faces +Z
};

/* ------------------------------- bootstrap --------------------------------- */
const stage = document.getElementById('scene-stage');
const container = document.getElementById('scene-3d');
if (!stage || !container) throw new Error('scene3d: no stage');

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
} catch (e) {
  throw new Error('scene3d: WebGL unavailable');
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
container.appendChild(renderer.domElement);

const scene = new THREE.Scene();
/* No background, no fog, no clearing: the eagle stands on the
   page itself, exactly where the 2D sprites stood. */

/* FIXED camera — the old stage's framing. It never moves:
   no orbit, no auto-rotate, no zoom. */
const camera = new THREE.PerspectiveCamera(42, 2, 0.1, 50);
camera.position.set(0, 1.45, 2.66);
camera.lookAt(0, 0.90, 0);
function sizeRenderer() {
  const w = container.clientWidth || stage.clientWidth || 300;
  const h = container.clientHeight || stage.clientHeight || 200;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
sizeRenderer();

/* --------------------------------- lighting -------------------------------- */
scene.add(new THREE.HemisphereLight(0xfff3dd, 0xcfa06a, 0.95));
const sun = new THREE.DirectionalLight(0xffe7bd, 1.7);
sun.position.set(4, 6.5, 4);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -4.5; sun.shadow.camera.right = 4.5;
sun.shadow.camera.top = 4.5;   sun.shadow.camera.bottom = -4.5;
sun.shadow.radius = 6;
scene.add(sun);
const fill = new THREE.DirectionalLight(0xdfeaff, 0.35);
fill.position.set(-4, 2.5, -3);
scene.add(fill);

/* Contact shadows only — an invisible floor that catches the
   eagle's shadow so he stands on the page, not floats. */
const shadowCatcher = new THREE.Mesh(
  new THREE.PlaneGeometry(30, 30), new THREE.ShadowMaterial({ opacity: 0.16 })
);
shadowCatcher.rotation.x = -Math.PI / 2;
shadowCatcher.receiveShadow = true;
scene.add(shadowCatcher);

/* ------------------------------ the G itself -------------------------------
   The play object is the logo's G and nothing else: two
   planes (front + back) carrying /static/logo-g-t.png — the
   G glyph cropped from the frozen original artwork, its
   paper background keyed to alpha. NO board, NO frame, NO
   feet: the mark stands on the page exactly as the 2D hero
   logo does. The eagle only ever MOVES it; the artwork
   itself is never edited, recoloured or redrawn.
   Transforms only. */
const logoGroup = new THREE.Group();
{
  const tex = new THREE.TextureLoader().load('/static/logo-g-t.png');
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  // Basic material: scene lighting must not wash out or tint
  // the artwork. alphaTest keeps the shadow glyph-shaped and
  // the soft keyed edge intact.
  const artMat = new THREE.MeshBasicMaterial({
    map: tex, transparent: true, alphaTest: 0.35
  });
  const artF = new THREE.Mesh(new THREE.PlaneGeometry(LOGO_W, LOGO_H), artMat);
  artF.position.z = 0.012; artF.castShadow = true;
  const artB = artF.clone(); artB.rotation.y = Math.PI; artB.position.z = -0.012;
  logoGroup.add(artF, artB);
}
logoGroup.scale.setScalar(LOGO_SCALE);
logoGroup.position.set(0, LOGO_REST_Y, 0);
scene.add(logoGroup);

/* The kiss's heart: a small canvas-drawn heart sprite that
   pops beside the G at the beak-touch moment (the old
   scene's playful tone), then rises and fades. */
const heart = (() => {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.translate(64, 62);
  g.beginPath();
  g.moveTo(0, 36);
  g.bezierCurveTo(-54, 2, -42, -36, -17, -36);
  g.bezierCurveTo(-6, -36, 0, -28, 0, -21);
  g.bezierCurveTo(0, -28, 6, -36, 17, -36);
  g.bezierCurveTo(42, -36, 54, 2, 0, 36);
  g.fillStyle = '#d94f3d';
  g.fill();
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({
    map: tex, transparent: true, depthWrite: false, opacity: 0
  }));
  sp.visible = false;
  sp.scale.setScalar(0.001);
  scene.add(sp);
  return sp;
})();

/* ------------------------------ tween engine -------------------------------
   Every tween is stamped with the current scene epoch. Bumping
   the epoch (scene cancelled / stage reset) resolves all
   pending tweens with `false`, and the routines bail at their
   next await — no orphaned motion, ever. */
let epoch = 0;
const activeTweens = new Set();
const easeInOut = (k) => k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
const easeOut = (k) => 1 - Math.pow(1 - k, 3);
function tweenRaw(dur, onUpdate, ease = easeInOut) {
  const ep = epoch;
  return new Promise((resolve) => {
    activeTweens.add({
      start: performance.now(), dur: Math.max(dur, 0.01) * 1000,
      onUpdate, ease, resolve, epoch: ep
    });
  });
}
const waitS = (s) => tweenRaw(s, () => {}, (k) => k);
function stepTweens(now) {
  for (const tw of [...activeTweens]) {
    if (tw.epoch !== epoch) { activeTweens.delete(tw); tw.resolve(false); continue; }
    const k = Math.min(1, (now - tw.start) / tw.dur);
    tw.onUpdate(tw.ease(k));
    if (k >= 1) { activeTweens.delete(tw); tw.resolve(true); }
  }
}
function lerpAngle(a, b, k) {
  let d = (b - a) % (Math.PI * 2);
  if (d > Math.PI) d -= Math.PI * 2;
  if (d < -Math.PI) d += Math.PI * 2;
  return a + d * k;
}

/* -------------------------------- the eagle -------------------------------- */
const loader = new GLTFLoader();
const actors = {};   // key -> { key, cfg, group, fit, faceYaw }
let eagleLoaded = false;
let loadFailed = false;

function loadEagle() {
  loader.load(EAGLE_CFG.file, (gltf) => {
    const root = gltf.scene;
    root.traverse((o) => { if (o.isMesh) o.castShadow = true; });
    root.scale.setScalar(EAGLE_CFG.fitScale);
    root.position.copy(EAGLE_CFG.fitPos);
    const fit = new THREE.Group();
    fit.add(root);
    const group = new THREE.Group();
    group.add(fit);
    group.visible = false;               // the eagle exists only inside his scene
    scene.add(group);
    actors.eagle = { key: 'eagle', cfg: EAGLE_CFG, group, fit, faceYaw: 0 };
    eagleLoaded = true;
    if (!loadFailed) activate3D();
  }, undefined, () => {
    // Silent fallback: the 2D scene simply stays.
    loadFailed = true;
    console.warn('scene3d: eagle failed to load, staying with the 2D scene');
  });
}

function faceNow(actor, yaw) {
  actor.faceYaw = yaw;
  actor.group.rotation.y = yaw + actor.cfg.faceOffset;
}
function setFacing(actor, yaw, k = 1) {
  actor.faceYaw = lerpAngle(actor.faceYaw, yaw, k);
  actor.group.rotation.y = actor.faceYaw + actor.cfg.faceOffset;
}
/* While the eagle carries the G, the G hangs from his talons:
   its top edge stays at the talons, trailing his x by a
   whisper, swaying gently. Call inside a tween's onUpdate
   AFTER the eagle's own position for the frame is set. */
function pinLogoToTalons(e, sway) {
  logoGroup.position.x = e.group.position.x * 0.94;
  logoGroup.position.y = e.group.position.y + EAGLE_FOOT_DROP - GLYPH_TOP_OFFSET;
  logoGroup.rotation.z = sway || 0;
}

/* ------------------------------ stage reset -------------------------------- */
function resetStage() {
  for (const key in actors) {
    const a = actors[key];
    a.group.visible = false;
    a.fit.position.set(0, 0, 0);
    a.fit.rotation.set(0, 0, 0);
    a.fit.scale.set(1, 1, 1);
  }
  logoGroup.position.set(0, LOGO_REST_Y, 0);
  logoGroup.rotation.set(0, 0, 0);
  logoGroup.scale.setScalar(LOGO_SCALE);
  logoGroup.visible = true;
  heart.visible = false;
  heart.material.opacity = 0;
}

/* ============================ THE EAGLE'S SCENES ===========================
   The director's eagle slot is the old 4.4s. Three
   performances rotate inside it — perch, carry, kiss —
   never the same one twice in a row. Every performance ends
   with the stage exactly as it started: the G at centre,
   the eagle gone. */

/* --- PERCH (the classic Scene A, 4.4s): glide in from the
   top-left, perch ON the G with a gentle bob, fly off
   top-right. The scan cannot flap, so the flight legs are
   SHORT hops from just off-frame; the perch — the heart of
   the scene — keeps its full ~2.5s. */
async function playEaglePerch() {
  const e = actors.eagle;
  if (!e) return;
  e.group.position.set(-2.3, 2.35, 0.3);
  e.group.visible = true;
  faceNow(e, Math.atan2(2.3, -0.3));
  // 0 -> 16%: glide down to the perch
  const sx = e.group.position.x, sy = e.group.position.y, sz = e.group.position.z;
  let ok = await tweenRaw(0.7, (k) => {
    e.group.position.set(
      sx + (0 - sx) * k,
      sy + (PERCH_Y - sy) * k + Math.sin(k * Math.PI) * 0.12,
      sz + (0 - sz) * k);
    setFacing(e, 0, 0.12);
  });
  if (!ok) return;
  faceNow(e, 0);
  // 16% -> 72%: perched, gentle bob (the old 30/44/58% dips)
  ok = await tweenRaw(2.47, (k) => {
    e.fit.position.y = Math.sin(k * Math.PI * 6) * 0.028;
    e.fit.rotation.z = Math.sin(k * Math.PI * 3) * 0.02;
  }, (k) => k);
  e.fit.position.y = 0; e.fit.rotation.z = 0;
  if (!ok) return;
  // 72% -> 100%: up and away to the right, out of frame
  const sx2 = e.group.position.x, sy2 = e.group.position.y;
  await tweenRaw(1.23, (k) => {
    e.group.position.set(
      sx2 + (2.4 - sx2) * k,
      sy2 + (2.45 - sy2) * k,
      0.3 * k);
    setFacing(e, Math.atan2(2.4, 0.3), 0.15);
  });
  e.group.visible = false;
}

/* --- CARRY (4.4s): the eagle grips the G WITH ITS TALONS,
   lifts off carrying it, flies it across the stage and sets
   it back down gently — coming in from the other side —
   then re-perches on it for a breath before darting off. */
async function playEagleCarry() {
  const e = actors.eagle;
  if (!e) return;
  e.group.position.set(-2.3, 2.35, 0.3);
  e.group.visible = true;
  faceNow(e, Math.atan2(2.3, -0.3));
  // arrive + perch (0.55s)
  const sx = e.group.position.x, sy = e.group.position.y, sz = e.group.position.z;
  let ok = await tweenRaw(0.55, (k) => {
    e.group.position.set(
      sx + (0 - sx) * k,
      sy + (PERCH_Y - sy) * k + Math.sin(k * Math.PI) * 0.10,
      sz + (0 - sz) * k);
    setFacing(e, 0, 0.12);
  });
  if (!ok) return;
  faceNow(e, 0);
  // the grip (0.20s): he crouches a touch, the G rises to meet his talons
  ok = await tweenRaw(0.20, (k) => {
    e.fit.position.y = -0.025 * k;
    logoGroup.position.y = LOGO_REST_Y + 0.035 * k;
  }, (k) => k);
  if (!ok) return;
  // lift off with the G (0.50s)
  ok = await tweenRaw(0.50, (k) => {
    e.group.position.y = PERCH_Y + 0.60 * k;
    e.fit.position.y = -0.025 * (1 - k);
    pinLogoToTalons(e, 0);
  });
  if (!ok) return;
  // carry across (1.00s): the G sways beneath him
  const cx = e.group.position.x, cy = e.group.position.y;
  ok = await tweenRaw(1.00, (k) => {
    e.group.position.x = cx + (1.80 - cx) * k;
    e.group.position.y = cy + Math.sin(k * Math.PI) * 0.12;
    setFacing(e, Math.PI / 2, 0.10);
    pinLogoToTalons(e, Math.sin(k * Math.PI * 2) * 0.06);
  }, (k) => k);
  if (!ok) return;
  // swing back toward home (0.65s), still carrying
  const bx = e.group.position.x, by = e.group.position.y;
  ok = await tweenRaw(0.65, (k) => {
    e.group.position.x = bx + (0.30 - bx) * k;
    e.group.position.y = by + (PERCH_Y + 0.28 - by) * k;
    setFacing(e, -Math.PI / 2, 0.10);
    pinLogoToTalons(e, Math.sin(k * Math.PI) * -0.04);
  }, (k) => k);
  if (!ok) return;
  // set it back down gently, from the other side (0.40s)
  const dx = e.group.position.x, dy = e.group.position.y;
  const lx = logoGroup.position.x, ly = logoGroup.position.y;
  const lrz = logoGroup.rotation.z;
  ok = await tweenRaw(0.40, (k) => {
    e.group.position.x = dx + (0.12 - dx) * k;
    e.group.position.y = dy + (PERCH_Y + 0.02 - dy) * k;
    setFacing(e, 0, 0.15);
    logoGroup.position.x = lx + (0 - lx) * k;
    logoGroup.position.y = ly + (LOGO_REST_Y - ly) * k;
    logoGroup.rotation.z = lrz * (1 - k);
  });
  logoGroup.position.set(0, LOGO_REST_Y, 0);
  logoGroup.rotation.z = 0;
  if (!ok) return;
  // re-perch on the G he just delivered (0.30s)
  const rx = e.group.position.x, ry = e.group.position.y;
  ok = await tweenRaw(0.30, (k) => {
    e.group.position.x = rx + (0 - rx) * k;
    e.group.position.y = ry + (PERCH_Y - ry) * k
      + Math.sin(k * Math.PI) * 0.05;
    e.fit.position.y = Math.sin(k * Math.PI * 2) * 0.012;
  }, (k) => k);
  e.fit.position.y = 0;
  if (!ok) return;
  // and off (0.80s)
  const ex = e.group.position.x, ey = e.group.position.y;
  await tweenRaw(0.80, (k) => {
    e.group.position.set(
      ex + (2.4 - ex) * k,
      ey + (2.45 - ey) * k,
      0.3 * k);
    setFacing(e, Math.atan2(2.4, 0.3), 0.15);
  });
  e.group.visible = false;
}

/* --- KISS / PYAAR (4.4s): perch, lean down and give the G
   a gentle beak-touch kiss — a small heart pops — then a
   soft nuzzle before he settles and flies off. */
async function playEagleKiss() {
  const e = actors.eagle;
  if (!e) return;
  e.group.position.set(-2.3, 2.35, 0.3);
  e.group.visible = true;
  faceNow(e, Math.atan2(2.3, -0.3));
  // arrive + perch (0.70s, the classic path)
  const sx = e.group.position.x, sy = e.group.position.y, sz = e.group.position.z;
  let ok = await tweenRaw(0.70, (k) => {
    e.group.position.set(
      sx + (0 - sx) * k,
      sy + (PERCH_Y - sy) * k + Math.sin(k * Math.PI) * 0.12,
      sz + (0 - sz) * k);
    setFacing(e, 0, 0.12);
  });
  if (!ok) return;
  faceNow(e, 0);
  // settle (0.30s): one small bob
  ok = await tweenRaw(0.30, (k) => {
    e.fit.position.y = Math.sin(k * Math.PI) * 0.02;
  }, (k) => k);
  e.fit.position.y = 0;
  if (!ok) return;
  // lean in (0.60s): his head dips toward the G's face
  ok = await tweenRaw(0.60, (k) => {
    e.fit.rotation.x = 0.36 * k;
    e.fit.position.y = -0.045 * k;
    e.fit.position.z = 0.05 * k;
  });
  if (!ok) return;
  // the kiss (0.70s): beak touches — a small heart pops,
  // rises and fades beside the G
  heart.position.set(0.38, G_TOP_Y + 0.30, 0.32);
  heart.visible = true;
  ok = await tweenRaw(0.70, (k) => {
    e.fit.rotation.x = 0.36 + Math.sin(k * Math.PI) * 0.03;
    if (k < 0.32) {
      const p = easeOut(k / 0.32);
      heart.scale.setScalar(0.30 * p);
      heart.material.opacity = p;
    } else {
      const p = (k - 0.32) / 0.68;
      heart.position.y = G_TOP_Y + 0.30 + 0.12 * p;
      heart.material.opacity = 1 - p * p;
    }
  }, (k) => k);
  heart.visible = false;
  heart.material.opacity = 0;
  if (!ok) return;
  // the nuzzle (0.60s): a soft side-to-side head rub
  ok = await tweenRaw(0.60, (k) => {
    e.fit.rotation.z = Math.sin(k * Math.PI * 2) * 0.07;
    e.fit.rotation.x = 0.36 - 0.06 * k;
  }, (k) => k);
  if (!ok) return;
  // straighten + a happy bob (0.50s)
  const lean = e.fit.rotation.x;
  ok = await tweenRaw(0.50, (k) => {
    e.fit.rotation.x = lean * (1 - k);
    e.fit.rotation.z = 0;
    e.fit.position.y = -0.045 * (1 - k) + Math.sin(k * Math.PI) * 0.03;
    e.fit.position.z = 0.05 * (1 - k);
  }, (k) => k);
  e.fit.rotation.set(0, 0, 0);
  e.fit.position.set(0, 0, 0);
  if (!ok) return;
  // and off (1.00s)
  const ex = e.group.position.x, ey = e.group.position.y;
  await tweenRaw(1.00, (k) => {
    e.group.position.set(
      ex + (2.4 - ex) * k,
      ey + (2.45 - ey) * k,
      0.3 * k);
    setFacing(e, Math.atan2(2.4, 0.3), 0.15);
  });
  e.group.visible = false;
}

const EAGLE_VARIANTS = [playEaglePerch, playEagleCarry, playEagleKiss];
let variantIdx = 0;
/* The director's one eagle scene, performed by the next
   variant in the rotation (perch -> carry -> kiss -> ...). */
async function playEagle() {
  const v = EAGLE_VARIANTS[variantIdx % EAGLE_VARIANTS.length];
  variantIdx++;
  return v();
}

const ROUTINES = { eagle: playEagle };

/* --------------------- director <-> 3D bridge ------------------------------
   The Wave 23 director owns ALL scheduling; it speaks in stage
   classes. We watch the classes: a scene class appearing starts
   the matching 3D performance; the class disappearing (scene
   over, student started typing, tab hidden and reset) cancels
   it and restores the stage. In 3D mode only the eagle class
   can appear — the other scenes were marked broken at
   activation, so their classes never get added. */
let currentScene = null;
function sceneFromClass() {
  for (const n of ['eagle', 'tiger', 'chase', 'lion']) {
    if (stage.classList.contains('playing-' + n)) return n;
  }
  return null;
}
function cancelScene() {
  epoch++;
  currentScene = null;
  resetStage();
}
let activated = false;
function onSceneClass() {
  if (!activated) return;
  const s = sceneFromClass();
  if (s === currentScene) return;
  cancelScene();
  if (s && ROUTINES[s] && actors.eagle) {
    currentScene = s;
    const ep = epoch;
    ROUTINES[s]().catch(() => {}).then(() => {
      if (epoch === ep) { currentScene = null; resetStage(); }
    });
  }
}
new MutationObserver(onSceneClass).observe(stage, {
  attributes: true, attributeFilter: ['class']
});

/* ------------------------------ activation ---------------------------------
   The swap happens ONCE, when the eagle model is in: the stage
   gets "scene-3d-on" (CSS hides the 2D sprites + logo img,
   fades the canvas in) and the performed rotation becomes
   eagle-only. Until then — and forever, if anything failed —
   the 2D Logo Jungle runs exactly as before. */
function activate3D() {
  if (activated || loadFailed) return;
  activated = true;
  stage.classList.add('scene-3d-on');
  window.__friendsReady = true;               // verification hook (prototype parity)
  window.__scene3d = { active: true, mode: 'oldscene', actors: ['eagle'] };
  /* Wave 62B: in 3D the eagle performs ALONE. Setting the
     flag first (the director's pickSceneName consults it when
     the no-repeat rule would otherwise empty the pool), then
     marking the other friends broken, leaves the eagle as the
     rotation's only scene. The 2D visit is untouched: the
     flag is never set there and the marks below never happen. */
  window.__sceneEagleOnly3D = true;
  if (window.__sceneSetBroken) {
    window.__sceneSetBroken('eagle', false);
    window.__sceneSetBroken('tiger', true);
    window.__sceneSetBroken('boy', true);
    window.__sceneSetBroken('lion', true);
  }
  onSceneClass();   // a 2D scene may be mid-play: if it is the eagle's, perform it in 3D
}
window.__scene3d = { active: false, actors: [] };

const watchdog = window.setTimeout(() => {
  if (!activated) loadFailed = true;          // too slow: stay 2D for this visit
}, LOAD_WATCHDOG_MS);

/* ------------------------------ render loop -------------------------------- */
let rafId = null;
let running = false;
let stageVisible = true;
const clock = new THREE.Clock();

function animate() {
  rafId = requestAnimationFrame(animate);
  if (!document.getElementById('scene-stage')) { stopForever(); return; }
  stepTweens(performance.now());
  renderer.render(scene, camera);
}
function startLoop() {
  if (running || !stageVisible || document.hidden) return;
  running = true;
  clock.getDelta();
  rafId = requestAnimationFrame(animate);
}
function stopLoop() {
  running = false;
  if (rafId) cancelAnimationFrame(rafId);
  rafId = null;
}
function stopForever() {
  stopLoop();
  window.clearTimeout(watchdog);
  epoch++;                       // cancel any scene in flight
  try { renderer.dispose(); } catch (e) { /* already gone */ }
}

document.addEventListener('visibilitychange', () => {
  if (document.hidden) stopLoop(); else startLoop();
});
if ('IntersectionObserver' in window) {
  new IntersectionObserver((entries) => {
    stageVisible = entries.some(en => en.isIntersecting);
    if (stageVisible) startLoop(); else stopLoop();
  }, { threshold: 0.05 }).observe(stage);
}
if ('ResizeObserver' in window) {
  new ResizeObserver(() => sizeRenderer()).observe(container);
}
window.addEventListener('resize', sizeRenderer);

/* Kick off: load the eagle — the ONLY model this scene uses.
   The loop runs from the start (behind the 2D scene,
   invisible) so the first frame is warm when the swap
   happens. */
loadEagle();
startLoop();
