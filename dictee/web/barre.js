// Canard Dictée — la barre flottante (animations reprises du design « Canard Dictée »).
// Les costumes (mots, couleurs, personnalités) sont dans costumes.js.
'use strict';

const $ = id => document.getElementById(id);
const R = {};
['tearL', 'tearR', 'ring1', 'ring2', 'duck', 'body', 'belly', 'head', 'headBall', 'face', 'hat',
 'eyeL', 'eyeR', 'pupilL', 'pupilR', 'mouth', 'beakLow', 'lidL', 'lidR', 'snot', 'z1', 'z2', 'z3'].forEach(k => R[k] = $(k));

// ------------------------------------------------------------------ détection des mots magiques
// Texte simplifié : minuscules, sans accents, sans ponctuation, entouré d'espaces.
function simplifier(t) {
  return ' ' + t.toLowerCase().replace(/œ/g, 'oe').replace(/æ/g, 'ae')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, ' ').trim() + ' ';
}
const singulier = m => m.length > 3 && /[sx]$/.test(m) ? m.slice(0, -1) : m;

// Le costume le plus évident : celui qui a le plus de mots trouvés
// (à égalité, celui dont un mot vient en premier). null si aucun.
function trouverCostume(texte) {
  const t = simplifier(texte);
  const mots = t.trim().split(' ');
  let meilleur = null;
  MAGIC.forEach(c => {
    let score = 0, premier = Infinity;
    c.mots.forEach(entree => {
      let pos;
      if (entree.includes(' ')) {                        // expression
        const i = t.indexOf(' ' + entree + ' ');
        pos = i < 0 ? -1 : t.slice(0, i).split(' ').length - 1;
      } else if (entree.endsWith('*')) {                  // début de mot
        const debut = entree.slice(0, -1);
        pos = mots.findIndex(m => m.startsWith(debut));
      } else {                                            // mot exact, pluriel accepté
        pos = mots.findIndex(m => m === entree || singulier(m) === entree);
      }
      if (pos >= 0) { score += entree.includes(' ') ? 2 : 1; premier = Math.min(premier, pos); }
    });
    if (score > 0 && (!meilleur || score > meilleur.score
        || (score === meilleur.score && premier < meilleur.premier)))
      meilleur = { key: c.key, msg: c.msg, score, premier };
  });
  return meilleur;
}

let pont = null;
const S = {                     // état de l'interface
  ecoute: false, reflechit: false, pret: false, reglages: {}, navs: [], nomTouche: 'Ctrl droit',
  panel: false, help: false, sub: null, crying: false, skin: null, dodo: 10,
  costume: null, costumeMsg: null, quack: false, msg: null, maxPanneau: 600
};
let niveau = 0, mx = -1e4, my = -1e4;
let amp = 0, nextBlink = 2, blinkEnd = 0, spinStart = null, wantSpin = false, openAt = null, enterAt = null, ewig = 0;
// sommeil
let dort = false, debutSommeil = 0, dernierGeste = 0, reveilAt = null, profond = false, baille = 0, yeuxSommeil = 1, hocheTete = 0, popTw = 0;
// physique (pompon du bonnet de Noël, cravache), apparition des briques
let pere = null, crop = null, oreilles = null, cosAt = 0, dernierCos = null;
let timers = {};
const now = () => performance.now() / 1000;
const nomSkin = m => m.word;

// ------------------------------------------------------------------ rendu
let couleursDe = undefined;
function majCostume() {
  document.querySelectorAll('.cos').forEach(el => el.style.display = el.dataset.cos === S.costume ? 'contents' : 'none');
  R.hat.style.display = S.costume ? 'none' : 'block';
  if (couleursDe !== S.costume) { couleursDe = S.costume; appliquerCouleurs(R, S.costume); }
}

function majBulles() {
  const libre = !S.panel && !S.help && !S.crying;
  const reflexion = S.reflechit && !S.ecoute && libre;
  $('bulle-reflexion').classList.toggle('cache', !reflexion);
  $('bulle-pleurs').classList.toggle('cache', !S.crying);
  const texte = S.quack ? 'Coin !' : S.ecoute ? 'Je t’écoute…' : (S.costumeMsg || S.msg);
  const visible = libre && !reflexion && !!texte;
  $('bulle').classList.toggle('cache', !visible);
  if (visible) $('bulle').textContent = texte;
  requestAnimationFrame(signalerTaille);
}

// Les cartes (paramètres / aide) entrent et sortent en douceur.
// Passer de l'une à l'autre : l'ancienne s'en va, la nouvelle arrive juste après.
let carteAffichee = null;
const SORTIE_MS = 170;
function majCartes() {
  const voulue = S.panel ? 'panneau' : S.help ? 'aide' : null;
  if (voulue === carteAffichee) return;
  const ancienne = carteAffichee ? $(carteAffichee) : null;
  if (ancienne) {
    ancienne.classList.remove('entree', 'apres');
    ancienne.classList.add('sortie');
    setTimeout(() => {
      if (carteAffichee !== ancienne.id) { ancienne.classList.add('cache'); ancienne.classList.remove('sortie'); }
      signalerTaille();
    }, SORTIE_MS);
  }
  carteAffichee = voulue;
  if (voulue) {
    const n = $(voulue);
    n.classList.remove('cache', 'sortie', 'entree', 'apres');
    void n.offsetWidth;                                // relance l'animation
    n.classList.add('entree');
    if (ancienne) n.classList.add('apres');            // attend que l'autre soit partie
    n.scrollTop = 0;
  }
}

