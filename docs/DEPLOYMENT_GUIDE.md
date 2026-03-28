# Certivo Blog - Deployment Guide

This guide covers deploying Certivo to production environments.

---

## ⚠️ Pre-Deployment Checklist

### **Critical Security Actions**

1. **Change Default Admin Credentials**
   - Default: `admin@certivo.com` / `admin123`
   - Change immediately after first login

2. **Remove Hardcoded Credentials from .env**
   ```bash
   # Current .env has exposed Gmail credentials
   # Delete and recreate with secure values
   ```

3. **Generate New SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. **Update DATABASE_URL** for production (PostgreSQL recommended)

5. **Set FLASK_ENV=production**

---

## 📦 Option 1: Deploy to Railway (Recommended for Beginners)

### Step 1: Prepare Your Repository

```bash
# Create these files in your project root
```

**railway.json:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 app:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**nixpacks.toml:**
```toml
[phases.setup]
nixPkgs = ["python312"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = ["python compile_scss.py"]

[start]
cmd = "gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 app:app"
```

### Step 2: Configure Environment Variables

In Railway dashboard, set these variables:

```bash
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<your-generated-secret-key>
DATABASE_URL=<postgresql-connection-string>
SITE_URL=https://your-domain.railway.app
SITE_NAME=Certivo
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-app-password@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@certivo.com
ADSENSE_ENABLED=false
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true
```

### Step 3: Deploy

1. Push code to GitHub
2. Connect Railway to your GitHub repo
3. Railway auto-detects and deploys
4. Run migrations: `railway run flask db upgrade`

---

## 📦 Option 2: Deploy to Render

### render.yaml

```yaml
services:
  - type: web
    name: certivo-blog
    env: python
    region: oregon
    plan: starter
    branch: main
    buildCommand: "pip install -r requirements.txt && python compile_scss.py"
    startCommand: "gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 app:app"
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: certivo-db
          property: connectionString
      - key: SITE_URL
        fromService:
          type: web
          name: certivo-blog
          property: host
      - key: MAIL_SERVER
        value: smtp.gmail.com
      - key: MAIL_USERNAME
        sync: false
      - key: MAIL_PASSWORD
        sync: false
      - key: ADMIN_EMAIL
        sync: false

  - type: web
    name: certivo-db
    databaseName: certivo
    plan: starter
    region: oregon

```

### Deploy Steps

1. Create `render.yaml` in project root
2. Push to GitHub
3. Connect to Render
4. Set remaining environment variables in dashboard
5. Deploy automatically

---

## 📦 Option 3: Deploy to VPS (DigitalOcean, Linode, AWS EC2)

### Server Setup Script

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib supervisor

# Create application user
useradd -m -s /bin/bash certivo
su - certivo

# Clone your repository
git clone https://github.com/yourusername/certivo.git
cd certivo

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create production .env
nano .env
```

### Production .env

```bash
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<your-64-character-secret-key>
DATABASE_URL=postgresql://certivo_user:password@localhost:5432/certivo_db
SITE_URL=https://your-domain.com
SITE_NAME=Certivo
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@certivo.com
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true
WTF_CSRF_ENABLED=true
```

### PostgreSQL Setup

```bash
# Switch to postgres user
sudo -i -u postgres

# Create database and user
psql
CREATE DATABASE certivo_db;
CREATE USER certivo_user WITH PASSWORD 'strong_password';
ALTER ROLE certivo_user SET client_encoding TO 'utf8';
ALTER ROLE certivo_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE certivo_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE certivo_db TO certivo_user;
\q
exit
```

### Gunicorn Systemd Service

```bash
sudo nano /etc/systemd/system/certivo.service
```

**certivo.service:**
```ini
[Unit]
Description=Gunicorn instance to serve Certivo Blog
After=network.target

[Service]
User=certivo
Group=www-data
WorkingDirectory=/home/certivo/certivo
Environment="PATH=/home/certivo/certivo/venv/bin"
ExecStart=/home/certivo/certivo/venv/bin/gunicorn --workers 4 --threads 2 --bind 0.0.0.0:8000 app:app

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable certivo
sudo systemctl start certivo
sudo systemctl status certivo
```

### Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/certivo
```

**certivo:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /home/certivo/certivo/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;
    limit_req zone=one burst=20 nodelay;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/certivo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## 📦 Option 4: Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 certivo && chown -R certivo:certivo /app
USER certivo

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "app:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://certivo:password@db:5432/certivo_db
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - uploads:/app/app/static/uploads
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=certivo_db
      - POSTGRES_USER=certivo
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U certivo"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./static:/app/static:ro
      - uploads:/app/app/static/uploads:ro
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  uploads:
```

### Deploy with Docker

```bash
# Build and run
docker-compose up -d --build

