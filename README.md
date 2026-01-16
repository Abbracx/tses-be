# TSES Backend API

A Django REST API with OTP authentication, audit logging, Redis-based rate limiting, and async task processing.

## Features

- **OTP Authentication**: Passwordless login with email OTP verification
- **Redis Rate Limiting**: Atomic operations for request throttling
- **Audit Logging**: Comprehensive event tracking with async processing
- **Celery Task Queue**: Async email sending and audit log creation
- **JWT Authentication**: Secure token-based authentication
- **Service Layer Architecture**: Decoupled business logic from views
- **API Documentation**: Swagger/ReDoc integration

## Installation & Setup

### Prerequisites

- Python 3.12+
- Redis (for caching and Celery)
- PostgreSQL (optional, SQLite used by default)

### Option 1: Local Installation

1. **Clone the repository**
```bash
git clone git@github.com:Abbracx/tses-be.git
cd tses-be
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment setup**
```bash
cp .env.example .env.local
# Edit .env.local for local development settings
```

5. **Install and start Redis**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# Test Redis connection
redis-cli ping  # Should return: PONG
```

6. **Database setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

7. **Create logs directory**
```bash
mkdir logs
```

8. **Run the application**
```bash
# Terminal 1: Django server
export DJANGO_SETTINGS_MODULE=tses_be.settings.development
python manage.py runserver

# Terminal 2: Celery worker
celery -A tses_be worker --loglevel=info

# Terminal 3: Celery flower (optional monitoring)
celery -A tses_be flower
```

### Option 2: Docker Installation

1. **Clone and navigate**
```bash
git clone git@github.com:Abbracx/tses-be.git
cd tses-be
```

2. **Environment setup**
```bash
cp .env.example .env
# Edit .env for Docker settings (use service names like 'redis', 'postgres')
```

3. **Build and run**
```bash
make build
```

4. **Create superuser**
```bash
make superuser
```

5. **Access services**
- **API**: http://localhost:8080
- **Admin**: http://localhost:8080/admin
- **MailHog**: http://localhost:8025 (Email testing)
- **Flower**: http://localhost:5555 (Celery monitoring)

### Docker Commands

```bash
make build          # Build and start containers
make up             # Start containers
make down           # Stop containers
make show-logs      # View all logs
make show-logs-web  # Django logs
make show-logs-celery  # Celery logs
make show-logs-redis   # Redis logs
make exec           # Access web container shell
make migrate        # Run migrations
make superuser      # Create superuser
make test           # Run tests
make black          # Format code
make isort          # Sort imports
make down-v         # Stop and remove volumes
```

## Configuration

### Environment Variables

```bash
# Security
SECRET_KEY='your-secret-key'
SIGNING_KEY='your-signing-key'
DEBUG=True

# Domain
DOMAIN=localhost:8000

# Database
DATABASE_URL=sqlite:///db.sqlite3  # Local
# DATABASE_URL=postgres://user:pass@postgres:5432/db  # Docker

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0  # Local
# CELERY_BROKER_URL=redis://redis:6379/0  # Docker
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@example.com
```

### Settings Structure

- `base.py`: Common settings (Redis, Celery, JWT, logging)
- `development.py`: Development overrides
- `test.py`: Test-specific settings

## API Endpoints

### OTP Authentication
- `POST /api/v1/auth/otp/request/` - Request OTP (202 on success, 429 on rate limit)
- `POST /api/v1/auth/otp/verify/` - Verify OTP (200 with JWT, 400 on invalid, 423 on lockout)

### Audit Logs
- `GET /api/v1/audit/logs/` - List audit logs (JWT required)
  - Query params: `email`, `event`, `from`, `to`, `page`, `page_size`

### Users
- `GET /api/v1/auth/users/` - List users (admin)
- `GET /api/v1/auth/users/{id}/` - Get user details

### Documentation
- `GET /api/v1/auth/swagger/` - Swagger UI
- `GET /api/v1/auth/redoc/` - ReDoc UI

## Architecture

