# Prisma IA SaaS Profissional v8

Aplicação Flask com 100 ferramentas de IA, módulo de controle financeiro por conta e bônus de conteúdo para 30 dias.

## Novidades v8
- Financeiro com entradas, despesas, categorias, data, observação, resumo mensal e exclusão de lançamentos.
- Login e criação de conta pelo Supabase Auth. Os registros financeiros são isolados por usuário usando Row Level Security (RLS).
- Exportação do controle financeiro para Excel (.xlsx), compatível com Excel e Google Sheets.
- Bônus integrado de 30 dias com tema, ideia de publicação e chamada para ação; exportável para Excel.
- As 100 ferramentas de IA e a geração Gemini permanecem disponíveis.

## Ativar o financeiro
1. No painel Supabase, abra SQL Editor e execute todo o arquivo `supabase/schema.sql`.
2. No Render, em Environment, adicione `SUPABASE_URL` (Project URL) e `SUPABASE_ANON_KEY` (chave pública/anon do projeto).
3. Preserve `GEMINI_API_KEY` e `GEMINI_MODEL` existentes e aguarde o deploy.
4. No Prisma IA, abra Financeiro, crie sua conta e confirme o e-mail se solicitado. Use a mesma conta em celular e computador para sincronizar os registros.

Não configure a chave `service_role` no navegador nem publique segredos no GitHub. A chave anon/public pode ser entregue ao navegador porque o acesso aos registros é protegido pelas políticas RLS do schema.

## Deploy
Render inicia com `gunicorn main:app`; health check em `/health`.
