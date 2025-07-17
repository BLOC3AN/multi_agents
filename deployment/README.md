# Multi-Agent System API Deployment

Complete Docker-based deployment solution for the Multi-Agent System with parallel execution capabilities.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Python 3.11+ (for health checks)
- API keys (Google Gemini or OpenAI)

### Development Deployment
```bash
# Clone and navigate to project
cd multi_agents

# Set up environment (optional for dev)
cp deployment/.env.production deployment/.env
# Edit deployment/.env with your API keys

# Deploy in development mode
./deployment/scripts/deploy.sh dev --build

# View logs
./deployment/scripts/deploy.sh dev --logs
```

### Production Deployment
```bash
# Set up production environment
cp deployment/.env.production deployment/.env
# Edit deployment/.env with your actual API keys and configuration

# Deploy in production mode
./deployment/scripts/deploy.sh prod --build

# Check status
docker-compose -f deployment/docker-compose.yml ps
```

## 📋 API Endpoints

### Core Endpoints
- **POST /process** - Process user input through multi-agent system
- **GET /health** - Health check endpoint
- **GET /agents** - List available agents and intents
- **GET /config** - Get system configuration
- **GET /docs** - Interactive API documentation (Swagger UI)
- **GET /redoc** - Alternative API documentation

### Example API Usage

#### Single Intent Processing
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Solve 2x + 3 = 7",
    "use_parallel": false
  }'
```

#### Multi-Intent Parallel Processing
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain machine learning and solve 2x + 5 = 11",
    "use_parallel": true,
    "confidence_threshold": 0.3
  }'
```

#### Health Check
```bash
curl http://localhost:8000/health
```

## 🏗️ Architecture

### Services Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │  Multi-Agent    │    │     Redis       │
│   (Port 80)     │───▶│     API         │───▶│   (Caching)     │
│                 │    │   (Port 8000)   │    │   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Grafana      │    │   Prometheus    │    │  Health Check   │
│   (Port 3000)   │    │   (Port 9090)   │    │    Scripts      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Container Details

#### multi-agent-api
- **Image**: Custom built from Dockerfile
- **Port**: 8000
- **Purpose**: Main FastAPI application
- **Health Check**: `/health` endpoint
- **Environment**: Configurable via .env file

#### redis
- **Image**: redis:7-alpine
- **Port**: 6379
- **Purpose**: Caching and session management
- **Persistence**: Volume mounted for data persistence

#### nginx (Production)
- **Image**: nginx:alpine
- **Port**: 80, 443
- **Purpose**: Reverse proxy, load balancing, SSL termination
- **Configuration**: Custom nginx.conf with rate limiting

#### prometheus (Optional)
- **Image**: prom/prometheus:latest
- **Port**: 9090
- **Purpose**: Metrics collection and monitoring

#### grafana (Optional)
- **Image**: grafana/grafana:latest
- **Port**: 3000
- **Purpose**: Metrics visualization and dashboards

## ⚙️ Configuration

### Environment Variables
```bash
# LLM Configuration
LLM_PROVIDER=gemini                    # "gemini" or "openai"
LLM_MODEL=gemini-2.0-flash            # Model name
LLM_TEMPERATURE=0.2                   # Temperature (0.0-1.0)
LLM_TOP_P=0.2                         # Top-p sampling
LLM_TOP_K=40                          # Top-k sampling

# API Keys (REQUIRED)
GOOGLE_API_KEY=your_google_api_key    # For Gemini
OPENAI_API_KEY=your_openai_api_key    # For OpenAI

# Application Settings
DEBUG=false                           # Debug mode

# Security (Production)
GRAFANA_PASSWORD=secure_password      # Grafana admin password
```

### Docker Compose Profiles

#### Development (`docker-compose.dev.yml`)
- Hot reload enabled
- Debug mode on
- Minimal services (API + Redis)
- Source code mounted as volume

#### Production (`docker-compose.yml`)
- Optimized for performance
- Full monitoring stack
- Nginx reverse proxy
- Health checks enabled
- Resource limits configured

## 🔧 Management Commands

### Deployment Script
```bash
# Development deployment
./deployment/scripts/deploy.sh dev --build

# Production deployment  
./deployment/scripts/deploy.sh prod --build

# Show logs
./deployment/scripts/deploy.sh --logs

# Help
./deployment/scripts/deploy.sh --help
```

### Manual Docker Commands
```bash
# Start services
docker-compose -f deployment/docker-compose.yml up -d

# Stop services
docker-compose -f deployment/docker-compose.yml down

# View logs
docker-compose -f deployment/docker-compose.yml logs -f

# Rebuild and restart
docker-compose -f deployment/docker-compose.yml up -d --build

# Scale API instances
docker-compose -f deployment/docker-compose.yml up -d --scale multi-agent-api=3
```

### Health Check Script
```bash
# Basic health check
python3 deployment/scripts/health_check.py

# Full functionality test
python3 deployment/scripts/health_check.py --functional --verbose

# JSON output for monitoring
python3 deployment/scripts/health_check.py --json

# Custom URL
python3 deployment/scripts/health_check.py --url http://your-domain.com
```

## 📊 Monitoring & Observability

### Health Monitoring
- **Endpoint**: `/health`
- **Docker Health Checks**: Built-in container health monitoring
- **Custom Script**: `deployment/scripts/health_check.py`

### Metrics (Production)
- **Prometheus**: Metrics collection at `:9090`
- **Grafana**: Visualization at `:3000` (admin/admin)
- **Custom Dashboards**: Pre-configured for API metrics

### Logging
- **Application Logs**: Structured JSON logging
- **Access Logs**: Nginx access and error logs
- **Container Logs**: `docker-compose logs`

## 🔒 Security Considerations

### Production Security
1. **API Keys**: Store in secure environment variables
2. **HTTPS**: Configure SSL certificates in nginx
3. **Rate Limiting**: Configured in nginx (10 req/s)
4. **CORS**: Properly configured for your domain
5. **Firewall**: Restrict access to necessary ports only

### Network Security
- **Internal Network**: Services communicate via Docker network
- **Exposed Ports**: Only necessary ports exposed to host
- **Health Checks**: Regular monitoring of service health

## 🚨 Troubleshooting

### Common Issues

#### API Not Starting
```bash
# Check logs
docker-compose logs multi-agent-api

# Common causes:
# - Missing API keys
# - Port conflicts
# - Memory issues
```

#### Health Check Failing
```bash
# Run detailed health check
python3 deployment/scripts/health_check.py --functional --verbose

# Check service status
docker-compose ps
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Scale API instances
docker-compose up -d --scale multi-agent-api=2

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Debug Mode
```bash
# Enable debug mode
echo "DEBUG=true" >> deployment/.env

# Restart with debug
docker-compose up -d --force-recreate multi-agent-api

# View detailed logs
docker-compose logs -f multi-agent-api
```

## 📈 Performance Tuning

### Scaling Options
1. **Horizontal Scaling**: Multiple API instances
2. **Resource Limits**: Configure CPU/memory limits
3. **Caching**: Redis for response caching
4. **Load Balancing**: Nginx upstream configuration

### Optimization Tips
- Use production WSGI server (uvicorn with workers)
- Configure appropriate timeout values
- Monitor and tune LLM parameters
- Implement response caching for common queries

---

**For more information, see the main project README.md**
