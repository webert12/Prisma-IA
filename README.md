# Prisma IA — versão 0.3 (Gemini + Render)

## Publicação no Render

Este projeto usa Flask e Google Gemini. A chave da API deve ser configurada como variável de ambiente, nunca escrita no código-fonte nem enviada ao GitHub.

No Render, abra o serviço `prisma-ia` → **Environment** e adicione:

- `AI_PROVIDER` = `gemini`
- `GEMINI_API_KEY` = sua chave privada do Google AI Studio
- `GEMINI_MODEL` = `gemini-2.5-flash`
- `SECRET_KEY` = uma chave longa e aleatória

Build Command: `pip install -r requirements.txt`
Start Command: `gunicorn main:app`
Health Check Path: `/health`

O arquivo `.env.example` é apenas um modelo e não contém chaves reais. Para uso local, copie-o para `.env` e preencha `GEMINI_API_KEY`. O `.gitignore` exclui `.env` para evitar o envio de segredos.

## Enviar ao GitHub pelo Termux

Extraia o ZIP em `Download/prisma_ia_mvp_v2` e execute o script de publicação fornecido separadamente. Confirme o repositório e revise as alterações antes de enviar. Se o GitHub pedir senha, use um Personal Access Token; nunca cole esse token em conversas.

## Recursos

- Biblioteca com 100 comandos divididos em quatro módulos.
- Backend Flask `/api/generate` para gerar respostas usando Gemini.
- Endpoint `/health`.

## Limitações desta versão

Cadastro/login, autenticação Supabase, histórico persistente, limites por usuário e isolamento de dados ainda não estão conectados. O arquivo `supabase/schema.sql` é apenas preparação.
