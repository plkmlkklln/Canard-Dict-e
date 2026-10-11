// Canard Dictée — les costumes : mots magiques, couleurs, petites têtes du menu « Skin »,
// et la « personnalité » de chaque costume (sa façon de bouger). Repris du design.
'use strict';

// Mots magiques. Écrire les mots SANS accents. « mot* » = tout ce qui commence par « mot ».
// « deux mots » = expression (compte double). Les pluriels (s, x) marchent tout seuls.
const MAGIC = [
  { key: 'france', word: 'France', msg: 'Oh là là !', mots: ['france', 'francais', 'francaise', 'paris', 'baguette*', 'croissant*', 'fromage*', 'camembert', 'beret*', 'tour eiffel', 'marseillaise', 'vin rouge', 'escargot*', 'cocorico'] },
  { key: 'italie', word: 'Italie', msg: 'Mamma mia !', mots: ['itali*', 'pizza*', 'pizzeria', 'pate', 'pates', 'pasta', 'spaghett*', 'lasagne*', 'ravioli*', 'risotto', 'tiramisu', 'mozzarella', 'carbonara', 'bolognaise', 'gelato', 'parmesan', 'pesto', 'mamma mia', 'rome', 'venise', 'milan', 'naples', 'ciao', 'bella', 'gnocchi*', 'panini*', 'prosciutto', 'espresso'] },
  { key: 'frog', word: 'Grenouille', msg: 'Croâ. C’est un mème.', mots: ['meme', 'memes', 'grenouille*', 'croa', 'croaa*', 'lol', 'mdr', 'ptdr', 'xptdr', 'jpp', 'troll*', 'shitpost*', 'pepe', 'crapaud*', 'rigol*', 'marrant*'] },
  { key: 'pirate', word: 'Pirate', msg: 'Arrr, moussaillon !', mots: ['pirate*', 'tresor', 'tresors', 'rhum', 'bateau*', 'perroquet*', 'corsaire*', 'moussaillon*', 'capitaine', 'abordage', 'sabre*', 'ile au tresor', 'jambe de bois', 'caraibe*', 'navire*', 'flibustier*'] },
  { key: 'anniv', word: 'Anniversaire', msg: 'Joyeux coin-niversaire !', mots: ['anniversaire*', 'anniv', 'gateau*', 'fete', 'fetes', 'feter', 'bougie*', 'cadeau', 'cadeaux', 'surprise*', 'joyeux anniversaire', 'confetti*', 'souffler les bougies', 'happy birthday', 'champagne'] },
  { key: 'cafe', word: 'Café', msg: 'Pas avant mon café…', mots: ['cafe', 'cafes', 'expresso', 'cappuccino', 'latte', 'fatigu*', 'reveil*', 'dodo', 'sommeil', 'dormir', 'dors', 'baill*', 'epuise*', 'creve', 'crevee', 'lundi matin', 'nuit blanche', 'insomnie*', 'sieste*'] },
  { key: 'amour', word: 'Amour', msg: 'Coin coin d’amour', mots: ['amour*', 'amoureu*', 'bisou*', 'cheri', 'cherie', 'je t aime', 'je vous aime', 'love', 'coeur*', 'mariage*', 'marier', 'romanti*', 'calin*', 'saint valentin', 'valentin', 'fiance', 'fiancee', 'mon coeur', 'tendresse'] },
  { key: 'riche', word: 'Millionnaire', msg: 'Canard millionnaire.', mots: ['argent', 'riche*', 'salaire*', 'euro', 'euros', 'dollar*', 'thune*', 'fric', 'banque*', 'loto', 'millionnaire*', 'milliardaire*', 'fortune*', 'pognon', 'oseille', 'bitcoin*', 'jackpot', 'paye', 'investi*', 'bourse'] },
  { key: 'noel', word: 'Noël', msg: 'Ho ho coin !', mots: ['noel', 'pere noel', 'neige*', 'hiver', 'sapin*', 'renne*', 'traineau*', 'lutin*', 'flocon*', 'bonhomme de neige', 'reveillon*', 'guirlande*', 'joyeux noel', 'decembre'] },
  { key: 'astro', word: 'Astronaute', msg: 'Un petit coin pour l’humanité.', mots: ['espace', 'fusee*', 'lune', 'nasa', 'planete*', 'etoile*', 'astronaute*', 'cosmonaute*', 'galaxie*', 'univers', 'cosmos', 'satellite*', 'extraterrestre*', 'alien*', 'ovni*', 'spatial*', 'apesanteur', 'soleil'] },
  { key: 'sport', word: 'Foot', msg: 'GOOOAL !', mots: ['foot', 'football*', 'footballeur*', 'match', 'matchs', 'sport*', 'ballon*', 'muscu*', 'courir', 'jogging', 'basket*', 'tennis', 'rugby', 'stade*', 'penalty', 'goal', 'marquer un but', 'gym', 'salle de sport', 'coupe du monde', 'champion*', 'entrainement*', 'velo*'] },
  { key: 'musique', word: 'Musique', msg: 'Coin coin, baby !', mots: ['musique*', 'musicien*', 'guitar*', 'rock', 'concert*', 'chanson*', 'chanter', 'chante', 'danse*', 'danser', 'playlist*', 'rap', 'rappeur*', 'piano*', 'batterie', 'festival*', 'spotify', 'karaoke', 'album*', 'dj', 'metal', 'jazz', 'disco'] },
  { key: 'pluie', word: 'Pluie', msg: 'Quelle journée…', mots: ['pluie*', 'pleut', 'pleuvoir', 'triste*', 'tristesse', 'deprim*', 'orage*', 'meteo', 'parapluie*', 'nuage*', 'grisaille', 'sale journee', 'mauvaise journee', 'snif', 'pleure*', 'pleurer', 'deception', 'decu', 'decue', 'mouille*'] },
  { key: 'ninja', word: 'Ninja', msg: 'Hi-yah !', mots: ['ninja*', 'karate*', 'kung fu', 'kungfu', 'japon*', 'japonais*', 'sushi*', 'samourai*', 'judo*', 'katana*', 'shuriken*', 'tokyo', 'arts martiaux', 'taekwondo', 'dojo', 'ramen'] },
  { key: 'detective', word: 'Enquête', msg: 'Élémentaire, mon cher coin.', mots: ['enquete*', 'enqueter', 'police*', 'policier*', 'mystere*', 'mysterieu*', 'detective*', 'sherlock', 'indice*', 'suspect*', 'coupable*', 'crime*', 'meurtre*', 'inspecteur*', 'loupe*', 'cluedo', 'interrogatoire*', 'alibi*', 'temoin*'] },
  { key: 'malade', word: 'Malade', msg: 'J’ai de la fièvre…', mots: ['malade*', 'maladie*', 'docteur*', 'rhume*', 'medecin*', 'grippe*', 'fievre*', 'tousse*', 'toux', 'mal a la tete', 'mal au ventre', 'hopital*', 'pharmacie*', 'medicament*', 'virus', 'covid', 'enrhume*', 'thermometre*', 'migraine*', 'nausee*', 'vomi*', 'gastro'] },
  { key: 'flocage', word: 'Robot flocage', msg: 'Mode flocage activé.', mots: ['flocage*', 'floquer', 'floque', 'nova life', 'novalife', 'robot*', 'androide*', 'cyborg*'] },
  { key: 'citrouille', word: 'Halloween', msg: 'Joyeux Halloween… coin !', mots: ['halloween', 'citrouille*', 'bonbon*', 'un bonbon ou un sort', 'potiron*', 'trick or treat', 'deguisement*', 'squelette*', 'zombie*'] },
  { key: 'fantome', word: 'Fantôme', msg: 'Bouh ! Coin…', mots: ['fantome*', 'bouh', 'bouhh*', 'hante', 'hantee', 'hantes', 'hantees', 'spectre*', 'esprit frappeur', 'revenant*', 'paranormal*', 'maison hantee'] },
  { key: 'sorciere', word: 'Sorcière', msg: 'Abracadacoin !', mots: ['sorcier*', 'sorciere*', 'magie', 'magique*', 'balai', 'balais', 'potion*', 'chaudron*', 'sortilege*', 'abracadabra', 'harry potter', 'baguette magique', 'grimoire*'] },
  { key: 'fierte', word: 'LGBT', msg: 'Fier d’être un canard !', mots: ['lgbt*', 'lgbtq*', 'fierte', 'pride', 'arc en ciel', 'gay', 'gays', 'lesbienne*', 'trans', 'bisexuel*', 'queer', 'marche des fiertes'] },
  { key: 'manga', word: 'Manga', msg: 'Chut… la forêt dort. Coin.', mots: ['manga*', 'anime', 'animes', 'ghibli', 'totoro', 'miyazaki', 'kawaii', 'otaku*', 'one piece', 'naruto', 'dragon ball', 'chihiro', 'pokemon*'] },
  { key: 'furry', word: 'Furry', msg: 'UwU… coin !', mots: ['furry', 'furries', 'fursuit*', 'renard*', 'peluche*', 'poilu', 'poilue', 'poilus', 'uwu', 'owo', 'mignon tout plein'] },
  { key: 'brique', word: 'Lego', msg: 'Clic ! Canard assemblé.', mots: ['lego', 'legos', 'brique*', 'jouet*', 'playmobil*', 'kapla', 'construction en lego'] },
  { key: 'armure', word: 'Iron Man', msg: 'Armure activée. Coin.', mots: ['iron man', 'ironman', 'armure*', 'super heros', 'superheros', 'super heroine', 'marvel', 'avenger*', 'tony stark', 'jarvis', 'spiderman', 'batman', 'superman'] },
  { key: 'goth', word: 'Gothique', msg: 'Tout est sombre… coin.', mots: ['goth', 'goths', 'gothique*', 'vampire*', 'chauve souris', 'chauves souris', 'tenebres', 'dracula', 'cercueil*', 'emo', 'darkness'] },
  { key: 'president', word: 'Trump', msg: 'Un canard formidable. Le meilleur.', mots: ['trump', 'president*', 'presidente*', 'maison blanche', 'election*', 'elysee', 'macron', 'ministre*', 'politique*', 'vote', 'voter'] },
  { key: 'pixel', word: 'Cubes', msg: 'Coin… en 8 bits !', mots: ['minecraft', 'pixel*', '8 bits', '8bit', '8bits', 'creeper*', 'retro gaming', 'jeu video', 'jeux video', 'mario', 'zelda', 'tetris', 'arcade'] },
  { key: 'cartoon', word: 'Dessin animé', msg: 'Coin coin, mec !', mots: ['south park', 'southpark', 'cartoon*', 'dessin anime', 'dessins animes', 'simpson*', 'cartman', 'bob l eponge', 'looney*'] },
  { key: 'cuir', word: 'BDSM', msg: 'Mot de sécurité : coin.', mots: ['bdsm', 'cuir', 'fouet*', 'sexe', 'sexy', 'sex', 'xxx', 'regle 34', 'rule 34', 'coquin*', 'menotte*', 'fessee*', 'latex', 'domina*', 'soumis', 'soumise', 'kinky', 'porno*', 'sado*', 'maso', 'masochiste*', 'lingerie', 'cravache*', 'strip*', 'chaud lapin', 'safe word', 'mot de securite', '50 nuances', 'cinquante nuances'] }
];