// Les sous-menus sont construits une seule fois (tant que rien ne change),
// puis s'ouvrent et se ferment en glissant.
// « Skin du canard » : une grille de petites têtes, en premier.
function navsAvecSkin() {
  return [{ cle: 'skin', icone: 'palette', titre: 'Skin du canard', valeur: S.skin,
            options: [[null, 'Cowboy'], ...MAGIC.map(m => [m.key, nomSkin(m)])] }, ...S.navs];
}
let signatureNavs = '';
function construireNavs() {
  const liste = navsAvecSkin();
  const sig = JSON.stringify(liste);
  if (sig === signatureNavs) return;
  signatureNavs = sig;
  const navs = $('navs');
  navs.textContent = '';
  liste.forEach(n => {
    const grille = n.cle === 'skin';
    const bloc = document.createElement('div');
    bloc.className = 'bloc-nav';
    bloc.dataset.cle = n.cle;
    const sel = n.options.find(o => o[0] === n.valeur);
    const b = document.createElement('button');
    b.className = 'nav';
    b.innerHTML = `<span class="ico" style="font-size:21px;color:#c9c9ce">${n.icone}</span><div class="titre"></div><span class="val"></span><span class="ico chev">chevron_right</span>`;
    b.querySelector('.titre').textContent = n.titre;
    b.querySelector('.val').textContent = n.cle === 'micro' ? '' : (sel ? sel[1] : '');
    b.onclick = () => { S.sub = S.sub === n.cle ? null : n.cle; majSousMenus(); };
    const env = document.createElement('div');
    env.className = 'enveloppe';
    const interieur = document.createElement('div');
    const sous = document.createElement('div');
    sous.className = 'sous' + (grille ? ' grille' : '');
    n.options.forEach(([val, lib]) => {
      const c = document.createElement('button');
      c.className = 'choix' + (grille ? ' visage' : '') + (val === n.valeur ? ' actif' : '');
      c.innerHTML = (grille ? petiteTete(val) : '<span class="point"></span>') + '<span class="lib"></span>';
      c.querySelector('.lib').textContent = lib;
      c.title = lib;
      c.onclick = () => {
        sous.querySelectorAll('.choix').forEach(x => x.classList.toggle('actif', x === c));   // le choix se voit tout de suite
        b.querySelector('.val').textContent = n.cle === 'micro' ? '' : lib;
        n.valeur = val;
        if (grille) { choisirSkin(val); return; }        // la grille reste ouverte : on peut essayer
        S.sub = null;
        setTimeout(majSousMenus, 140);                   // on voit le choix, puis ça se referme
        pont && pont.choix(n.cle, JSON.stringify(val));
      };
      sous.appendChild(c);
    });
    interieur.appendChild(sous);
    env.appendChild(interieur);
    bloc.appendChild(b);
    bloc.appendChild(env);
    navs.appendChild(bloc);
  });
  majSousMenus();
}
function majSousMenus() {
  document.querySelectorAll('.bloc-nav').forEach(bl => {
    const ouvrir = bl.dataset.cle === S.sub;
    if (ouvrir && !bl.classList.contains('ouvert'))     // on fait défiler doucement jusqu'au sous-menu
      setTimeout(() => bl.scrollIntoView({ block: 'nearest', behavior: 'smooth' }), 280);
    bl.classList.toggle('ouvert', ouvrir);
  });
}

function majPanneau() {
  majCartes();
  $('panneau').style.maxHeight = $('aide').style.maxHeight = S.maxPanneau + 'px';
  $('engrenage').classList.toggle('actif', S.panel);
  $('aide-bouton').classList.toggle('actif', S.help);
  document.querySelectorAll('.inter').forEach(b => b.classList.toggle('on', !!S.reglages[b.dataset.cle]));
  document.querySelectorAll('.nom-touche').forEach(e => e.textContent = S.nomTouche);
  $('aide-winh').classList.toggle('cache', !S.reglages.win_h);
  construireNavs();
  majSousMenus();
}

function rendre() {
  majCostume(); majBulles(); majPanneau();
  requestAnimationFrame(signalerTaille);
}

