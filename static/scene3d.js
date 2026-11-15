/* ============================================================================
   Wave 61 — the 3D Logo Jungle, live in the chat empty state.

   Ported from the verified local prototype (~/workspace/ganitra-3d-demo,
   REPORT-3D-PROTO.md §1–§12) into the SAME slot the 2D Logo Jungle has
   always used: #scene-stage inside #chat-empty. The four real models
   (lion, Mowgli, golden eagle, white tiger — the files Suraj downloaded
   from Sketchfab) play with the logo plaque exactly as in the prototype:
   the lion and the tiger push it like a ball, Mowgli carries it back and
   sets it down gently, and the eagle lives perched on it, taking off
   whenever the plaque moves and landing back when it settles. The logo
   artwork is the app's own /static/logo-full-t.png, used byte-for-byte
   as-is on the plaque face — never edited, recoloured or redrawn.

   NON-BLOCKING CONTRACT (hard rules):
   - This module is imported lazily by the bootstrap in index.html
     (idle callback + IntersectionObserver), long after first paint.
     The chat is fully usable before, during and without it.
   - The 2D scene stays on stage until ALL FOUR models have loaded;
     only then does the stage swap (class "scene-3d-on"). Any failure
     — no WebGL, a model error, a 30 s watchdog — leaves the 2D scene
     running untouched, silently.
   - Rendering pauses when the tab is hidden or the stage scrolls off
     screen, and stops for good when the empty state is removed
     (hideEmpty() deletes #chat-empty when chatting starts).
   - The canvas is absolutely positioned inside the stage box, so it
     can never shift the docked composer or the answer cards.
   - Drag-orbit: mouse drag (or a horizontal touch drag) orbits the
     camera; the canvas keeps `touch-action: pan-y`, so a vertical
     touch drag still scrolls the page — orbit never traps scrolling.
     No pinch/wheel zoom (it would fight page scroll); a slow idle
     auto-orbit resumes after 6 s, as in the prototype.
   ========================================================================== */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const MODEL_V = '61';   // model URL pin — bump with the wave that changes a model
const modelURL = (name) => `/static/models/${name}.glb?v=${MODEL_V}`;
const LOAD_WATCHDOG_MS = 30000;

const CHARACTERS = {
  lion: {
    label: 'Lion',
    file: modelURL('lion'),
    targetHeight: 1.02,
    home: new THREE.Vector3(-1.75, 0, 0.15),
    homeYaw: 0.9,
    faceOffset: -Math.PI / 2 // model geometry runs along +X (length axis)
  },
  boy: {
    label: 'Mowgli',
    file: modelURL('boy'),
    targetHeight: 1.38,
    home: new THREE.Vector3(1.7, 0, 0.1),
    homeYaw: -0.9,
    faceOffset: Math.PI / 2 // FBX export faces along -X
  },
  eagle: {
    label: 'Eagle',
    file: modelURL('eagle'),
    // Wave 61: the web eagle is KHR_mesh_quantization-encoded, so three.js
    // cannot measure it with Box3 (CPU-side it would read the raw uint16
    // attribute, not the dequantised bird). The fit below was computed
    // offline from the float original (world bbox height 0.8563 for
    // targetHeight 0.71) and reproduces the prototype's fitByHeight
    // result exactly: scale 0.82919, offset (0.03496, -0.02661, 0.06267).
    fitMode: 'manual',
    fitScale: 0.82919,
    fitPos: new THREE.Vector3(0.03496, -0.02661, 0.06267),
    home: new THREE.Vector3(0, 1.0, 0.55),   // load-time fallback; the perch logic rules
    homeYaw: 0,
    faceOffset: 0            // museum scan faces +Z
  },
  tiger: {
    label: 'Tiger',
    file: modelURL('tiger'),
    targetHeight: 1.06,
    home: new THREE.Vector3(1.8, 0, -1.5),
    homeYaw: -0.88,
    faceOffset: 0,
    fitMode: 'skinned'       // Box3 mis-measures this rig — fit from the skinned pose box
  },
};

/* Logo display spots the boy can carry the plaque to (centre clearing). */
const LOGO_SPOTS = [
  new THREE.Vector3(0, 0, 0.55),
  new THREE.Vector3(-0.95, 0, 0.2),
  new THREE.Vector3(0.95, 0, 0.2),
  new THREE.Vector3(0, 0, -0.75),
];
/* The app logo artwork is 900x478 (~1.88:1): plaque face 1.30 x 0.69. */
const PLAQUE_W = 1.30, PLAQUE_H = 0.69;
const LOGO_REST_Y = 0.49;    // plaque centre height when standing on the ground

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
scene.fog = new THREE.Fog(0xf7e8cd, 11, 22);