// Couleur d'accent de chaque costume (interrupteurs, anneaux, boutons...).
const ACC = { citrouille: '#FF9A2E', fantome: '#C9D4FF', sorciere: '#A47CFF', fierte: '#FF6FB5', manga: '#A8D47A', furry: '#FF9A4D', brique: '#FFD54A', armure: '#F2C14E', goth: '#B48CE0', president: '#E0263F', pixel: '#6CC644', cartoon: '#E5484D', flocage: '#4fc3ff', frog: '#7ccf5a', pirate: '#e0574a', anniv: '#a48bff', noel: '#e8494b', amour: '#ff7aa2', riche: '#F5C542', cafe: '#c8916a', astro: '#8FD3FF', sport: '#3DD68C', musique: '#a48bff', pluie: '#a9b6c8', ninja: '#e6e6e6', detective: '#c9a878', malade: '#8FD3FF', italie: '#4fbf7a', france: '#5b8dff', cuir: '#e2304e' };

// Ambiance de la barre et des menus : [fond barre, bordure, lueur, (fond menus)].
const THEMES = {
  citrouille: ['linear-gradient(135deg,#2a1608,#1c1024)', 'rgba(255,154,46,.5)', 'rgba(255,154,46,.25)'],
  fantome: ['linear-gradient(135deg,#161a24,#232838)', 'rgba(230,235,255,.4)', 'rgba(200,210,255,.22)'],
  sorciere: ['linear-gradient(135deg,#1c1028,#14201a)', 'rgba(164,124,255,.5)', 'rgba(110,220,122,.18)'],
  fierte: ['linear-gradient(90deg,#e40303,#ff8c00,#ffed00,#008026,#004dff,#750787) 0 100%/100% 3px no-repeat, linear-gradient(135deg,#1e1a2a,#2a1830)', 'rgba(255,111,181,.5)', 'rgba(160,80,255,.25)', 'linear-gradient(135deg,#1e1a2a,#2a1830)'],
  manga: ['repeating-linear-gradient(100deg,rgba(255,255,255,.03) 0 2px,transparent 2px 9px), linear-gradient(135deg,#14241a,#1d2a1a)', 'rgba(168,212,122,.45)', 'rgba(255,240,140,.18)', 'linear-gradient(135deg,#1a1d3a,#2a1530)'],
  furry: ['linear-gradient(135deg,#2a1a10,#2a1420)', 'rgba(255,154,77,.5)', 'rgba(255,183,197,.22)'],
  brique: ['radial-gradient(circle at 45% 40%,rgba(255,255,255,.22) 0 1.2px,transparent 1.6px) 0 0/16px 16px, radial-gradient(circle at 50% 50%,#8a1a1e 0 4.5px,rgba(0,0,0,.35) 4.6px 5.4px,transparent 5.6px) 0 0/16px 16px, linear-gradient(180deg,#7a1418,#5c0e12)', 'rgba(255,120,120,.35)', 'rgba(255,74,74,.22)', 'linear-gradient(180deg,#2a1214,#1f1416)'],
  armure: ['linear-gradient(135deg,#2a0d10,#3a1a0e)', 'rgba(242,193,78,.5)', 'rgba(79,220,255,.22)'],
  goth: ['linear-gradient(135deg,#0d0b10,#1d1428)', 'rgba(180,140,224,.4)', 'rgba(120,60,180,.25)'],
  president: ['linear-gradient(135deg,#141c33,#2a1418)', 'rgba(224,38,63,.5)', 'rgba(60,90,200,.22)'],
  pixel: ['linear-gradient(180deg,#1f3317 0%,#1f3317 30%,#2a1f15 30%,#2a1f15 100%)', 'rgba(108,198,68,.55)', 'rgba(108,198,68,.18)'],
  cartoon: ['linear-gradient(135deg,#2a1618,#16203a)', 'rgba(200,55,59,.5)', 'rgba(47,93,168,.22)'],
  flocage: ['linear-gradient(135deg,#1c1442,#2a1c63)', 'rgba(138,99,255,.55)', 'rgba(79,195,255,.28)'],
  frog: ['linear-gradient(135deg,#1a2617,#24361f)', 'rgba(78,154,58,.5)', 'rgba(78,154,58,.2)'],
  pirate: ['linear-gradient(135deg,#2a1816,#33201b)', 'rgba(192,57,43,.45)', 'rgba(192,57,43,.15)'],
  anniv: ['linear-gradient(135deg,#231c3a,#2e2045)', 'rgba(124,92,255,.5)', 'rgba(255,92,138,.18)'],
  noel: ['linear-gradient(135deg,#2a1719,#331c1e)', 'rgba(214,40,40,.5)', 'rgba(214,40,40,.18)'],
  amour: ['linear-gradient(135deg,#2e1b26,#3a2030)', 'rgba(255,92,138,.5)', 'rgba(255,92,138,.22)'],
  riche: ['linear-gradient(135deg,#24200f,#302914)', 'rgba(245,197,66,.55)', 'rgba(245,197,66,.22)'],
  cafe: ['linear-gradient(135deg,#251c16,#2f231b)', 'rgba(140,90,60,.5)', 'rgba(140,90,60,.15)'],
  astro: ['linear-gradient(135deg,#121a33,#1b2547)', 'rgba(143,211,255,.45)', 'rgba(143,211,255,.2)'],
  sport: ['linear-gradient(135deg,#17261d,#1f3226)', 'rgba(230,57,70,.45)', 'rgba(61,214,140,.15)'],
  musique: ['linear-gradient(135deg,#1f1a36,#2a2148)', 'rgba(124,92,255,.5)', 'rgba(124,92,255,.22)'],
  pluie: ['linear-gradient(135deg,#1b2029,#232a35)', 'rgba(141,152,168,.45)', 'rgba(143,211,255,.12)'],
  ninja: ['linear-gradient(135deg,#121212,#1c1c1c)', 'rgba(255,255,255,.14)', 'rgba(0,0,0,0)'],
  detective: ['linear-gradient(135deg,#251f15,#2f271a)', 'rgba(138,110,75,.5)', 'rgba(138,110,75,.15)'],
  malade: ['linear-gradient(135deg,#17262a,#1d3035)', 'rgba(143,211,255,.4)', 'rgba(143,211,255,.12)'],
  italie: ['linear-gradient(135deg,#1d2a1f,#2e1d1c)', 'rgba(206,43,55,.45)', 'rgba(0,146,70,.15)'],
  france: ['linear-gradient(135deg,#161d3a,#2a1a22)', 'rgba(0,85,164,.55)', 'rgba(239,65,53,.15)'],
  cuir: ['linear-gradient(135deg,#160c0e,#221114)', 'rgba(200,16,46,.55)', 'rgba(200,16,46,.2)']
};

