'use strict';

let commands = [];
let selectedCommand = null;
let favoritesOnly = false;
const favorites = new Set(readList('prisma-ia-favorites'));
const recentCommands = readList('prisma-ia-recent');
function readList(key) { try { const value = JSON.parse(localStorage.getItem(key) || '[]'); return Array.isArray(value) ? value : []; } catch { return []; } }
function saveList(key, values) { try { localStorage.setItem(key, JSON.stringify(values)); } catch {} }
function refreshPersonalCounts() { const el = document.getElementById('favorites-count'); if (el) el.textContent = favorites.size; const recent = document.getElementById('recent-count'); if (recent) recent.textContent = `${recentCommands.length} recentes`; }
const list = document.getElementById('command-list');
const search = document.getElementById('search');
const filter = document.getElementById('module-filter');
const workbench = document.getElementById('workbench');
const form = document.getElementById('tool-form');
const statusBox = document.getElementById('generation-status');
const resultPanel = document.getElementById('result-panel');
const resultOutput = document.getElementById('result-output');
const generateBtn = document.getElementById('generate-btn');
const moduleNames = {1:'Conteúdo que atrai',2:'IA para vendas',3:'IA para WhatsApp',4:'IA para estratégia'};
const moduleDescriptions = {1:'Ideias, Reels, legendas, Stories e conteúdo que chama atenção.',2:'Ofertas, promoções, argumentos, recuperação e estratégias comerciais.',3:'Atendimento, follow-up, orçamento, pós-venda e relacionamento.',4:'Público, posicionamento, diagnóstico, planejamento e crescimento.'};
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const pad = number => String(number).padStart(2, '0');

function renderCommands() {
  const term = search.value.trim().toLocaleLowerCase('pt-BR');
  const moduleId = Number(filter.value);
  const filtered = commands.filter(command => (!moduleId || command.module === moduleId) &&
    (!favoritesOnly || favorites.has(command.id)) &&
    (`${command.id} ${command.title} ${command.objective} ${command.module_title}`.toLocaleLowerCase('pt-BR').includes(term)));
  list.innerHTML = '';
  document.getElementById('empty-state').hidden = filtered.length > 0;
  document.getElementById('result-count').textContent = `${filtered.length} ${filtered.length === 1 ? 'ferramenta encontrada' : 'ferramentas encontradas'}`;
  filtered.forEach(command => {
    const card = document.createElement('article');
    card.className = `command-card command-module-${command.module}`;
    card.innerHTML = `<div class="command-top"><span class="command-number">${pad(command.id)}</span><span class="command-module">${esc(moduleNames[command.module] || command.module_title || 'Ferramenta')}</span><button class="favorite-btn ${favorites.has(command.id) ? 'is-favorite' : ''}" type="button" aria-label="${favorites.has(command.id) ? 'Remover dos' : 'Adicionar aos'} favoritos" aria-pressed="${favorites.has(command.id)}">${favorites.has(command.id) ? '★' : '☆'}</button></div><h3>${esc(command.title)}</h3><p>${esc(command.objective || 'Ferramenta prática para seu negócio.')}</p><button class="tool-link" type="button"><span>Abrir ferramenta</span><span aria-hidden="true">↗</span></button>`;
    card.querySelector('.tool-link').addEventListener('click', () => openTool(command.id));
    card.querySelector('.favorite-btn').addEventListener('click', event => { event.stopPropagation(); if (favorites.has(command.id)) favorites.delete(command.id); else favorites.add(command.id); saveList('prisma-ia-favorites', [...favorites]); refreshPersonalCounts(); renderCommands(); });
    list.appendChild(card);
  });
}