/* Camera: fixed framing of the clearing, orbited by azimuth/polar
   offsets (custom mini-orbit — see the header note on why OrbitControls
   is not used in the app). */
const CAM_TARGET = new THREE.Vector3(0, 0.72, 0);
const CAM_R = 6.3;
let camAz = 0.10, camPol = 1.22;          // current spherical angles
let azGoal = 0.10, polGoal = 1.22;        // drag goals (eased toward)
let autoOrbit = true, lastInteract = 0;
const camera = new THREE.PerspectiveCamera(42, 2, 0.1, 100);
function placeCamera() {
  camAz += (azGoal - camAz) * 0.08;
  camPol += (polGoal - camPol) * 0.08;
  camera.position.set(
    CAM_TARGET.x + CAM_R * Math.sin(camPol) * Math.sin(camAz),
    CAM_TARGET.y + CAM_R * Math.cos(camPol),
    CAM_TARGET.z + CAM_R * Math.sin(camPol) * Math.cos(camAz));
  camera.lookAt(CAM_TARGET);
}
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
sun.shadow.mapSize.set(1024, 1024);   // prototype used 2048; 1024 for phone GPUs
sun.shadow.camera.left = -6; sun.shadow.camera.right = 6;
sun.shadow.camera.top = 6;   sun.shadow.camera.bottom = -6;
sun.shadow.radius = 6;
scene.add(sun);
const fill = new THREE.DirectionalLight(0xdfeaff, 0.35);
fill.position.set(-4, 2.5, -3);
scene.add(fill);

/* ------------------------------ jungle clearing ---------------------------- */
const ground = new THREE.Mesh(
  new THREE.CircleGeometry(11, 48),
  new THREE.MeshStandardMaterial({ color: 0x9db38a, roughness: 1 })
);
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true;
scene.add(ground);
const clearing = new THREE.Mesh(
  new THREE.CircleGeometry(3.4, 48),
  new THREE.MeshStandardMaterial({ color: 0xefdcb2, roughness: 1 })
);
clearing.rotation.x = -Math.PI / 2; clearing.position.y = 0.005; clearing.receiveShadow = true;
scene.add(clearing);
const shadowCatcher = new THREE.Mesh(
  new THREE.CircleGeometry(3.4, 48), new THREE.ShadowMaterial({ opacity: 0.16 })
);
shadowCatcher.rotation.x = -Math.PI / 2; shadowCatcher.position.y = 0.01;
shadowCatcher.receiveShadow = true;
scene.add(shadowCatcher);

const trunkMat = new THREE.MeshStandardMaterial({ color: 0x8a5a2b, roughness: 1, flatShading: true });
const leafMats = [0x4e7a3a, 0x5d8a44, 0x6b9a4f].map(c =>
  new THREE.MeshStandardMaterial({ color: c, roughness: 1, flatShading: true }));
const rockMat = new THREE.MeshStandardMaterial({ color: 0xa89a86, roughness: 1, flatShading: true });
function makeTree(scale) {
  const g = new THREE.Group();
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.14, 1.3, 6), trunkMat);
  trunk.position.y = 0.65; trunk.castShadow = true; g.add(trunk);
  const blobs = 2 + Math.floor(Math.random() * 2);
  for (let i = 0; i < blobs; i++) {
    const r = 0.55 + Math.random() * 0.4;
    const leaf = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 0), leafMats[i % 3]);
    leaf.position.set((Math.random() - 0.5) * 0.7, 1.5 + i * 0.42, (Math.random() - 0.5) * 0.7);
    leaf.castShadow = true; g.add(leaf);
  }
  g.scale.setScalar(scale);
  return g;
}
for (let i = 0; i < 11; i++) {
  const a = (i / 11) * Math.PI * 2 + Math.random() * 0.4;
  const r = 5.6 + Math.random() * 2.6;
  const tree = makeTree(0.9 + Math.random() * 0.9);
  tree.position.set(Math.cos(a) * r, 0, Math.sin(a) * r);
  tree.rotation.y = Math.random() * Math.PI;
  scene.add(tree);
}
for (let i = 0; i < 5; i++) {
  const a = Math.random() * Math.PI * 2;
  const r = 3.9 + Math.random() * 1.6;
  const rock = new THREE.Mesh(new THREE.DodecahedronGeometry(0.16 + Math.random() * 0.16, 0), rockMat);
  rock.position.set(Math.cos(a) * r, 0.1, Math.sin(a) * r);
  rock.rotation.set(Math.random() * 3, Math.random() * 3, Math.random() * 3);
  rock.castShadow = true; rock.receiveShadow = true;
  scene.add(rock);
}
/* drifting golden dust motes */
const MOTES = 70;
const motePos = new Float32Array(MOTES * 3);
const moteSeed = [];
for (let i = 0; i < MOTES; i++) {
  motePos[i * 3] = (Math.random() - 0.5) * 9;
  motePos[i * 3 + 1] = 0.3 + Math.random() * 2.6;
  motePos[i * 3 + 2] = (Math.random() - 0.5) * 9;
  moteSeed.push(Math.random() * Math.PI * 2);
}
const moteGeo = new THREE.BufferGeometry();
moteGeo.setAttribute('position', new THREE.BufferAttribute(motePos, 3));
const motes = new THREE.Points(moteGeo, new THREE.PointsMaterial({
  color: 0xe8a33d, size: 0.05, transparent: true, opacity: 0.65, depthWrite: false
}));
scene.add(motes);

