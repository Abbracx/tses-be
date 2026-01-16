build:
	docker compose -f docker-compose.yml up --build -d --remove-orphans

up:
	docker compose -f docker-compose.yml up -d --remove-orphans

down:
	docker compose -f docker-compose.yml down

exec:
	docker compose -f docker-compose.yml exec -it web /bin/bash

config:
	docker compose -f docker-compose.yml config

show-logs:
	docker compose -f docker-compose.yml logs

show-logs-redis:
	docker compose -f docker-compose.yml logs redis

show-logs-celery:
	docker compose -f docker-compose.yml logs celery_worker

show-logs-web:
	docker compose -f docker-compose.yml logs web

migrations:
	docker compose -f docker-compose.yml run --rm web python manage.py makemigrations

migrate:
	docker compose -f docker-compose.yml run --rm web python manage.py migrate

migrate-audits:
	docker compose -f docker-compose.yml run --rm web python manage.py makemigrations audits
	docker compose -f docker-compose.yml run --rm web python manage.py migrate audits

collectstatic:
	docker compose -f docker-compose.yml run --rm web python manage.py collectstatic --no-input --clear

superuser:
	docker compose -f docker-compose.yml run --rm web python manage.py createsuperuser

superuser-auto:
	@echo "Creating superuser automatically..."
	docker compose -f docker-compose.yml exec -T web python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='admin@example.com').exists() or User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass123', first_name='Admin', last_name='User')"

down-v:
	docker compose -f docker-compose.yml down -v

volume:
	docker volume inspect local_postgres_data

redis-cli:
	docker compose -f docker-compose.yml exec redis redis-cli

redis-monitor:
	docker compose -f docker-compose.yml exec redis redis-cli MONITOR

redis-keys:
	docker compose -f docker-compose.yml exec redis redis-cli KEYS "*"

redis-flush:
	docker compose -f docker-compose.yml exec redis redis-cli FLUSHALL

black:
	docker compose -f docker-compose.yml exec web black --exclude=migrations --exclude=venv .

isort:
	docker compose -f docker-compose.yml exec web isort . --skip venv --skip migrations

test:
	docker compose -f docker-compose.yml exec web pytest -p no:warnings -v

cov:
	docker compose -f docker-compose.yml exec web pytest tests/ -p no:warnings --ds=tses_be.settings.test --cov=apps -vv

cov-html:
	docker compose -f docker-compose.yml exec web pytest tests/ -p no:warnings --ds=tses_be.settings.test --cov=apps --cov-report html

install-newman:
	@echo "Installing Newman..."
	cd api-tests && yarn install

test-integration:
	@echo "Running integration tests..."
	cd api-tests && yarn test:integration

test-otp:
	@echo "Running OTP tests..."
	cd api-tests && yarn test:otp

test-audit:
	@echo "Running audit tests..."
	cd api-tests && yarn test:audit

ci-integration:
	@echo "Running CI integration simulation..."
	./scripts/integration-ci-simulation.sh

act-full:
	@echo "Running full GitHub Actions workflow locally..."
	act

