'use strict';
(() => {
 const {api,post,escape,status,date,safeUrl}=window.SR;
 const $=id=>document.getElementById(id);
 const sections={requests:'Class requests',comments:'Reviews',complaints:'Suggestions',doubts:'Questions',news:'News',sessions:'Sessions',papers:'Current paper',paper_feedback:'Paper feedback'};
 const definitions={news:[['title','Title',true],['image_url','Image URL',false],['description','Description',false,'textarea']],sessions:[['title','Title',true],['youtube_url','YouTube URL',true],['description','Description',false,'textarea']],papers:[['name','Paper name',true],['description','Description',false,'textarea']]};
 let store={},active='requests',loading=false,editing=null,editorType='',paperFilterInitialized=false;
 const message=(text,error=false)=>status($('adminStatus'),text,error);
 function loggedIn(value){$('adminLogin').hidden=value;$('adminDashboard').hidden=!value;if(!value){store={};$('adminItems').replaceChildren();$('adminPassword').value='';}}
 function unauthorized(error){if(error.status===401){loggedIn(false);status($('loginForm').querySelector('.form-status'),'Your session has expired. Please sign in again.',true);return true;}return false;}
 function paperName(id){return (store.papers||[]).find(p=>Number(p.id)===Number(id))?.name||'Paper #'+id;}
 function feedbackForPaper(){const id=$('adminPaperFilter').value;return (store.paper_feedback||[]).filter(r=>!id||String(r.paper_id)===id);}
 function filtered(){let items=active==='paper_feedback'?feedbackForPaper():(store[active]||[]);const q=$('adminSearch').value.toLowerCase();const filter=$('adminStatusFilter').value;
  return items.filter(r=>(!filter||r.status===filter)&&(!q||(JSON.stringify(r)+(active==='paper_feedback'?paperName(r.paper_id):'')).toLowerCase().includes(q)));}
 function parse(value){try{const array=JSON.parse(value||'[]');return Array.isArray(array)?array:[];}catch{return [];}}
 async function load(){if(loading)return;loading=true;$('adminRefresh').disabled=true;message('Loading console…');
  try{const snapshot=await api('/api/admin/snapshot');store=snapshot.items;
    const old=$('adminPaperFilter').value;
    $('adminPaperFilter').innerHTML=store.papers.map(p=>`<option value="${p.id}">${escape(p.name)} (#${p.id})${p.status==='archived'?' — archived':''}</option>`).join('');
    if(!paperFilterInitialized){$('adminPaperFilter').value=String(store.papers[0]?.id||'');paperFilterInitialized=true;}else if(store.papers.some(p=>String(p.id)===old))$('adminPaperFilter').value=old;
    const total=['requests','comments','complaints','doubts','paper_feedback'].flatMap(t=>store[t]);$('adminCounts').textContent=total.length+' submissions · '+total.filter(r=>r.status==='new').length+' new';
    render();message('Console up to date.');
  }catch(err){if(!unauthorized(err))message('Could not refresh: '+err.message,true);}finally{loading=false;$('adminRefresh').disabled=false;}
 }
 $('adminTabs').innerHTML=Object.entries(sections).map(([key,label])=>`<button type="button" data-section="${key}" aria-pressed="${key===active}">${label}</button>`).join('');
 $('adminTabs').onclick=e=>{const b=e.target.closest('button');if(!b)return;active=b.dataset.section;$('adminSearch').value='';$('adminStatusFilter').value='';render();};
 function render(){
   $('adminTabs').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.section===active)));
   $('adminAdd').hidden=!definitions[active];$('adminAdd').textContent=(active==='papers'&&store.papers?.length?'Replace ':'Add ')+(active==='papers'?'paper':active==='news'?'announcement':'session')+' +';
   $('adminPaperFilterWrap').hidden=true;$('adminStats').hidden=active!=='paper_feedback';
   const items=filtered();$('adminItems').innerHTML=items.map(card).join('')||'<div class="empty"><h2>No items to show</h2><p>Add a resource or adjust your filters.</p></div>';
   if(active==='paper_feedback')renderStats();
 }
 function renderStats(){
   // Counts are always derived from this paper, never the backend's all-paper stats endpoint.
   const rows=filtered(), counts={mcq:{},structured:{},essays:{}};
   rows.forEach(r=>Object.keys(counts).forEach(k=>parse(r[k]).forEach(q=>counts[k][q]=(counts[k][q]||0)+1)));
   const heading=$('adminPaperFilter').value?paperName($('adminPaperFilter').value):'Current paper';
   $('adminStats').innerHTML=`<p class="eyebrow">QUESTION SUMMARY / CURRENT FILTERS</p><h2>${escape(heading)}</h2><p class="muted">${rows.length} feedback submission${rows.length===1?'':'s'}. Counts show how many students flagged each question.</p><div class="stats-columns">`+Object.entries(counts).map(([key,map])=>`<div><h3>${{mcq:'Multiple choice',structured:'Structured',essays:'Essays'}[key]}</h3>`+(Object.entries(map).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],undefined,{numeric:true})).map(([q,n])=>`<div class="question-stat"><span>Q${escape(q)}</span><meter min="0" max="${Math.max(rows.length,1)}" value="${n}" aria-label="Question ${escape(q)}: ${n} students"></meter><strong>${n}</strong></div>`).join('')||'<p class="hint">No questions flagged.</p>')+'</div>').join('')+'</div>';
 }
 function card(row){
   const title=active==='paper_feedback'?paperName(row.paper_id):row.title||row.name||row.topic||('Submission #'+row.id);
   let content=''; const omitted=new Set(['id','status','created_at','title','name','paper_id']);
   Object.entries(row).forEach(([key,value])=>{if(omitted.has(key)||value===null||value==='')return;
    if(['mcq','structured','essays'].includes(key))value=parse(value).map(q=>'Q'+q).join(', ')||'None';
    content+=`<dt>${escape(key.replaceAll('_',' '))}</dt><dd>${escape(value)}</dd>`;});
   if(active==='paper_feedback')content=`<dt>Student</dt><dd>${escape(row.name||'Anonymous')}</dd>`+content;
   let actions='';
   if(active==='papers'){
     const count=(store.paper_feedback||[]).filter(f=>Number(f.paper_id)===Number(row.id)).length;
     content+=`<dt>Responses</dt><dd>${count}</dd><dt>Auto-removal</dt><dd>${escape(new Date(new Date(row.created_at.replace(' ','T')+'Z').getTime()+7*86400000).toLocaleString())}</dd>`;
     actions+=`<button class="action" data-action="feedback" data-id="${row.id}">View feedback (${count})</button><a class="action" href="/papers?paper=${row.id}" target="_blank" rel="noopener">Student link ↗</a><button class="action" data-action="edit" data-id="${row.id}">Edit</button>`;
   }
   if(['news','sessions'].includes(active))actions+=`<button class="action" data-action="status" data-id="${row.id}" data-status="${row.status==='archived'?'published':'archived'}">${row.status==='archived'?'Publish':'Archive'}</button>`;
   else if(active!=='papers') {const next=active==='requests'?'contacted':active==='complaints'||active==='doubts'?'resolved':'read';actions+=`<button class="action" data-action="status" data-id="${row.id}" data-status="${row.status==='new'?next:'new'}">${row.status==='new'?'Mark '+next:'Mark new'}</button>`;}
   actions+=`<button class="action danger" data-action="delete" data-id="${row.id}">Delete</button>`;
   return `<article class="content-card"><span class="status-badge">${escape(row.status)}</span><p class="hint">#${row.id} · ${date(row.created_at)}</p><h3>${escape(title)}</h3><dl class="card-data">${content}</dl><div class="card-actions">${actions}</div></article>`;
 }
 $('adminItems').onclick=async e=>{
   const button=e.target.closest('[data-action]');if(!button||button.disabled)return;const action=button.dataset.action,id=Number(button.dataset.id),type=active;
   if(action==='feedback'){active='paper_feedback';$('adminSearch').value='';$('adminStatusFilter').value='';$('adminPaperFilter').value=String(id);render();return;}
   if(action==='edit'){openEditor((store[type]||[]).find(r=>r.id===id));return;}
   if(action==='delete'&&!confirm(type==='papers'?'Delete this paper and ALL of its feedback? This cannot be undone.':'Delete this item? This cannot be undone.'))return;
   button.disabled=true;
   try{const path=type==='papers'?'/api/admin/papers/'+id:'/api/admin/data/'+type+'/'+id;
     if(action==='delete')await api(path,{method:'DELETE'});else await post(path,{status:button.dataset.status},'PATCH');
     await load();
   }catch(err){if(!unauthorized(err))message(err.message,true);}finally{button.disabled=false;}
 };
 function openEditor(row=null){
   editing=row;editorType=active;$('editorTitle').textContent=(row?'Edit ':'Add ')+(active==='papers'?'paper':active==='sessions'?'session':'announcement');
   $('editorFields').innerHTML=definitions[active].map(([name,label,required,kind])=>`<label>${label}${kind==='textarea'?`<textarea name="${name}" rows="4" maxlength="5000">${escape(row?.[name]||'')}</textarea>`:`<input name="${name}" ${required?'required':''} type="${name.endsWith('_url')?'url':'text'}" value="${escape(row?.[name]||'')}" maxlength="1000">`}</label>`).join('');
   $('adminEditorForm').querySelector('.form-status').textContent='';$('adminEditor').showModal();
 }
 $('adminEditorForm').onsubmit=async e=>{
   e.preventDefault();const form=e.currentTarget,b=form.querySelector('[type=submit]');if(b.disabled)return;b.disabled=true;
   try{const payload=Object.fromEntries(new FormData(form));if(editorType==='papers'&&!editing&&store.papers[0]){if(!confirm('Replace the current paper? Its feedback will be permanently removed. Export it first if needed.'))return;payload.replace_id=store.papers[0].id;}const path='/api/admin/'+editorType+(editing?'/'+editing.id:'');await post(path,payload,editing?'PATCH':'POST');$('adminEditor').close();await load();}
   catch(err){if(unauthorized(err))$('adminEditor').close();else status(form.querySelector('.form-status'),err.message,true);}finally{b.disabled=false;}
 };
 $('closeEditor').onclick=()=>$('adminEditor').close();$('adminAdd').onclick=()=>openEditor();
 $('adminSearch').oninput=render;$('adminStatusFilter').onchange=render;$('adminPaperFilter').onchange=render;
 $('adminRefresh').onclick=load;
 setInterval(()=>{if(!document.hidden&&!$('adminDashboard').hidden&&!$('adminEditor').open&&['papers','paper_feedback'].includes(active))load();},15000);
 $('loginForm').onsubmit=async e=>{e.preventDefault();const b=e.currentTarget.querySelector('button');if(b.disabled)return;b.disabled=true;
   try{await post('/api/admin/login',{password:$('adminPassword').value});loggedIn(true);await load();}catch(err){status($('loginForm').querySelector('.form-status'),err.message,true);}finally{b.disabled=false;}
 };
 $('adminLogout').onclick=async()=>{try{await post('/api/admin/logout',{});loggedIn(false);}catch(err){message(err.message,true);}};
 $('adminExport').onclick=()=>{
   const rows=filtered();if(!rows.length){message('There are no matching items to export.',true);return;}
   const records=rows.map(r=>active==='paper_feedback'?{paper_name:paperName(r.paper_id),...r}:r);const fields=[...new Set(records.flatMap(Object.keys))];
   function csv(value){let v=String(value??'');if(/^[\s]*[=+@-]/.test(v))v="'"+v;return '"'+v.replaceAll('"','""')+'"';}
   const data='\uFEFF'+[fields.map(csv).join(','),...records.map(r=>fields.map(k=>csv(r[k])).join(','))].join('\r\n');
   const url=URL.createObjectURL(new Blob([data],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='sr-physics-'+active+(active==='paper_feedback'&&$('adminPaperFilter').value?'-paper-'+$('adminPaperFilter').value:'')+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('Exported '+rows.length+' matching items.');
 };
 (async()=>{try{const d=await api('/api/admin/whoami');loggedIn(d.admin);if(d.admin)await load();}catch(err){status($('loginForm').querySelector('.form-status'),'Cannot reach the server. Start the project with python run.py.',true);}})();
})();
