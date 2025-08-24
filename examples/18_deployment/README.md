# 18 部署指南

## 概述

本指南详细介绍如何将数字孪生水力系统部署到不同的生产环境中，包括本地服务器、云平台和容器化部署等多种方案。

## 学习目标

- 掌握系统部署的完整流程
- 了解不同部署环境的特点和选择
- 学会配置生产环境和监控系统
- 实现自动化部署和持续集成

## 部署方案对比

| 部署方案 | 优点 | 缺点 | 适用场景 |
|---------|------|------|----------|
| 本地服务器 | 完全控制、低延迟 | 维护成本高、扩展性差 | 小型项目、内网环境 |
| 云虚拟机 | 易扩展、按需付费 | 网络延迟、依赖云服务 | 中小型项目 |
| 容器化部署 | 环境一致、易迁移 | 学习成本、复杂性 | 现代化应用 |
| Serverless | 免维护、自动扩展 | 冷启动、功能限制 | 轻量级应用 |

## 文件结构

```
examples/18_deployment/
├── README.md                    # 本文档
├── local_deployment/            # 本地部署
│   ├── install_script.sh
│   ├── nginx.conf
│   ├── systemd_service.conf
│   └── backup_script.sh
├── docker_deployment/          # Docker部署
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── .dockerignore
├── cloud_deployment/           # 云平台部署
│   ├── aws/
│   │   ├── cloudformation.yaml
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── azure/
│   │   ├── arm_template.json
│   │   └── azure_functions.py
│   └── gcp/
│       ├── app.yaml
│       └── cloudbuild.yaml
├── kubernetes/                 # K8s部署
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── monitoring/                 # 监控配置
│   ├── prometheus.yml
│   ├── grafana_dashboard.json
│   └── alertmanager.yml
├── ci_cd/                      # CI/CD配置
│   ├── .github/
│   │   └── workflows/
│   │       ├── test.yml
│   │       └── deploy.yml
│   ├── jenkins/
│   │   └── Jenkinsfile
│   └── gitlab/
│       └── .gitlab-ci.yml
├── scripts/                    # 部署脚本
│   ├── deploy.sh
│   ├── rollback.sh
│   ├── health_check.py
│   └── migration.py
└── configs/                    # 配置文件
    ├── production.py
    ├── staging.py
    └── development.py
```

## 本地服务器部署

### 系统要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Python**: 3.8+
- **内存**: 最少4GB，推荐8GB+
- **存储**: 最少20GB可用空间
- **网络**: 稳定的网络连接

### 自动安装脚本
```bash
#!/bin/bash
# install_script.sh - 自动化安装脚本

set -e

echo "开始安装数字孪生水力系统..."

# 检查系统
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "错误: 此脚本仅支持Linux系统"
    exit 1
fi

# 更新系统包
sudo apt-get update
sudo apt-get upgrade -y

# 安装Python和pip
sudo apt-get install -y python3 python3-pip python3-venv

# 安装系统依赖
sudo apt-get install -y nginx redis-server postgresql postgresql-contrib

# 创建项目目录
PROJECT_DIR="/opt/digital_twin"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# 克隆项目代码
cd $PROJECT_DIR
git clone https://github.com/your-repo/digital-twin-system.git .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 配置数据库
sudo -u postgres createdb digital_twin
sudo -u postgres createuser digital_twin_user

# 生成配置文件
cp configs/production.example.py configs/production.py
echo "请编辑 configs/production.py 配置文件"

# 配置Nginx
sudo cp nginx.conf /etc/nginx/sites-available/digital_twin
sudo ln -sf /etc/nginx/sites-available/digital_twin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 配置系统服务
sudo cp systemd_service.conf /etc/systemd/system/digital_twin.service
sudo systemctl daemon-reload
sudo systemctl enable digital_twin
sudo systemctl start digital_twin

echo "安装完成!"
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
```

### Nginx配置
```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;

    # 静态文件
    location /static {
        alias /opt/digital_twin/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket代理
    location /socket.io {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 系统服务配置
```ini
# systemd_service.conf
[Unit]
Description=Digital Twin Hydraulic System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/digital_twin
Environment=PATH=/opt/digital_twin/venv/bin
ExecStart=/opt/digital_twin/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --worker-class eventlet app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## Docker容器化部署

