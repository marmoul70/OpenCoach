#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd
)"

PACKAGES="$PROJECT_ROOT/scripts/lib/packages.sh"
INSTALL_APP="$PROJECT_ROOT/scripts/bootstrap/install-application.sh"
INSTALL_SERVICES="$PROJECT_ROOT/scripts/bootstrap/install-services.sh"
BACKEND_SERVICE="$PROJECT_ROOT/systemd/opencoach-backend.service"
NGINX_CONFIG="$PROJECT_ROOT/nginx/opencoach.conf"

passed=0
failed=0


check() {
    local description="$1"
    shift

    if "$@"; then
        printf '[ OK ] %s\n' "$description"
        passed=$((passed + 1))
    else
        printf '[FAIL] %s\n' "$description" >&2
        failed=$((failed + 1))
    fi
}


check_nginx_package() {
    grep -Eq \
        '^[[:space:]]+nginx$' \
        "$PACKAGES"
}


check_frontend_build() {
    grep -Fq \
        'npm run build' \
        "$INSTALL_APP"
}


check_backend_loopback() {
    grep -Fq \
        -- '--host 127.0.0.1 --port 8000' \
        "$BACKEND_SERVICE"
}


check_nginx_proxy() {
    grep -Fq \
        'proxy_pass http://127.0.0.1:8000;' \
        "$NGINX_CONFIG"
}


check_nginx_spa_fallback() {
    grep -Fq \
        'try_files $uri $uri/ /index.html;' \
        "$NGINX_CONFIG"
}


check_nginx_installation() {
    grep -Fq \
        'install_nginx_configuration()' \
        "$INSTALL_SERVICES" \
        && grep -Fq \
            'nginx -t' \
            "$INSTALL_SERVICES"
}


check \
    "nginx est une dépendance système" \
    check_nginx_package

check \
    "le frontend est compilé pendant le bootstrap" \
    check_frontend_build

check \
    "FastAPI production écoute uniquement sur localhost" \
    check_backend_loopback

check \
    "Nginx proxifie /api vers FastAPI" \
    check_nginx_proxy

check \
    "Nginx supporte le fallback SPA" \
    check_nginx_spa_fallback

check \
    "le bootstrap installe et valide Nginx" \
    check_nginx_installation


printf '\n'
printf 'Tests réussis : %d\n' "$passed"
printf 'Tests échoués : %d\n' "$failed"

if (( failed > 0 )); then
    exit 1
fi

printf '\n'
printf '[ OK ] Tous les tests Nginx sont réussis.\n'