/* --------------------------- the logo "ball" -------------------------------
   The app's own logo artwork (/static/logo-full-t.png — the very file the
   2D empty state displays) is used EXACTLY as-is on a little wooden-framed
   plaque; characters only ever MOVE the plaque (push / carry / set down)
   — the artwork itself is never edited, recoloured or redrawn. The face
   plane behind the transparent artwork is the page cream, so the plaque
   reads exactly like the logo the student already knows. Transforms only. */
const logoGroup = new THREE.Group();
{
  const tex = new THREE.TextureLoader().load('/static/logo-full-t.png');
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  // Basic materials: scene lighting must not wash out or tint the logo.
  const faceMat = new THREE.MeshBasicMaterial({ color: 0xfdf6ec });
  const artMat = new THREE.MeshBasicMaterial({ map: tex, transparent: true });
  const W = PLAQUE_W, H = PLAQUE_H;
  const faceF = new THREE.Mesh(new THREE.PlaneGeometry(W, H), faceMat);
  faceF.position.z = 0.031;
  const artF = new THREE.Mesh(new THREE.PlaneGeometry(W, H), artMat);
  artF.position.z = 0.034; artF.castShadow = true;
  const faceB = faceF.clone(); faceB.rotation.y = Math.PI; faceB.position.z = -0.031;
  const artB = artF.clone(); artB.rotation.y = Math.PI; artB.position.z = -0.034;
  const frame = new THREE.Mesh(
    new THREE.BoxGeometry(W + 0.16, H + 0.14, 0.06),
    new THREE.MeshStandardMaterial({ color: 0x8a5a2b, roughness: 0.85 })
  );
  frame.castShadow = true;
  const footL = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.1, 0.22), frame.material);
  footL.position.set(-0.5, -H / 2 - 0.08, 0);
  const footR = footL.clone(); footR.position.x = 0.5;
  logoGroup.add(frame, faceF, artF, faceB, artB, footL, footR);
}
let logoHome = LOGO_SPOTS[0].clone();
let logoYaw = 0;
logoGroup.position.set(logoHome.x, LOGO_REST_Y, logoHome.z);
scene.add(logoGroup);

/* ------------------------------ tween engine ------------------------------- */
const activeTweens = new Set();
const easeInOut = (k) => k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
const easeOut = (k) => 1 - Math.pow(1 - k, 3);
function tween(dur, onUpdate, ease = easeInOut) {
  return new Promise((resolve) => {
    activeTweens.add({ start: performance.now(), dur: Math.max(dur, 0.01) * 1000, onUpdate, ease, resolve });
  });
}
const wait = (s) => tween(s, () => {}, (k) => k);
function stepTweens(now) {
  for (const tw of [...activeTweens]) {
    const k = Math.min(1, (now - tw.start) / tw.dur);
    tw.onUpdate(tw.ease(k));
    if (k >= 1) { activeTweens.delete(tw); tw.resolve(); }
  }
}
function lerpAngle(a, b, k) {
  let d = (b - a) % (Math.PI * 2);
  if (d > Math.PI) d -= Math.PI * 2;
  if (d < -Math.PI) d += Math.PI * 2;
  return a + d * k;
}