// La fenêtre ne change jamais de taille. On dit seulement à Python quelles zones sont
// visibles : là, la souris est attrapée ; ailleurs, les clics passent derrière.
// Une carte qui part (animation de sortie) compte encore, jusqu'à la fin.
let dernieresZones = '', grandeEntree = false;
function signalerTaille() {
  const zones = [];
  const ajoute = (el, haut, cote, bas) => {
    const r = el.getBoundingClientRect();
    zones.push([Math.floor(r.left - cote), Math.floor(r.top - haut),
                Math.ceil(r.width + 2 * cote), Math.ceil(r.height + haut + bas)]);
  };
  ajoute($('barre'), grandeEntree ? 170 : 80, 24, 20);   // + le canard, son chapeau, ses Zzz
  // Les menus : on prend leur taille FINALE (sans l'animation, qui les fait grandir/rétrécir),
  // sinon le haut du menu resterait coupé une fois l'animation finie.
  const scene = $('scene').getBoundingClientRect();
  ['panneau', 'aide'].forEach(id => {
    const el = $(id);
    if (el.classList.contains('cache')) return;
    const gauche = scene.left + el.offsetLeft - el.offsetWidth / 2;   // centré (translateX(-50%))
    const haut = scene.top + el.offsetTop;
    zones.push([Math.floor(gauche - 24), Math.floor(haut - 30),
                Math.ceil(el.offsetWidth + 48), Math.ceil(el.offsetHeight + 60)]);
  });
  ['bulle', 'bulle-pleurs', 'bulle-reflexion'].forEach(id => {
    const el = $(id);
    if (!el.classList.contains('cache')) ajoute(id === 'bulle-reflexion' ? el.firstElementChild : el, 10, 12, 30);
  });
  const t = JSON.stringify(zones);
  if (t !== dernieresZones && pont) { dernieresZones = t; pont.zones(t); }
}
// Un sous-menu qui s'ouvre agrandit la carte : la zone suit.
new ResizeObserver(() => signalerTaille()).observe($('panneau'));
new ResizeObserver(() => signalerTaille()).observe($('aide'));
new ResizeObserver(() => signalerTaille()).observe($('bulle'));

// ------------------------------------------------------------------ actions
function reveiller() {                       // un geste réveille le canard
  if (dort) { reveilAt = now(); dort = false; }
  dernierGeste = now();
}
function quack() {
  S.quack = true; wantSpin = true; reveiller();
  clearTimeout(timers.q); timers.q = setTimeout(() => { S.quack = false; majBulles(); }, 900);
}
function costume(key, msg) {
  wantSpin = true; S.costume = key; S.costumeMsg = msg; reveiller(); rendre();
  pont && pont.retenir(7.5);      // la barre reste le temps qu'on voie le costume
  clearTimeout(timers.c);         // puis le canard remet son skin
  timers.c = setTimeout(() => { S.costume = S.skin; S.costumeMsg = null; rendre(); }, 7000);
}
function choisirSkin(cle) {
  clearTimeout(timers.c);
  S.skin = cle; S.costume = cle; S.costumeMsg = null; wantSpin = true; reveiller();
  rendre();
  pont && pont.choix('skin', JSON.stringify(cle));
}
function scanMagic(texte) {
  if (!S.reglages.costumes) return;
  const m = trouverCostume(texte);
  if (m) costume(m.key, m.msg);
}
function message(texte, duree) {
  S.msg = texte || null; majBulles();
  clearTimeout(timers.m);
  if (duree > 0) timers.m = setTimeout(() => { S.msg = null; majBulles(); }, duree * 1000);
}

$('engrenage').onclick = () => { if (!S.panel) { openAt = now(); pont && pont.panneauOuvert(); } S.panel = !S.panel; S.help = false; S.sub = null; rendre(); };
$('aide-bouton').onclick = () => { if (!S.help) openAt = now(); S.help = !S.help; S.panel = false; S.sub = null; rendre(); };
$('mes-mots').onclick = () => { S.panel = false; rendre(); pont && pont.mesMots(); };
$('compris').onclick = () => { S.help = false; rendre(); };
$('canard-bouton').onclick = () => { S.panel = false; S.help = false; rendre(); pont && pont.ecouter(); };
$('fermer').onclick = () => { S.panel = false; S.help = false; rendre(); pont && pont.masquer(); };
$('quitter').onclick = () => {
  S.crying = true; S.panel = false; S.help = false; S.sub = null; rendre();
  pont && pont.quitter();
};
document.querySelectorAll('.inter').forEach(b => b.onclick = () => {
  const cle = b.dataset.cle;
  S.reglages[cle] = !S.reglages[cle];
  rendre();
  pont && pont.reglage(cle, S.reglages[cle]);
});
// Déplacer la barre : attraper le fond de la barre.
$('barre').addEventListener('mousedown', e => { if (e.target === $('barre') && e.button === 0 && pont) pont.deplacer(); });
document.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });
document.addEventListener('pointerdown', reveiller);

// ------------------------------------------------------------------ animation (reprise du design)
const tous = sel => R.duck.querySelectorAll(sel);

