(function(){
var D='M484.09,342.33l44.38-44.38c15.43-15.43,15.43-40.44,0-55.86l-44.38-44.38c-7.41-7.41-11.57-17.45-11.57-27.93v-62.76c0-21.82-17.68-39.5-39.5-39.5h-62.76c-10.48,0-20.52-4.16-27.93-11.57l-44.38-44.38c-15.43-15.43-40.44-15.43-55.86,0l-44.38,44.38c-7.41,7.41-17.45,11.57-27.93,11.57h-62.76c-21.82,0-39.5,17.68-39.5,39.5v62.76c0,10.48-4.16,20.52-11.57,27.93l-44.38,44.38c-15.43,15.43-15.43,40.44,0,55.86l44.38,44.38c7.41,7.41,11.57,17.45,11.57,27.93v62.76c0,21.82,17.68,39.5,39.5,39.5h62.76c10.48,0,20.52,4.16,27.93,11.57l44.38,44.38c15.43,15.43,40.44,15.43,55.86,0l44.38-44.38c7.41-7.41,17.45-11.57,27.93-11.57h62.76c21.82,0,39.5-17.68,39.5-39.5v-62.76c0-10.48,4.16-20.52,11.57-27.93Z';
function star(filled){return '<svg viewBox="-10 -10 560.03 560.03"><path d="'+D+'" '+(filled?'fill="#B8863C"':'fill="none" stroke="#B8863C" stroke-width="14" stroke-linejoin="round"')+'/></svg>'}
var orns=[{t:'8%',l:'4%',s:120,o:.16},{t:'62%',l:'88%',s:140,o:.14},{t:'30%',l:'92%',s:44,o:.09,f:1,b:5},{t:'78%',l:'10%',s:90,o:.18},{t:'18%',l:'48%',s:34,o:.08,f:1,b:3},{t:'86%',l:'56%',s:56,o:.1,f:1,b:7},{t:'46%',l:'2%',s:30,o:.07,f:1,b:4}];
function init(){
var L=document.createElement('div');L.className='ice-orn-layer';L.setAttribute('aria-hidden','true');
orns.forEach(function(o,i){var d=document.createElement('div');d.className='ice-orn'+(i%2?' rev':'');
d.style.cssText='top:'+o.t+';left:'+o.l+';width:'+o.s+'px;height:'+o.s+'px;opacity:'+o.o+';--fd:'+(6+i%4)+'s;--dl:'+(i*.7)+'s;--sd:'+(50+i*6)+'s;'+(o.f?'filter:blur('+o.b+'px);':'');
d.innerHTML=star(o.f);L.appendChild(d)});
document.body.prepend(L);
document.querySelectorAll('.ic-circle').forEach(function(e,i){e.style.animationDelay=(i%4*.6)+'s'});
if(!('IntersectionObserver' in window)||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
var els=document.querySelectorAll('main > *:not(script):not(style), .plan, .tpl, .path, .group');
var io=new IntersectionObserver(function(es){es.forEach(function(en){if(!en.isIntersecting)return;var e=en.target;io.unobserve(e);
e.classList.remove('ice-pre');e.classList.add('ice-in');e.addEventListener('animationend',function h(){e.classList.remove('ice-in');e.removeEventListener('animationend',h)})})},{threshold:.12});
var n=0;els.forEach(function(e){if(e.closest('.ice-pre'))return;var r=e.getBoundingClientRect();if(!r.height)return;e.classList.add('ice-pre');if(r.top<innerHeight)e.style.animationDelay=(Math.min(n++,6)*.06)+'s';io.observe(e)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(init,30)});else setTimeout(init,30);
})();
