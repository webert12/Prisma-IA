# Prisma IA SaaS Profissional v7

Aplicação Flask com biblioteca de 100 ferramentas e integração com Gemini.

## Melhorias v7
- Brief de geração inclui nome, objetivo e prompt específico de cada ferramenta.
- Instruções para respostas mais personalizadas, explicadas e aplicáveis, com profundidade proporcional à tarefa.
- Regras explícitas para evitar respostas genéricas, repetição e fatos inventados.
- A interface exige ao menos um campo preenchido e explica que a resposta está sendo criada pela IA.
- Limite de saída ampliado para tarefas que precisam de mais detalhes.

## Configuração
Configure `GEMINI_API_KEY` e `GEMINI_MODEL` nas variáveis do Render. Não compartilhe nem versione a chave.

## Deploy
Render inicia com `gunicorn main:app`; health check em `/health`.
