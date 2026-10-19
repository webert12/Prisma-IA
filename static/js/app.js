let commands=[], selectedCommand=null;
const list=document.getElementById('command-list'), search=document.getElementById('search'), filter=document.getElementById('module-filter'), workbench=document.getElementById('workbench'), form=document.getElementById('tool-form'), statusBox=document.getElementById('generation-status'), resultPanel=document.getElementById('result-panel'), resultOutput=document.getElementById('result-output'), generateBtn=document.getElementById('generate-btn');
const moduleNames={1:'Conteúdo que atrai',2:'IA para vendas',3:'IA para WhatsApp',4:'IA para estratégia'};
function esc(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function normalizeOutput(text){return String(text||'').replace(/\r/g,'').replace(/[ \t]+$/gm,'').trim();}
function splitOutput(text){
  const lines=normalizeOutput(text).split('\n');
  const sections=[]; let current={title:'Resultado',lines:[]};
  const isHeading=line=>/^#{1,4}\s+/.test(line)||(/^.{2,80}:$/.test(line.trim())&&!/^https?:/i.test(line.trim()));
  for(const raw of lines){
    const line=raw.trim();
    if(!line){if(current.lines.length&&current.lines[current.lines.length-1]!=='')current.lines.push('');continue;}
    if(isHeading(line)){
      if(current.lines.some(x=>x.trim()))sections.push(current);
      current={title:line.replace(/^#{1,4}\s+/,'').replace(/:$/,'').trim(),lines:[]};
    }else current.lines.push(line);
  }
  if(current.lines.some(x=>x.trim()))sections.push(current);
  return sections.length?sections:[{title:'Resultado',lines:lines.filter(x=>x.trim())}];
}
function renderResult(text){
  const container=resultOutput; container.innerHTML='';
  const sections=splitOutput(text);
  sections.forEach((section,index)=>{
    const card=document.createElement('article'); card.className='result-card';
    const head=document.createElement('div'); head.className='result-card-head';
    const title=document.createElement('h4'); title.textContent=section.title||`Parte ${index+1}`;
    const copy=document.createElement('button'); copy.type='button'; copy.className='section-copy'; copy.textContent='Copiar seção';
    const body=document.createElement('div'); body.className='result-card-body';
    let list=null;
    section.lines.forEach(raw=>{
      const line=raw.trim(); if(!line){list=null;return;}
      const bullet=/^(?:[-*•]|\d+[.)])\s+/.test(line);
      if(bullet){if(!list){list=document.createElement('ul');body.appendChild(list);}const li=document.createElement('li');li.textContent=line.replace(/^(?:[-*•]|\d+[.)])\s+/,'');list.appendChild(li);}
      else{list=null;const para=document.createElement('p');para.textContent=line.replace(/\*\*(.*?)\*\*/g,'$1').replace(/^>\s?/,'');body.appendChild(para);}
    });
    copy.addEventListener('click',async()=>{const content=section.title+'\n\n'+section.lines.join('\n');try{await navigator.clipboard.writeText(content);copy.textContent='Copiado ✓';setTimeout(()=>copy.textContent='Copiar seção',1500);}catch{copy.textContent='Selecione o texto';}});
    head.append(title,copy);card.append(head,body);container.appendChild(card);
  });
}
function renderCommands(){const term=search.value.trim().toLocaleLowerCase('pt-BR'), mod=Number(filter.value);const arr=commands.filter(c=>(!mod||c.module===mod)&&(`${c.id} ${c.title} ${c.objective} ${c.module_title}`).toLocaleLowerCase('pt-BR').includes(term));list.innerHTML='';document.getElementById('empty-state').hidden=arr.length!==0;arr.forEach(c=>{const card=document.createElement('article');card.className=`command-card command-module-${c.module}`;card.innerHTML=`<div class="command-top"><span class="command-number">${String(c.id).padStart(2,'0')}</span><span class="command-module">${esc(moduleNames[c.module])}</span></div><h3>${esc(c.title)}</h3><p>${esc(c.objective||'Ferramenta prática para seu negócio.')}</p><button class="tool-link" type="button">Abrir ferramenta <span>↗</span></button>`;card.querySelector('button').addEventListener('click',()=>openTool(c.id));list.appendChild(card);});}
function openTool(id){selectedCommand=commands.find(c=>c.id===id);if(!selectedCommand)return;document.getElementById('form-title').textContent=`${String(selectedCommand.id).padStart(2,'0')} — ${selectedCommand.title}`;document.getElementById('form-objective').textContent=selectedCommand.objective||'';const fields=document.getElementById('dynamic-fields');fields.innerHTML='';if(!selectedCommand.fields.length){fields.innerHTML='<p>Esta ferramenta não precisa de campos adicionais.</p>';}else selectedCommand.fields.forEach((field,i)=>{const wrap=document.createElement('label');wrap.className='field';wrap.innerHTML=`<span>${esc(field)}</span><textarea id="field-${i}" name="${esc(field)}" rows="${field.length>42?3:2}" autocomplete="off"></textarea>`;fields.appendChild(wrap);});statusBox.hidden=true;resultPanel.hidden=true;workbench.hidden=false;workbench.scrollIntoView({behavior:'smooth',block:'start'});}
document.getElementById('close-form').addEventListener('click',()=>workbench.hidden=true);search.addEventListener('input',renderCommands);filter.addEventListener('change',renderCommands);document.querySelectorAll('[data-module]').forEach(b=>b.addEventListener('click',()=>{filter.value=b.dataset.module;renderCommands();document.getElementById('biblioteca').scrollIntoView({behavior:'smooth',block:'start'});}));
form.addEventListener('submit',async e=>{e.preventDefault();if(!selectedCommand)return;const values={};selectedCommand.fields.forEach((f,i)=>values[f]=document.getElementById(`field-${i}`)?.value||'');generateBtn.disabled=true;generateBtn.textContent='Gerando resultado…';statusBox.hidden=false;statusBox.className='status';statusBox.textContent='A IA está preparando seu resultado. Isso pode levar alguns segundos.';resultPanel.hidden=true;try{const response=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command_id:selectedCommand.id,values})});const data=await response.json();if(!response.ok)throw new Error(data.error||'Não foi possível gerar o resultado.');document.getElementById('result-title').textContent=data.title;renderResult(data.output);resultPanel.hidden=false;statusBox.className='status success';statusBox.textContent='Resultado gerado. Revise antes de usar.';resultPanel.scrollIntoView({behavior:'smooth',block:'start'});}catch(err){statusBox.className='status error';statusBox.textContent=err.message||'Ocorreu um erro. Tente novamente.';}finally{generateBtn.disabled=false;generateBtn.innerHTML='✦ Gerar resultado com IA';}});
document.getElementById('copy-result').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(`${document.getElementById('result-title').textContent}\n\n${resultOutput.innerText}`);document.getElementById('copy-result').textContent='Copiado!';setTimeout(()=>document.getElementById('copy-result').textContent='Copiar resultado',1800);}catch{const range=document.createRange();range.selectNodeContents(resultOutput);const sel=window.getSelection();sel.removeAllRanges();sel.addRange(range);document.getElementById('copy-result').textContent='Selecione e copie';}});
fetch('/api/commands').then(r=>r.json()).then(data=>{commands=data;renderCommands();}).catch(()=>list.innerHTML='<div class="loading">Não foi possível carregar a biblioteca. Atualize a página.</div>');