function animerSommeil(s, L, T, C) {
  const peutDormir = !L && !T && !C && (!S.costume || S.costume === S.skin) && !S.panel && !S.help;
  if (!peutDormir) dernierGeste = s;
  const avant = dort;
  dort = peutDormir && S.dodo > 0 && s - dernierGeste > S.dodo;
  if (dort && !avant) debutSommeil = s;
  const t = dort ? s - debutSommeil : 0;
  baille = dort && t < 1.4 ? Math.sin(t / 1.4 * Math.PI) : 0;
  let eo = 1, nod = 0;
  if (dort) {                                // bâille, pique du nez, se réveille à moitié, s'endort
    if (t < 1.4) { eo = 1 - baille * 0.8; nod = -baille * 8; }
    else if (t < 2.3) { const k = (t - 1.4) / 0.9; eo = 1 - k * 0.85; nod = k * 12; }
    else if (t < 2.6) { const k = (t - 2.3) / 0.3; eo = 0.15 + k * 0.75; nod = 12 * (1 - k); }
    else if (t < 3.6) { const k = t - 2.6; eo = 0.9 * (1 - k); nod = k * 15; }
    else { eo = 0; nod = 15 + Math.sin(s * 1.2) * 2.5; }
  }
  yeuxSommeil = eo; hocheTete = nod; profond = dort && t >= 3.6;
  const fondu = profond ? Math.min(1, (t - 3.6) / 1) : 0;
  [R.z1, R.z2, R.z3].forEach((z, i) => {
    const p = (s * 0.4 + i / 3) % 1;
    z.style.transform = `translate(${p * 16 + Math.sin(s * 2 + i) * 3}px, ${-p * 34}px) rotate(${Math.sin(s * 2 + i) * 14}deg) scale(${0.6 + p * 0.7})`;
    z.style.opacity = Math.sin(p * Math.PI) * fondu;
  });
}

