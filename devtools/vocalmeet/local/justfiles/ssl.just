# =============================================================================
# SSL Certificate Commands
# =============================================================================

# Domain name
domain := "vocalmeet.local"

# Generate SSL certificate for HTTPS (first time setup)
ssl-generate:
    @echo "🔐 Generating SSL certificate..."
    ./scripts/generate-ssl.sh

# Check SSL certificate status
ssl-check:
    @echo "🔍 Checking SSL certificate..."
    @if [ -f ./ssl/{{domain}}.crt ]; then \
        echo "✅ SSL certificate exists for {{domain}}"; \
        openssl x509 -in ./ssl/{{domain}}.crt -noout -dates 2>/dev/null || echo "   (Could not read certificate details)"; \
    else \
        echo "❌ SSL certificate not found. Run: just ssl-generate"; \
    fi

# Check if domain is in /etc/hosts
hosts-check:
    @echo "🔍 Checking /etc/hosts for {{domain}}..."
    @grep -q "{{domain}}" /etc/hosts && echo "✅ {{domain}} found in /etc/hosts" || echo "❌ {{domain}} NOT in /etc/hosts. Run: just hosts-add"

# Add domain to /etc/hosts (requires sudo)
hosts-add:
    @echo "📝 Adding {{domain}} to /etc/hosts..."
    @grep -q "{{domain}}" /etc/hosts || sudo sh -c 'echo "127.0.0.1 {{domain}}" >> /etc/hosts'
    @echo "✅ Done. {{domain}} is now in /etc/hosts"
