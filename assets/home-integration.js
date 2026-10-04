'use strict';
(async function loadNews(){
  const root=document.getElementById('homeNews');if(!root)return;
  try{
    window.SRNewsPromise ||= fetch('/api/news',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('Unavailable');return r.json();});const data=await window.SRNewsPromise;
    const items=(data.items||[]).filter(i=>i.status==='published');root.replaceChildren();
    if(!items.length){const p=document.createElement('p');p.className='sr-empty';p.textContent='No new announcements yet. Visit the Magic Portal for learning resources.';root.append(p);}
    for(const item of items){const card=document.createElement('article');const title=document.createElement('h3');title.textContent=item.title;const text=document.createElement('p');text.textContent=item.description||'';if(item.image_url){try{const url=new URL(item.image_url,location.origin);if(['https:','http:'].includes(url.protocol)){const img=new Image();img.src=url.href;img.alt='';img.loading='lazy';img.onerror=()=>img.remove();card.append(img);}}catch{}}
      card.append(title,text);root.append(card);}
  }catch{root.replaceChildren();const p=document.createElement('p');p.className='sr-empty';p.textContent='Announcements could not be loaded. ';const b=document.createElement('button');b.textContent='Try again';b.onclick=()=>{window.SRNewsPromise=null;loadNews();};p.append(b);root.append(p);}
})();

// Keep content visible when optional CDN animation libraries are unavailable.
(() => {
  if (!(window.gsap && window.ScrollTrigger) || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.documentElement.classList.add('sr-native-reveal');
    document.querySelectorAll('.stat-num[data-count]').forEach(el => { el.textContent=el.dataset.count; });
  }
})();

// The embedded form uses the same paper-wise UI and API as the full page.
addEventListener('message', event => {
  const frame=document.getElementById('homePaperFrame');
  if(!frame||event.origin!==location.origin||event.source!==frame.contentWindow||event.data?.type!=='sr-paper-height')return;
  const height=Number(event.data.height);
  if(Number.isFinite(height)&&height>0&&height<10000)frame.style.height=Math.ceil(height)+'px';
});

(() => {
 const form=document.getElementById('homeJoinForm');if(!form)return;
 form.addEventListener('submit',async event=>{
  event.preventDefault();const button=form.querySelector('[type=submit]'),message=form.querySelector('.form-status');if(button.disabled)return;
  const data=Object.fromEntries(new FormData(form));button.disabled=true;message.className='form-status';message.textContent='Sending your class request…';
  try{const response=await fetch('/api/join-request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||'Could not send your request. Please try again.');form.reset();message.className='form-status success';message.textContent='Thank you! Your class request has been sent. Our team will follow up.';}
  catch(error){message.className='form-status error';message.textContent=error.message||'Could not send your request. Please try again.';}
  finally{button.disabled=false;}
 });
})();
