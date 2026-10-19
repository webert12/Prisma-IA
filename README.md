# Prisma IA SaaS Profissional v6

Versão com correção no tratamento das respostas da API. A interface agora identifica quando o servidor devolve HTML em vez de JSON e exibe uma mensagem útil, sem o erro técnico `Unexpected token '<'`. Erros inesperados das rotas `/api/` também são devolvidos em JSON.

## Configuração

No Render, mantenha `GEMINI_API_KEY` e `GEMINI_MODEL` configuradas. O comando de inicialização é `gunicorn main:app`.

## Publicar pelo Termux

Extraia o ZIP em `Download` e execute `bash atualizar_github_termux.sh` dentro da pasta Download.