/* ------------------------------- actors ------------------------------------ */
const loader = new GLTFLoader();
const actors = {};   // key -> { group, fit, mixer, busy, faceOffset, cfg }
let loadedCount = 0;
let loadFailed = false;

function fitByHeight(obj, targetHeight) {
  const box = new THREE.Box3().setFromObject(obj);
  const size = box.getSize(new THREE.Vector3());
  const centre = box.getCenter(new THREE.Vector3());
  const s = targetHeight / (size.y || 1);
  obj.scale.setScalar(s);
  obj.position.set(-centre.x * s, -box.min.y * s, -centre.z * s);
  const fit = new THREE.Group();
  fit.add(obj);
  return fit;
}

/* Skinned rigs: Box3.setFromObject reads raw geometry bounds, which for
   the tiger's Maya-style rig gives a nonsense box. Fit from the skinned
   pose box instead — what the renderer will actually draw. */
function fitBySkinnedBox(obj, targetHeight) {
  obj.updateMatrixWorld(true);
  const box = new THREE.Box3();
  obj.traverse((o) => {
    if (o.isSkinnedMesh) {
      if (o.skeleton) o.skeleton.update();
      o.computeBoundingBox();
      box.union(o.boundingBox.clone().applyMatrix4(o.matrixWorld));
    }
  });
  const size = box.getSize(new THREE.Vector3());
  const centre = box.getCenter(new THREE.Vector3());
  const s = targetHeight / (size.y || 1);
  obj.scale.setScalar(s);
  obj.position.set(-centre.x * s, -box.min.y * s, -centre.z * s);
  const fit = new THREE.Group();
  fit.add(obj);
  return fit;
}

/* Pre-measured fit (eagle — see CHARACTERS note): the numbers come from
   the float original, so the quantised web build lands exactly where
   the prototype's Box3 fit put it. */
function fitManual(obj, cfg) {
  obj.scale.setScalar(cfg.fitScale);
  obj.position.copy(cfg.fitPos);
  const fit = new THREE.Group();
  fit.add(obj);
  return fit;
}

function fitActor(obj, cfg) {
  if (cfg.fitMode === 'skinned') return fitBySkinnedBox(obj, cfg.targetHeight);
  if (cfg.fitMode === 'manual') return fitManual(obj, cfg);
  return fitByHeight(obj, cfg.targetHeight);
}

function loadActor(key) {
  const cfg = CHARACTERS[key];
  loader.load(cfg.file, (gltf) => {
    const root = gltf.scene;
    root.traverse((o) => { if (o.isMesh) o.castShadow = true; });
    const fit = fitActor(root, cfg);
    const group = new THREE.Group();
    group.add(fit);
    group.position.copy(cfg.home);
    group.rotation.y = cfg.homeYaw + cfg.faceOffset;
    scene.add(group);
    const actor = { key, cfg, group, fit, mixer: null, busy: false, faceYaw: cfg.homeYaw };
    if (gltf.animations && gltf.animations.length) {
      actor.mixer = new THREE.AnimationMixer(root);
      actor.mixer.clipAction(gltf.animations[0]).setLoop(THREE.LoopRepeat).play();
    }
    group.userData.actorKey = key;
    actors[key] = actor;
    if (key === 'eagle') { setEagleState('perched'); snapEagleToPerch(); }
    loadedCount++;
    if (loadedCount === 4 && !loadFailed) activate3D();
  }, undefined, () => {
    // Silent fallback: the 2D scene simply stays. (No console noise in
    // production beyond this single line; the chat is unaffected.)
    loadFailed = true;
    console.warn('scene3d: model failed to load, staying with the 2D scene:', key);
  });
}

