# =============================================================================
# Common Variables & Settings
# =============================================================================
# Shared configuration for all justfiles
# =============================================================================

set shell := ["bash", "-cu"]
set dotenv-load

# Docker compose file for assessment
compose := "docker compose -f ./docker-compose-assessment.yaml"

# Source code path (from .env WORDPRESS_SOURCE_PATH)
source_path := env_var_or_default("WORDPRESS_SOURCE_PATH", "/Users/kai/work/k/vocalmeet/vocalmeet/assessment/wordpress")

# URLs
wordpress_url := "https://vocalmeet.local"
phpmyadmin_url := "http://vocalmeet.local:8081"
