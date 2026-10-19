'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const config = window.PRISMA_SUPABASE || {};
  const warning = $('finance-config-warning');
  const authBox = $('finance-auth');
  const financeApp = $('finance-app');
  const authStatus = $('finance-auth-status');
  const entryStatus = $('finance-entry-status');
  const fmt = value => Number(value || 0).toLocaleString('pt-BR', {style:'currency', currency:'BRL'});
  const today = new Date();
  const dateValue = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  $('finance-date').value = dateValue(today);
  let client = null;
  let currentUser = null;
  let transactions = [];

  const bonus = [
    ['Apresente seu negócio','Publique quem você é, o que oferece e para quem trabalha.','Conte sua história e convide as pessoas a conhecerem seu perfil.'],
    ['Mostre seu produto campeão','Destaque o produto ou serviço mais procurado.','Peça para chamar no direct ou WhatsApp.'],
    ['Bastidores reais','Mostre preparação, organização ou rotina de trabalho.','Convide o público a acompanhar o dia a dia.'],
    ['Benefício principal','Explique qual problema seu produto resolve.','Pergunte se a pessoa já passou por essa situação.'],
    ['Pergunta frequente','Responda uma dúvida que os clientes sempre fazem.','Deixe outras dúvidas nos comentários.'],
    ['Demonstração','Mostre como o produto funciona ou como o serviço é feito.','Chame para pedir informações.'],
    ['Depoimento verdadeiro','Compartilhe uma avaliação real, com autorização.','Convide clientes a contar a própria experiência.'],
    ['Escolha do público','Compare duas opções do seu catálogo.','Peça para votar na favorita.'],
    ['Dica útil','Ensine uma dica relacionada ao seu segmento.','Salve a dica e compartilhe com alguém.'],
    ['Detalhes e qualidade','Mostre materiais, ingredientes, acabamento ou processo.','Fale com a equipe para saber mais.'],
    ['Apresente uma novidade','Destaque um item novo ou uma atualização real.','Consulte disponibilidade pelo atendimento.'],
    ['Perguntas e respostas','Abra uma caixa de perguntas nos Stories.','Envie sua pergunta para respondermos.'],
    ['Como escolher','Ajude o cliente a escolher a opção certa.','Conte sua necessidade para receber uma indicação.'],
    ['Equipe e pessoas','Apresente quem faz o negócio acontecer.','Deixe uma mensagem para a equipe.'],
    ['Combinação ou uso','Sugira combinações, formas de usar ou ocasiões adequadas.','Peça uma recomendação personalizada.'],
    ['Mitos e verdades','Esclareça um equívoco comum no segmento.','Compartilhe com quem precisa saber.'],
    ['Catálogo em destaque','Monte uma seleção de produtos ou serviços.','Peça o catálogo ou consulte as opções.'],
    ['História de um produto','Conte como um item é feito ou escolhido.','Qual detalhe você mais gostou?'],
    ['Checklist do cliente','Crie uma lista curta para ajudar o cliente a decidir.','Salve este checklist para consultar depois.'],
    ['Responda uma objeção','Explique com transparência uma dúvida sobre preço, prazo ou entrega.','Fale conosco para avaliar sua necessidade.'],
    ['Rotina de atendimento','Mostre como funciona o atendimento ou agendamento.','Entre em contato para verificar horários.'],
    ['Destaque sazonal','Relacione sua oferta a uma data ou ocasião relevante.','Consulte as opções disponíveis.'],
    ['Conteúdo educativo','Explique um cuidado ou erro comum do seu segmento.','Envie sua dúvida para a equipe.'],
    ['Comparativo útil','Compare duas soluções sem desmerecer nenhuma.','Peça ajuda para escolher.'],
    ['Mostre resultados reais','Apresente um resultado real e autorizado, sem prometer que todos terão o mesmo.','Converse conosco sobre o que faz sentido para você.'],
    ['Convide para conhecer','Mostre o espaço, a loja, o cardápio ou o processo de compra.','Veja como chegar ou fale com a equipe.'],
    ['Oferta transparente','Divulgue uma condição comercial real, com preço e prazo corretos.','Consulte as condições antes de comprar.'],
    ['Resuma os benefícios','Liste três benefícios objetivos do produto ou serviço.','Peça mais detalhes pelo atendimento.'],
    ['Agradeça aos clientes','Agradeça o apoio e compartilhe uma conquista verdadeira.','Marque o negócio quando compartilhar sua experiência.'],
    ['Convite para comprar','Reúna os destaques da semana e explique como comprar.','Chame no WhatsApp ou acesse o link de pedidos.']
  ];
  $('bonus-grid').innerHTML = bonus.map((item,i) => `<article class="bonus-day"><div class="bonus-day-top"><span>DIA ${String(i+1).padStart(2,'0')}</span><b>30 DIAS DE CONTEÚDO</b></div><h3>${item[0]}</h3><p>${item[1]}</p><small>CTA: ${item[2]}</small></article>`).join('');
  $('bonus-export').addEventListener('click', () => {
    if (!window.XLSX) { alert('Não foi possível carregar a exportação. Atualize a página e tente novamente.'); return; }
    const rows = [['Dia','Tema','Ideia de publicação','Chamada para ação'], ...bonus.map((x,i)=>[i+1,x[0],x[1],x[2]])];
    const wb = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rows), 'Plano 30 dias'); XLSX.writeFile(wb,'Prisma_IA_Bonus_30_Dias.xlsx');
  });

  function setStatus(el, message, kind='') { el.textContent = message; el.className = `finance-note ${kind}`.trim(); }
  function showConfigError(message) { warning.hidden = false; warning.className = 'status finance-config-note'; warning.textContent = message; }
  function refreshMonthOptions() {
    const select = $('finance-month'); const previous = select.value;
    const keys = new Set([dateValue(new Date()).slice(0,7), ...transactions.map(t => String(t.transaction_date).slice(0,7))]);
    const sorted = [...keys].sort().reverse();
    select.innerHTML = sorted.map(key => { const [y,m] = key.split('-'); const label = new Date(Number(y),Number(m)-1,1).toLocaleDateString('pt-BR',{month:'long',year:'numeric'}); return `<option value="${key}">${label.charAt(0).toUpperCase()+label.slice(1)}</option>`; }).join('');
    if (sorted.includes(previous)) select.value = previous;
  }
  function renderTransactions() {
    const month = $('finance-month').value || dateValue(new Date()).slice(0,7);
    const visible = transactions.filter(t => String(t.transaction_date).startsWith(month)).sort((a,b)=>b.transaction_date.localeCompare(a.transaction_date) || String(b.created_at).localeCompare(String(a.created_at)));
    const income = visible.filter(t=>t.type==='entrada').reduce((sum,t)=>sum+Number(t.amount),0);
    const expenses = visible.filter(t=>t.type==='despesa').reduce((sum,t)=>sum+Number(t.amount),0);
    $('finance-income').textContent = fmt(income); $('finance-expense').textContent = fmt(expenses); $('finance-balance').textContent = fmt(income-expenses);
    $('finance-rows').innerHTML = visible.length ? visible.map(t => `<tr><td>${new Date(`${t.transaction_date}T12:00:00`).toLocaleDateString('pt-BR')}</td><td>${escapeHtml(t.description)}${t.note ? `<br><small>${escapeHtml(t.note)}</small>` : ''}</td><td>${escapeHtml(t.category)}</td><td class="${t.type==='entrada'?'finance-positive':'finance-negative'}">${t.type==='entrada'?'Entrada':'Despesa'}</td><td class="${t.type==='entrada'?'finance-positive':'finance-negative'}">${t.type==='entrada'?'+':'−'} ${fmt(t.amount)}</td><td><button class="finance-delete" data-delete="${t.id}" type="button">Excluir</button></td></tr>`).join('') : '<tr><td colspan="6" class="finance-empty">Nenhum lançamento neste mês. Adicione sua primeira entrada ou despesa.</td></tr>';
    $('finance-rows').querySelectorAll('[data-delete]').forEach(btn => btn.addEventListener('click', async () => {
      if (!confirm('Excluir este lançamento financeiro?')) return;
      const {error} = await client.from('financial_transactions').delete().eq('id',btn.dataset.delete).eq('user_id',currentUser.id);
      if (error) { setStatus(entryStatus,'Não foi possível excluir. Confira se a tabela financeira foi criada no Supabase.','finance-error'); return; }
      transactions = transactions.filter(t=>String(t.id)!==btn.dataset.delete); refreshMonthOptions(); renderTransactions(); setStatus(entryStatus,'Lançamento excluído.','finance-ok');
    }));
  }
  function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  async function loadTransactions() {
    $('finance-rows').innerHTML = '<tr><td colspan="6" class="finance-empty">Carregando lançamentos…</td></tr>';
    const {data,error} = await client.from('financial_transactions').select('id,user_id,type,description,category,amount,transaction_date,note,created_at').eq('user_id',currentUser.id).order('transaction_date',{ascending:false});
    if (error) { $('finance-rows').innerHTML = '<tr><td colspan="6" class="finance-empty">Não foi possível carregar. Confira se executou o arquivo supabase/schema.sql no projeto correto.</td></tr>'; setStatus(entryStatus,'Erro ao carregar os dados financeiros. Confira a configuração do Supabase e as políticas de segurança.','finance-error'); return; }
    transactions = data || []; refreshMonthOptions(); renderTransactions();
  }
  function setSignedIn(user) {
    currentUser = user || null; authBox.hidden = !!currentUser; financeApp.hidden = !currentUser;
    if (currentUser) { $('finance-user-email').textContent = currentUser.email || 'Conta conectada'; loadTransactions(); }
  }
  if (!config.url || !config.anonKey || !window.supabase?.createClient) {
    showConfigError('Para ativar o financeiro sincronizado, configure SUPABASE_URL e SUPABASE_ANON_KEY no Render e execute supabase/schema.sql no SQL Editor do Supabase. O restante do Prisma IA continua disponível.');
    authBox.hidden = true;
  } else {
    client = window.supabase.createClient(config.url, config.anonKey);
    client.auth.getSession().then(({data})=>setSignedIn(data.session?.user || null));
    client.auth.onAuthStateChange((_event,session)=>setSignedIn(session?.user || null));
  }
  $('finance-auth-form').addEventListener('submit', async e => {
    e.preventDefault(); if (!client) return;
    setStatus(authStatus,'Entrando…');
    const {data,error} = await client.auth.signInWithPassword({email:$('finance-email').value.trim(),password:$('finance-password').value});
    if (error) { setStatus(authStatus,error.message || 'Não foi possível entrar.','finance-error'); return; }
    setSignedIn(data.user); setStatus(authStatus,'Login realizado.','finance-ok');
  });
  $('finance-signup').addEventListener('click', async () => {
    if (!client) return;
    const email=$('finance-email').value.trim(), password=$('finance-password').value;
    if (!email || password.length < 6) { setStatus(authStatus,'Informe um e-mail válido e uma senha com pelo menos 6 caracteres.','finance-error'); return; }
    setStatus(authStatus,'Criando conta…');
    const {data,error} = await client.auth.signUp({email,password});
    if (error) { setStatus(authStatus,error.message || 'Não foi possível criar a conta.','finance-error'); return; }
    if (data.session) { setSignedIn(data.user); setStatus(authStatus,'Conta criada.','finance-ok'); }
    else setStatus(authStatus,'Conta criada. Confira seu e-mail para confirmar o cadastro e depois entre no sistema.','finance-ok');
  });
  $('finance-logout').addEventListener('click', async () => { if (client) await client.auth.signOut(); setSignedIn(null); });
  $('finance-entry-form').addEventListener('submit', async e => {
    e.preventDefault(); if (!client || !currentUser) return;
    const amount=Number($('finance-amount').value);
    if (!Number.isFinite(amount) || amount <= 0) { setStatus(entryStatus,'Informe um valor maior que zero.','finance-error'); return; }
    $('finance-save').disabled=true; setStatus(entryStatus,'Salvando lançamento…');
    const item={user_id:currentUser.id,type:$('finance-type').value,description:$('finance-description').value.trim(),category:$('finance-category').value,amount,transaction_date:$('finance-date').value,note:$('finance-note').value.trim() || null};
    const {error}=await client.from('financial_transactions').insert(item);
    $('finance-save').disabled=false;
    if (error) { setStatus(entryStatus,'Não foi possível salvar. Confira o schema e as políticas RLS no Supabase.','finance-error'); return; }
    $('finance-description').value=''; $('finance-amount').value=''; $('finance-note').value=''; $('finance-date').value=dateValue(new Date());
    setStatus(entryStatus,'Lançamento salvo com segurança.','finance-ok'); await loadTransactions();
  });
  $('finance-month').addEventListener('change',renderTransactions);
  $('finance-export').addEventListener('click', () => {
    if (!currentUser) { setStatus(authStatus,'Entre na sua conta para exportar seus dados.','finance-error'); return; }
    if (!window.XLSX) { alert('Não foi possível carregar a exportação. Atualize a página e tente novamente.'); return; }
    const rows=[['Data','Descrição','Categoria','Tipo','Valor (R$)','Observação'],...transactions.map(t=>[t.transaction_date,t.description,t.category,t.type,Number(t.amount),t.note || ''])];
    const wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet(rows),'Movimentações');
    const selectedMonth=$('finance-month').value;
    const monthItems=transactions.filter(t=>String(t.transaction_date).startsWith(selectedMonth));
    const monthIncome=monthItems.filter(t=>t.type==='entrada').reduce((sum,t)=>sum+Number(t.amount),0);
    const monthExpenses=monthItems.filter(t=>t.type==='despesa').reduce((sum,t)=>sum+Number(t.amount),0);
    const summary=[['Mês','Entradas (R$)','Despesas (R$)','Resultado (R$)'],[selectedMonth,monthIncome,monthExpenses,monthIncome-monthExpenses]];
    XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet(summary),'Resumo'); XLSX.writeFile(wb,'Prisma_IA_Controle_Financeiro.xlsx');
  });
})();