### Project Structure
```
tses-be/
├── apps/
│   ├── audits/          # Audit logging
│   │   ├── models.py    # AuditLog model
│   │   ├── serializers.py
│   │   ├── services.py  # Business logic
│   │   ├── views.py     # HTTP layer
│   │   └── urls.py
│   ├── common/          # Shared utilities
│   │   ├── helpers.py   # get_client_ip, get_user_agent
│   │   └── models.py    # TimeStampedModel
│   └── users/           # User & OTP management
│       ├── models.py    # User model
│       ├── serializers.py # OTPRequestSerializer, OTPVerifySerializer
│       ├── services.py  # OTPService (business logic)
│       ├── tasks.py     # Celery tasks
│       ├── views.py     # HTTP layer
│       └── urls/
│           ├── base.py  # User endpoints
│           └── otp.py   # OTP endpoints
├── tses_be/
│   ├── settings/
│   │   ├── base.py      # Common settings
│   │   ├── development.py
│   │   └── test.py
│   ├── celery.py        # Celery config
│   └── urls.py          # URL routing
├── api-tests/           # Postman collections
├── scripts/             # CI/CD scripts
└── makefile             # Docker commands
```

### Service Layer Pattern

**OTPService** (`apps/users/services.py`):
- `request_otp()`: Rate limiting, OTP generation, Redis storage
- `verify_otp()`: Lockout check, OTP validation, JWT generation
- `check_rate_limit()`: Email (3/10min) & IP (10/hour) limits
- `check_lockout()`: 5 failed attempts = 15min lockout

**AuditService** (`apps/audits/services.py`):
- `filter_audit_logs()`: Date range and event filtering

**Helpers** (`apps/common/helpers.py`):
- `get_client_ip()`: Extract IP from request
- `get_user_agent()`: Extract user agent

### Redis Usage

**Keys:**
- `otp:{email}` - OTP storage (5min TTL)
- `otp_request_email:{email}` - Email rate limit counter (10min TTL)
- `otp_request_ip:{ip}` - IP rate limit counter (1hr TTL)
- `otp_failed:{email}` - Failed attempt counter (15min TTL)
- `otp_lockout:{email}` - Lockout flag (15min TTL)

**Operations:**
- Atomic `INCR` with `EXPIRE` for rate limiting
- `TTL` for retry_after/unlock_eta calculations
- `DELETE` for one-time OTP use

### Celery Tasks

**send_otp_email** (`apps/users/tasks.py`):
- Async email sending with retry logic
- Max 3 retries with 60s countdown

**write_audit_log** (`apps/users/tasks.py`):
- Async audit log creation
- Events: OTP_REQUESTED, OTP_VERIFIED, OTP_FAILED, OTP_LOCKED

## OTP Implementation Details

### Models

**User** (`apps/users/models.py`):
- UUID for public IDs
- Email as USERNAME_FIELD
- OTP fields (otp, otp_expiry, otp_try_count)
- is_verified flag
- Indexes on email, is_active, is_verified

**AuditLog** (`apps/audits/models.py`):
- TimeStampedModel inheritance
- ForeignKey to User (nullable)
- Email field (for non-registered users)
- Action choices: OTP_REQUESTED, OTP_VERIFIED, OTP_FAILED, OTP_LOCKED
- JSONField for details
- Indexes on email, action, created_at

### OTP Flow Logic

**Request OTP:**
1. Validate email (serializer)
2. Check rate limits (Redis)
3. Generate 6-digit OTP
4. Store in Redis (5min TTL)
5. Increment rate counters (atomic)
6. Queue email task (Celery)
7. Queue audit log task (Celery)
8. Return 202 or 429

**Verify OTP:**
1. Validate email + OTP (serializer)
2. Check lockout status (Redis)
3. Retrieve stored OTP (Redis)
4. Compare OTP values
5. On failure: increment counter, check lockout threshold
6. On success: delete OTP, create/update user, generate JWT
7. Queue audit log task (Celery)
8. Return 200, 400, or 423

### Rate Limiting Strategy

**Email Limit (3/10min):**
- Key: `otp_request_email:{email}`
- First request: SET with TTL=600
- Subsequent: INCR (preserves TTL)
- Check: GET >= 3