# Run migrations
docker-compose exec web flask db upgrade

# View logs
docker-compose logs -f
```

---

## 🔧 Post-Deployment Tasks

### 1. Initialize Database

```bash
# For Railway/Render (via console)
python run.py --init-db

# For VPS
source venv/bin/activate
python run.py --init-db
```

### 2. Create First Admin User

```python
# In Python shell
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = User(
        username="admin",
        email="admin@certivo.com",
        password_hash=generate_password_hash("YourSecurePassword123!"),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
```

### 3. Set Up Monitoring

**Add to requirements.txt:**
```
sentry-sdk[flask]==1.40.0
```

**In app/__init__.py:**
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
    environment=os.environ.get("FLASK_ENV", "production")
)
```

### 4. Set Up Database Backups

**For PostgreSQL:**
```bash
# Create backup script
nano /home/certivo/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/certivo/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U certivo_user certivo_db > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

```bash
# Add to crontab
crontab -e
# Add: 0 2 * * * /home/certivo/backup.sh
```

---

## 📊 Performance Optimization

### 1. Add Caching (Redis)

**requirements.txt:**
```
redis==5.0.1
Flask-Caching==2.1.0
```

**app/config.py:**
```python
CACHE_TYPE = "RedisCache"
CACHE_REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
CACHE_REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
CACHE_REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
CACHE_DEFAULT_TIMEOUT = 300
```

**app/__init__.py:**
```python
from flask_caching import Cache
cache = Cache()

def create_app():
    # ...
    cache.init_app(app)
```

### 2. Enable Database Connection Pooling

**app/config.py:**
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}
```

### 3. Add Gzip Compression (Nginx)

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied expired no-cache no-store private auth;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript;
gzip_disable "MSIE [1-6]\.";
```

---

## 🛡️ Security Hardening

### 1. Add Rate Limiting

**requirements.txt:**
```
Flask-Limiter==3.5.0
```

**app/__init__.py:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
```

**app/routes/auth.py:**
```python
from app import limiter

@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@anonymous_required()
def login():
    # ...
```

### 2. Add CAPTCHA to Forms

Use Cloudflare Turnstile or Google reCAPTCHA v3.

### 3. Security Headers

Add to Nginx config or Flask after_request:

```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://pagead2.googlesyndication.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://www.google-analytics.com;"
    return response
```

---

## 📈 Monitoring & Logging

### 1. Structured Logging

**app/config.py:**
```python
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = os.environ.get("LOG_FILE", "logs/certivo.log")
```

**app/__init__.py:**
```python
import logging
from logging.handlers import RotatingFileHandler

def create_app():
    # ...
    if not app.debug:
        handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,
            backupCount=5
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(app.config['LOG_LEVEL'])
        app.logger.addHandler(handler)
        app.logger.setLevel(app.config['LOG_LEVEL'])
```

### 2. Health Check Endpoint

**app/routes/main.py:**
```python
@bp.route("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}, 200
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection string
echo $DATABASE_URL
```

**2. Permission Denied on Uploads**
```bash
sudo chown -R www-data:www-data /path/to/uploads
sudo chmod -R 755 /path/to/uploads
```

**3. SCSS Compilation Fails**
```bash
# Manually compile
python compile_scss.py
```

**4. Gunicorn Workers Timeout**
```ini
# Increase timeout in systemd service
TimeoutStartSec=60
```

---

## 📝 Maintenance Tasks

### Weekly
- Review error logs
- Check disk space
- Verify backups are working

### Monthly
- Update dependencies: `pip list --outdated`
- Review security advisories
- Clean up old sessions/cache

### Quarterly
- Full security audit
- Performance review
- Database optimization (VACUUM for PostgreSQL)

---

## 🎯 Quick Start Commands

```bash
# Development
python run.py

# Production (local testing)
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app

# Initialize database
python run.py --init-db

# Run migrations
flask db upgrade

# Check database
flask shell
>>> from app.models.user import User
>>> User.query.count()

# View logs
tail -f logs/certivo.log

# Backup database (PostgreSQL)
pg_dump -U certivo_user certivo_db > backup.sql

# Restore database
psql -U certivo_user certivo_db < backup.sql
```

---

## 📞 Support

For issues:
1. Check logs first
2. Review Flask documentation
3. Search GitHub issues
4. Contact hosting provider support

---

**Last Updated:** March 24, 2026
**Version:** 1.0.0
