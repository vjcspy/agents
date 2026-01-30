# =============================================================================
# Log Commands
# =============================================================================

# View logs from all services
logs:
    {{compose}} logs -f

# View WordPress logs only
log-wordpress:
    {{compose}} logs -f wordpress

# View MySQL logs only
log-mysql:
    {{compose}} logs -f mysql

# View Nginx logs only
log-nginx:
    {{compose}} logs -f nginx
