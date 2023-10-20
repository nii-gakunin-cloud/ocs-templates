#!/bin/sh

set -e

url=https://raw.githubusercontent.com/jupyter/docker-stacks
commit=10e52ee84369aaa37630aea13c137b766ace307b
path=docker-stacks-foundation/start.sh

curl -sfL -o start ${url}/${commit}/${path}
sed -i -e '/secure_path/s#CONDA_DIR#NB_PYTHON_PREFIX#' start
chmod +x start

touch apt.txt
if ! grep -q sudo apt.txt; then
    echo "sudo" >> apt.txt
fi

git init -q
git add start apt.txt
