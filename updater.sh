#!/bin/bash

shopt -s expand_aliases
source ~/.bashrc

echo "Updating service images..."

docker compose pull

echo "Recreating containers..."

docker compose up --force-recreate -d

echo "Cleaning old images..."

docker image prune -f