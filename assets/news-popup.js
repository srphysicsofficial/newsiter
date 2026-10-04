'use strict';
(() => {
 if(window.top!==window.self||document.body.dataset.page==='admin')return;
 const seenKey='sr-latest-news-dismissed';
 function seen(id){try{return sessionStorage.getItem(seenKey)===String(id);}catch{return false;}}
 function mark(id){try{sessionStorage.setItem(seenKey,String(id));}catch{}}
 async function start(){
  try{
   window.SRNewsPromise ||= fetch('/api/news',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('News unavailable');return r.json();});
   const data=await window.SRNewsPromise;
   const latest=(data.items||[]).filter(n=>n.status==='published').sort((a,b)=>Number(b.id)-Number(a.id))[0];
   if(!latest||seen(latest.id))return;
   const popup=document.createElement('dialog');popup.id='latestNewsPopup';popup.setAttribute('aria-labelledby','latestNewsTitle');
   popup.innerHTML='<div class="sr-popup-top"><span>LATEST NEWS / SR PHYSICS</span><button type="button" class="sr-popup-close" aria-label="Close latest news">✕</button></div><div class="sr-popup-body"><div class="sr-popup-image"></div><p class="sr-popup-date"></p><h2 id="latestNewsTitle"></h2><p class="sr-popup-description"></p><div class="sr-popup-actions"><button type="button" class="sr-popup-continue">Continue to website →</button><a href="/#news">View all news</a></div></div>';
   popup.querySelector('h2').textContent=latest.title;
   popup.querySelector('.sr-popup-description').textContent=latest.description||'';
   const date=new Date(String(latest.created_at).replace(' ','T')+'Z');popup.querySelector('.sr-popup-date').textContent=Number.isNaN(+date)?'':date.toLocaleDateString(undefined,{year:'numeric',month:'long',day:'numeric'});
   if(latest.image_url){try{const url=new URL(latest.image_url,location.origin);if(['https:','http:'].includes(url.protocol)){const img=new Image();img.src=url.href;img.alt=latest.title;img.onerror=()=>img.remove();popup.querySelector('.sr-popup-image').append(img);}}catch{}}
   document.body.append(popup);let overflow='';
   const dismiss=()=>{mark(latest.id);popup.close();};popup.querySelector('.sr-popup-close').onclick=dismiss;popup.querySelector('.sr-popup-continue').onclick=dismiss;popup.querySelector('a').onclick=dismiss;popup.addEventListener('cancel',()=>mark(latest.id));
   popup.addEventListener('close',()=>{mark(latest.id);document.body.style.overflow=overflow;popup.remove();});
   popup.addEventListener('click',e=>{if(e.target===popup){const r=popup.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dismiss();}});
   function show(){if(seen(latest.id)){popup.remove();return;}if(document.hidden||document.getElementById('loader')||document.querySelector('dialog[open]')){setTimeout(show,300);return;}overflow=document.body.style.overflow;popup.showModal();document.body.style.overflow='hidden';}
   show();
  }catch{/* News failure must never block the website. The homepage provides retry. */}
 }
 start();
})();
