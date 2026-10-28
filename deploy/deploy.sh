#!/bin/sh
# copy site/ to the homelab and reload nginx.
# one-time setup on the box:
#   sudo mkdir -p /var/www/g8row.xyz && sudo chown debian:debian /var/www/g8row.xyz
#   sudo cp g8row.xyz.conf /etc/nginx/sites-available/ && sudo ln -s ../sites-available/g8row.xyz.conf /etc/nginx/sites-enabled/
#   sudo nginx -t && sudo systemctl reload nginx && sudo certbot --nginx -d g8row.xyz -d www.g8row.xyz
set -eu
HOST=${HOST:-debian@debian}
cd "$(dirname "$0")/.."
rsync -az --delete --exclude '.DS_Store' --exclude lastfm.json site/ "$HOST:/var/www/g8row.xyz/"
echo "deployed to $HOST:/var/www/g8row.xyz"