// Petites têtes du menu « Skin du canard ».
const FACE = {
  classic: { p: 'brim crown', hat: '#8B5E4A' },
  frog: { head: '#4E9A3A', beak: '#8E2F1E', noCheeks: true },
  flocage: { p: 'hair visor', head: '#2b1d66', hat: '#5a3ad0', visor: '#1a6fe8', eye: '#c9f4ff', beak: 'transparent', noCheeks: true },
  cartoon: { p: 'hair', head: '#F2D06B', hat: '#C8373B', noCheeks: true },
  pixel: { head: '#F2C230', rad: '2px', sq: true, beak: '#F08A1C', noCheeks: true },
  goth: { p: 'hair', head: '#ECE8F0', hat: '#141016', beak: '#4a1f5c', noCheeks: true },
  armure: { p: 'visor', head: '#b3141c', visor: '#E3B23C', eye: '#9ff3ff', beak: 'transparent', noCheeks: true },
  furry: { p: 'ears', head: '#F08A3E', hat: '#C85A1E' },
  manga: { p: 'ears sprout', head: '#858B91', hat: '#757B81', beak: '#C98E36' },
  brique: { p: 'stud', head: '#FFCD1F', rad: '4px', hat: '#FFE35A', noCheeks: true },
  fierte: { p: 'visor', visor: '#ff4fa0', eye: 'transparent' },
  president: { p: 'hair', hat: '#F0C25E' },
  cafe: { p: 'hair', hat: '#3a2418', noCheeks: true },
  cuir: { p: 'hair band', hat: '#1b1b1d' },
  noel: { p: 'cone', hat: '#D62828' },
  pirate: { p: 'band', hat: '#C0392B' },
  ninja: { p: 'band', hat: '#141414' },
  astro: { p: 'band', hat: 'rgba(160,210,255,.85)' },
  malade: { p: 'crown', hat: '#8FD3FF' },
  detective: { p: 'brim crown', hat: '#8A6E4B' },
  musique: { p: 'band', hat: '#7C5CFF' },
  anniv: { p: 'cone', hat: '#7C5CFF' },
  italie: { p: 'crown', hat: '#ffffff' },
  france: { p: 'hair', hat: '#222' },
  sport: { p: 'band', hat: '#E63946' },
  riche: { p: 'visor', visor: '#111', eye: 'rgba(255,255,255,.4)' },
  pluie: { p: 'hair', hat: '#8d98a8' },
  amour: {},
  citrouille: { p: 'stud', head: '#F07E1E', hat: '#4E7A2A', eye: '#FFC93A', beak: '#FFC93A', noCheeks: true },
  fantome: { head: '#F4F4F8', beak: '#1b1b24' },
  sorciere: { p: 'cone brim', hat: '#2a1a3a' }
};