/* --------------------------- movement helpers ------------------------------ */
function setFacing(actor, yaw, k = 1) {
  actor.faceYaw = lerpAngle(actor.faceYaw, yaw, k);
  actor.group.rotation.y = actor.faceYaw + actor.cfg.faceOffset;
}
async function walkTo(actor, dest, { speed = 1.15, faceAtEnd = null } = {}) {
  const start = actor.group.position.clone();
  const dist = Math.hypot(dest.x - start.x, dest.z - start.z);
  if (dist < 0.02) { if (faceAtEnd !== null) await turnTo(actor, faceAtEnd); return; }
  const travelYaw = Math.atan2(dest.x - start.x, dest.z - start.z);
  const dur = dist / speed;
  const bobAmp = actor.key === 'boy' ? 0.045 : 0.025;
  await tween(dur, (k) => {
    actor.group.position.set(
      start.x + (dest.x - start.x) * k, 0, start.z + (dest.z - start.z) * k);
    setFacing(actor, travelYaw, 0.25);
    actor.fit.position.y = Math.abs(Math.sin(k * dist * 5.2)) * bobAmp;
    actor.fit.rotation.z = Math.sin(k * dist * 5.2) * 0.035;
  }, (k) => k);
  actor.fit.position.y = 0; actor.fit.rotation.z = 0;
  if (faceAtEnd !== null) await turnTo(actor, faceAtEnd);
}
async function turnTo(actor, yaw, dur = 0.45) {
  const from = actor.faceYaw;
  await tween(dur, (k) => {
    actor.faceYaw = lerpAngle(from, yaw, k);
    actor.group.rotation.y = actor.faceYaw + actor.cfg.faceOffset;
  }, (k) => k);
}
async function hop(actor, height = 0.32) {
  await tween(0.55, (k) => {
    actor.fit.position.y = Math.sin(k * Math.PI) * height;
    const sq = 1 - 0.13 * Math.sin(k * Math.PI * 2);
    actor.fit.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq));
  }, (k) => k);
  actor.fit.position.y = 0; actor.fit.scale.set(1, 1, 1);
}
function logoWobble(strength = 1) {
  return tween(0.9, (k) => {
    logoGroup.rotation.z = Math.sin(k * Math.PI * 3) * 0.1 * (1 - k) * strength;
    logoGroup.rotation.x = Math.sin(k * Math.PI * 2) * 0.05 * (1 - k) * strength;
  }, (k) => k).then(() => { logoGroup.rotation.z = 0; logoGroup.rotation.x = 0; });
}

/* ------------------------------ play routines ------------------------------ */
async function lionPush() {
  const lion = actors.lion;
  if (!lion || lion.busy) return;
  lion.busy = true;
  try {
    const lp = logoGroup.position;
    const away = new THREE.Vector3(lp.x - lion.group.position.x, 0, lp.z - lion.group.position.z).normalize();
    const standAt = new THREE.Vector3(lp.x - away.x * 0.95, 0, lp.z - away.z * 0.95);
    await walkTo(lion, standAt, { speed: 1.0 });
    await turnTo(lion, Math.atan2(away.x, away.z));
    await wait(0.25);
    const slideFrom = logoGroup.position.clone();
    const slideTo = slideFrom.clone().addScaledVector(away, 0.6);
    const r = Math.hypot(slideTo.x, slideTo.z);
    if (r > 2.0) slideTo.multiplyScalar(2.0 / r);
    const yawFrom = logoYaw; logoYaw += 0.45;
    await Promise.all([
      tween(0.35, (k) => { lion.fit.rotation.x = Math.sin(k * Math.PI) * 0.16; }, (k) => k),
      tween(0.8, (k) => {
        logoGroup.position.x = slideFrom.x + (slideTo.x - slideFrom.x) * k;
        logoGroup.position.z = slideFrom.z + (slideTo.z - slideFrom.z) * k;
        logoGroup.rotation.y = yawFrom + (logoYaw - yawFrom) * k;
        logoGroup.rotation.z = Math.sin(k * Math.PI * 2) * 0.08 * (1 - k);
      }, easeOut),
    ]);
    lion.fit.rotation.x = 0; logoGroup.rotation.z = 0;
    logoHome.copy(slideTo);
    await hop(lion, 0.26);
    await walkTo(lion, lion.cfg.home, { speed: 1.05, faceAtEnd: lion.cfg.homeYaw });
  } finally { lion.busy = false; }
}

let carrying = false;
async function boyCarry() {
  const boy = actors.boy;
  if (!boy || boy.busy) return;
  boy.busy = true;
  try {
    const lp = logoGroup.position.clone();
    const side = new THREE.Vector3(boy.group.position.x - lp.x, 0, boy.group.position.z - lp.z)
      .normalize().multiplyScalar(0.62);
    await walkTo(boy, new THREE.Vector3(lp.x + side.x, 0, lp.z + side.z), { speed: 1.25 });
    await turnTo(boy, Math.atan2(-side.x, -side.z));
    await wait(0.2);
    carrying = true;
    await wait(0.45);
    const choices = LOGO_SPOTS.filter(s => s.distanceTo(logoHome) > 0.4);
    const spot = choices[Math.floor(Math.random() * choices.length)].clone();
    await walkTo(boy, new THREE.Vector3(spot.x + side.x * 0.9, 0, spot.z + side.z * 0.9), { speed: 1.0 });
    await turnTo(boy, Math.atan2(-side.x, -side.z));
    const from = logoGroup.position.clone();
    carrying = false;
    await tween(0.7, (k) => {
      logoGroup.position.set(
        from.x + (spot.x - from.x) * k,
        from.y + (LOGO_REST_Y - from.y) * k,
        from.z + (spot.z - from.z) * k);
      logoGroup.rotation.y = lerpAngle(logoGroup.rotation.y, 0, k * 0.4);
    });
    logoYaw = logoGroup.rotation.y;
    logoHome.copy(spot);
    await logoWobble(0.6);
    await hop(boy, 0.3);
    await walkTo(boy, boy.cfg.home, { speed: 1.25, faceAtEnd: boy.cfg.homeYaw });
  } finally { boy.busy = false; carrying = false; }
}

