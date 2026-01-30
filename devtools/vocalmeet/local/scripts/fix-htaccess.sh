#!/bin/bash
# =============================================================================
# Fix .htaccess for WordPress pretty permalinks
# =============================================================================
# WP-CLI can't generate .htaccess rewrite rules in CLI context
# This script writes the correct rules directly to the container
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/../docker-compose-assessment.yaml"

echo "   📝 Writing .htaccess rewrite rules..."

docker compose -f "$COMPOSE_FILE" exec -T wordpress bash -c 'cat > /var/www/html/.htaccess << "EOF"
# BEGIN WordPress
# The directives (lines) between "BEGIN WordPress" and "END WordPress" are
# dynamically generated, and should only be modified via WordPress filters.
# Any changes to the directives between these markers will be overwritten.
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
RewriteBase /
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
</IfModule>
# END WordPress
EOF'

if [ $? -eq 0 ]; then
    echo "   ✅ Permalinks configured"
else
    echo "   ❌ Failed to write .htaccess"
    exit 1
fi
