# Prisma IA — Workspace SaaS v5

Aplicação Flask responsiva para criação de conteúdo, vendas, WhatsApp e estratégia com 100 comandos e integração Gemini no servidor.

## Melhorias da v5
- Biblioteca de comandos com filtro por módulo e pesquisa.
- Favoritos persistidos localmente no navegador, com filtro dedicado.
- Atalhos de teclado: `Ctrl+K` para focar a busca e `Esc` para limpar a busca.
- Registro local das últimas ferramentas utilizadas e contador de atividade.
- Cards com estados de foco, hover e controles acessíveis.
- Layout responsivo para computador, tablet e celular.
- Respostas organizadas em seções e botões de copiar tudo ou por seção.
- Segredos mantidos no servidor via variáveis de ambiente.

## Variáveis do Render
- `GEMINI_API_KEY`: chave do Google AI Studio.
- `GEMINI_MODEL`: modelo Gemini habilitado para sua chave (valor padrão no código: `gemini-3.8-flash`).
- `SECRET_KEY`: chave secreta da aplicação.

Não coloque chaves de API no frontend ou no GitHub.

## Publicação pelo Termux
Extraia `prisma_ia_saas_profissional_v5.zip` na pasta Download e execute o arquivo `atualizar_github_termux.sh` conforme `COMO_ENVIAR_NO_TERMUX.txt`.

O script publica a pasta extraída no repositório `webert12/Prisma-IA`, mantendo `.git` e o `.env` local. Se o GitHub pedir uma senha HTTPS, use um Personal Access Token.