async function tigerPush() {
  const tiger = actors.tiger;
  if (!tiger || tiger.busy) return;
  tiger.busy = true;
  try {
    const lp = logoGroup.position;
    const away = new THREE.Vector3(lp.x - tiger.group.position.x, 0, lp.z - tiger.group.position.z).normalize();
    const standAt = new THREE.Vector3(lp.x - away.x * 1.0, 0, lp.z - away.z * 1.0);
    await walkTo(tiger, standAt, { speed: 0.8 });
    await turnTo(tiger, Math.atan2(away.x, away.z));
    await wait(0.3);
    const slideFrom = logoGroup.position.clone();
    const slideTo = slideFrom.clone().addScaledVector(away, 0.55);
    const r = Math.hypot(slideTo.x, slideTo.z);
    if (r > 2.0) slideTo.multiplyScalar(2.0 / r);
    const yawFrom = logoYaw; logoYaw -= 0.4;
    await Promise.all([
      tween(0.35, (k) => { tiger.fit.rotation.x = Math.sin(k * Math.PI) * 0.14; }, (k) => k),
      tween(0.8, (k) => {
        logoGroup.position.x = slideFrom.x + (slideTo.x - slideFrom.x) * k;
        logoGroup.position.z = slideFrom.z + (slideTo.z - slideFrom.z) * k;
        logoGroup.rotation.y = yawFrom + (logoYaw - yawFrom) * k;
        logoGroup.rotation.z = Math.sin(k * Math.PI * 2) * 0.08 * (1 - k);
      }, easeOut),
    ]);
    tiger.fit.rotation.x = 0; logoGroup.rotation.z = 0;
    logoHome.copy(slideTo);
    await hop(tiger, 0.34);
    await walkTo(tiger, tiger.cfg.home, { speed: 1.05, faceAtEnd: tiger.cfg.homeYaw });
  } finally { tiger.busy = false; }
}

/* ------------------------------- the eagle ---------------------------------
   He lives ON the logo plaque — talons directly on the plaque's wooden
   frame (the driftwood perch fused into his museum scan was removed in
   the prototype work, REPORT-3D-PROTO.md §12). While perched he rides
   the plaque; the moment the friends move the "ball" he takes off,
   circles above, and lands back once it settles. His own game is a
   swoop: a wide circle, a low pass that brushes the plaque into a
   wobble, then back to his perch. */
const EAGLE_PERCH_LIFT = (PLAQUE_H + 0.14) / 2;   // plaque centre -> top of its frame (0.415)
const EAGLE_FOOT_DROP = 0.054;   // fit origin is the model's lowest point (tail tip); talons rest higher
let eagleState = 'perched';      // 'perched' | 'flying'
function setEagleState(s) { eagleState = s; window.__eaglePerched = (s === 'perched'); }
window.__eaglePerched = true;
const lastLogoPos = new THREE.Vector3(1e9, 0, 0);

