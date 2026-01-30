# =============================================================================
# Assessment Specific Commands
# =============================================================================

# Quick setup for assessment: start + install required plugins + configure permalinks
assessment-start: start
    @echo "⏳ Waiting for WordPress to be ready..."
    @sleep 15
    @echo "📦 Checking plugins..."
    @echo ""
    @echo "   Elementor:"
    @{{compose}} run --rm wpcli plugin is-installed elementor 2>/dev/null && echo "   ✅ Already installed" || ({{compose}} run --rm wpcli plugin install elementor --activate && echo "   ✅ Installed & activated")
    @echo ""
    @echo "   WooCommerce:"
    @{{compose}} run --rm wpcli plugin is-installed woocommerce 2>/dev/null && echo "   ✅ Already installed" || ({{compose}} run --rm wpcli plugin install woocommerce --activate && echo "   ✅ Installed & activated")
    @echo ""
    @echo "🔧 Configuring permalinks..."
    @{{compose}} run --rm wpcli rewrite structure '/%postname%/' 2>&1 | grep -v "Warning:" || true
    @just fix-htaccess
    @echo ""
    @echo "✅ Assessment environment ready!"
    @echo "   WordPress:   {{wordpress_url}}"
    @echo "   phpMyAdmin:  {{phpmyadmin_url}}"

# Fix .htaccess for pretty permalinks (WP-CLI can't generate rewrite rules in CLI context)
fix-htaccess:
    @./scripts/fix-htaccess.sh

# Verify assessment setup with health checks
assessment-verify:
    @echo "🔍 Verifying assessment setup..."
    @echo ""
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "📡 Health Checks"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo ""
    @echo "1️⃣  WordPress Site ({{wordpress_url}}):"
    @curl -sk -o /dev/null -w "   HTTP Status: %{http_code}\n   Response Time: %{time_total}s\n" {{wordpress_url}} || echo "   ❌ FAILED - WordPress not responding"
    @echo ""
    @echo "2️⃣  WordPress REST API (/wp-json):"
    @curl -sk -o /dev/null -w "   HTTP Status: %{http_code}\n   Response Time: %{time_total}s\n" {{wordpress_url}}/wp-json || echo "   ❌ FAILED - REST API not responding"
    @echo ""
    @echo "3️⃣  WooCommerce REST API (/wp-json/wc/v3):"
    @curl -sk -o /dev/null -w "   HTTP Status: %{http_code}\n   Response Time: %{time_total}s\n" {{wordpress_url}}/wp-json/wc/v3 || echo "   ❌ FAILED - WooCommerce API not responding"
    @echo ""
    @echo "4️⃣  phpMyAdmin ({{phpmyadmin_url}}):"
    @curl -s -o /dev/null -w "   HTTP Status: %{http_code}\n   Response Time: %{time_total}s\n" {{phpmyadmin_url}} || echo "   ❌ FAILED - phpMyAdmin not responding"
    @echo ""
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "📋 WordPress Info"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo ""
    @echo "WordPress version:"
    @{{compose}} run --rm wpcli core version 2>/dev/null || echo "   ❌ Could not get WordPress version"
    @echo ""
    @echo "Active plugins:"
    @{{compose}} run --rm wpcli plugin list --status=active 2>/dev/null || echo "   ❌ Could not list plugins"
    @echo ""
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "🔑 WooCommerce API Keys"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo ""
    @{{compose}} run --rm wpcli wc api keys list 2>/dev/null || echo "   ⚠️  No API keys found. Create one:"
    @echo "   → WP Admin: {{wordpress_url}}/wp-admin/admin.php?page=wc-settings&tab=advanced&section=keys"
    @echo "   → Or run:   just wc-create-api-keys"
    @echo ""
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "✅ Verification complete!"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if required plugins are installed
assessment-check-plugins:
    @echo "📦 Checking required plugins..."
    @echo ""
    @echo "Elementor:"
    @{{compose}} run --rm wpcli plugin is-installed elementor 2>/dev/null && {{compose}} run --rm wpcli plugin is-active elementor 2>/dev/null && echo "   ✅ Installed & Active" || echo "   ❌ Not installed or inactive"
    @echo ""
    @echo "WooCommerce:"
    @{{compose}} run --rm wpcli plugin is-installed woocommerce 2>/dev/null && {{compose}} run --rm wpcli plugin is-active woocommerce 2>/dev/null && echo "   ✅ Installed & Active" || echo "   ❌ Not installed or inactive"