### Dockerfile
```dockerfile
# 多阶段构建
FROM python:3.9-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 生产阶段
FROM python:3.9-slim

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app

# 设置工作目录
WORKDIR /app

# 从builder阶段复制安装的包
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --chown=app:app . .

# 切换到非root用户
USER app

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python health_check.py || exit 1

# 启动命令
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--worker-class", "eventlet", "app:app"]
```

### Docker Compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    container_name: digital_twin_app
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:password@db:5432/digital_twin
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - app_data:/app/data
    networks:
      - digital_twin_network

  db:
    image: postgres:13
    container_name: digital_twin_db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=digital_twin
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - digital_twin_network

  redis:
    image: redis:6-alpine
    container_name: digital_twin_redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - digital_twin_network

  nginx:
    image: nginx:alpine
    container_name: digital_twin_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - digital_twin_network

volumes:
  postgres_data:
  redis_data:
  app_data:

networks:
  digital_twin_network:
    driver: bridge
```

### 生产环境Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: your-registry/digital-twin:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    secrets:
      - db_password
      - api_key
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

secrets:
  db_password:
    external: true
  api_key:
    external: true
```

## Kubernetes部署

### 部署清单
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: digital-twin-app
  namespace: digital-twin
  labels:
    app: digital-twin
spec:
  replicas: 3
  selector:
    matchLabels:
      app: digital-twin
  template:
    metadata:
      labels:
        app: digital-twin
    spec:
      containers:
      - name: app
        image: your-registry/digital-twin:v1.0.0
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 服务配置
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: digital-twin-service
  namespace: digital-twin
spec:
  selector:
    app: digital-twin
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: ClusterIP
```

### Ingress配置
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: digital-twin-ingress
  namespace: digital-twin
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  tls:
  - hosts:
    - digitaltwin.yourdomain.com
    secretName: digital-twin-tls
  rules:
  - host: digitaltwin.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: digital-twin-service
            port:
              number: 80
```

## 云平台部署

### AWS部署 (CloudFormation)
```yaml
# cloudformation.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Digital Twin Hydraulic System on AWS'

Parameters:
  InstanceType:
    Type: String
    Default: t3.medium
    Description: EC2 instance type

Resources:
  # VPC和网络配置
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true

  # 公共子网
  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  # 互联网网关
  InternetGateway:
    Type: AWS::EC2::InternetGateway

  # EC2实例
  DigitalTwinInstance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c55b159cbfafe1d0  # Ubuntu 20.04
      InstanceType: !Ref InstanceType
      SubnetId: !Ref PublicSubnet
      SecurityGroupIds:
        - !Ref SecurityGroup
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          apt-get update
          apt-get install -y docker.io docker-compose
          systemctl start docker
          systemctl enable docker
          
          # 下载并启动应用
          git clone https://github.com/your-repo/digital-twin-system.git
          cd digital-twin-system
          docker-compose up -d

  # 安全组
  SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Digital Twin system
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 0.0.0.0/0

Outputs:
  PublicIP:
    Description: 'Public IP of the instance'
    Value: !GetAtt DigitalTwinInstance.PublicIp
```

### Azure部署 (ARM模板)
```json
{
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {
        "vmSize": {
            "type": "string",
            "defaultValue": "Standard_B2s",
            "metadata": {
                "description": "Virtual machine size"
            }
        }
    },
    "resources": [
        {
            "type": "Microsoft.ContainerInstance/containerGroups",
            "apiVersion": "2019-12-01",
            "name": "digital-twin-containers",
            "location": "[resourceGroup().location]",
            "properties": {
                "containers": [
                    {
                        "name": "digital-twin-app",
                        "properties": {
                            "image": "your-registry/digital-twin:latest",
                            "ports": [
                                {
                                    "port": 5000,
                                    "protocol": "TCP"
                                }
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": 1,
                                    "memoryInGB": 2
                                }
                            },
                            "environmentVariables": [
                                {
                                    "name": "FLASK_ENV",
                                    "value": "production"
                                }
                            ]
                        }
                    }
                ],
                "osType": "Linux",
                "ipAddress": {
                    "type": "Public",
                    "ports": [
                        {
                            "port": 5000,
                            "protocol": "TCP"
                        }
                    ]
                }
            }
        }
    ]
}
```