function openTool(id) {
  selectedCommand = commands.find(command => command.id === id);
  if (!selectedCommand) return;
  const previousIndex = recentCommands.indexOf(id); if (previousIndex >= 0) recentCommands.splice(previousIndex, 1); recentCommands.unshift(id); recentCommands.splice(8); saveList('prisma-ia-recent', recentCommands); refreshPersonalCounts();
  document.getElementById('form-title').textContent = `${pad(selectedCommand.id)} · ${selectedCommand.title}`;
  document.getElementById('form-objective').textContent = selectedCommand.objective || '';
  const fieldsContainer = document.getElementById('dynamic-fields');
  fieldsContainer.innerHTML = '';
  if (!selectedCommand.fields?.length) {
    fieldsContainer.innerHTML = '<p>Esta ferramenta não precisa de campos adicionais.</p>';
  } else {
    selectedCommand.fields.forEach((field, index) => {
      const wrapper = document.createElement('label');
      wrapper.className = 'field';
      wrapper.innerHTML = `<span>${esc(field)}</span><textarea id="field-${index}" name="field-${index}" rows="4" autocomplete="off" aria-label="${esc(field)}"></textarea>`;
      fieldsContainer.appendChild(wrapper);
    });
  }
  statusBox.hidden = true;
  resultPanel.hidden = true;
  workbench.hidden = false;
  workbench.scrollIntoView({behavior:'smooth', block:'start'});
}

function splitOutput(text) {
  const lines = String(text || '').replace(/\r/g, '').replace(/[ \t]+$/gm, '').trim().split('\n');
  const sections = [];
  let current = {title:'Visão geral', lines:[]};
  const isHeading = line => /^#{1,4}\s+/.test(line) || (/^.{2,80}:$/.test(line.trim()) && !/^https?:/i.test(line.trim()));
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) { if (current.lines.length && current.lines[current.lines.length - 1] !== '') current.lines.push(''); continue; }
    if (isHeading(line)) {
      if (current.lines.some(item => item.trim())) sections.push(current);
      current = {title:line.replace(/^#{1,4}\s+/, '').replace(/:$/, '').trim(), lines:[]};
    } else current.lines.push(line);
  }
  if (current.lines.some(item => item.trim())) sections.push(current);
  return sections.length ? sections : [{title:'Resultado', lines:lines.filter(Boolean)}];
}

function renderResult(text) {
  resultOutput.innerHTML = '';
  splitOutput(text).forEach((section, index) => {
    const card = document.createElement('article');
    card.className = 'result-card';
    const head = document.createElement('div'); head.className = 'result-card-head';
    const title = document.createElement('h4'); title.textContent = section.title || `Parte ${index + 1}`;
    const copy = document.createElement('button'); copy.type = 'button'; copy.className = 'section-copy'; copy.textContent = 'Copiar seção';
    const body = document.createElement('div'); body.className = 'result-card-body';
    let currentList = null;
    section.lines.forEach(raw => {
      const line = raw.trim();
      if (!line) { currentList = null; return; }
      const bullet = /^(?:[-*•]|\d+[.)])\s+/.test(line);
      if (bullet) {
        if (!currentList) { currentList = document.createElement('ul'); body.appendChild(currentList); }
        const item = document.createElement('li'); item.textContent = line.replace(/^(?:[-*•]|\d+[.)])\s+/, '').replace(/\*\*(.*?)\*\*/g, '$1'); currentList.appendChild(item);
      } else {
        currentList = null;
        const paragraph = document.createElement('p');
        paragraph.textContent = line.replace(/\*\*(.*?)\*\*/g, '$1').replace(/^>\s?/, '');
        body.appendChild(paragraph);
      }
    });
    copy.addEventListener('click', async () => {
      const content = `${section.title}\n\n${section.lines.join('\n')}`;
      try { await navigator.clipboard.writeText(content); copy.textContent = 'Copiado ✓'; }
      catch { copy.textContent = 'Selecione o texto'; }
      window.setTimeout(() => { copy.textContent = 'Copiar seção'; }, 1600);
    });
    head.append(title, copy); card.append(head, body); resultOutput.appendChild(card);
  });
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!selectedCommand) return;
  const values = {};
  selectedCommand.fields.forEach((field, index) => { values[field] = document.getElementById(`field-${index}`)?.value || ''; });
  generateBtn.disabled = true;
  generateBtn.innerHTML = '<span>◌</span> Preparando seu resultado…';
  statusBox.hidden = false; statusBox.className = 'status';
  statusBox.textContent = 'A IA está organizando sua resposta. Isso pode levar alguns segundos.';
  resultPanel.hidden = true;
  try {
    const response = await fetch('/api/generate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({command_id:selectedCommand.id, values})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível gerar o resultado.');
    document.getElementById('result-title').textContent = data.title || selectedCommand.title;
    renderResult(data.output);
    resultPanel.hidden = false;
    statusBox.className = 'status success';
    statusBox.textContent = 'Resultado gerado com sucesso. Revise e adapte antes de usar.';
    resultPanel.scrollIntoView({behavior:'smooth', block:'start'});
  } catch (error) {
    statusBox.className = 'status error';
    statusBox.textContent = error.message || 'Ocorreu um erro. Tente novamente.';
  } finally {
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<span>✦</span> Gerar com inteligência artificial <b>→</b>';
  }
});

