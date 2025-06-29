# GitHub Deployment Guide - Multi-Tenant SaaS Platform

## 🚀 Quick Start

### 1. Push to GitHub

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit: Multi-Tenant SaaS Platform with External Integrations"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git push -u origin main
```

### 2. Test Locally Before Deployment

```bash
# Run the deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Or manually:
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py test
python scripts/test_endpoints.py
```

### 3. Production Deployment Options

## 🌐 Deployment Options

### Option A: Heroku (Recommended for Quick Deployment)

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Or download from: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku App**
   ```bash
   heroku create your-saas-platform
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY="your-secret-key"
   heroku config:set DEBUG="False"
   heroku config:set DATABASE_URL="your-postgres-url"
   heroku config:set ALLOWED_HOSTS="your-app.herokuapp.com"
   ```

4. **Deploy**
   ```bash
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

### Option B: DigitalOcean App Platform

1. **Connect GitHub Repository**
   - Go to DigitalOcean App Platform
   - Connect your GitHub account
   - Select your repository

2. **Configure App**
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn config.wsgi:application`
   - Environment Variables: Set all required Django settings

3. **Deploy**
   - Click "Deploy" and wait for build to complete

### Option C: AWS Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB Application**
   ```bash
   eb init -p python-3.11 your-saas-platform
   eb create production
   ```

3. **Configure Environment**
   ```bash
   eb setenv SECRET_KEY="your-secret-key" DEBUG="False"
   ```

4. **Deploy**
   ```bash
   eb deploy
   ```

### Option D: Docker Deployment

1. **Build and Run with Docker**
   ```bash
   # Build the image
   docker build -t saas-platform .
   
   # Run the container
   docker run -p 8000:8000 -e SECRET_KEY="your-key" saas-platform
   ```

2. **Docker Compose (Recommended)**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Run migrations
   docker-compose exec web python manage.py migrate
   ```

## 🔧 Environment Configuration

### Required Environment Variables

Create a `.env` file or set these in your deployment platform:

```bash
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database (for production)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Redis (for caching and Celery)
REDIS_URL=redis://localhost:6379/0

# Email (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=5
JWT_REFRESH_TOKEN_LIFETIME=1
```

### Production Settings Checklist

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` is set and secure
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] Database is PostgreSQL (not SQLite)
- [ ] Static files are served by web server
- [ ] SSL/HTTPS is configured
- [ ] Logging is configured
- [ ] Monitoring is set up

## 🧪 Testing in Production

### 1. Run Endpoint Tests

```bash
# Test against your production URL
python scripts/test_endpoints.py --base-url "https://your-domain.com"

# Save results to file
python scripts/test_endpoints.py --base-url "https://your-domain.com" --output test_results.json
```

### 2. Manual Testing Checklist

- [ ] Health endpoint: `GET /health/`
- [ ] User registration: `POST /api/auth/register/`
- [ ] User login: `POST /api/auth/login/`
- [ ] JWT token: `POST /api/auth/token/`
- [ ] User profile: `GET /api/auth/profile/`
- [ ] Users list: `GET /api/users/`
- [ ] Webhook endpoints: `POST /api/integrations/webhooks/*`

### 3. Load Testing (Optional)

```bash
# Install Apache Bench
# macOS: brew install httpd
# Ubuntu: sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 https://your-domain.com/health/

# Test registration endpoint
ab -n 100 -c 5 -p test_data.json -T application/json https://your-domain.com/api/auth/register/
```

## 📊 Monitoring and Logging

### 1. Application Monitoring

- **Sentry**: Error tracking and performance monitoring
- **New Relic**: Application performance monitoring
- **Datadog**: Infrastructure and application monitoring

### 2. Logging Configuration

Add to your production settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/app.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🔒 Security Checklist

- [ ] HTTPS/SSL is enabled
- [ ] `SECRET_KEY` is secure and not in version control
- [ ] `DEBUG = False` in production
- [ ] Database credentials are secure
- [ ] CORS is properly configured
- [ ] Rate limiting is enabled
- [ ] Input validation is working
- [ ] Audit logging is active
- [ ] Regular security updates

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check database URL
   echo $DATABASE_URL
   
   # Test connection
   python manage.py dbshell
   ```

2. **Static Files Not Loading**
   ```bash
   # Collect static files
   python manage.py collectstatic --noinput
   
   # Check static files directory
   ls -la staticfiles/
   ```

3. **Migration Errors**
   ```bash
   # Check migration status
   python manage.py showmigrations
   
   # Reset migrations (if needed)
   python manage.py migrate --fake-initial
   ```

4. **Permission Errors**
   ```bash
   # Check file permissions
   chmod +x scripts/*.sh
   chmod 755 staticfiles/
   ```

### Getting Help

1. Check the logs: `heroku logs --tail` (Heroku)
2. Check application logs: `/var/log/django/app.log`
3. Run tests: `python scripts/test_endpoints.py`
4. Check Django admin: `https://your-domain.com/admin/`

## 📈 Performance Optimization

1. **Database Optimization**
   - Add database indexes
   - Use database connection pooling
   - Monitor slow queries

2. **Caching**
   - Enable Redis caching
   - Cache expensive database queries
   - Use CDN for static files

3. **Code Optimization**
   - Use select_related() and prefetch_related()
   - Optimize database queries
   - Use async tasks for heavy operations

## 🎉 Success!

Your Multi-Tenant SaaS Platform is now deployed and ready for production use!

**Next Steps:**
1. Set up monitoring and alerting
2. Configure automated backups
3. Set up CI/CD pipeline
4. Plan for scaling
5. Document API for users

---

**Need Help?** Check the `docs/` directory for detailed documentation. 