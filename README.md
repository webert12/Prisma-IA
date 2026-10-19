# Prisma IA — SaaS Workspace v1.0

Central de ferramentas de IA para pequenos negócios, com 100 comandos organizados em quatro módulos:

1. Conteúdo que atrai
2. IA para vendas
3. IA para WhatsApp
4. IA para estratégia

## Interface
- Dashboard profissional com navegação lateral e resumo da biblioteca.
- Módulos apresentados em blocos visuais distintos.
- Pesquisa por nome, objetivo e número; filtro por módulo.
- Formulários dinâmicos e resultados organizados em seções com cópia por seção ou resultado completo.
- Layout responsivo para celular, tablet, notebook e monitor.
- Identidade visual em azul-marinho, roxo e azul elétrico.

## Executar localmente

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Configure `GEMINI_API_KEY` e `GEMINI_MODEL` nas variáveis de ambiente. Não publique chaves de API no GitHub. Para o Render, configure as variáveis no painel do serviço.

## Deploy no Render

O serviço usa `gunicorn main:app`, dependências de `requirements.txt` e health check em `/health`.