document.getElementById('close-form').addEventListener('click', () => { workbench.hidden = true; });
document.getElementById('copy-result').addEventListener('click', async () => {
  const button = document.getElementById('copy-result');
  const content = `${document.getElementById('result-title').textContent}\n\n${resultOutput.innerText}`;
  try { await navigator.clipboard.writeText(content); button.innerHTML = '<span>✓</span> Copiado!'; }
  catch { const range = document.createRange(); range.selectNodeContents(resultOutput); const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range); button.innerHTML = '<span>▣</span> Selecione e copie'; }
  window.setTimeout(() => { button.innerHTML = '<span>▣</span> Copiar tudo'; }, 1800);
});

search.addEventListener('input', renderCommands);
filter.addEventListener('change', renderCommands);
const favoritesToggle = document.getElementById('favorites-toggle');
favoritesToggle.addEventListener('click', () => { favoritesOnly = !favoritesOnly; favoritesToggle.classList.toggle('active', favoritesOnly); favoritesToggle.setAttribute('aria-pressed', String(favoritesOnly)); favoritesToggle.querySelector('span').textContent = favoritesOnly ? '★' : '☆'; renderCommands(); });
document.addEventListener('keydown', event => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); search.focus(); search.scrollIntoView({behavior:'smooth', block:'center'}); } if (event.key === 'Escape' && document.activeElement === search) { search.value = ''; renderCommands(); search.blur(); } });
document.querySelectorAll('[data-module]').forEach(button => button.addEventListener('click', () => {
  filter.value = button.dataset.module;
  renderCommands();
  document.getElementById('biblioteca').scrollIntoView({behavior:'smooth', block:'start'});
  closeMobileMenu();
}));

const sidebar = document.getElementById('sidebar');
const scrim = document.getElementById('mobile-scrim');
function closeMobileMenu() { sidebar.classList.remove('open'); scrim.classList.remove('show'); }
document.getElementById('menu-toggle').addEventListener('click', () => { sidebar.classList.toggle('open'); scrim.classList.toggle('show'); });
scrim.addEventListener('click', closeMobileMenu);
document.querySelectorAll('.side-nav a').forEach(link => link.addEventListener('click', closeMobileMenu));

fetch('/api/commands')
  .then(response => { if (!response.ok) throw new Error('Falha ao carregar'); return response.json(); })
  .then(data => { commands = Array.isArray(data) ? data : []; refreshPersonalCounts(); renderCommands(); })
  .catch(() => { list.innerHTML = '<div class="loading">Não foi possível carregar a biblioteca. Atualize a página para tentar novamente.</div>'; document.getElementById('result-count').textContent = 'Biblioteca indisponível'; });
