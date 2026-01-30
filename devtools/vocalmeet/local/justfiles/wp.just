# =============================================================================
# WP-CLI Commands
# =============================================================================

# Run WP-CLI command (usage: just wp <command>)
wp *args:
    {{compose}} run --rm wpcli {{args}}

# Install and activate a plugin
plugin-install name:
    {{compose}} run --rm wpcli plugin install {{name}} --activate

# List installed plugins
plugin-list:
    {{compose}} run --rm wpcli plugin list

# WordPress core version
wp-version:
    {{compose}} run --rm wpcli core version

# Create WooCommerce REST API keys (run after WooCommerce is installed)
wc-create-api-keys:
    @echo "🔑 Creating WooCommerce REST API keys..."
    @echo "   Go to: {{wordpress_url}}/wp-admin/admin.php?page=wc-settings&tab=advanced&section=keys"
    @echo "   Or run the following WP-CLI command after completing WordPress setup:"
    @echo ""
    @echo "   just wp wc api keys create --name=\"Assessment API\" --user=admin --permissions=read_write"
