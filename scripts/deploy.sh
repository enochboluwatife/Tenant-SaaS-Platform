#!/bin/bash

# Production Deployment Script for Multi-Tenant SaaS Platform
# This script handles the complete deployment process

set -e  # Exit on any error

echo "🚀 Starting Production Deployment..."

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
PYTHON_PATH="python3"
MANAGE_PY="$PROJECT_DIR/manage.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "$MANAGE_PY" ]; then
    print_error "manage.py not found. Please run this script from the project root."
    exit 1
fi

print_status "Project directory: $PROJECT_DIR"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not detected. Please activate your virtual environment first."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
        print_status "Created .env file from .env.example"
        print_warning "Please edit .env file with your production settings before continuing."
        read -p "Continue after editing .env? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_error ".env.example not found. Please create a .env file manually."
        exit 1
    fi
fi

# Install/upgrade dependencies
print_status "Installing/upgrading dependencies..."
$PYTHON_PATH -m pip install --upgrade pip
$PYTHON_PATH -m pip install -r "$PROJECT_DIR/requirements.txt"

# Run database migrations
print_status "Running database migrations..."
$PYTHON_PATH "$MANAGE_PY" migrate --noinput

# Collect static files
print_status "Collecting static files..."
$PYTHON_PATH "$MANAGE_PY" collectstatic --noinput

# Create superuser if it doesn't exist
print_status "Checking for superuser..."
$PYTHON_PATH "$MANAGE_PY" shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found. Creating one...')
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass123')
    print('Superuser created: admin/adminpass123')
else:
    print('Superuser already exists')
"

# Run tests
print_status "Running tests..."
$PYTHON_PATH "$MANAGE_PY" test --verbosity=2

# Test endpoints
print_status "Testing endpoints..."
if [ -f "$PROJECT_DIR/scripts/test_endpoints.py" ]; then
    $PYTHON_PATH "$PROJECT_DIR/scripts/test_endpoints.py" --base-url "http://localhost:8000"
else
    print_warning "Endpoint test script not found. Skipping endpoint tests."
fi

# Check if we should start the server
print_status "Deployment completed successfully!"
echo
echo "Next steps:"
echo "1. Configure your production server (Gunicorn, uWSGI, etc.)"
echo "2. Set up your web server (Nginx, Apache)"
echo "3. Configure SSL certificates"
echo "4. Set up monitoring and logging"
echo
echo "For development testing, you can start the server with:"
echo "python manage.py runserver 0.0.0.0:8000"
echo
read -p "Start development server now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting development server..."
    $PYTHON_PATH "$MANAGE_PY" runserver 0.0.0.0:8000
fi 