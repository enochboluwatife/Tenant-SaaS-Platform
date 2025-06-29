# Deployment Guide

## Overview

This guide covers deploying the Multi-Tenant SaaS Platform with External Integrations to various environments.

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **PostgreSQL**: 13 or higher
- **Redis**: 6 or higher
- **Docker**: 20.10 or higher (optional)
- **Nginx**: 1.18 or higher (production)

### Required Services

- **Database**: PostgreSQL for production, SQLite for development
- **Cache**: Redis for session storage and caching
- **Message Queue**: Redis/Celery for background tasks
- **Web Server**: Nginx for production

## Environment Setup

### 1. Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Copy the example file
cp .env.example .env

# Edit with your production values
nano .env
```

**Required Environment Variables:**

```bash
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-production-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/saas_platform

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Database Setup

#### PostgreSQL Installation

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Create Database:**
```bash
sudo -u postgres psql
CREATE DATABASE saas_platform;
CREATE USER saas_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE saas_platform TO saas_user;
\q
```

### 3. Redis Setup

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

## Development Deployment

### 1. Local Development

```bash
# Clone the repository
git clone <repository-url>
cd saas-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your local settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### 2. Docker Development

```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f
```

## Production Deployment

### 1. Server Preparation

#### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx postgresql redis-server
```

#### Create Application User
```bash
sudo adduser saas
sudo usermod -aG sudo saas
sudo su - saas
```

### 2. Application Deployment

#### Clone Repository
```bash
cd /home/saas
git clone <repository-url> saas-platform
cd saas-platform
```

#### Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

#### Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with production values
```

#### Database Setup
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 3. Gunicorn Configuration

Create `/home/saas/saas-platform/gunicorn.conf.py`:

```python
# Gunicorn configuration
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
```

### 4. Systemd Service

Create `/etc/systemd/system/saas-platform.service`:

```ini
[Unit]
Description=SaaS Platform Gunicorn daemon
After=network.target

[Service]
User=saas
Group=saas
WorkingDirectory=/home/saas/saas-platform
Environment="PATH=/home/saas/saas-platform/venv/bin"
ExecStart=/home/saas/saas-platform/venv/bin/gunicorn --config gunicorn.conf.py config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start saas-platform
sudo systemctl enable saas-platform
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/saas-platform`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Client Max Body Size
    client_max_body_size 10M;
    
    # Static Files
    location /static/ {
        alias /home/saas/saas-platform/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media Files
    location /media/ {
        alias /home/saas/saas-platform/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health Check
    location /health/ {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/saas-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Celery Setup

Create `/etc/systemd/system/saas-platform-celery.service`:

```ini
[Unit]
Description=SaaS Platform Celery Worker
After=network.target

[Service]
Type=forking
User=saas
Group=saas
WorkingDirectory=/home/saas/saas-platform
Environment="PATH=/home/saas/saas-platform/venv/bin"
ExecStart=/home/saas/saas-platform/venv/bin/celery multi start worker1 -A config -l info
ExecStop=/home/saas/saas-platform/venv/bin/celery multi stopwait worker1 -A config
ExecReload=/home/saas/saas-platform/venv/bin/celery multi restart worker1 -A config

[Install]
WantedBy=multi-user.target
```

Start Celery:
```bash
sudo systemctl daemon-reload
sudo systemctl start saas-platform-celery
sudo systemctl enable saas-platform-celery
```

### 7. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Docker Production Deployment

### 1. Docker Compose Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    restart: always
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgresql://saas_user:password@db:5432/saas_platform
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    networks:
      - saas_network

  db:
    image: postgres:13
    restart: always
    environment:
      - POSTGRES_DB=saas_platform
      - POSTGRES_USER=saas_user
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - saas_network

  redis:
    image: redis:6-alpine
    restart: always
    networks:
      - saas_network

  celery:
    build: .
    restart: always
    command: celery -A config worker -l info
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgresql://saas_user:password@db:5432/saas_platform
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    networks:
      - saas_network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - web
    networks:
      - saas_network

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  saas_network:
    driver: bridge
```

### 2. Deploy with Docker

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Monitoring and Maintenance

### 1. Health Checks

```bash
# Check application health
curl https://yourdomain.com/health/

# Check service status
sudo systemctl status saas-platform
sudo systemctl status saas-platform-celery
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis
```

### 2. Log Monitoring

```bash
# Application logs
sudo journalctl -u saas-platform -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Database logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

### 3. Backup Strategy

#### Database Backup
```bash
# Create backup script
sudo nano /home/saas/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/saas/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="saas_platform"

mkdir -p $BACKUP_DIR
pg_dump $DB_NAME > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

```bash
chmod +x /home/saas/backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/saas/backup.sh
```

### 4. Performance Monitoring

#### Install Monitoring Tools
```bash
sudo apt install htop iotop nethogs
```

#### Database Performance
```bash
# Check slow queries
sudo -u postgres psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
sudo -u postgres psql -c "\l"
```

#### 2. Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping
```

#### 3. Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check permissions
sudo chown -R saas:saas /home/saas/saas-platform/staticfiles
```

#### 4. Celery Tasks Not Running
```bash
# Check Celery status
sudo systemctl status saas-platform-celery

# Check Celery logs
sudo journalctl -u saas-platform-celery -f
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Create indexes for common queries
CREATE INDEX idx_tenant_user_email ON tenants_tenantuser(email);
CREATE INDEX idx_audit_log_timestamp ON audit_auditlog(timestamp);
CREATE INDEX idx_webhook_event_created ON integrations_webhookevent(created_at);
```

#### 2. Caching Strategy
```python
# Add to settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Security Considerations

### 1. Firewall Configuration
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Regular Updates
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Security updates
sudo unattended-upgrades
```

### 3. SSL/TLS Configuration
- Use strong SSL/TLS protocols
- Enable HSTS
- Regular certificate renewal
- Perfect Forward Secrecy

## Scaling Considerations

### 1. Horizontal Scaling
- Multiple Django instances behind load balancer
- Database read replicas
- Redis clustering
- CDN for static files

### 2. Vertical Scaling
- Increase server resources
- Database optimization
- Application profiling
- Caching strategies

This deployment guide provides a comprehensive approach to deploying the SaaS platform in production environments.
