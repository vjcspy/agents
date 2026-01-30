# =============================================================================
# Database Commands
# =============================================================================

# Access MySQL shell
db-shell:
    {{compose}} exec mysql mysql -u vocalmeet -pvocalmeet_pass vocalmeet

# Access MySQL as root
db-root:
    {{compose}} exec mysql mysql -u root -pvocalmeet_root_pass

# Export database to file
db-export:
    @echo "📤 Exporting database..."
    {{compose}} exec mysql mysqldump -u root -pvocalmeet_root_pass vocalmeet > ./backup.sql
    @echo "✅ Database exported to ./backup.sql"

# Import database from file
db-import file:
    @echo "📥 Importing database from {{file}}..."
    {{compose}} exec -T mysql mysql -u root -pvocalmeet_root_pass vocalmeet < {{file}}
    @echo "✅ Database imported"

# Reset database (drop and recreate)
db-reset:
    @echo "⚠️  This will DELETE all data. Press Ctrl+C to cancel..."
    @sleep 3
    {{compose}} exec mysql mysql -u root -pvocalmeet_root_pass -e "DROP DATABASE IF EXISTS vocalmeet; CREATE DATABASE vocalmeet;"
    @echo "✅ Database reset complete"
