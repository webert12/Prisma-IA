# Prisma IA — versão 0.2

## Incluído
- Biblioteca com 100 comandos dos quatro módulos do PDF KIT IA VENDEDORA (25 por módulo).
- Busca, filtros por módulo e formulários criados a partir dos campos de cada comando.
- Backend `/api/generate` que monta o comando e chama uma API compatível com OpenAI Chat Completions.
- Resposta exibida na plataforma e botão para copiar.
- Endpoint `/health` para teste e configuração inicial para Render.

## Para gerar respostas reais
É necessário configurar um provedor de IA compatível. O sistema não finge gerar respostas se a API não estiver configurada. O uso pode ter limites ou custos conforme o provedor/modelo; não há garantia de IA ilimitada e gratuita.

No `.env` local ou no painel Render → Environment, configure:
- `AI_API_BASE`: URL base do provedor, normalmente terminando em `/v1`.
- `AI_API_KEY`: chave privada do provedor.
- `AI_MODEL`: nome exato de um modelo disponível para sua chave.

Use os valores oficiais do provedor escolhido. Não coloque chaves no HTML/JavaScript, não envie `.env` ao GitHub e não compartilhe chaves em mensagens.

## Rodar no Termux
Extraia este ZIP numa nova pasta ou faça backup antes de substituir a versão antiga:

```bash
pkg update -y
pkg install python git unzip -y
cd ~/storage/downloads
unzip prisma_ia_mvp_v2.zip
cd prisma_ia_mvp_v2
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Acesse `http://127.0.0.1:5000`.

## Publicar no Render
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn main:app`
- Health check path: `/health`
- Configure `SECRET_KEY`, `AI_API_BASE`, `AI_API_KEY` e `AI_MODEL` nas variáveis de ambiente.

Se já houver um serviço Render para a versão 0.1, envie os arquivos atualizados para o mesmo repositório. Faça backup antes de substituir arquivos.

## Próxima etapa necessária
Cadastro/login, autenticação Supabase, perfil de negócio, histórico persistente, limites por usuário e isolamento de dados ainda não estão conectados nesta versão. Antes de abrir para clientes reais, vamos implementar e testar esses controles. O arquivo `supabase/schema.sql` é apenas preparação e não é usado pela versão atual.