function animerAccessoires(s, L, lookX) {
  const vb = s < blinkEnd ? 0.15 : 1;
  const S2 = t => Math.sin(t * 2.3) * 0.6 + Math.sin(t * 5.1) * 0.4;
  tous('[data-spray]').forEach((d, i) => { const p = (s * 1.4 + i * 0.25) % 1; d.style.transform = `translate(${-p * 26}px, ${Math.sin(i * 2.1) * 7 * p + p * p * 6}px) scale(${1.1 - p * 0.5})`; d.style.opacity = 1 - p; });
  tous('[data-cartp]').forEach(d => { d.style.transform = `translate(${S.costume === 'pixel' ? Math.round(lookX) : lookX * 1.2}px, 0)`; });
  if (dernierCos !== S.costume) { dernierCos = S.costume; cosAt = s; }
  tous('[data-brick]').forEach(d => {          // les briques Lego tombent une par une
    const t = s - cosAt - (+d.dataset.brick) * 0.09;
    if (t < 0) { d.style.opacity = 0; d.style.transform = 'translateY(-30px)'; return; }
    d.style.opacity = 1;
    if (t < 0.22) { const k = t / 0.22; d.style.transform = `translateY(${-30 * (1 - k * k)}px)`; }
    else if (t < 0.34) { const k = Math.sin((t - 0.22) / 0.12 * Math.PI); d.style.transform = `translateY(${-k * 3}px) scale(${1 + k * 0.04},${1 - k * 0.06})`; }
    else d.style.transform = '';
  });
  tous('[data-lens]').forEach(d => { const ph = (s % 3) / 3, x = -20 + ph * 60; d.style.backgroundPosition = `${x}px 0, 0 0`; });
  tous('[data-glass]').forEach(d => { d.style.transform = `translateY(${-amp * 2 + Math.max(0, Math.sin(s * 5)) * -0.8}px)`; });
  tous('[data-fly]').forEach(d => { const i = +d.dataset.fly, a1 = s * (0.5 + i * 0.17) + i * 2.1; d.style.transform = `translate(${42 + Math.cos(a1) * (40 + i * 6)}px, ${30 + Math.sin(a1 * 1.7) * 26 - 10}px)`; d.style.opacity = 0.35 + (Math.sin(s * 3 + i * 1.3) + 1) * 0.32; });
  tous('[data-sprout]').forEach(d => { d.style.transform = `rotate(${Math.sin(s * 1.6) * 14 + amp * 18}deg)`; });
  tous('[data-shroom]').forEach(d => { const ph = s % 3.4, b = ph < 0.4 ? Math.sin(ph / 0.4 * Math.PI) : 0; d.style.transform = `translateY(${-b * 5}px) scale(${1 + b * 0.06},${1 - b * 0.04}) rotate(${Math.sin(s * 1.3) * 4}deg)`; });
  tous('[data-glow]').forEach((d, i) => { d.style.opacity = 0.7 + 0.3 * Math.abs(Math.sin(s * 13 + i) * Math.sin(s * 7.3 + i * 2)) + amp * 0.2; });
  tous('[data-boo]').forEach(d => { d.style.transform = `scale(${0.8 + Math.sin(s * 2) * 0.1}, ${0.8 + amp * 0.8 + Math.sin(s * 2) * 0.15})`; });
  tous('[data-flapL]').forEach(d => { d.style.transform = `rotate(${Math.sin(s * 3) * 18}deg)`; });
  tous('[data-flapR]').forEach(d => { d.style.transform = `rotate(${-Math.sin(s * 3) * 18}deg)`; });
  tous('[data-sway]').forEach(d => { d.style.transform = `rotate(${Math.sin(s * 2.2) * 10}deg)`; });
  tous('[data-witch]').forEach(d => { d.style.transform = `rotate(${Math.sin(s * 1.6) * 5 - amp * 6}deg)`; });
  tous('[data-flag]').forEach(d => { d.style.transform = `skewY(${Math.sin(s * 5) * 8}deg) scaleX(${0.92 + Math.sin(s * 5 + 1) * 0.08})`; });
  const flex = (Math.sin(s * 2.2) + 1) / 2, pump = flex * flex;
  tous('[data-flex]').forEach(d => { const i = +d.dataset.flex; d.style.transform = `rotate(${(i ? 1 : -1) * (-4 + pump * 10 + amp * 8)}deg)`; });
  tous('[data-bicep]').forEach(d => { d.style.transform = `scale(${1 + pump * 0.35 + amp * 0.2})`; });
  tous('[data-burst]').forEach(d => { d.style.transform = `rotate(${s * 12}deg) scale(${1 + pump * 0.06})`; d.style.opacity = 0.6 + pump * 0.4; });
  tous('[data-grin]').forEach(d => { d.style.transform = `scaleY(${1 + amp * 0.4})`; });
  tous('[data-ahoge]').forEach(d => { d.style.transform = `rotate(${Math.sin(s * 4) * 12 + amp * 20}deg)`; });
  tous('[data-sweat]').forEach(d => { const ph = s % 6, k = ph > 4 && ph < 5.2 ? (ph - 4) / 1.2 : -1; d.style.opacity = k < 0 ? 0 : 1 - k * k; d.style.transform = `translateY(${k < 0 ? 0 : k * 10}px)`; });
  tous('[data-tail]').forEach(d => { d.style.transform = `rotate(${Math.sin(s * (L ? 14 : 7)) * (L ? 22 : 16) - 10}deg)`; });
  const ears = tous('[data-ear]');
  if (ears.length) {                            // oreilles qui ballottent quand le canard bouge
    const E = oreilles || (oreilles = { py: null, e: [{ a: 0, v: 0 }, { a: 0, v: 0 }] });
    const y = R.duck.getBoundingClientRect().top, vy = E.py == null ? 0 : y - E.py; E.py = y;
    ears.forEach(d => {
      const i = +d.dataset.ear, sg = i ? 1 : -1, q = E.e[i];
      const ph = (s + i * 0.15) % 2.8, tw = ph < 0.16 ? Math.sin(ph / 0.16 * Math.PI) : 0;
      const cible = sg * (-6 + amp * 12) + sg * tw * 16;
      q.v += (cible - q.a) * 0.16 - q.v * 0.18 + sg * vy * 0.9;
      q.a += q.v;
      d.style.transform = `rotate(${q.a}deg) scaleY(${1 + amp * 0.06})`;
    });
  } else oreilles = null;
  tous('[data-flame]').forEach((d, i) => { const f = 0.75 + Math.abs(Math.sin(s * 23 + i * 1.7)) * 0.35 + amp * 0.4; d.style.transform = `scale(${0.85 + Math.sin(s * 31 + i) * 0.12}, ${f})`; d.style.opacity = 0.75 + Math.sin(s * 19 + i) * 0.2; });
  tous('[data-core]').forEach(d => { const g = 8 + Math.sin(s * 3) * 3 + amp * 14; d.style.boxShadow = `0 0 ${g}px #4fdcff, 0 0 0 2px #7a5410`; });
  tous('[data-armeye]').forEach(d => { d.style.opacity = s < blinkEnd ? 0.3 : 1; d.style.boxShadow = `0 0 ${5 + amp * 8}px #4fdcff, 0 0 2px #fff`; });
  tous('[data-bat]').forEach(d => { const i = +d.dataset.bat; const ang = s * 1.1 + i * Math.PI; d.style.transform = `translate(${Math.cos(ang) * 40 - 1}px, ${Math.sin(ang * 2) * 6 - 18 + i * 4}px) scaleY(${0.35 + Math.abs(Math.sin(s * 13 + i)) * 0.75}) scaleX(${Math.cos(ang) > 0 ? 1 : -1})`; d.style.zIndex = Math.sin(ang) > 0 ? 4 : 0; });
  tous('[data-hair]').forEach(d => { d.style.transform = `rotate(${S2(s) * 6 - amp * 14}deg) translateY(${-amp * 2}px)`; });
  tous('[data-pixbeak]').forEach(d => { d.style.transform = `translateY(${Math.round(amp * 3) * 2}px)`; });
  tous('[data-visor]').forEach(d => { d.style.transform = `translate(${lookX * 0.9}px, ${-amp * 2}px) scaleY(${vb * (1 + amp * 0.4)})`; });
  tous('[data-rain]').forEach((d, i) => { const p = (s * 1.6 + i * 0.33) % 1; d.style.transform = `translateY(${p * 30}px)`; d.style.opacity = 1 - p; });
  tous('[data-bounce]').forEach(d => { d.style.transform = `translateY(${-Math.abs(Math.sin(s * 5)) * 12}px) rotate(${s * 200}deg)`; });
  tous('[data-float]').forEach((d, i) => { const p = (s * 0.6 + i * 0.5) % 1; d.style.transform = `translate(${Math.sin(s * 3 + i) * 3}px, ${-p * 24}px)`; d.style.opacity = 1 - p; });
}