## CI/CD管道

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=digital_twin_hydraulic_system

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: |
        docker build -t ${{ secrets.REGISTRY_URL }}/digital-twin:${{ github.sha }} .
        docker tag ${{ secrets.REGISTRY_URL }}/digital-twin:${{ github.sha }} ${{ secrets.REGISTRY_URL }}/digital-twin:latest
    
    - name: Push to registry
      run: |
        echo ${{ secrets.REGISTRY_PASSWORD }} | docker login ${{ secrets.REGISTRY_URL }} -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
        docker push ${{ secrets.REGISTRY_URL }}/digital-twin:${{ github.sha }}
        docker push ${{ secrets.REGISTRY_URL }}/digital-twin:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@v0.1.2
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USER }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/digital_twin
          docker-compose pull
          docker-compose up -d
          docker system prune -f
```

## 监控和日志

### Prometheus配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'digital-twin'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana仪表板
```json
{
  "dashboard": {
    "title": "Digital Twin System Dashboard",
    "panels": [
      {
        "title": "System Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"digital-twin\"}",
            "legendFormat": "System Status"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(flask_http_request_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      }
    ]
  }
}
```

## 安全加固

### SSL/TLS配置
```bash
# 获取Let's Encrypt证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 防火墙配置
```bash
# UFW配置
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 应用安全
```python
# 安全配置
import os
from datetime import timedelta

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # 数据库连接加密
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace(
        'postgres://', 'postgresql://', 1) + '?sslmode=require'
```

## 备份和恢复

### 数据库备份脚本
```bash
#!/bin/bash
# backup_script.sh

BACKUP_DIR="/backup/digital_twin"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="digital_twin"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
pg_dump $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# 应用数据备份
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz /opt/digital_twin/data

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
```

### 恢复脚本
```bash
#!/bin/bash
# restore_script.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <backup_file>"
    exit 1
fi

echo "开始恢复数据库..."
psql digital_twin < $BACKUP_FILE

echo "恢复完成"
```

## 性能调优

### 应用优化
```python
# 生产环境配置
import multiprocessing

# Gunicorn配置
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "eventlet"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

### 数据库优化
```sql
-- PostgreSQL优化
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- 重启服务生效
SELECT pg_reload_conf();
```

## 故障排除

### 常见问题
1. **端口冲突**: 检查端口占用 `netstat -tulpn | grep :5000`
2. **权限问题**: 确保用户有正确的文件权限
3. **内存不足**: 监控内存使用，必要时增加swap
4. **数据库连接**: 检查数据库配置和网络连通性

### 日志分析
```bash
# 查看应用日志
sudo journalctl -u digital_twin -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 查看Docker日志
docker logs digital_twin_app -f
```

## 运维脚本

### 健康检查脚本
```python
#!/usr/bin/env python3
# health_check.py

import requests
import sys
import time

def check_health():
    try:
        response = requests.get('http://localhost:5000/health', timeout=10)
        if response.status_code == 200:
            print("✅ 应用健康检查通过")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

if __name__ == "__main__":
    if not check_health():
        sys.exit(1)
```

### 部署脚本
```bash
#!/bin/bash
# deploy.sh

set -e

echo "开始部署..."

# 备份当前版本
./backup_script.sh

# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 数据库迁移
python migrate.py

# 重启服务
sudo systemctl restart digital_twin

# 健康检查
sleep 10
python health_check.py

echo "部署完成!"
```

## 总结

本部署指南涵盖了从开发到生产的完整部署流程，包括：

1. **多种部署方案**: 本地、Docker、K8s、云平台
2. **自动化脚本**: 安装、部署、备份脚本
3. **监控运维**: 日志、监控、告警系统
4. **安全配置**: SSL、防火墙、应用安全
5. **性能优化**: 应用和数据库调优

选择适合你项目需求的部署方案，并根据实际情况调整配置参数。建议从简单的本地部署开始，逐步迁移到更复杂的容器化和云原生部署。