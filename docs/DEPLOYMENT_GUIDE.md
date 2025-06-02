# CineSense Deployment Guide

> **Complete guide for deploying CineSense movie recommendation system to production**

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Method 1: Vercel + Render (Recommended)](#method-1-vercel--render-recommended)
- [Method 2: Docker Deployment](#method-2-docker-deployment)
- [Method 3: Manual VPS Deployment](#method-3-manual-vps-deployment)
- [Method 4: AWS Deployment](#method-4-aws-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [SSL and Domain Setup](#ssl-and-domain-setup)
- [Monitoring and Logging](#monitoring-and-logging)
- [Performance Optimization](#performance-optimization)
- [Maintenance and Updates](#maintenance-and-updates)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

CineSense consists of two main components:
- **Frontend**: React application (Static Site)
- **Backend**: FastAPI application with ML models (Server Application)

This guide covers multiple deployment strategies from simple cloud platforms to advanced containerized deployments.

## ✅ Prerequisites

### Required Accounts
- [ ] GitHub account (for code repository)
- [ ] Domain name (optional but recommended)
- [ ] Cloud provider account (Vercel, Render, AWS, etc.)

### Required Tools
```bash
# Node.js 18+ and npm
node --version  # Should be 18+
npm --version

# Python 3.11+ and pip
python --version  # Should be 3.11+
pip --version

# Git
git --version

# Docker (optional)
docker --version
docker-compose --version
```

### API Keys (Optional)
- [ ] Gemini API Key (for AI enhancement)
- [ ] Claude API Key (for AI enhancement)
- [ ] TMDB API Key (for movie posters)

## 🚀 Deployment Options

| Method | Difficulty | Cost | Best For |
|--------|------------|------|----------|
| **Vercel + Render** | 🟢 Easy | $0-20/month | Quick deployment, demos |
| **Docker** | 🟡 Medium | $5-50/month | Scalable, consistent |
| **Manual VPS** | 🟡 Medium | $5-30/month | Full control, custom setup |
| **AWS** | 🔴 Hard | $10-100/month | Enterprise, high traffic |

---

## Method 1: Vercel + Render (Recommended)

**Best for**: Quick deployment, demos, small to medium traffic

### Step 1: Prepare Your Repository

```bash
# 1. Clone your repository
git clone https://github.com/yourusername/cinesense.git
cd cinesense

# 2. Ensure your project structure matches:
cinesense/
├── frontend/          # React app
├── backend/           # FastAPI app
├── docs/
└── README.md
```

### Step 2: Deploy Backend to Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure service:

```yaml
# render.yaml (place in root directory)
services:
  - type: web
    name: cinesense-backend
    env: python
    region: oregon
    buildCommand: |
      cd backend
      pip install -r requirements.txt
    startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: GEMINI_API_KEY
        sync: false
      - key: CLAUDE_API_KEY
        sync: false
      - key: DATABASE_URL
        value: sqlite:///./data/cinesense.db
      - key: CORS_ORIGINS
        value: https://your-frontend-domain.vercel.app,http://localhost:3000
```

3. **Set Environment Variables**
   ```bash
   # In Render dashboard, go to Environment tab
   GEMINI_API_KEY=your_gemini_api_key_here
   CLAUDE_API_KEY=your_claude_api_key_here
   DATABASE_URL=sqlite:///./data/cinesense.db
   LOG_LEVEL=INFO
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Note your backend URL: `https://cinesense-backend.onrender.com`

### Step 3: Deploy Frontend to Vercel

1. **Create Vercel Account**
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub

2. **Deploy Project**
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Navigate to frontend directory
   cd frontend
   
   # Deploy
   vercel --prod
   ```

3. **Configure Environment Variables**
   ```bash
   # In Vercel dashboard or via CLI
   vercel env add REACT_APP_API_URL
   # Enter: https://cinesense-backend.onrender.com
   
   vercel env add REACT_APP_APP_NAME
   # Enter: CineSense
   ```

4. **Update vercel.json**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "package.json",
         "use": "@vercel/static-build",
         "config": {
           "distDir": "build"
         }
       }
     ],
     "routes": [
       {
         "src": "/static/(.*)",
         "dest": "/static/$1"
       },
       {
         "src": "/(.*)",
         "dest": "/index.html"
       }
     ],
     "env": {
       "REACT_APP_API_URL": "https://cinesense-backend.onrender.com"
     }
   }
   ```

### Step 4: Configure CORS

Update your backend CORS settings:

```python
# backend/app/main.py
ALLOWED_ORIGINS = [
    "https://your-frontend-domain.vercel.app",
    "http://localhost:3000",  # for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 5: Test Deployment

```bash
# Test backend
curl https://cinesense-backend.onrender.com/api/health

# Test frontend
curl https://your-frontend-domain.vercel.app
```

---

## Method 2: Docker Deployment

**Best for**: Consistent deployments, scalability, local development

### Step 1: Create Docker Configuration

#### Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data models logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### Frontend Nginx Configuration
```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### Step 2: Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/cinesense.db
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=http://localhost:3000,http://localhost
    volumes:
      - ./backend/data:/app/data
      - ./backend/models:/app/models
      - ./backend/logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  # Optional: Reverse proxy with SSL
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  backend_data:
  backend_models:
  backend_logs:
```

### Step 3: Environment Configuration

```bash
# .env (create in root directory)
GEMINI_API_KEY=your_gemini_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
DATABASE_URL=sqlite:///./data/cinesense.db
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Step 4: Deploy with Docker

```bash
# Development deployment
docker-compose up -d

# Production deployment with resource limits
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backend=2
```

### Step 5: Production Docker Compose Override

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1GB
          cpus: '0.5'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    deploy:
      resources:
        limits:
          memory: 512MB
          cpus: '0.25'
```

---

## Method 3: Manual VPS Deployment

**Best for**: Full control, cost optimization, learning

### Step 1: Server Setup

```bash
# Connect to your VPS
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install required software
apt install -y python3 python3-pip nodejs npm nginx certbot python3-certbot-nginx git curl

# Install PM2 for process management
npm install -g pm2

# Create application user
useradd -m -s /bin/bash cinesense
usermod -aG sudo cinesense
```

### Step 2: Deploy Backend

```bash
# Switch to application user
su - cinesense

# Clone repository
git clone https://github.com/yourusername/cinesense.git
cd cinesense/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data models logs

# Set up environment variables
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
DATABASE_URL=sqlite:///./data/cinesense.db
LOG_LEVEL=INFO
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com,http://localhost:3000
EOF

# Test application
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Press Ctrl+C to stop

# Create PM2 configuration
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'cinesense-backend',
    cwd: '/home/cinesense/cinesense/backend',
    script: 'venv/bin/uvicorn',
    args: 'app.main:app --host 0.0.0.0 --port 8000',
    instances: 2,
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Step 3: Deploy Frontend

```bash
# Navigate to frontend directory
cd /home/cinesense/cinesense/frontend

# Install dependencies
npm install

# Create production environment file
cat > .env.production << EOF
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_APP_NAME=CineSense
GENERATE_SOURCEMAP=false
EOF

# Build application
npm run build

# Move build to web directory
sudo mkdir -p /var/www/cinesense
sudo cp -r build/* /var/www/cinesense/
sudo chown -R www-data:www-data /var/www/cinesense
```

### Step 4: Configure Nginx

```bash
# Create Nginx configuration
sudo cat > /etc/nginx/sites-available/cinesense << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Frontend
    location / {
        root /var/www/cinesense;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/cinesense /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 5: SSL Certificate

```bash
# Install SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run

# Set up auto-renewal cron job
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

---

## Method 4: AWS Deployment

**Best for**: Enterprise deployments, high traffic, scalability

### Step 1: AWS Infrastructure Setup

#### Using AWS CDK (TypeScript)

```typescript
// infrastructure/lib/cinesense-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';

export class CineSenseStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // VPC
    const vpc = new ec2.Vpc(this, 'CineSenseVPC', {
      maxAzs: 2,
      natGateways: 1,
    });

    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'CineSenseCluster', {
      vpc,
      containerInsights: true,
    });

    // S3 Bucket for frontend
    const frontendBucket = new s3.Bucket(this, 'CineSenseFrontend', {
      bucketName: 'cinesense-frontend',
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'index.html',
      publicReadAccess: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS,
    });

    // CloudFront Distribution
    const distribution = new cloudfront.CloudFrontWebDistribution(this, 'CineSenseDistribution', {
      originConfigs: [{
        s3OriginSource: {
          s3BucketSource: frontendBucket,
        },
        behaviors: [{
          isDefaultBehavior: true,
          compress: true,
          allowedMethods: cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
        }],
      }],
      errorConfigurations: [{
        errorCode: 404,
        responseCode: 200,
        responsePagePath: '/index.html',
      }],
    });

    // Application Load Balancer
    const alb = new elbv2.ApplicationLoadBalancer(this, 'CineSenseALB', {
      vpc,
      internetFacing: true,
    });

    // ECS Service for backend
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'CineSenseBackendTask', {
      memoryLimitMiB: 2048,
      cpu: 1024,
    });

    const container = taskDefinition.addContainer('backend', {
      image: ecs.ContainerImage.fromRegistry('your-docker-registry/cinesense-backend:latest'),
      environment: {
        DATABASE_URL: 'postgresql://user:pass@rds-endpoint:5432/cinesense',
        LOG_LEVEL: 'INFO',
      },
      secrets: {
        GEMINI_API_KEY: ecs.Secret.fromSecretsManager(/* your secret */),
        CLAUDE_API_KEY: ecs.Secret.fromSecretsManager(/* your secret */),
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'cinesense-backend',
      }),
    });

    container.addPortMappings({
      containerPort: 8000,
      protocol: ecs.Protocol.TCP,
    });

    const service = new ecs.FargateService(this, 'CineSenseBackendService', {
      cluster,
      taskDefinition,
      desiredCount: 2,
      assignPublicIp: false,
    });

    // Target Group
    const targetGroup = new elbv2.ApplicationTargetGroup(this, 'CineSenseTargetGroup', {
      vpc,
      port: 8000,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [service],
      healthCheck: {
        path: '/api/health',
        healthyHttpCodes: '200',
      },
    });

    // ALB Listener
    alb.addListener('CineSenseListener', {
      port: 443,
      protocol: elbv2.ApplicationProtocol.HTTPS,
      certificates: [/* your certificate */],
      defaultTargetGroups: [targetGroup],
    });
  }
}
```

### Step 2: Deploy Infrastructure

```bash
# Install AWS CDK
npm install -g aws-cdk

# Initialize CDK project
mkdir cinesense-infrastructure
cd cinesense-infrastructure
cdk init app --language typescript

# Install dependencies
npm install

# Deploy infrastructure
cdk bootstrap
cdk deploy

# Build and push Docker images
docker build -t your-registry/cinesense-backend ./backend
docker push your-registry/cinesense-backend

# Deploy frontend to S3
aws s3 sync ./frontend/build s3://cinesense-frontend
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

---

## Environment Configuration

### Backend Environment Variables

```bash
# Required
DATABASE_URL=sqlite:///./data/cinesense.db
LOG_LEVEL=INFO
ENVIRONMENT=production

# Optional AI Enhancement
GEMINI_API_KEY=your_gemini_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here

# Security
SECRET_KEY=your-secret-key-here-make-it-long-and-random
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=https://yourdomain.com,http://localhost:3000

# Performance
CACHE_TTL_HOURS=24
MAX_CACHE_SIZE=1000
RATE_LIMIT_PER_MINUTE=60

# Features
AI_ENHANCEMENT_ENABLED=true
ENABLE_ANALYTICS=false
```

### Frontend Environment Variables

```bash
# API Configuration
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_APP_NAME=CineSense
REACT_APP_VERSION=1.0.0

# Features
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_AI_ENHANCEMENT=true

# Development
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
```

---

## Database Setup

### SQLite (Development/Small Scale)

```bash
# Already configured - no additional setup needed
# Data will be stored in backend/data/cinesense.db
```

### PostgreSQL (Production)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE cinesense;
CREATE USER cinesense_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE cinesense TO cinesense_user;
\q

# Update environment variable
DATABASE_URL=postgresql://cinesense_user:secure_password_here@localhost:5432/cinesense
```

### Database Migration

```python
# backend/app/database_setup.py
import asyncio
import json
from pathlib import Path
from app.data.movie_dataset import MovieDatabase

async def initialize_database():
    """Initialize database with movie data"""
    db = MovieDatabase()
    await db.initialize()
    
    print(f"Database initialized with {len(db.movies)} movies")

if __name__ == "__main__":
    asyncio.run(initialize_database())
```

```bash
# Run database initialization
cd backend
python app/database_setup.py
```

---

## SSL and Domain Setup

### Custom Domain Configuration

```bash
# 1. Point your domain to your server/load balancer
# Create A records:
# yourdomain.com -> your.server.ip.address
# www.yourdomain.com -> your.server.ip.address

# 2. Update Nginx configuration with your domain
sudo nano /etc/nginx/sites-available/cinesense
# Replace 'yourdomain.com' with your actual domain

# 3. Install SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 4. Update CORS origins in backend
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 5. Update frontend API URL
REACT_APP_API_URL=https://yourdomain.com/api
```

### SSL Best Practices

```nginx
# Add to Nginx configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_session_timeout 1d;
ssl_session_cache shared:MozTLS:10m;
ssl_session_tickets off;

# HSTS
add_header Strict-Transport-Security "max-age=63072000" always;
```

---

## Monitoring and Logging

### Application Monitoring

```python
# backend/app/monitoring.py
import logging
import time
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Log request details
        logging.info(
            f"{request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.3f}s"
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

# Add to main.py
app.add_middleware(MonitoringMiddleware)
```

### Log Configuration

```python
# backend/app/logging_config.py
import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging():
    """Configure application logging"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(),
            
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                logs_dir / "cinesense.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

# Call in main.py
setup_logging()
```

### Health Check Endpoint

```python
# Enhanced health check
@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime": get_uptime(),
        "database": {
            "status": "connected",
            "size": len(movie_db.movies)
        },
        "ml_model": {
            "status": "ready" if recommendation_engine.is_trained() else "not_ready",
            "last_trained": get_last_training_time()
        },
        "memory_usage": get_memory_usage(),
        "disk_usage": get_disk_usage(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }
    
    return health_data
```

### External Monitoring

```bash
# Set up monitoring with external services

# 1. Uptime monitoring (UptimeRobot, Pingdom)
# Monitor: https://yourdomain.com/api/health

# 2. Log aggregation (LogDNA, Papertrail)
# Configure log shipping

# 3. Error tracking (Sentry)
pip install sentry-sdk[fastapi]
```

```python
# Add Sentry integration
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "development")
)
```

---

## Performance Optimization

### Backend Optimization

```python
# backend/app/performance.py

# 1. Response compression
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 2. Response caching
from functools import lru_cache
import asyncio

@lru_cache(maxsize=128)
def get_cached_recommendations(preferences_hash: str):
    # Cached recommendation logic
    pass

# 3. Database connection pooling
import asyncpg
import asyncio

class DatabasePool:
    def __init__(self):
        self.pool = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=2,
            max_size=10
        )

# 4. Async processing
async def process_recommendations_async(preferences):
    tasks = [
        asyncio.create_task(content_based_recommendations(preferences)),
        asyncio.create_task(collaborative_recommendations(preferences)),
        asyncio.create_task(trending_movies()),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return combine_results(results)
```

### Frontend Optimization

```bash
# 1. Build optimization
cd frontend

# Install production dependencies only
npm ci --only=production

# Optimize build
npm run build

# Analyze bundle size
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js
```

```javascript
// 2. Code splitting and lazy loading
import React, { lazy, Suspense } from 'react';

const Recommendations = lazy(() => import('./components/Recommendations'));
const MovieCard = lazy(() => import('./components/MovieCard'));

function App() {
  return (
    <div className="App">
      <Suspense fallback={<div>Loading...</div>}>
        <Recommendations />
      </Suspense>
    </div>
  );
}

// 3. Service Worker for caching
// public/sw.js
const CACHE_NAME = 'cinesense-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});
```

### Database Optimization

```python
# backend/app/database_optimization.py

# 1. Query optimization
class OptimizedMovieDatabase:
    def __init__(self):
        self.movies_index = {}
        self.genre_index = {}
        self.year_index = {}
    
    def build_indexes(self):
        """Build indexes for faster queries"""
        for i, movie in enumerate(self.movies):
            # Title index
            self.movies_index[movie['title'].lower()] = i
            
            # Genre index
            for genre in movie['genre'].split(', '):
                if genre not in self.genre_index:
                    self.genre_index[genre] = []
                self.genre_index[genre].append(i)
            
            # Year index
            year = movie['year']
            if year not in self.year_index:
                self.year_index[year] = []
            self.year_index[year].append(i)
    
    def fast_genre_search(self, genre: str):
        """Fast genre-based search using index"""
        return self.genre_index.get(genre, [])

# 2. Connection pooling for PostgreSQL
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### CDN and Static Asset Optimization

```nginx
# Nginx optimization
server {
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json
        image/svg+xml;

    # Browser caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
    }

    # API caching
    location /api/movies {
        proxy_pass http://backend;
        proxy_cache api_cache;
        proxy_cache_valid 200 10m;
        proxy_cache_key "$request_uri";
        add_header X-Cache-Status $upstream_cache_status;
    }
}

# Set up proxy cache
http {
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
}
```

---

## Maintenance and Updates

### Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/cinesense"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
if [ "$DATABASE_TYPE" = "sqlite" ]; then
    cp backend/data/cinesense.db $BACKUP_DIR/database_$DATE.db
elif [ "$DATABASE_TYPE" = "postgresql" ]; then
    pg_dump $DATABASE_URL > $BACKUP_DIR/database_$DATE.sql
fi

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    .

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz backend/logs/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Set up daily backups
chmod +x scripts/backup.sh
echo "0 2 * * * /path/to/cinesense/scripts/backup.sh" | crontab -
```

### Zero-Downtime Deployment

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "Starting deployment..."

# 1. Pull latest code
git pull origin main

# 2. Backend deployment
echo "Deploying backend..."
cd backend

# Create new virtual environment
python3 -m venv venv_new
source venv_new/bin/activate
pip install -r requirements.txt

# Test new backend
uvicorn app.main:app --host 127.0.0.1 --port 8001 &
BACKEND_PID=$!

# Health check
sleep 10
if curl -f http://127.0.0.1:8001/api/health; then
    echo "New backend is healthy"
    
    # Stop old backend
    pm2 stop cinesense-backend
    
    # Switch virtual environments
    rm -rf venv_old
    mv venv venv_old
    mv venv_new venv
    
    # Start new backend
    pm2 start cinesense-backend
    
    # Clean up test instance
    kill $BACKEND_PID
    
    echo "Backend deployment completed"
else
    echo "New backend failed health check"
    kill $BACKEND_PID
    rm -rf venv_new
    exit 1
fi

# 3. Frontend deployment
echo "Deploying frontend..."
cd ../frontend

# Build new version
npm ci
npm run build

# Test build
if [ -f "build/index.html" ]; then
    # Backup current version
    sudo mv /var/www/cinesense /var/www/cinesense_backup
    
    # Deploy new version
    sudo mkdir -p /var/www/cinesense
    sudo cp -r build/* /var/www/cinesense/
    sudo chown -R www-data:www-data /var/www/cinesense
    
    # Test new frontend
    if curl -f http://localhost; then
        echo "Frontend deployment completed"
        sudo rm -rf /var/www/cinesense_backup
    else
        echo "Frontend deployment failed, rolling back"
        sudo rm -rf /var/www/cinesense
        sudo mv /var/www/cinesense_backup /var/www/cinesense
        exit 1
    fi
else
    echo "Frontend build failed"
    exit 1
fi

echo "Deployment completed successfully!"
```

### Health Monitoring Script

```bash
#!/bin/bash
# scripts/health_monitor.sh

BACKEND_URL="https://yourdomain.com/api/health"
FRONTEND_URL="https://yourdomain.com"
SLACK_WEBHOOK="your-slack-webhook-url"

send_alert() {
    local message=$1
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 CineSense Alert: $message\"}" \
        $SLACK_WEBHOOK
}

check_backend() {
    if ! curl -f --max-time 10 $BACKEND_URL > /dev/null 2>&1; then
        send_alert "Backend is down!"
        return 1
    fi
    return 0
}

check_frontend() {
    if ! curl -f --max-time 10 $FRONTEND_URL > /dev/null 2>&1; then
        send_alert "Frontend is down!"
        return 1
    fi
    return 0
}

check_disk_space() {
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 85 ]; then
        send_alert "Disk usage is at ${DISK_USAGE}%"
    fi
}

check_memory() {
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $MEMORY_USAGE -gt 90 ]; then
        send_alert "Memory usage is at ${MEMORY_USAGE}%"
    fi
}

# Run all checks
check_backend
check_frontend
check_disk_space
check_memory

echo "Health check completed at $(date)"
```

```bash
# Run health checks every 5 minutes
echo "*/5 * * * * /path/to/cinesense/scripts/health_monitor.sh" | crontab -
```

### Update Script

```bash
#!/bin/bash
# scripts/update.sh

echo "Updating CineSense..."

# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Update Python dependencies
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade

# 3. Update Node.js dependencies
cd ../frontend
npm update

# 4. Update ML models if needed
cd ../backend
python -c "
from app.models.ml_model import MovieRecommendationEngine
from app.data.movie_dataset import MovieDatabase

# Retrain model with latest data
db = MovieDatabase()
db.initialize()
engine = MovieRecommendationEngine()
engine.train(db.get_training_data())
engine.save_model('models/')
print('Model updated successfully')
"

# 5. Restart services
pm2 restart cinesense-backend
sudo systemctl reload nginx

echo "Update completed!"
```

---

## Troubleshooting

### Common Issues and Solutions

#### Backend Issues

**1. Module Import Errors**
```bash
# Problem: ImportError: No module named 'app'
# Solution: Check Python path and virtual environment
cd backend
source venv/bin/activate
python -c "import sys; print(sys.path)"
pip install -r requirements.txt
```

**2. Database Connection Issues**
```bash
# Problem: Database file not found
# Solution: Check database path and permissions
ls -la backend/data/
mkdir -p backend/data
python backend/app/database_setup.py
```

**3. CORS Errors**
```python
# Problem: CORS errors in browser console
# Solution: Update CORS origins in backend
CORS_ORIGINS=https://yourdomain.com,http://localhost:3000

# In main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**4. High Memory Usage**
```bash
# Problem: Backend using too much memory
# Solution: Optimize caching and limit model size
# In backend config
MAX_CACHE_SIZE=500  # Reduce cache size
TFIDF_MAX_FEATURES=1000  # Reduce feature count

# Monitor memory usage
htop
free -h
```

#### Frontend Issues

**1. Build Failures**
```bash
# Problem: npm run build fails
# Solution: Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
npm run build
```

**2. API Connection Issues**
```bash
# Problem: Frontend can't connect to API
# Solution: Check API URL and network
# In .env.production
REACT_APP_API_URL=https://yourdomain.com/api

# Test API connectivity
curl https://yourdomain.com/api/health
```

**3. Routing Issues**
```nginx
# Problem: React Router not working on refresh
# Solution: Update Nginx configuration
location / {
    try_files $uri $uri/ /index.html;
}
```

#### Deployment Issues

**1. SSL Certificate Problems**
```bash
# Problem: SSL certificate expired or invalid
# Solution: Renew certificate
sudo certbot renew
sudo nginx -t
sudo systemctl reload nginx

# Check certificate status
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

**2. PM2 Process Issues**
```bash
# Problem: PM2 processes not starting
# Solution: Check logs and restart
pm2 logs cinesense-backend
pm2 restart cinesense-backend
pm2 save
pm2 resurrect
```

**3. Nginx Configuration Issues**
```bash
# Problem: Nginx configuration errors
# Solution: Test and fix configuration
sudo nginx -t
sudo nginx -s reload

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

#### Performance Issues

**1. Slow API Responses**
```python
# Problem: Recommendations taking too long
# Solution: Optimize ML model and caching

# Enable response caching
@lru_cache(maxsize=128)
def get_recommendations_cached(preferences_hash):
    return engine.recommend(preferences)

# Reduce model complexity
config = {
    'tfidf_max_features': 1000,  # Reduce from 5000
    'n_neighbors': 20,           # Reduce from 50
}
```

**2. High Server Load**
```bash
# Problem: Server overloaded
# Solution: Scale resources or optimize

# Monitor server resources
htop
iotop
nethogs

# Scale PM2 processes
pm2 scale cinesense-backend 4

# Add server-level caching
sudo apt install redis-server
```

#### Monitoring and Debugging

**1. Enable Debug Logging**
```bash
# Temporary debug mode
export LOG_LEVEL=DEBUG
pm2 restart cinesense-backend

# Check logs
pm2 logs cinesense-backend --lines 100
tail -f backend/logs/cinesense.log
```

**2. Health Check Script**
```bash
#!/bin/bash
# scripts/debug_health.sh

echo "=== CineSense Health Debug ==="
echo "Date: $(date)"
echo ""

echo "=== Backend Status ==="
curl -v https://yourdomain.com/api/health
echo ""

echo "=== Frontend Status ==="
curl -I https://yourdomain.com
echo ""

echo "=== PM2 Status ==="
pm2 status
echo ""

echo "=== Nginx Status ==="
sudo systemctl status nginx
echo ""

echo "=== Disk Usage ==="
df -h
echo ""

echo "=== Memory Usage ==="
free -h
echo ""

echo "=== Recent Logs ==="
pm2 logs cinesense-backend --lines 20 --nostream
```

**3. Performance Profiling**
```python
# backend/app/profiling.py
import cProfile
import pstats
from fastapi import Request
import time

async def profile_endpoint(request: Request, call_next):
    """Profile API endpoints"""
    if request.url.path.startswith('/api/recommendations'):
        profiler = cProfile.Profile()
        profiler.enable()
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        profiler.disable()
        
        # Save profile stats
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        # Add performance headers
        response.headers['X-Response-Time'] = str(duration)
        
        return response
    else:
        return await call_next(request)

# Add to main.py for debugging
app.middleware('http')(profile_endpoint)
```

### Emergency Recovery

**1. Complete Service Restart**
```bash
#!/bin/bash
# scripts/emergency_restart.sh

echo "Emergency restart initiated..."

# Stop all services
pm2 stop all
sudo systemctl stop nginx

# Check for zombie processes
sudo pkill -f uvicorn
sudo pkill -f python

# Clear temporary files
sudo rm -rf /tmp/cinesense_*

# Restart services
sudo systemctl start nginx
pm2 resurrect

# Wait and check health
sleep 30
curl -f https://yourdomain.com/api/health

echo "Emergency restart completed"
```

**2. Rollback to Previous Version**
```bash
#!/bin/bash
# scripts/rollback.sh

echo "Rolling back to previous version..."

# Rollback code
git reset --hard HEAD~1

# Rollback frontend
sudo rm -rf /var/www/cinesense
sudo mv /var/www/cinesense_backup /var/www/cinesense

# Rollback backend
cd backend
mv venv venv_broken
mv venv_old venv
pm2 restart cinesense-backend

echo "Rollback completed"
```

---

## 📞 Support and Resources

### Getting Help

- **Documentation**: [docs.cinesense.ai](https://docs.cinesense.ai)
- **GitHub Issues**: [github.com/cinesense/issues](https://github.com/cinesense/issues)
- **Community Discord**: [discord.gg/cinesense](https://discord.gg/cinesense)
- **Email Support**: support@cinesense.ai

### Useful Commands

```bash
# Quick status check
curl -s https://yourdomain.com/api/health | jq '.'

# View recent logs
pm2 logs cinesense-backend --lines 50

# Monitor in real-time
watch -n 5 'curl -s https://yourdomain.com/api/health | jq ".data.memory_usage"'

# Performance test
ab -n 100 -c 10 https://yourdomain.com/api/health

# SSL check
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -text
```

### Configuration Files Quick Reference

```bash
# Important file locations
/etc/nginx/sites-available/cinesense       # Nginx config
/home/cinesense/cinesense/backend/.env      # Backend environment
/var/www/cinesense/                         # Frontend files
/home/cinesense/cinesense/backend/logs/     # Application logs
/var/log/nginx/                             # Nginx logs
```

---

**Last Updated**: January 15, 2024  
**Guide Version**: 1.0.0

This deployment guide provides comprehensive instructions for deploying CineSense to production. Choose the deployment method that best fits your needs and follow the step-by-step instructions for a successful deployment.