function animerPhysique(s, L, a, tiltTete) {
  if (S.costume === 'noel') {                  // le pompon du bonnet ballotte
    const t1 = R.duck.querySelector('[data-santa="1"]'), t2 = R.duck.querySelector('[data-santa="2"]');
    if (t1 && t2) {
      const P = pere || (pere = { a1: 0, v1: 0, a2: 0, v2: 0, py: null, pt: 0 });
      const y = R.head.getBoundingClientRect().top;
      const vy = P.py == null ? 0 : y - P.py; P.py = y;
      const dtl = tiltTete - P.pt; P.pt = tiltTete;
      P.v1 += (-tiltTete * 0.85 - P.a1) * 0.1 - P.v1 * 0.14 - dtl * 0.8 - vy * 1.6;
      P.a1 = Math.max(-60, Math.min(55, P.a1 + P.v1));
      P.v2 += (-P.a1 * 0.3 - P.a2) * 0.14 - P.v2 * 0.12 - P.v1 * 0.55;
      P.a2 = Math.max(-70, Math.min(70, P.a2 + P.v2));
      t1.style.transform = `rotate(${40 + P.a1}deg)`;
      t2.style.transform = `rotate(${25 + P.a2}deg)`;
    }
  } else pere = null;
  if (S.costume === 'cuir') {                  // la cravache se balance
    const c1 = R.duck.querySelector('[data-crop="1"]'), c2 = R.duck.querySelector('[data-crop="2"]');
    if (c1 && c2) {
      const P = crop || (crop = { a1: 0, v1: 0, a2: 0, v2: 0, py: null, lf: s });
      const y = R.duck.getBoundingClientRect().top;
      const vy = P.py == null ? 0 : y - P.py; P.py = y;
      if (s - P.lf > 3) { P.v1 -= 9; P.lf = s; }
      const sway = Math.sin(s * 2.1) * 7 + Math.sin(s * 3.7) * 3;
      P.v1 += (sway - P.a1) * 0.08 - P.v1 * 0.07 - vy * 0.9 + (L ? Math.sin(s * 14) * a * 2.5 : 0);
      P.a1 = Math.max(-30, Math.min(30, P.a1 + P.v1));
      P.v2 += (-P.a1 * 0.9 - P.a2) * 0.12 - P.v2 * 0.06 - P.v1 * 1.3 - vy * 1.1;
      P.a2 = Math.max(-50, Math.min(50, P.a2 + P.v2));
      c1.style.transform = `rotate(${22 + P.a1}deg)`;
      c2.style.transform = `rotate(${P.a2}deg)`;
    }
  } else crop = null;
}

