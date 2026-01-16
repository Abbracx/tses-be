#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

cleanup() {
    log "Cleaning up..."
    make down-v 2>/dev/null || true
}
trap cleanup EXIT

log "🚀 Starting Integration CI Simulation"

log "📋 Setting up environment..."
cp .env.example .env
mkdir -p logs api-tests/newman-reports

log "🐳 Building services..."
make build

log "⏳ Waiting for services..."
for i in {1..15}; do
    if curl -f http://0.0.0.0:8080/api/v1/auth/redoc/ 2>/dev/null; then
        success "Services ready!"
        break
    fi
    echo "Waiting... ($i/15)"
    sleep 5
done

log "👤 Creating superuser..."
make superuser-auto || error "Failed to create superuser"

log "🔍 Installing API test dependencies..."
cd api-tests && yarn install

# log "🔍 Running OTP tests..."
# yarn test:otp || error "OTP tests failed"
# success "OTP tests passed"

log "🔍 Running audit tests..."
yarn test:audit || error "Audit tests failed"
success "Audit tests passed"

log "🔍 Running full integration tests..."
yarn test:integration || error "Integration tests failed"
success "Integration tests passed"

success "🎉 Integration CI simulation completed!"
log "📁 Reports: api-tests/newman-reports/"
