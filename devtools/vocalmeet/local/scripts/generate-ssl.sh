#!/bin/bash
# =============================================================================
# Generate Locally-Trusted SSL Certificate using mkcert
# =============================================================================
# Requires: mkcert (https://github.com/FiloSottile/mkcert)
# Install: brew install mkcert && mkcert -install
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="${SCRIPT_DIR}/../ssl"
DOMAIN="vocalmeet.local"

mkdir -p "${SSL_DIR}"

# Check if mkcert is installed
if ! command -v mkcert &> /dev/null; then
    echo "❌ mkcert not found. Please install it first:"
    echo "   brew install mkcert"
    echo "   mkcert -install"
    exit 1
fi

# Check if mkcert CA is installed
if ! mkcert -CAROOT &> /dev/null; then
    echo "📦 Installing mkcert CA..."
    mkcert -install
fi

echo "🔐 Generating locally-trusted SSL certificate for ${DOMAIN}..."

# Generate certificate with mkcert
cd "${SSL_DIR}"
mkcert -key-file "${DOMAIN}.key" -cert-file "${DOMAIN}.crt" "${DOMAIN}" localhost 127.0.0.1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL certificate generated successfully!"
    echo "   - Certificate: ${SSL_DIR}/${DOMAIN}.crt"
    echo "   - Private Key: ${SSL_DIR}/${DOMAIN}.key"
    echo ""
    echo "🎉 Certificate is automatically trusted by your system!"
    echo "   No browser warnings for https://${DOMAIN}"
else
    echo "❌ Failed to generate SSL certificate"
    exit 1
fi