function tick(s) {
  const L = S.ecoute;
  const target = L ? Math.min(1, niveau) : 0;
  amp += (target - amp) * (target > amp ? 0.45 : 0.18);
  const a = amp, C = S.crying, T = S.reflechit && !L;
  animerSommeil(s, L, T, C);
  let lookX = 0;
  ['L', 'R'].forEach(side => {
    const eye = R['eye' + side], pupil = R['pupil' + side];
    let dx = 0, dy = 0;
    if (C) { dy = 3.5; }
    else if (T) { dx = 2.6 + Math.sin(s * 1.5) * 0.6; dy = -3.4; }
    else {
      const b = eye.getBoundingClientRect(), cx = b.left + b.width / 2, cy = b.top + b.height / 2;
      const vx = mx - cx, vy = my - cy, d = Math.hypot(vx, vy) || 1, k = Math.min(d / 60, 1);
      dx = vx / d * 3.2 * k; dy = vy / d * 3.6 * k;
    }
    lookX += dx / 2;
    pupil.style.transform = `translate(${dx}px,${dy}px)`;
  });
  if (s > nextBlink) { blinkEnd = s + 0.13; nextBlink = s + 2 + Math.random() * 3.5; }
  const blink = dort ? Math.max(0.05, yeuxSommeil) : C ? 0.45 : S.costume === 'cafe' ? 0.5 : S.costume === 'frog' ? 0.75 : s < blinkEnd ? 0.1 : (L ? 1 - a * 0.25 : 1);
  [R.tearL, R.tearR].forEach((tr, i) => {
    if (!C) { tr.style.opacity = 0; return; }
    const p = (s * 1.3 + i * 0.45) % 1;
    tr.style.opacity = p < 0.85 ? 1 - p : 0;
    tr.style.transform = `translate(${(i ? 1 : -1) * p * 4}px, ${p * p * 26}px) scale(${0.7 + p * 0.5})`;
  });
  R.eyeL.style.transform = R.eyeR.style.transform = `scaleY(${blink})`;
  const breath = Math.sin(s * 1.6);
  const hop = L ? Math.abs(Math.sin(s * 7)) * a * 6 : 0;
  let spin = 0, jump = 0;
  if (wantSpin) { spinStart = s; wantSpin = false; }
  if (spinStart != null) {
    const p = Math.min(1, (s - spinStart) / 0.7), e = 1 - Math.pow(1 - p, 3);
    spin = e * 360; jump = Math.sin(p * Math.PI) * 10;
    if (p >= 1) spinStart = null;
  }
  const th = spin * Math.PI / 180, c = Math.cos(th), sn = Math.sin(th), fc = Math.max(c, 0);
  const sob = C ? Math.abs(Math.sin(s * 9)) : 0;
  if (openAt != null) {
    const op = (s - openAt) / 0.45;
    if (op >= 0 && op < 1) jump += Math.sin(op * Math.PI) * 9; else if (op >= 1) openAt = null;
  }
  let ex = 0, ey = 0, eop = 1; ewig = 0;
  if (enterAt != null) {
    const e = s - enterAt;
    if (e < 0.3) { eop = 0; jump += 120; }
    else if (e < 0.8) { const t = (e - 0.3) / 0.5; jump += 120 * (1 - t * t); }
    else if (e < 1.1) { const k = Math.sin((e - 0.8) / 0.3 * Math.PI); ex = k * 0.18; ey = -k * 0.22; }
    else if (e < 1.6) { ewig = Math.sin((e - 1.1) * 30) * 10 * (1 - (e - 1.1) / 0.5); }
    else enterAt = null;
  }
  if (profond) { const b = Math.sin(s * 1.2); ex += b * 0.05; ey -= b * 0.04; jump -= 2; }   // il respire en dormant
  if (baille) { ey += baille * 0.08; ex -= baille * 0.04; }
  if (reveilAt != null) {                      // petit sursaut au réveil
    const w = (s - reveilAt) / 0.4;
    if (w < 1) { jump += Math.sin(w * Math.PI) * 13; ey += Math.sin(w * Math.PI) * 0.08; } else reveilAt = null;
  }
  R.duck.style.opacity = eop;
  if (S.costume) animerAccessoires(s, L, lookX);
  const F = S.costume === 'frog' && !L;
  let fy = 0, fsx = 0, fsy = 0;
  if (F) {
    const ph = (s % 1.8) / 1.8;
    if (ph < 0.12) { const k = Math.sin(ph / 0.12 * Math.PI); fsx = k * 0.1; fsy = -k * 0.12; }
    else if (ph < 0.42) { const k = Math.sin((ph - 0.12) / 0.3 * Math.PI); fy = k * 16; fsx = -k * 0.05; fsy = k * 0.08; }
    else if (ph < 0.5) { const k = Math.sin((ph - 0.42) / 0.08 * Math.PI); fsx = k * 0.08; fsy = -k * 0.08; }
    const q = sel => R.duck.querySelector(`[data-frog=${sel}]`);
    const sac = q('sac'), tongue = q('tongue'), fly = q('fly');
    const air = ph >= 0.12 && ph < 0.42;
    if (sac) sac.style.transform = `scale(${air ? 0.5 : 0.7 + 0.35 * Math.abs(Math.sin(s * 4))})`;
    const tp = s % 3.6;
    const lick = tp > 2.6 && tp < 2.9 ? Math.sin((tp - 2.6) / 0.3 * Math.PI) : 0;
    if (tongue) tongue.style.transform = `rotate(-28deg) scaleX(${lick})`;
    if (fly) {
      const caught = tp > 2.75 && tp < 3.4;
      let fx = 42 + Math.cos(s * 3.1) * 34, fyy = 12 + Math.sin(s * 4.7) * 10;
      if (tp > 2.1 && tp <= 2.75) { const k = Math.min(1, (tp - 2.1) / 0.5); fx += (70 - fx) * k; fyy += (14 - fyy) * k; }
      fly.style.transform = `translate(${fx}px, ${fyy}px)`;
      fly.style.opacity = caught ? 0 : 1;
    }
  }
  const P = (S.costume && !C && !dort) ? personnalite(S.costume, s, L) : null;
  const pTilt = P ? P.t || 0 : 0;
  let ty = -a * 5 - hop + breath - jump - fy + (C ? 3 - sob * 2 : 0) + (P ? P.y || 0 : 0);
  let tx = P ? P.x || 0 : 0, rot = P ? P.r || 0 : 0;
  let scx = 1 + a * 0.05 + sob * 0.03 + fsx + ex + (P ? P.sx || 0 : 0), scy = 1 - a * 0.04 - sob * 0.04 + fsy + ey + (P ? P.sy || 0 : 0);
  if (S.costume === 'pixel') { ty = Math.round(ty / 2) * 2; tx = Math.round(tx / 2) * 2; rot = 0; scx = Math.round(scx * 10) / 10; scy = Math.round(scy * 10) / 10; }
  R.duck.style.transform = `translate(${tx}px, ${ty}px) rotate(${rot}deg) scale(${scx},${scy})`;
  if (C) {
    R.beakLow.style.transform = `translateY(${1.5 + sob * 2}px)`;
    R.mouth.style.height = (3 + sob * 2) + 'px';
    R.hat.style.transform = 'translateY(3px) rotate(-4deg)';
  }
  R.face.style.transform = `translateX(${sn * 16}px) scaleX(${fc})`;
  R.face.style.opacity = c > 0.05 ? 1 : 0;
  R.belly.style.transform = `translateX(${sn * 14}px) scaleX(${fc})`;
  R.belly.style.opacity = c > 0.05 ? 1 : 0;
  const tilt = dort ? hocheTete + popTw : C ? Math.sin(s * 11) * 2.5 : F ? Math.sin(s * 1.3) * 5 - 3 : L ? Math.sin(s * 6) * (4 + a * 10) : T ? 8 + Math.sin(s * 2.2) * 5 : Math.sin(s * 1.1) * 2.5;
  document.querySelectorAll('#bulle-reflexion .pt').forEach((d, i) => { d.style.transform = `translateY(${-Math.max(0, Math.sin(s * 7 - i * 0.9)) * 4}px)`; });
  if (T) R.hat.style.transform = `rotate(${Math.sin(s * 2.2) * 3}deg)`;
  R.head.style.transform = `translateX(${lookX * 0.7}px) rotate(${tilt + lookX * 1.5 + ewig + pTilt}deg)`;
  animerPhysique(s, L, a, tilt + lookX * 1.5 + ewig);
  if (C) return;
  if (!T) R.hat.style.transform = `translateY(${-a * 4 - hop * 0.4}px) rotate(${L ? Math.sin(s * 7) * a * 6 : 0}deg)`;
  R.beakLow.style.transform = `translateY(${a * 6}px)`;
  R.mouth.style.height = (2 + a * 6) + 'px';
  if (dort) {                                  // bouche qui bâille puis ronfle
    const ronfle = profond ? (Math.sin(s * 1.2) + 1) / 2 : 0;
    R.beakLow.style.transform = `translateY(${baille * 8 + ronfle * 1.5}px)`;
    R.mouth.style.height = (2 + baille * 8 + ronfle * 1.5) + 'px';
  }
  const endormi = dort && yeuxSommeil < 0.12;
  R.eyeL.style.opacity = R.eyeR.style.opacity = endormi ? 0 : 1;
  R.lidL.style.opacity = R.lidR.style.opacity = endormi ? 1 : 0;
  if (profond) {                               // la bulle de morve grossit... et éclate
    const cyc = s * 1.2 / (2 * Math.PI), n = Math.floor(cyc), ph = cyc - n, grosse = n % 3 === 2;
    const pop = grosse && ph > 0.93;
    const sc = grosse ? 0.3 + ph * 1.6 : 0.3 + 0.6 * Math.sin(ph * Math.PI);
    R.snot.style.transform = `scale(${pop ? 2.2 : sc})`;
    R.snot.style.opacity = pop ? 0 : 0.9;
    popTw = pop ? -6 : popTw * 0.85;
  } else { R.snot.style.opacity = 0; popTw = 0; }
  [R.ring1, R.ring2].forEach((ring, i) => {
    const ph = ((s * 0.9 + i * 0.5) % 1);
    ring.style.transform = `scale(${0.8 + ph * 0.6 + a * 0.15})`;
    ring.style.opacity = L ? (1 - ph) * (0.25 + a * 0.6) : 0;
  });
}
(function boucle(t) { tick(t / 1000); requestAnimationFrame(boucle); })(0);