function perchPoint(out) {
  out.copy(logoGroup.position);
  out.y = logoGroup.position.y + EAGLE_PERCH_LIFT - EAGLE_FOOT_DROP;
  return out;
}
function snapEagleToPerch() {
  const e = actors.eagle;
  if (!e) return;
  perchPoint(e.group.position);
  e.faceYaw = logoGroup.rotation.y;
  e.group.rotation.y = e.faceYaw + e.cfg.faceOffset;
}
async function flyTo(eagle, dest, dur = 1.4, arc = 0.6) {
  const from = eagle.group.position.clone();
  const travelYaw = Math.atan2(dest.x - from.x, dest.z - from.z);
  await tween(dur, (k) => {
    eagle.group.position.lerpVectors(from, dest, k);
    eagle.group.position.y += Math.sin(k * Math.PI) * arc;
    setFacing(eagle, travelYaw, 0.18);
    eagle.fit.rotation.z = Math.sin(k * Math.PI * 2) * 0.1;
  }, (k) => k);
  eagle.fit.rotation.z = 0;
}
async function eagleScatter() {
  const e = actors.eagle;
  if (!e || e.busy || eagleState !== 'perched') return;
  e.busy = true; setEagleState('flying');
  try {
    const hover = new THREE.Vector3(logoGroup.position.x * 0.4, 3.1, logoGroup.position.z * 0.4 - 0.6);
    await flyTo(e, hover, 1.1, 0.8);
    let waited = 0;
    while (waited < 12000 &&
           (carrying || logoGroup.position.distanceToSquared(lastLogoPos) > 0.0004)) {
      const a0 = waited / 1100;
      await tween(1.3, (k) => {
        const a = a0 + k * Math.PI * 1.5;
        e.group.position.set(
          hover.x + Math.sin(a) * 0.75,
          hover.y + Math.sin(k * Math.PI * 2) * 0.07,
          hover.z + Math.cos(a) * 0.75);
        setFacing(e, Math.atan2(Math.cos(a), -Math.sin(a)), 0.3);
        e.fit.rotation.z = -0.22;
      }, (k) => k);
      waited += 1300;
    }
    e.fit.rotation.z = 0;
    await flyTo(e, perchPoint(new THREE.Vector3()), 1.2, 0.5);
    setEagleState('perched');
    snapEagleToPerch();
  } finally { e.busy = false; }
}
async function eagleSwoop() {
  const e = actors.eagle;
  if (!e || e.busy) return;
  e.busy = true; setEagleState('flying');
  try {
    const c = logoGroup.position.clone();
    await flyTo(e, new THREE.Vector3(c.x - 2.3, 2.5, c.z - 1.7), 1.3, 0.8);
    await flyTo(e, new THREE.Vector3(c.x, 1.6, c.z), 1.0, 0.3);
    logoWobble(0.9);
    await flyTo(e, new THREE.Vector3(c.x + 2.1, 2.4, c.z + 1.5), 1.1, 0.7);
    await flyTo(e, perchPoint(new THREE.Vector3()), 1.3, 0.6);
    setEagleState('perched');
    snapEagleToPerch();
  } finally { e.busy = false; }
}

/* --------------------------- tap + drag on canvas -------------------------- */
const raycaster = new THREE.Raycaster();
let downX = 0, downY = 0, downTime = 0, dragging = false;
const cvs = renderer.domElement;
cvs.addEventListener('pointerdown', (e) => {
  downX = e.clientX; downY = e.clientY; downTime = performance.now();
  dragging = true; autoOrbit = false; lastInteract = performance.now();
});
cvs.addEventListener('pointermove', (e) => {
  if (!dragging) return;
  const dx = e.movementX || 0, dy = e.movementY || 0;
  azGoal = THREE.MathUtils.clamp(azGoal + dx * 0.005, -1.15, 1.35);
  polGoal = THREE.MathUtils.clamp(polGoal + dy * 0.003, 0.95, 1.42);
  lastInteract = performance.now();
});
window.addEventListener('pointerup', (e) => {
  if (!dragging) return;
  dragging = false;
  lastInteract = performance.now();
  const moved = Math.hypot(e.clientX - downX, e.clientY - downY);
  if (moved > 7 || performance.now() - downTime > 350) return;   // it was a drag
  if (e.target !== cvs) return;
  const rect = cvs.getBoundingClientRect();
  const ndc = new THREE.Vector2(
    ((e.clientX - rect.left) / rect.width) * 2 - 1,
    -((e.clientY - rect.top) / rect.height) * 2 + 1);
  raycaster.setFromCamera(ndc, camera);
  for (const key of ['lion', 'boy', 'tiger', 'eagle']) {
    const a = actors[key];
    if (a && raycaster.intersectObject(a.group, true).length) { tapReact(a); return; }
  }
  if (raycaster.intersectObject(logoGroup, true).length) { logoWobble(1); return; }
  playRandom();   // tap on empty clearing: a friend plays (the 2D tap behaviour)
});
async function tapReact(actor) {
  if (actor.busy) return;
  actor.busy = true;
  try {
    if (actor.key === 'lion') {
      await hop(actor, 0.3);
    } else if (actor.key === 'tiger') {
      await hop(actor, 0.34);
    } else if (actor.key === 'eagle') {
      const from = actor.fit.rotation.y;
      await tween(0.55, (k) => {
        actor.fit.position.y = Math.abs(Math.sin(k * Math.PI * 2)) * 0.07;
        actor.fit.rotation.y = from + Math.sin(k * Math.PI * 4) * 0.13;
      }, (k) => k);
      actor.fit.rotation.y = from; actor.fit.position.y = 0;
    } else {
      const from = actor.fit.rotation.y;
      await Promise.all([
        hop(actor, 0.38),
        tween(0.6, (k) => { actor.fit.rotation.y = from + k * Math.PI * 2; }, (k) => k),
      ]);
      actor.fit.rotation.y = from;
    }
  } finally { actor.busy = false; }
}

