#!/bin/bash
set -e

echo "🚀 Starting Local CI/CD Simulation..."

echo "📋 Setting up environment..."
cp .env.example .env
mkdir -p logs api-tests/newman-reports

echo "🐳 Starting Docker services..."
make build

echo "⏳ Waiting for services..."
for i in {1..20}; do
    if curl -f http://localhost:8080/api/v1/auth/redoc/ 2>/dev/null; then
        echo "✅ Services ready!"
        break
    fi
    echo "Waiting... ($i/20)"
    sleep 5
done

echo "👤 Creating superuser..."
make superuser-auto

echo "🔍 Running integration tests..."
cd api-tests && yarn install
yarn test:integration

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi

echo "📊 Reports: api-tests/newman-reports/"
