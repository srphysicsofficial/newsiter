'use strict';
(() => {
 const embedded=new URLSearchParams(location.search).get('embedded')==='1';
 const reduce=matchMedia('(prefers-reduced-motion: reduce)');const fine=matchMedia('(hover: hover) and (pointer: fine)');
 const hoverSelector='.feature-card,.content-card,.panel,.callout,.paper-item,.sr-service-grid>a,.sr-news article,.sr-story-previews>a,.result-row,.story-card';
 function bind(){document.querySelectorAll(hoverSelector).forEach(el=>{el.classList.add('sr-hover');if(el.matches('.feature-card,.content-card,.sr-story-previews>a,.sr-service-grid>a'))el.classList.add('sr-tilt');});}
 bind();let bindQueued=false;new MutationObserver(()=>{if(bindQueued)return;bindQueued=true;requestAnimationFrame(()=>{bindQueued=false;bind();});}).observe(document.body,{childList:true,subtree:true});
 let hover=null,hoverFrame=0,point={x:0,y:0};
 document.addEventListener('pointermove',e=>{if(reduce.matches||!fine.matches)return;const card=e.target.closest?.('.sr-hover');if(card!==hover){if(hover){hover.style.removeProperty('--rx');hover.style.removeProperty('--ry');}hover=card;}point={x:e.clientX,y:e.clientY};if(hoverFrame)return;hoverFrame=requestAnimationFrame(()=>{hoverFrame=0;if(!hover)return;const r=hover.getBoundingClientRect(),x=point.x-r.left,y=point.y-r.top;hover.style.setProperty('--mx',x+'px');hover.style.setProperty('--my',y+'px');hover.style.setProperty('--rx',((.5-y/r.height)*3)+'deg');hover.style.setProperty('--ry',((x/r.width-.5)*3)+'deg');});},{passive:true});
 if(embedded)return;
 const layer=document.createElement('div');layer.className='sr-ambient';layer.setAttribute('aria-hidden','true');const canvas=document.createElement('canvas');layer.append(canvas);document.body.prepend(layer);const ctx=canvas.getContext('2d');if(!ctx)return;
 let width=0,height=0,dots=[],frame=0,last=0;const mouse={x:-1000,y:-1000};
 function resize(){width=innerWidth;height=innerHeight;const ratio=Math.min(devicePixelRatio||1,1.5);canvas.width=width*ratio;canvas.height=height*ratio;ctx.setTransform(ratio,0,0,ratio,0,0);dots=Array.from({length:width<700?22:48},()=>({x:Math.random()*width,y:Math.random()*height,vx:(Math.random()-.5)*.24,vy:(Math.random()-.5)*.24,r:Math.random()*1.4+.6}));}
 function draw(now){frame=0;if(reduce.matches||document.hidden)return;frame=requestAnimationFrame(draw);if(now-last<32)return;const delta=Math.min((now-last)/32,2);last=now;ctx.clearRect(0,0,width,height);
  dots.forEach((p,i)=>{p.x=(p.x+p.vx*delta+width)%width;p.y=(p.y+p.vy*delta+height)%height;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle=i%5===0?'#ffd166':'#b49aff';ctx.fill();
   for(let j=i+1;j<dots.length;j++){const q=dots[j],d=Math.hypot(p.x-q.x,p.y-q.y);if(d<125){ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.strokeStyle=`rgba(180,154,255,${(1-d/125)*.19})`;ctx.lineWidth=.65;ctx.stroke();}}
   const distance=Math.hypot(mouse.x-p.x,mouse.y-p.y);if(distance<170){ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(mouse.x,mouse.y);ctx.strokeStyle=`rgba(255,209,102,${(1-distance/170)*.22})`;ctx.stroke();}
  });
 }
 function motion(){cancelAnimationFrame(frame);frame=0;document.documentElement.classList.toggle('sr-ambient-paused',document.hidden);if(!reduce.matches&&!document.hidden){last=performance.now();frame=requestAnimationFrame(draw);}else ctx.clearRect(0,0,width,height);}
 addEventListener('resize',resize,{passive:true});document.addEventListener('pointermove',e=>{if(fine.matches){mouse.x=e.clientX;mouse.y=e.clientY;}},{passive:true});document.addEventListener('pointerleave',()=>{mouse.x=-1000;mouse.y=-1000;});document.addEventListener('visibilitychange',motion);reduce.addEventListener('change',motion);resize();motion();
})();