function petiteTete(cle) {
  const F = FACE[cle || 'classic'] || {};
  const parts = (F.p || '').split(' ');
  const d = x => parts.includes(x) ? 'block' : 'none';
  const yeux = parts.includes('visor') ? 'none' : 'block', joues = F.noCheeks ? 'none' : 'block';
  const head = F.head || '#FFD23F', eye = F.eye || '#141414', eyeR = F.sq ? '1px' : '50%';
  const beak = F.beak || '#FF8A1A', rad = F.rad || '50%', hat = F.hat || 'transparent', visor = F.visor || '#111';
  return `<span style="position:relative;flex:none;width:24px;height:24px">
<span style="position:absolute;left:2px;top:3px;width:4px;height:6px;clip-path:polygon(50% 0,100% 100%,0 100%);background:${hat};display:${d('ears')}"></span>
<span style="position:absolute;left:18px;top:3px;width:4px;height:6px;clip-path:polygon(50% 0,100% 100%,0 100%);background:${hat};display:${d('ears')}"></span>
<span style="position:absolute;left:3px;top:5px;width:18px;height:18px;border-radius:${rad};background:radial-gradient(circle at 34% 28%,rgba(255,255,255,.6) 0 1.5px,rgba(255,255,255,0) 5px),${head};box-shadow:inset -2px -2.5px 3px rgba(0,0,0,.25), 0 0 0 1px rgba(0,0,0,.25)"></span>
<span style="position:absolute;left:3px;top:4px;width:18px;height:8px;border-radius:9px 9px 3px 3px;background:${hat};display:${d('hair')}"></span>
<span style="position:absolute;left:3px;top:8px;width:18px;height:2.5px;background:${hat};display:${d('band')}"></span>
<span style="position:absolute;left:6.5px;top:10.5px;width:4.5px;height:5px;border-radius:${eyeR};background:#fff;display:${yeux}"><span style="position:absolute;left:1.3px;top:1.5px;width:2.2px;height:2.6px;border-radius:${eyeR};background:${eye}"></span></span>
<span style="position:absolute;left:13px;top:10.5px;width:4.5px;height:5px;border-radius:${eyeR};background:#fff;display:${yeux}"><span style="position:absolute;left:1px;top:1.5px;width:2.2px;height:2.6px;border-radius:${eyeR};background:${eye}"></span></span>
<span style="position:absolute;left:5px;top:10.5px;width:14px;height:5px;border-radius:2px 2px 3px 3px;background:${visor};display:${d('visor')}"><span style="position:absolute;left:2.5px;top:1.5px;width:3.5px;height:1.6px;border-radius:1px;background:${eye}"></span><span style="position:absolute;left:8px;top:1.5px;width:3.5px;height:1.6px;border-radius:1px;background:${eye}"></span></span>
<span style="position:absolute;left:4.5px;top:16px;width:3px;height:2px;border-radius:50%;background:#FF8FA3;display:${joues}"></span>
<span style="position:absolute;left:16.5px;top:16px;width:3px;height:2px;border-radius:50%;background:#FF8FA3;display:${joues}"></span>
<span style="position:absolute;left:9px;top:15px;width:6px;height:3px;border-radius:50% 50% 40% 40%;background:${beak};box-shadow:0 1px 0 rgba(0,0,0,.25)"></span>
<span style="position:absolute;left:0;top:4.5px;width:24px;height:3.5px;border-radius:50%;background:${hat};display:${d('brim')}"></span>
<span style="position:absolute;left:7px;top:0;width:10px;height:6px;border-radius:5px 5px 1px 1px;background:${hat};display:${d('crown')}"></span>
<span style="position:absolute;left:8px;top:-2px;width:8px;height:9px;clip-path:polygon(50% 0,100% 100%,0 100%);background:${hat};display:${d('cone')}"></span>
<span style="position:absolute;left:10px;top:-3.5px;width:4px;height:4px;border-radius:50%;background:#fff;display:${d('cone')}"></span>
<span style="position:absolute;left:9px;top:2.5px;width:6px;height:3.5px;border-radius:2px 2px 0 0;background:${hat};display:${d('stud')}"></span>
<span style="position:absolute;left:11.5px;top:1px;width:1.5px;height:5px;background:#5E8A45;display:${d('sprout')}"></span>
<span style="position:absolute;left:12.5px;top:0;width:4.5px;height:2.5px;border-radius:70% 10% 70% 10%;background:#8DB36A;display:${d('sprout')}"></span>
</span>`;
}

