import streamlit.components.v1 as components

components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  body { margin:0; background:#87CEEB; font-family: 'Press Start 2P', monospace; text-align:center; overflow:hidden }
  #game { width:360px; height:640px; background:#7CFC00; margin:auto; position:relative; border:4px solid #654321; overflow:hidden; }
  #kampung { width:100%; height:100px; background:#DEB887; position:absolute; bottom:0; }
  #kandang { position:absolute; right:10px; bottom:20px; font-size:60px; }
  .ayam { position:absolute; font-size:40px; transition: all 0.3s; }
  #maling { position:absolute; font-size:45px; left:10px; bottom:80px; transition:left 0.2s; }
  #btns { margin-top:10px; }
  button { padding:12px 10px; font-size:16px; margin:5px; border-radius:12px; border:none; font-weight:bold; }
  #score { background:white; padding:8px; border-radius:10px; display:inline-block; margin:5px; }
</style>
</head>
<body>
<div id="score">🐔 <span id="ayamCount">5</span> | 🪙 <span id="koin">0</span> | ❤️ <span id="nyawa">3</span></div>
<div id="game">
  <div id="kampung"></div>
  <div id="kandang">🏠</div>
  <div id="maling">🦹‍♂️</div>
</div>
<div id="btns">
  <button onclick="senter()" style="background:#FFD700">🔦 SENTER</button>
  <button onclick="jebak()" style="background:#FF6347">🪤 JEBAK</button>
  <button onclick="anjing()" style="background:#8B4513; color:white">🐕 ANJING</button>
</div>
<p id="log" style="background:white; width:340px; margin:10px auto; padding:5px; border-radius:8px; font-size:12px; height:60px; overflow:auto">Malam sunyi... ayam petok petok...</p>

<script>
let ayamCount = 5, koin = 0, nyawa = 3, posMaling = 10;
let malingEl = document.getElementById('maling');
let gameEl = document.getElementById('game');
let audioContext = new (window.AudioContext || window.webkitAudioContext)();

function playSound(freq, dur){
  let o = audioContext.createOscillator();
  let g = audioContext.createGain();
  o.frequency.value = freq;
  o.connect(g); g.connect(audioContext.destination);
  o.start(); g.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + dur);
  o.stop(audioContext.currentTime + dur);
}

function log(t){ document.getElementById('log').innerHTML = t + '<br>' + document.getElementById('log').innerHTML; }

function spawnAyam(){
  gameEl.querySelectorAll('.ayam').forEach(e=>e.remove());
  for(let i=0;i<ayamCount;i++){
    let a = document.createElement('div');
    a.className='ayam';
    a.innerHTML='🐔';
    a.style.left = (200 + Math.random()*100)+'px';
    a.style.bottom = (30 + Math.random()*50)+'px';
    a.style.transform = `scale(${0.8+Math.random()*0.5})`;
    gameEl.appendChild(a);
    // ayam lari dikit-dikit
    setInterval(()=>{
      a.style.left = (parseInt(a.style.left) + (Math.random()*20-10))+'px';
      a.style.bottom = (30 + Math.random()*60)+'px';
    }, 800);
  }
}

function updateUI(){
  document.getElementById('ayamCount').innerText=ayamCount;
  document.getElementById('koin').innerText=koin;
  document.getElementById('nyawa').innerText=nyawa;
  malingEl.style.left = posMaling+'px';
}

function senter(){
  playSound(800,0.2);
  posMaling = Math.max(10, posMaling-60);
  log('🔦 SENTER! Maling silau mundur!');
  updateUI();
}
function jebak(){
  playSound(200,0.4);
  if(Math.random()>0.4){
    posMaling=10; koin+=2;
    log('🪤 JEBAKAN KENA! +2 koin!');
  } else {
    posMaling+=20;
    log('💨 Jebakan meleset!');
  }
  updateUI();
}
function anjing(){
  if(koin>=1){ 
    koin--; playSound(120,0.5); playSound(300,0.3);
    posMaling=10;
    log('🐕 GUK GUK GUK! Maling kabur!');
  } else log('❌ Butuh 1 koin buat pakan anjing!');
  updateUI();
}

// maling jalan otomatis
setInterval(()=>{
  if(ayamCount<=0 || nyawa<=0) return;
  posMaling += 8 + Math.random()*15;
  if(posMaling >= 270){
    ayamCount--; nyawa--; posMaling=10;
    playSound(100,0.8);
    log('😭 AYAM HILANG! Petok!!');
    spawnAyam();
    if(ayamCount<=0){ log('💀 GAME OVER - Ayam habis!'); alert('GAME OVER!'); }
  }
  updateUI();
  // ayam nelor
  if(Math.random()>0.85){ koin++; log('🥚 Petok petok! Telur +1'); playSound(600,0.15); updateUI(); }
}, 700);

spawnAyam();
updateUI();
</script>
</body>
</html>
""", height=780)