**IP Limit (10/hour):**
- Key: `otp_request_ip:{ip}`
- First request: SET with TTL=3600
- Subsequent: INCR (preserves TTL)
- Check: GET >= 10

**Failed Attempts (5/15min):**
- Key: `otp_failed:{email}`
- Increment on wrong OTP
- On 5th failure: SET lockout key, DELETE failed key
- Lockout key: `otp_lockout:{email}` (TTL=900)

## Testing

### Unit Tests
```bash
# Local
pytest tests/ --ds=tses_be.settings.test -v

# Docker
make test

# Coverage
make cov-html
```

### Integration Tests

**Postman Collections** (`api-tests/collections/`):

#### OTP Authentication Tests
1. **OTP Request - Happy Path** (202)
2. **OTP Request - Rate Limit** (429)
3. **OTP Verify - Wrong OTP** (400)
4. **OTP Verify - Lockout** (423)
5. **OTP Verify - Success** (200)

#### Audit Log Tests
1. **Authenticated Access** (200)
2. **Filter by Email**
3. **Filter by Event**
4. **Newest First Ordering**
5. **Pagination**

#### Run Tests
```bash
make install-newman     # Install Newman
make test-integration   # Run all tests
make test-otp          # OTP tests only
make test-audit        # Audit tests only
```

## Development Workflow

### Testing OTP Flow

**1. Request OTP:**
```bash
curl -X POST http://localhost:8080/api/v1/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Response (202):
{"message": "OTP sent successfully", "expires_in": 300}
```

**2. Check Celery logs for OTP:**
```bash
make show-logs-celery
# Look for: "✅ [CELERY TASK] OTP email sent to: test@example.com"
```

**3. Verify OTP:**
```bash
curl -X POST http://localhost:8080/api/v1/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp": "123456"}'

# Response (200):
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "test@example.com",
    "username": "test",
    "is_verified": true
  }
}
```

**4. Access Audit Logs:**
```bash
curl -X GET "http://localhost:8080/api/v1/audit/logs/?email=test@example.com" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Redis Debugging
```bash
make redis-cli          # Access Redis CLI
make redis-keys         # List all keys
make redis-monitor      # Monitor Redis commands
make redis-flush        # Clear all Redis data
```

## Troubleshooting

### Redis Issues

```bash
# Check Redis is running
make show-logs-redis

# Test connection
make redis-cli
> PING

# Check TTL
> TTL otp:test@example.com

# Clear stuck rate limits
> DEL otp_request_email:test@example.com
```

### Celery Issues

```bash
# Check worker is running
make show-logs-celery

# Check for task execution
make show-logs-celery | grep "CELERY TASK"
```

### Database Issues

```bash
# Reset migrations (development only)
make down-v
make build
make migrate

# Check audit logs
make exec
> python manage.py shell
>>> from apps.audits.models import AuditLog
>>> AuditLog.objects.count()
```

## CI/CD Pipeline

### Local Simulation
```bash
make ci-integration
# Or
./scripts/integration-ci-simulation.sh
```

**Pipeline Steps:**
1. 📋 Environment setup
2. 🐳 Docker services build
3. ⏳ Service health checks
4. 👤 Superuser creation
5. 🔍 OTP tests
6. 🔍 Audit tests
7. 📊 Report generation

### Monitoring

**Celery Tasks:**
- Flower UI: http://localhost:5555

**Redis:**
```bash
make redis-monitor
make redis-cli
> KEYS otp:*
```

**Logs:**
```bash
make show-logs
make show-logs-celery | grep "CELERY TASK"
```

## Production Considerations

### Security
- Change SECRET_KEY and SIGNING_KEY
- Set DEBUG=False
- Use HTTPS only
- Configure ALLOWED_HOSTS
- Use strong Redis password
- Rate limit at nginx/load balancer level

### Performance
- Redis clustering for high availability
- Celery worker scaling (multiple workers)
- Database connection pooling
- Monitoring (Sentry, DataDog)

### Backup
- Database backups (automated)
- Redis persistence (RDB/AOF)
- Audit log archival

## License

MIT License

## Author

Raphael Tanko - tankoraphael@gmail.com