// Couleurs du corps selon le costume.
const PAL_JAUNE = { head: '#E9A90E', body: '#E9A90E', belly: '#F2BA2A' };
const OMBRE_TETE = 'inset -5px -6px 10px rgba(140,70,0,.28), inset 5px 5px 9px rgba(255,255,255,.35)';
const OMBRE_CORPS = 'inset -6px -7px 12px rgba(140,70,0,.28), inset 6px 5px 10px rgba(255,255,255,.3)';
const OMBRE_FROIDE = 'inset -6px -7px 12px rgba(0,0,0,.38), inset 5px 5px 9px rgba(255,255,255,.32)';
const PALETTES = {
  frog: { head: '#4E9A3A', body: '#4E9A3A', belly: '#A8D86A' },
  flocage: { head: '#2b1d66', body: '#2b1d66', belly: '#3d2a8f' },
  cafe: { ...PAL_JAUNE, body: '#C98A3E', belly: '#C98A3E' },
  cartoon: { head: '#F2D06B', body: '#2F5DA8', belly: '#2F5DA8' },
  pixel: { head: '#F2C230', body: '#F2C230', belly: '#F2C230' },
  president: { ...PAL_JAUNE, body: '#1F2A48', belly: '#1F2A48' },
  goth: { head: '#ECE8F0', body: '#1d1a22', belly: '#2a2530' },
  armure: { head: '#b3141c', body: '#b3141c', belly: '#b3141c' },
  furry: { head: '#F08A3E', body: '#F08A3E', belly: '#FFF5EA' },
  citrouille: { ...PAL_JAUNE, body: '#3a2450', belly: '#4a2e66' },
  fantome: { head: '#F4F4F8', body: '#F4F4F8', belly: '#F4F4F8' },
  sorciere: { ...PAL_JAUNE, body: '#4a2e70', belly: '#5a3a80' }
};
const SANS_JOUES = ['cafe', 'cartoon', 'pixel', 'goth', 'armure', 'brique'];

