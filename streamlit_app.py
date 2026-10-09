import streamlit.components.v1 as components

components.html("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
 body{margin:0;background:black;overflow:hidden;text-align:center;color:white;font-family:monospace}
 #ui{position:absolute;top:10px;left:10px;z-index:10;background:rgba(0,0,0,0.7);padding:10px;border-radius:10px}
 #cross{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:30px;z-index:5;color:red}
 button{padding:8px 12px;margin:3px;border-radius:8px;font-weight:bold}
 canvas{display:block}
</style>
<script type="importmap">
{ "imports": { "three": "https://unpkg.com/three@0.160.0/build/three.module.js" } }
</script>
</head>
<body>
<div id="ui">
 ❤️ <span id="hp">100</span> | 💀 KILL <span id="kill">0</span><br>
 <button onclick="moveL()">⬅️</button>
 <button onclick="shoot()" style="background:red;color:white">🔫 TEMBAK</button>
 <button onclick="moveR()">➡️</button><br>
 <button onclick="moveF()">⬆️ MAJU</button>
 <button onclick="moveB()">⬇️ MUNDUR</button>
</div>
<div id="cross">+</div>

<script type="module">
import * as THREE from 'three';

let scene = new THREE.Scene();
scene.background = new THREE.Color(0x87CEEB);
scene.fog = new THREE.Fog(0x87CEEB, 20, 60);

let camera = new THREE.PerspectiveCamera(75, 360/580, 0.1, 1000);
camera.position.set(0,3,10);

let renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(360,580);
document.body.appendChild(renderer.domElement);

// tanah
let ground = new THREE.Mesh(new THREE.PlaneGeometry(100,100), new THREE.MeshStandardMaterial({color:0x228B22}));
ground.rotation.x = -Math.PI/2; scene.add(ground);
scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.2));
let dirLight = new THREE.DirectionalLight(0xffffff, 0.8); dirLight.position.set(10,20,10); scene.add(dirLight);

// player = kamera
let hp=100,kill=0;
let enemies=[];
let bullets=[];

function spawnEnemy(){
  let geo = new THREE.BoxGeometry(1,2,1);
  let mat = new THREE.MeshStandardMaterial({color:0xff0000});
  let m = new THREE.Mesh(geo,mat);
  m.position.set((Math.random()-0.5)*30,1, -20 - Math.random()*30);
  m.userData.hp=1;
  scene.add(m); enemies.push(m);
}
for(let i=0;i<5;i++) spawnEnemy();

function shoot(){
  // suara dor
  let ctx=new (window.AudioContext||window.webkitAudioContext)(); let o=ctx.createOscillator(); o.frequency.value=800; o.connect(ctx.destination); o.start(); o.stop(ctx.currentTime+0.1);
  let geo=new THREE.SphereGeometry(0.15,8,8); let mat=new THREE.MeshBasicMaterial({color:0xffff00});
  let b=new THREE.Mesh(geo,mat);
  b.position.copy(camera.position);
  b.userData.dir=new THREE.Vector3(0,0,-1).applyQuaternion(camera.quaternion);
  scene.add(b); bullets.push(b);
  setTimeout(()=>{ scene.remove(b); bullets.splice(bullets.indexOf(b),1); },2000);
}

function moveL(){ camera.position.x-=1; }
function moveR(){ camera.position.x+=1; }
function moveF(){ camera.translateZ(-1); }
function moveB(){ camera.translateZ(1); }
window.moveL=moveL; window.moveR=moveR; window.moveF=moveF; window.moveB=moveB; window.shoot=shoot;

let keys={};
window.addEventListener('keydown',e=>keys[e.key.toLowerCase()]=true);
window.addEventListener('keyup',e=>keys[e.key.toLowerCase()]=false);

function animate(){
  requestAnimationFrame(animate);

  if(keys['w']||keys['ArrowUp']) moveF();
  if(keys['s']||keys['ArrowDown']) moveB();
  if(keys['a']||keys['ArrowLeft']) moveL();
  if(keys['d']||keys['ArrowRight']) moveR();
  if(keys[' ']) { if(!window.lastShot||Date.now()-window.lastShot>200){shoot(); window.lastShot=Date.now();} }

  // peluru jalan
  bullets.forEach(b=>{ b.position.add(b.userData.dir.clone().multiplyScalar(0.8)); });

  // musuh ngejar + cek kena
  enemies.forEach((en,idx)=>{
    if(!en.parent) return;
    let dir=new THREE.Vector3().subVectors(camera.position, en.position); dir.y=0; dir.normalize().multiplyScalar(0.05);
    en.position.add(dir);
    en.lookAt(camera.position);

    bullets.forEach(bu=>{
      if(en.position.distanceTo(bu.position)<1.2){
        scene.remove(en); scene.remove(bu);
        enemies.splice(idx,1); kill++; document.getElementById('kill').innerText=kill;
        if(kill%5==0){ for(let i=0;i<2;i++) spawnEnemy(); }
        setTimeout(spawnEnemy,1000);
      }
    });
    if(en.position.distanceTo(camera.position)<2){
      hp-=0.5; document.getElementById('hp').innerText=Math.floor(hp);
      if(hp<=0){ alert('💀 KAMU GUGUR! KILL:'+kill); hp=100; kill=0; camera.position.set(0,3,10); }
    }
  });

  // mouse drag buat muter kamera
  renderer.render(scene,camera);
}
animate();

// drag mouse = muter
let isDrag=false,lastX=0;
renderer.domElement.addEventListener('mousedown',e=>{isDrag=true;lastX=e.clientX;});
renderer.domElement.addEventListener('mouseup',()=>isDrag=false);
renderer.domElement.addEventListener('mousemove',e=>{
  if(isDrag){ let dx=e.clientX-lastX; camera.rotation.y-=dx*0.01; lastX=e.clientX; }
});
renderer.domElement.addEventListener('touchmove',e=>{
  let dx=e.touches[0].clientX-lastX; camera.rotation.y-=dx*0.01; lastX=e.touches[0].clientX;
});
renderer.domElement.addEventListener('click',shoot);
</script>
</body>
</html>
""", height=700)
