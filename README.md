# 数字孪生水力系统

[![Build Status](https://github.com/your-org/digital-twin-hydraulic-system/workflows/CI/badge.svg)](https://github.com/your-org/digital-twin-hydraulic-system/actions)
[![Coverage Status](https://codecov.io/gh/your-org/digital-twin-hydraulic-system/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/digital-twin-hydraulic-system)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

## 项目简介

数字孪生水力系统是一套基于数字孪生技术的智能化水力系统仿真和监控平台。通过构建物理系统的数字化镜像，实现对水力系统的实时监控、故障诊断、参数辨识和优化控制。

本系统集成了先进的数值计算算法、机器学习技术和现代化的Web界面，为水利工程的智能化管理提供完整的解决方案。

## 核心功能

### 🔧 高保真物理建模
- 基于一维圣维南方程的有限体积法(FVM)模型
- 支持GPU加速计算，提升仿真效率
- 多种边界条件处理和非恒定流仿真

### 🧠 智能故障诊断
- 基于物理模型的故障检测算法
- 机器学习驱动的异常检测（Isolation Forest, SVM, Random Forest）
- 预测性维护和故障模式识别

### 📊 在线参数辨识
- 递归最小二乘法(RLS)参数估计
- 扩展卡尔曼滤波(EKF)状态估计
- 自适应滤波和多传感器数据融合

### 🖥️ 现代化用户界面
- 响应式Web界面，支持桌面和移动端
- 实时3D可视化展示水力系统状态
- 丰富的图表和仪表板组件

### 🚀 高性能计算
- Numba JIT编译优化数值计算
- 多线程/多进程并行处理
- 内存池管理和对象复用

### 🛡️ 完善的安全机制
- JWT认证和RBAC权限管理
- API访问限流和防护
- 数据传输加密和审计日志

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户界面层 (UI Layer)                    │
│  React/Vue.js Dashboard  │  Mobile App  │  CLI Tools        │
├─────────────────────────────────────────────────────────────┤
│                    应用服务层 (Service Layer)               │
│  API Gateway  │  Business Logic  │  Data Processing        │
├─────────────────────────────────────────────────────────────┤
│                    核心算法层 (Algorithm Layer)             │
│  FVM Model  │  ID Model  │  Fault Detection  │  ML Engine    │
├─────────────────────────────────────────────────────────────┤
│                    数据存储层 (Data Layer)                  │
│  Time-series DB  │  Relational DB  │  Cache  │  File System  │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 系统要求
- Python 3.8+
- Node.js 14+ (前端开发)
- Docker (可选，用于容器化部署)
- CUDA兼容GPU (可选，用于GPU加速)

### 安装步骤

1. **克隆代码库**
```bash
git clone https://github.com/your-org/digital-twin-hydraulic-system.git
cd digital-twin-hydraulic-system
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动后端服务**
```bash
uvicorn digital_twin_hydraulic_system.api.system_api:app --host 0.0.0.0 --port 8000
```

5. **启动前端界面**
```bash
cd frontend
npm install
npm start
```

6. **访问系统**
打开浏览器访问 `http://localhost:3000`

### Docker部署

```bash
# 构建镜像
docker build -t digital-twin-system .

# 运行容器
docker run -d -p 8000:8000 -p 3000:3000 digital-twin-system

# 或使用docker-compose
docker-compose up -d
```

### Kubernetes部署

```bash
kubectl apply -f k8s-deployment.yaml
```

## 项目结构

```
digital-twin-hydraulic-system/
├── digital_twin_hydraulic_system/  # 核心Python代码
│   ├── api/                       # RESTful API接口
│   ├── models/                    # 物理模型实现
│   ├── diagnostics/               # 故障诊断模块
│   ├── performance/               # 性能优化组件
│   ├── data/                      # 数据处理模块
│   ├── visualization/             # 可视化组件
│   └── config.py                  # 系统配置
├── frontend/                      # 前端React应用
├── mobile/                        # 移动端应用
├── tests/                         # 测试代码
├── docs/                          # 文档
├── examples/                      # 示例代码
├── k8s/                           # Kubernetes配置
├── monitoring/                    # 监控配置
├── docker/                        # Docker配置
├── requirements.txt               # Python依赖
└── README.md                     # 项目说明
```

## 文档资源

- [API文档](docs/api_documentation.md) - 详细的API接口说明
- [开发者指南](docs/developer_guide.md) - 开发环境搭建和贡献指南
- [用户手册](docs/user_manual.md) - 系统使用和操作说明
- [部署指南](examples/18_deployment/README.md) - 各种环境下的部署说明

## 示例代码

查看 `examples/` 目录中的完整示例：

1. [基础概念演示](examples/01_basic_concepts/) - 系统核心概念介绍
2. [快速开始指南](examples/02_quick_start/) - 快速上手示例
3. [故障诊断演示](examples/03_fault_diagnosis/) - 故障检测和诊断示例
4. [参数辨识演示](examples/04_parameter_identification/) - 在线参数估计示例
5. [性能优化演示](examples/05_performance_optimization/) - 计算加速和优化示例

## 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/

# 运行集成测试
pytest digital_twin_hydraulic_system/tests/test_integration.py

# 生成覆盖率报告
pytest --cov=digital_twin_hydraulic_system --cov-report=html
```

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork代码库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

请阅读 [开发者指南](docs/developer_guide.md) 了解更多详情。

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [Your Name](mailto:your.email@example.com)
- 问题跟踪: [GitHub Issues](https://github.com/your-org/digital-twin-hydraulic-system/issues)
- 用户社区: [Discussions](https://github.com/your-org/digital-twin-hydraulic-system/discussions)

## 致谢

- 感谢所有贡献者
- 感谢开源社区的支持
- 感谢用户提供的宝贵反馈