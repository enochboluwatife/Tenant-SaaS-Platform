#!/bin/bash

# Multi-Tenant SaaS Platform Deployment Script
# This script automates the deployment process for the Django SaaS platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="saas-platform"
DJANGO_SETTINGS_MODULE="config.settings.production"
ADMIN_EMAIL=${ADMIN_EMAIL:-"admin@example.com"}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-"admin_password_123"}

echo -e "${BLUE}🚀 Starting deployment of Multi-Tenant SaaS Platform...${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "manage.py not found. Please run this script from the project root."
    exit 1
fi

print_status "Project structure verified"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 0 ]]; then
    print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi
print_status "Python version check passed: $PYTHON_VERSION"

# Install/upgrade pip
print_status "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Set environment variables
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run database migrations
print_status "Running database migrations..."
python3 manage.py migrate --noinput

# Collect static files
print_status "Collecting static files..."
python3 manage.py collectstatic --noinput

# Create superuser if it doesn't exist
print_status "Setting up admin user..."
python3 manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='$ADMIN_EMAIL').exists():
    User.objects.create_superuser('admin', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print('Superuser created: admin/$ADMIN_EMAIL')
else:
    print('Superuser already exists')
EOF

# Run tests
print_status "Running tests..."
python3 manage.py test --verbosity=2

# Check for security issues
print_status "Running security checks..."
python3 manage.py check --deploy

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p media
mkdir -p static

# Set proper permissions
print_status "Setting file permissions..."
chmod 755 manage.py
chmod -R 755 static/
chmod -R 755 media/

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << EOF
# Django Settings
DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://saas_user:${POSTGRES_PASSWORD:-saas_password}@localhost:5432/saas_platform

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT Settings
JWT_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# External APIs
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
SENDGRID_API_KEY=your_sendgrid_key

# Admin User
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_PASSWORD=$ADMIN_PASSWORD
EOF
    print_warning "Please update the .env file with your actual credentials"
fi

# Create systemd service file (for Linux systems)
if command -v systemctl &> /dev/null; then
    print_status "Creating systemd service file..."
    sudo tee /etc/systemd/system/$PROJECT_NAME.service > /dev/null << EOF
[Unit]
Description=Multi-Tenant SaaS Platform
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
Environment=PYTHONPATH=$(pwd)
ExecStart=/usr/bin/python3 manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start the service
    sudo systemctl daemon-reload
    sudo systemctl enable $PROJECT_NAME
    print_status "Systemd service created and enabled"
fi

# Create nginx configuration (if nginx is available)
if command -v nginx &> /dev/null; then
    print_status "Creating nginx configuration..."
    sudo tee /etc/nginx/sites-available/$PROJECT_NAME > /dev/null << EOF
server {
    listen 80;
    server_name localhost;

    location /static/ {
        alias $(pwd)/static/;
    }

    location /media/ {
        alias $(pwd)/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    print_status "Nginx configuration created and enabled"
fi

# Create health check script
print_status "Creating health check script..."
cat > health_check.sh << 'EOF'
#!/bin/bash
# Health check script for the SaaS platform

BASE_URL="http://localhost:8000"

# Check if the server is running
if curl -f -s "$BASE_URL/health/" > /dev/null; then
    echo "✅ Server is healthy"
    exit 0
else
    echo "❌ Server is not responding"
    exit 1
fi
EOF

chmod +x health_check.sh

# Create backup script
print_status "Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash
# Backup script for the SaaS platform

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
python3 manage.py dumpdata --exclude auth.permission --exclude contenttypes > $BACKUP_DIR/backup_$DATE.json

# Backup media files
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz media/

echo "Backup completed: $BACKUP_DIR/backup_$DATE.json and $BACKUP_DIR/media_backup_$DATE.tar.gz"
EOF

chmod +x backup.sh

# Final status
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "1. Update the .env file with your actual credentials"
echo -e "2. Start the server: python3 manage.py runserver 0.0.0.0:8000"
echo -e "3. Access the admin panel: http://localhost:8000/admin/"
echo -e "4. API documentation: http://localhost:8000/api/docs/"
echo -e "5. Health check: http://localhost:8000/health/"
echo -e ""
echo -e "${YELLOW}🔐 Admin credentials:${NC}"
echo -e "Email: $ADMIN_EMAIL"
echo -e "Password: $ADMIN_PASSWORD"
echo -e ""
echo -e "${BLUE}📚 Useful commands:${NC}"
echo -e "- Run tests: python3 manage.py test"
echo -e "- Create backup: ./backup.sh"
echo -e "- Health check: ./health_check.sh"
echo -e "- View logs: tail -f logs/django.log"

print_status "Deployment script completed!" 