// ------------------------------------------------------------------ lien avec Python
function evenement(type, donnee) {
  switch (type) {
    case 'coin': quack(); break;
    case 'texte': scanMagic(donnee); break;
    case 'message': { const d = JSON.parse(donnee); message(d.texte, d.duree); break; }
    case 'entree':                       // le canard tombe d'en haut : on lui laisse la place
      enterAt = now(); grandeEntree = true; reveiller();
      clearTimeout(timers.e); timers.e = setTimeout(() => { grandeEntree = false; signalerTaille(); }, 1700);
      break;
    case 'panneau': if (!S.panel) { openAt = now(); S.panel = true; S.help = false; pont && pont.panneauOuvert(); } break;
    case 'aide': if (!S.help) { openAt = now(); S.help = true; S.panel = false; } break;
    case 'fermer': S.panel = false; S.help = false; S.sub = null; break;
    case 'pleurer': S.crying = true; S.panel = false; S.help = false; S.sub = null; break;
  }
  rendre();
}
function appliquerEtat(e) {
  const avant = S.ecoute, skinAvant = S.skin;
  Object.assign(S, e);
  if (S.ecoute && !avant) { S.panel = false; S.help = false; reveiller(); }
  if (S.skin !== skinAvant && (!S.costume || S.costume === skinAvant)) S.costume = S.skin;
  rendre();
}
window.addEventListener('load', () => {
  dernierGeste = now();
  rendre();
  if (typeof QWebChannel === 'undefined') return;   // ouvert dans un navigateur : aperçu seul
  new QWebChannel(qt.webChannelTransport, ch => {
    pont = ch.objects.pont;
    pont.etat.connect(j => appliquerEtat(JSON.parse(j)));
    pont.evenement.connect(evenement);
    pont.niveau.connect(v => { niveau = v; });
    pont.souris.connect((x, y) => {           // la souris bouge (n'importe où) : le canard se réveille
      if (Math.abs(x - mx) + Math.abs(y - my) > 2) reveiller();
      mx = x; my = y;
    });
    pont.pret();
  });
});
