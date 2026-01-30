# =============================================================================
# Development Helper Commands
# =============================================================================

# Open WordPress in browser
open:
    open {{wordpress_url}}

# Open phpMyAdmin in browser
open-db:
    open {{phpmyadmin_url}}

# Watch plugin directory for changes (requires fswatch)
watch-plugins:
    @echo "👀 Watching {{source_path}}/plugins for changes..."
    fswatch -o {{source_path}}/plugins | xargs -n1 -I{} echo "📁 Plugin files changed"

# Shell into WordPress container
shell:
    {{compose}} exec wordpress bash

# Show WordPress debug log
debug-log:
    {{compose}} exec wordpress tail -f /var/www/html/wp-content/debug.log

# Enable Xdebug
debug-on:
    @sed -i '' 's/xdebug.mode=off/xdebug.mode=debug/g' ./php/xdebug.ini
    @sed -i '' 's/xdebug.start_with_request=no/xdebug.start_with_request=yes/g' ./php/xdebug.ini
    @echo "🚀 Enabling Xdebug..."
    @{{compose}} exec wordpress apache2ctl graceful 2>/dev/null
    @echo "✅ Xdebug enabled (port 9003)"

# Disable Xdebug
debug-off:
    @sed -i '' 's/xdebug.mode=debug/xdebug.mode=off/g' ./php/xdebug.ini
    @sed -i '' 's/xdebug.start_with_request=yes/xdebug.start_with_request=no/g' ./php/xdebug.ini
    @echo "🛑 Disabling Xdebug..."
    @{{compose}} exec wordpress apache2ctl graceful 2>/dev/null
    @echo "✅ Xdebug disabled"
