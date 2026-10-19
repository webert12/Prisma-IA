#!/data/data/com.termux/files/usr/bin/bash
set -e
NOME="prisma_ia_saas_profissional_v6"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$SCRIPT_DIR/$NOME"
REPO="$HOME/Prisma-IA"

if [ ! -f "$SRC/main.py" ] || [ ! -f "$SRC/requirements.txt" ] || [ ! -f "$SRC/static/data/commands.json" ] || [ ! -f "$SRC/static/js/app.js" ]; then
  echo "ERRO: não encontrei a pasta extraída $NOME ao lado deste script."
  echo "Extraia o ZIP completo na pasta Download e execute: bash atualizar_github_termux.sh"
  exit 1
fi

if [ ! -d "$REPO/.git" ]; then
  git clone https://github.com/webert12/Prisma-IA.git "$REPO"
fi

cd "$REPO"
git remote set-url origin https://github.com/webert12/Prisma-IA.git

# Substitui o código do projeto, preservando o histórico Git e o .env local.
find "$REPO" -mindepth 1 -maxdepth 1 ! -name '.git' ! -name '.env' -exec rm -rf {} +
cp -R "$SRC"/. "$REPO"/
git add -A

if git diff --cached --quiet; then
  echo "Nenhuma alteração nova para enviar: o repositório já contém estes arquivos."
  exit 0
fi

git commit -m "Corrige respostas JSON da API Prisma IA v6"
git push -u origin main

echo "Prisma IA v6 enviado ao GitHub: https://github.com/webert12/Prisma-IA"
echo "Se o GitHub solicitar senha por HTTPS, use um Personal Access Token."
