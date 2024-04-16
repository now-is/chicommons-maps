#!/bin/sh
set -e

cd /app/

npm install --force -g yarn

yarn install

npm run build