function appliquerCouleurs(R, cle) {
  const p = PALETTES[cle] || PAL_JAUNE;
  R.headBall.style.background = p.head;
  R.body.style.background = p.body;
  R.belly.style.background = p.belly;
  if (cle === 'cartoon') {
    R.headBall.style.boxShadow = R.body.style.boxShadow = '0 0 0 2px #fff';
  } else if (cle === 'goth') {
    R.headBall.style.boxShadow = 'inset -5px -6px 10px rgba(60,40,90,.28), inset 5px 5px 9px rgba(255,255,255,.4)';
    R.body.style.boxShadow = 'inset -6px -7px 12px rgba(0,0,0,.45), inset 5px 5px 9px rgba(180,140,224,.18)';
  } else {
    R.headBall.style.boxShadow = p.head !== PAL_JAUNE.head ? OMBRE_FROIDE : OMBRE_TETE;
    R.body.style.boxShadow = p.body !== PAL_JAUNE.body ? OMBRE_FROIDE : OMBRE_CORPS;
  }
  const t = THEMES[cle];
  const racine = document.documentElement.style;
  racine.setProperty('--acc', ACC[cle] || '#FFD23F');
  racine.setProperty('--bar-bg', t ? t[0] : '#2a2a2c');
  racine.setProperty('--panneau-bg', t ? (t[3] || t[0]) : '#262628');
  racine.setProperty('--bar-border', t ? t[1] : 'rgba(255,255,255,.08)');
  racine.setProperty('--bar-shadow', t ? `0 14px 40px rgba(0,0,0,.45), 0 0 22px ${t[2]}` : '0 14px 40px rgba(0,0,0,.45)');
  racine.setProperty('--icone-barre', cle ? (ACC[cle] || '#c9c9ce') : '#c9c9ce');
  racine.setProperty('--joues', SANS_JOUES.includes(cle) ? 0 : 0.85);
  racine.setProperty('--tete-z', cle === 'cafe' ? 5 : 'auto');
}

