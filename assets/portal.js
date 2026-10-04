'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const escape = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  async function api(path, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(path, {credentials:'same-origin', ...options, signal:controller.signal});
      const data = await response.json();
      if (!response.ok || data.ok === false) {const err = new Error(data.error || 'Could not complete this request.'); err.status = response.status; throw err;}
      return data;
    } catch(error) {
      if (error.name === 'AbortError') throw new Error('The request timed out. Check your connection before retrying.');
      throw error;
    } finally {clearTimeout(timeout);}
  }
  const post = (path, data, method='POST') => api(path, {method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  function status(el, text, error=false) {el.textContent=text; el.className='form-status '+(error?'error':'success');}
  function safeUrl(value) {try {const url=new URL(value,location.origin); return ['http:','https:'].includes(url.protocol)?url.href:'';} catch {return '';}}
  function date(value) {const d=new Date(String(value).replace(' ','T')+'Z');return Number.isNaN(+d)?String(value||''):d.toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'});}
  function failure(el, error, retry) {
    el.replaceChildren();const box=document.createElement('div');box.className='empty';
    const p=document.createElement('p');p.textContent=error.message || 'Unable to load. Check your connection.';box.append(p);
    if(retry){const b=document.createElement('button');b.className='action';b.textContent='Try again';b.onclick=retry;box.append(b);}el.append(box);
  }
  window.SR={api,post,escape,status,safeUrl,date,failure};
  document.querySelector('.menu-toggle')?.addEventListener('click', e => {
    const open=$('portal-links').classList.toggle('open');e.currentTarget.setAttribute('aria-expanded',String(open));
  });
  if(document.body.dataset.page==='papers'){
    let papers=[],current=null,busy=false; const drafts=new Map();const form=$('paperForm');
    for(const [id,name,values] of [['mcqQuestions','mcq',Array.from({length:50},(_,i)=>i+1)],['structuredQuestions','structured',[1,2,3,4]],['essayQuestions','essays',['6','7','8','9A','9B','10A','10B']]]){
      $(id).innerHTML=values.map(q=>`<label class="question"><input type="checkbox" name="${name}" value="${q}" aria-label="${name} question ${q}"><span>${q}</span></label>`).join('');
    }
    function snapshot(){const d=Object.fromEntries(new FormData(form));for(const k of ['mcq','structured','essays'])d[k]=new FormData(form).getAll(k);return d;}
    function count(){$('selectionCount').textContent=form.querySelectorAll('input[type=checkbox]:checked').length+' questions selected';}
    form.addEventListener('change',count);
    function renderList(){
      const term=$('paperSearch').value.toLowerCase(); const list=papers.filter(p=>(p.name+' '+(p.description||'')).toLowerCase().includes(term));
      $('paperList').innerHTML=list.map(p=>`<button type="button" class="paper-item" data-paper="${p.id}" aria-pressed="${current?.id===p.id}" ${busy?'disabled':''}><strong>${escape(p.name)}</strong><small>Paper #${p.id} · ${date(p.created_at)}<br>Ends ${new Date(new Date(p.created_at.replace(' ','T')+'Z').getTime()+7*86400000).toLocaleString()}</small></button>`).join('') || '<div class="empty">'+(papers.length?'No matching papers.':'No current paper. Please check back after your teacher publishes the next paper.')+'</div>';
      $('paperList').querySelectorAll('button').forEach(b=>b.onclick=()=>select(Number(b.dataset.paper)));
    }
    function select(id){
      if(busy)return;
      if(current)drafts.set(current.id,snapshot());
      current=papers.find(p=>p.id===id);if(!current)return;
      form.reset();$('paperStatus').textContent='';$('paperEmpty').hidden=true;form.hidden=false;
      $('paperTitle').textContent=current.name;$('paperDescription').textContent=current.description||'';
      const draft=drafts.get(id);if(draft){for(const k of ['name','batch','comment'])form.elements[k].value=draft[k]||'';for(const k of ['mcq','structured','essays'])form.querySelectorAll(`input[name="${k}"]`).forEach(x=>x.checked=(draft[k]||[]).includes(x.value));}
      const url=new URL(location.href);url.searchParams.set('paper',id);history.replaceState(null,'',url);
      renderList();count();
    }
    $('paperSearch').oninput=renderList;
    async function load(){if(busy)return;try{papers=(await api('/api/papers')).items;const latest=papers[0];if(!latest){current=null;form.hidden=true;$('paperEmpty').hidden=false;drafts.clear();$('paperEmpty').innerHTML='<h2>No current paper</h2><p>The previous paper has ended. Your teacher will publish the next paper here.</p>';}else if(current?.id!==latest.id){drafts.clear();select(latest.id);}else{current=latest;$('paperTitle').textContent=latest.name;$('paperDescription').textContent=latest.description||'';}renderList();}catch(e){failure($('paperList'),e,load);}}
    setInterval(()=>{if(!document.hidden)load();},15000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)load();});
    form.onsubmit=async e=>{
      e.preventDefault();if(busy||!current)return;const data=snapshot();
      if(!data.mcq.length&&!data.structured.length&&!data.essays.length){status($('paperStatus'),'Select at least one question before sending.',true);return;}
      const submittedPaper=current;busy=true;const controls=[...form.querySelectorAll('input,select,textarea,button')];controls.forEach(x=>x.disabled=true);renderList();
      status($('paperStatus'),'Sending feedback for '+submittedPaper.name+'…');
      try{await post(`/api/papers/${submittedPaper.id}/feedback`,data);drafts.delete(submittedPaper.id);form.reset();count();status($('paperStatus'),'Thank you! Your feedback was saved for '+submittedPaper.name+'.');}
      catch(err){status($('paperStatus'),err.message,true);}
      finally{busy=false;controls.forEach(x=>x.disabled=false);renderList();}
    };load();
  }
  if(document.body.dataset.page==='sessions'){
    let items=[];
    function videoId(value){try{const u=new URL(value),host=u.hostname.replace(/^www\./,'');let id=host==='youtu.be'?u.pathname.split('/')[1]:['youtube.com','m.youtube.com','youtube-nocookie.com'].includes(host)?(u.searchParams.get('v')||u.pathname.split('/')[2]):'';return /^[\w-]{11}$/.test(id||'')?id:'';}catch{return '';}}
    function render(){const q=$('sessionSearch').value.toLowerCase(),list=items.filter(i=>(i.title+' '+(i.description||'')).toLowerCase().includes(q));
      $('sessionsList').innerHTML=list.map(i=>{const id=videoId(i.youtube_url);return `<article class="content-card session-card">${id?`<button class="session-cover" data-video="${id}" data-title="${escape(i.title)}" aria-label="Play ${escape(i.title)}"><img src="https://i.ytimg.com/vi/${id}/hqdefault.jpg" alt="${escape(i.title)} — video thumbnail" loading="lazy"><span class="session-play" aria-hidden="true">▶</span></button>`:''}<span class="eyebrow">SESSION · ${date(i.created_at)}</span><h2>${escape(i.title)}</h2><p>${escape(i.description)}</p>${id?`<button class="action primary" data-video="${id}" data-title="${escape(i.title)}">Watch session ▶</button>`:'<p>Session link unavailable.</p>'}</article>`;}).join('')||'<p class="empty">'+(items.length?'No matching sessions.':'No sessions have been published yet. Check back after class.')+'</p>';
      $('sessionsList').querySelectorAll('img').forEach(img=>img.onerror=()=>{img.hidden=true;});
    }
    const viewer=document.createElement('dialog');viewer.id='sessionViewer';viewer.setAttribute('aria-labelledby','sessionViewerTitle');viewer.innerHTML='<div class="dialog-heading"><h2 id="sessionViewerTitle"></h2><button class="action" id="sessionClose" aria-label="Close session">✕</button></div><div class="session-player"><iframe id="sessionFrame" title="Session video" allow="autoplay; encrypted-media; fullscreen; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div><p class="hint">Use the video controls to pause, change quality or enter fullscreen. Playback requires internet and permission from the video owner to embed.</p>';document.body.append(viewer);
    $('sessionsList').onclick=e=>{const b=e.target.closest('[data-video]');if(!b)return;$('sessionViewerTitle').textContent=b.dataset.title;$('sessionFrame').title=b.dataset.title;viewer.showModal();document.body.style.overflow='hidden';$('sessionFrame').src='https://www.youtube-nocookie.com/embed/'+b.dataset.video+'?autoplay=1&rel=0';};
    $('sessionClose').onclick=()=>viewer.close();viewer.addEventListener('close',()=>{$('sessionFrame').src='about:blank';document.body.style.overflow='';});
    async function load(){try{items=(await api('/api/sessions')).items.filter(i=>i.status==='published');render();}catch(e){failure($('sessionsList'),e,load);}}
    $('sessionSearch').oninput=render;load();
  }
  if(document.body.dataset.page==='simulations'){
    const sims=[['Mechanics','Masses and springs','masses-and-springs','Explore oscillations and spring forces.'],['Mechanics',"Hooke’s law",'hookes-law','Investigate spring constant, force and extension.'],['Mechanics','Balancing act','balancing-act','Balance torques and understand equilibrium.'],['Mechanics','Collision lab','collision-lab','Investigate momentum and collisions.'],['Mechanics','Gravity force lab','gravity-force-lab','Measure gravitational attraction between masses.'],['Mechanics','Gravity and orbits','gravity-and-orbits','Explore orbital motion and gravity.'],['Electricity',"Coulomb’s law",'coulombs-law','Explore the force between electric charges.'],['Electricity',"Faraday’s law",'faradays-law','Move a magnet to induce a current.'],['Electricity','Resistance in a wire','resistance-in-a-wire','Investigate length, area and resistivity.'],['Electricity','AC circuit construction','circuit-construction-kit-ac','Build and explore alternating-current circuits.'],['Waves & optics','Wave on a string','wave-on-a-string','Explore travelling and standing waves.'],['Waves & optics','Waves intro','waves-intro','Compare water, sound and light waves.'],['Thermal physics','Gas properties','gas-properties','Explore pressure, volume and temperature.'],['Thermal physics','Energy forms and changes','energy-forms-and-changes','Explore energy transfer and transformation.'],['Thermal physics','States of matter','states-of-matter-basics','Explore the particle model of matter.'],['Fluids','Under pressure','under-pressure','Investigate pressure at different depths.'],['Fluids','Density','density','Compare mass, volume and density.'],['Atomic physics','Build an atom','build-an-atom','Explore protons, neutrons and electrons.'],['Atomic physics','Rutherford scattering','rutherford-scattering','Explore evidence for the nuclear atom.'],['Mechanics','Forces and motion','forces-and-motion-basics','Explore force, friction and acceleration.'],['Mechanics','Energy skate park','energy-skate-park-basics','Follow kinetic and potential energy along a track.'],['Mechanics','Pendulum lab','pendulum-lab','Investigate period, length and gravity.'],['Mechanics','Projectile motion','projectile-motion','Explore trajectories, launch angles and air resistance.'],['Electricity',"Ohm’s law",'ohms-law','Connect voltage, current and resistance.'],['Electricity','Circuit construction kit: DC','circuit-construction-kit-dc','Build and investigate your own circuits.'],['Electricity','Capacitor lab: basics','capacitor-lab-basics','Change plate area, separation and voltage.'],['Electricity','Charges and fields','charges-and-fields','Explore electric fields and equipotential lines.'],['Waves & optics','Wave interference','wave-interference','Investigate superposition and interference.'],['Waves & optics','Bending light','bending-light','Explore reflection and refraction between media.'],['Waves & optics','Geometric optics','geometric-optics','Investigate images formed by lenses and mirrors.']];
    for(const cat of [...new Set(sims.map(s=>s[0]))]){if(![...$('simCategory').options].some(o=>o.value===cat))$('simCategory').add(new Option(cat,cat));}
    function render(){const q=$('simSearch').value.toLowerCase(),cat=$('simCategory').value;
      $('simulationsList').innerHTML=sims.filter(s=>(!cat||s[0]===cat)&&s.join(' ').toLowerCase().includes(q)).map(s=>`<article class="content-card"><span class="eyebrow">${escape(s[0])}</span><h2>${escape(s[1])}</h2><p>${escape(s[3])}</p><button type="button" class="action sim-launch" data-sim="${s[2]}" data-title="${escape(s[1])}">Open simulation ↗</button></article>`).join('')||'<p class="empty">No matching experiments.</p>';
    }$('simSearch').oninput=render;$('simCategory').onchange=render;render();
    setupSimulationViewer();
  }
  function setupSimulationViewer(){
    const dialog=document.createElement('dialog');dialog.id='simulationViewer';dialog.setAttribute('aria-labelledby','simulationTitle');
    dialog.innerHTML='<div class="sim-viewer-head"><div><p class="eyebrow">SR PHYSICS / INTERACTIVE LAB</p><h2 id="simulationTitle"></h2></div><div class="sim-viewer-actions"><button class="action" id="simReload" type="button">Reload</button><button class="action" id="simFullscreen" type="button">Fullscreen ⛶</button><button class="action" id="simClose" type="button" aria-label="Close simulation">✕</button></div></div><p id="simLoadStatus" role="status">Loading simulation…</p><div class="sim-frame-wrap"><iframe id="simFrame" title="Physics simulation" allow="fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div><p class="hint">Powered by PhET, University of Colorado Boulder. If the experiment stays blank, check your internet connection and use Reload.</p>';
    document.body.append(dialog);let timer=null,url='';const frame=$('simFrame');
    function load(){clearTimeout(timer);$('simLoadStatus').textContent='Loading simulation…';frame.src=url;timer=setTimeout(()=>{$('simLoadStatus').textContent='Taking longer than expected. Check your connection, then try Reload.';},15000);}
    frame.addEventListener('load',()=>{if(!dialog.open||frame.getAttribute('src')==='about:blank')return;clearTimeout(timer);$('simLoadStatus').textContent='Use the controls inside the experiment to explore.';});
    $('simulationsList').addEventListener('click',e=>{const b=e.target.closest('[data-sim]');if(!b)return;url='https://phet.colorado.edu/sims/html/'+b.dataset.sim+'/latest/'+b.dataset.sim+'_en.html';$('simulationTitle').textContent=b.dataset.title;frame.title=b.dataset.title+' simulation';dialog.showModal();document.body.style.overflow='hidden';load();});
    $('simClose').onclick=()=>dialog.close();$('simReload').onclick=load;
    $('simFullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else if(dialog.requestFullscreen)await dialog.requestFullscreen();else $('simLoadStatus').textContent='Fullscreen is unavailable in this browser.';}catch{$('simLoadStatus').textContent='Fullscreen is unavailable. You can continue in this window.';}};
    dialog.addEventListener('close',()=>{clearTimeout(timer);frame.src='about:blank';document.body.style.overflow='';if(document.fullscreenElement===dialog)document.exitFullscreen().catch(()=>{});});
    dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
  }
  if(document.body.dataset.page==='papers'&&new URLSearchParams(location.search).get('embedded')==='1'){
    document.body.classList.add('embedded-paper');const main=$('main');let last=0;
    const resize=()=>{const height=Math.ceil(main.getBoundingClientRect().height)+16;if(height!==last){last=height;parent.postMessage({type:'sr-paper-height',height},location.origin);}};
    new ResizeObserver(resize).observe(main);resize();
  }
  document.querySelectorAll('.community-form').forEach(form=>form.onsubmit=async e=>{
    e.preventDefault();const button=form.querySelector('[type=submit]');if(button.disabled)return;
    const data=Object.fromEntries(new FormData(form));button.disabled=true;const box=form.querySelector('.form-status');status(box,'Sending…');
    try{await post('/api/'+form.dataset.endpoint,data);form.reset();status(box,'Thank you. Your message has been sent to the SR Physics team.');}catch(err){status(box,err.message,true);}finally{button.disabled=false;}
  });
})();
