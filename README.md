# Prisma IA — versão 0.4 (interface organizada + Gemini)

## Publicação no Render

Este projeto usa Flask e Google Gemini. A chave da API deve ficar somente nas variáveis de ambiente do Render, nunca no código-fonte nem no GitHub.

No Render, abra o serviço `prisma-ia` → **Environment** e confira:

- `AI_PROVIDER` = `gemini`
- `GEMINI_API_KEY` = sua chave privada do Google AI Studio
- `GEMINI_MODEL` = `gemini-3.8-flash` (sem ponto no final)
- `SECRET_KEY` = uma chave longa e aleatória

Build Command: `pip install -r requirements.txt`
Start Command: `gunicorn main:app`
Health Check Path: `/health`

O `.env.example` é somente um modelo. O `.gitignore` exclui `.env` para evitar o envio de chaves privadas.

## O que mudou nesta versão

- Resultados divididos em cartões por seção, usando títulos detectados no texto gerado.
- Listas e etapas exibidas como listas formatadas, em vez de um bloco único de texto.
- Botão para copiar o resultado completo e botão para copiar cada seção individualmente.
- Formulário e cartões refinados para leitura em celular e computador.
- Mantidos os 100 comandos, as rotas Flask e a integração Gemini Interactions API.

## Publicar pelo Termux

Extraia `prisma_ia_profissional_v3.zip` em `Download`, deixando a pasta `prisma_ia_profissional_v3`. Depois execute o comando de publicação fornecido na conversa. O comando exclui `.env` e não deve enviar chaves privadas ao GitHub.

## Endpoints

- `/` — interface principal
- `/health` — verificação de saúde
- `/api/commands` — biblioteca de comandos
- `/api/generate` — geração com IA

## Observação

Cadastro/login, autenticação Supabase, histórico persistente, limites por usuário e isolamento de dados ainda não estão conectados. O arquivo `supabase/schema.sql` é apenas preparação.