// Chaque costume a sa façon de bouger (r = rotation, x/y = décalage, t = tête penchée, sx/sy = écrasement).
function personnalite(k, s, L) {
  const S = Math.sin, A = Math.abs;
  const beat = x => { const p = x % 1; return p < 0.12 ? S(p / 0.12 * Math.PI) : p > 0.22 && p < 0.34 ? S((p - 0.22) / 0.12 * Math.PI) * 0.6 : 0; };
  const k2 = L ? 0.4 : 1;
  switch (k) {
    case 'pirate': return { r: S(s * 1.2) * 6 * k2, x: S(s * 1.2) * 2 * k2, t: S(s * 1.2 + 0.6) * 4 };
    case 'ninja': { const ph = s % 2.6; if (ph < 0.3) { const q = S(ph / 0.3 * Math.PI); return { x: q * 9 * k2, sy: -q * 0.1, sx: q * 0.06, t: -q * 8 }; } if (ph > 1.3 && ph < 1.6) { const q = S((ph - 1.3) / 0.3 * Math.PI); return { x: -q * 9 * k2, sy: -q * 0.1, sx: q * 0.06, t: q * 8 }; } return { y: 1.5, sy: -0.02 }; }
    case 'musique': return { y: -A(S(s * 4.2)) * 4, t: S(s * 4.2) * 9, r: S(s * 2.1) * 3 };
    case 'malade': return { x: S(s * 38) * 0.8, y: 1.5, t: 7 + S(s * 0.9) * 2, sy: -0.02 };
    case 'pluie': return { y: 2.5, t: 11 + S(s * 0.8) * 2, sy: S(s * 0.8) * 0.02 - 0.03 };
    case 'riche': return { r: S(s * 2) * 4, x: S(s * 2) * 2, t: -6 + S(s * 2 + 1) * 3 };
    case 'amour': { const b = beat(s * 1.3); return { y: -2 - S(s * 1.5) * 2, sx: b * 0.06, sy: b * 0.06, t: S(s * 1.1) * 6 }; }
    case 'anniv': { const h = A(S(s * 5)); return { y: -h * 6 * k2, sy: (1 - h) * -0.06 + h * 0.04, sx: (1 - h) * 0.06, t: S(s * 2.5) * 6 }; }
    case 'astro': return { y: -4 + S(s * 0.9) * 5, r: S(s * 0.6) * 9, t: S(s * 0.75) * 5 };
    case 'sport': return { y: -A(S(s * 7)) * 3.5 * k2, r: S(s * 7) * 3, t: S(s * 3.5) * 3 };
    case 'detective': { const look = S(s * 0.7); return { t: look * 13, x: look * 3, y: 1, r: look * 2 }; }
    case 'cafe': { const ph = s % 4.5; const sip = ph > 3.2 && ph < 4 ? S((ph - 3.2) / 0.8 * Math.PI) : 0; return { t: -sip * 12 + S(s * 0.9) * 2, y: 1 - sip * 1.5, sy: -0.02 }; }
    case 'france': case 'italie': return { r: S(s * 1.6) * 4, t: S(s * 1.6 + 0.8) * 6, y: -A(S(s * 1.6)) * 1.5 };
    case 'flocage': return { y: -3 + S(s * 2.4) * 3, r: S(s * 1.2) * 2 };
    case 'cartoon': return { y: (Math.floor(s * 3) % 2) * -3, r: (Math.floor(s * 1.5) % 2 ? 3 : -3) };
    case 'pixel': return { y: Math.round(S(s * 2)) * -2, x: Math.round(S(s * 1)) * 2 };
    case 'citrouille': return { r: S(s * 1.8) * 4, y: -A(S(s * 1.8)) * 2, t: S(s * 1.8 + 1) * 5 };
    case 'fantome': return { y: -7 + S(s * 1.4) * 4, x: S(s * 0.7) * 4, r: S(s * 1.4) * 5, t: S(s * 0.9) * 6 };
    case 'sorciere': return { r: S(s * 1.3) * 3, t: S(s * 1.3 + 0.5) * 6, y: -A(S(s * 2.6)) * 1.5 };
    case 'fierte': return { r: S(s * 2.5) * 5, y: -A(S(s * 2.5)) * 3, t: S(s * 2.5 + 1) * 8 };
    case 'manga': { const ph = s % 5, hop = ph > 4.2 ? S((ph - 4.2) / 0.8 * Math.PI) : 0; return { y: -hop * 8 + S(s * 0.9) * 1, sx: S(s * 0.9) * 0.03 - hop * 0.04, sy: -S(s * 0.9) * 0.03 + hop * 0.06, t: S(s * 0.6) * 6 }; }
    case 'furry': return { r: S(s * 3) * 4, y: -A(S(s * 3)) * 2.5, t: S(s * 3 + 1) * 7 };
    case 'brique': { const st = Math.floor(s * 1.6) % 4; return { r: [0, 4, 0, -4][st], t: [0, -5, 0, 5][st], y: st % 2 ? -2 : 0 }; }
    case 'armure': return { y: -7 + S(s * 2.2) * 2.5, r: S(s * 1.1) * 3, x: S(s * 0.8) * 2 };
    case 'goth': return { t: 7 + S(s * 0.6) * 3, y: 1, r: S(s * 0.6) * 2, sy: -0.02 };
    case 'president': return { r: S(s * 1.4) * 3, t: -6 + S(s * 1.4 + 0.7) * 4, x: S(s * 0.7) * 2 };
    case 'cuir': return { r: S(s * 1.3) * 3, x: S(s * 1.3) * 1.5, t: -4 + S(s * 1.3 + 1) * 3 };
    case 'noel': return { r: S(s * 1.5) * 4, t: S(s * 1.5 + 0.5) * 7, y: -A(S(s * 1.5)) * 1.5 };
    default: return null;
  }
}
