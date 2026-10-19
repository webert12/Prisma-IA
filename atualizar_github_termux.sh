#!/data/data/com.termux/files/usr/bin/bash

set -e

REPO="https://github.com/webert12/Prisma-IA.git"

echo "=================================="
echo "       ATUALIZAR PRISMA IA"
echo "=================================="

read -r -p "GitHub username: " GH_USER
read -r -s -p "GitHub password/token: " GH_TOKEN
echo

if [ -z "$GH_USER" ] || [ -z "$GH_TOKEN" ]; then
    echo "Erro: username e token são obrigatórios."
    exit 1
fi

# Define a identidade do commit sem solicitar o e-mail.
git config --global user.name "webert12"
git config --global user.email "webert12@users.noreply.github.com"

# Usa o token somente durante esta execução.
AUTH_REPO="https://${GH_USER}:${GH_TOKEN}@github.com/webert12/Prisma-IA.git"

unset GH_TOKEN

if [ ! -d ".git" ]; then
    git init
    git branch -M main
    git remote add origin "$REPO"
else
    git remote set-url origin "$REPO"
    git branch -M main
fi

git add -A

if git diff --cached --quiet; then
    echo "Nenhuma alteração nova para enviar."
else
    git commit -m "Atualiza projeto Prisma IA"
fi

echo "Enviando arquivos para o GitHub..."
git -c credential.helper= push "$AUTH_REPO" main

echo "=================================="
echo "Atualização concluída!"
echo "=================================="