/* ------------------------------ idle play loop ----------------------------- */
const ROUTINES = { lion: lionPush, boy: boyCarry, tiger: tigerPush, eagle: eagleSwoop };
let lastPlayer = null;
let nextPlayAt = performance.now() + 6000;
function playRandom() {
  const ready = Object.keys(ROUTINES).filter(k => actors[k] && !actors[k].busy);
  if (!ready.length) return;
  const choices = ready.filter(k => k !== lastPlayer);
  const pick = choices[Math.floor(Math.random() * choices.length)] || ready[0];
  lastPlayer = pick;
  nextPlayAt = performance.now() + 10000 + Math.random() * 7000;
  ROUTINES[pick]().catch(() => {});
}
function idleScheduler(now) {
  if (document.hidden || now < nextPlayAt) return;
  if (!Object.keys(actors).length) { nextPlayAt = now + 2500; return; }
  playRandom();
}

/* ------------------------------ activation ---------------------------------
   The swap happens ONCE, when every model is in: the stage gets the
   "scene-3d-on" class (CSS hides the 2D sprites + logo img, fades the
   canvas in). Until then — and forever, if anything failed — the 2D
   Logo Jungle runs exactly as before. */
let activated = false;
function activate3D() {
  if (activated || loadFailed) return;
  activated = true;
  stage.classList.add('scene-3d-on');
  window.__friendsReady = true;               // verification hook (prototype parity)
  window.__scene3d = { active: true, actors: Object.keys(actors) };
  nextPlayAt = performance.now() + 2500;      // first 3D play lands quickly
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
  const dt = Math.min(clock.getDelta(), 0.05);
  const t = clock.elapsedTime;
  const now = performance.now();

  stepTweens(now);
  if (activated) idleScheduler(now);

  for (const key in actors) {
    const a = actors[key];
    if (a.mixer) a.mixer.update(dt);
    if (!a.busy) a.fit.position.y = Math.sin(t * 1.6 + (key === 'boy' ? 2 : 0)) * 0.02;
  }
  const eg = actors.eagle;
  if (eg && eagleState === 'perched' && !eg.busy) {
    if (carrying || logoGroup.position.distanceToSquared(lastLogoPos) > 0.0004) {
      eagleScatter().catch(() => {});
    } else {
      snapEagleToPerch();
    }
  }
  lastLogoPos.copy(logoGroup.position);

  if (carrying && actors.boy) {
    const boy = actors.boy;
    const dir = new THREE.Vector3(Math.sin(boy.faceYaw), 0, Math.cos(boy.faceYaw));
    const anchor = boy.group.position.clone().addScaledVector(dir, 0.45);
    logoGroup.position.lerp(new THREE.Vector3(anchor.x, 0.90, anchor.z), 0.12);
    logoGroup.rotation.y = lerpAngle(logoGroup.rotation.y, boy.faceYaw, 0.12);
  }
  const pos = moteGeo.attributes.position;
  for (let i = 0; i < MOTES; i++) {
    pos.array[i * 3 + 1] += Math.sin(t * 0.7 + moteSeed[i]) * 0.0009;
    pos.array[i * 3] += Math.cos(t * 0.4 + moteSeed[i]) * 0.0007;
  }
  pos.needsUpdate = true;

  if (!autoOrbit && now - lastInteract > 6000) autoOrbit = true;
  if (autoOrbit && !dragging) azGoal += 0.0006 * (dt * 60);   // ~0.036 rad/s gentle orbit
  placeCamera();
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

/* Kick off: load all four models in parallel; the loop runs from the
   start (behind the 2D scene, invisible) so the first frame is warm
   when the swap happens. */
loadActor('lion');
loadActor('boy');
loadActor('eagle');
loadActor('tiger');
startLoop();
