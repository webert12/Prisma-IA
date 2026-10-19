#!/data/data/com.termux/files/usr/bin/bash
set -e

NOME="prisma_ia_saas_profissional_v5"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$SCRIPT_DIR/$NOME"
REPO="$HOME/Prisma-IA"

if [ ! -f "$SRC/main.py" ] || [ ! -f "$SRC/requirements.txt" ] || [ ! -f "$SRC/static/data/commands.json" ]; then
  echo "ERRO: extraia o ZIP completo na pasta Download e execute este script novamente."
  echo "Pasta esperada: $SRC"
  exit 1
fi

if [ ! -d "$REPO/.git" ]; then
  git clone https://github.com/webert12/Prisma-IA.git "$REPO"
fi

cd "$REPO"
git remote set-url origin https://github.com/webert12/Prisma-IA.git

# Substitui os arquivos do projeto, mantendo o historico Git e o .env local.
find "$REPO" -mindepth 1 -maxdepth 1 ! -name '.git' ! -name '.env' -exec rm -rf {} +
cp -R "$SRC"/. "$REPO"/

 git add -A
if git diff --cached --quiet; then
  echo "Nenhuma alteracao nova para enviar: o GitHub ja possui estes arquivos."
  exit 0
fi

git commit -m "Atualiza Prisma IA SaaS profissional v5"
git push -u origin main

echo ""
echo "Prisma IA v5 enviado ao GitHub com sucesso:"
echo "https://github.com/webert12/Prisma-IA"
echo "Se o GitHub pedir senha, use um Personal Access Token, nao a senha normal da conta."
