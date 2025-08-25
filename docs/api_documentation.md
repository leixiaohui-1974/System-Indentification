# 数字孪生水力系统API文档

## 概述

本文档详细描述了数字孪生水力系统的RESTful API接口，包括端点、参数、响应格式和使用示例。

## 基础信息

- **API版本**: 1.0.0
- **基础URL**: `http://localhost:8000/api/v1`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON

## 认证

当前版本的API不需要认证。在生产环境中，建议使用JWT Token进行认证。

## 错误处理

所有API错误都遵循以下格式：

```json
{
  "detail": "错误描述信息"
}
```

常见的HTTP状态码：
- `200`: 请求成功
- `400`: 请求参数错误
- `404`: 资源未找到
- `500`: 服务器内部错误
- `503`: 服务不可用

## API端点

### 1. 系统状态

#### 获取系统状态
```
GET /system/status
```

**响应示例**:
```json
{
  "timestamp": 1640995200.0,
  "status": "normal",
  "health_score": 1.0,
  "active_faults": [],
  "estimated_parameters": {
    "manning_n": 0.025,
    "gate_coefficient": 0.65
  }
}
```

### 2. 仿真控制

#### 启动仿真
```
POST /simulation/start
```

**请求体**:
```json
{
  "duration": 3600.0,
  "timestep": 1.0,
  "upstream_inflow": 50.0,
  "gate_opening": 1.815
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "仿真已启动",
  "config": {
    "duration": 3600.0,
    "timestep": 1.0,
    "upstream_inflow": 50.0,
    "gate_opening": 1.815
  }
}
```

#### 执行仿真步骤
```
POST /simulation/step
```

**请求体**:
```json
{
  "steps": 1
}
```

**响应示例**:
```json
{
  "status": "success",
  "current_state": {
    "timestamp": 1640995200.0,
    "h_true": 2.5,
    "n_true": 0.025
  },
  "simulation_running": true
}
```

### 3. 传感器数据

#### 获取传感器数据
```
GET /sensors/data
```

**响应示例**:
```json
{
  "timestamp": 1640995200.0,
  "h_gate_up": 2.5,
  "h_gate_down": 2.0,
  "q_gate_down": 38.28,
  "h_channel_mid": 2.25,
  "q_channel_end": 36.37
}
```

### 4. 故障注入

#### 注入故障
```
POST /faults/inject
```

**请求体**:
```json
{
  "sensor_id": "q_gate_down",
  "fault_type": "stuck",
  "value": 0.0,
  "start_time": 0.0
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "故障已注入: q_gate_down (stuck)",
  "fault": {
    "sensor_id": "q_gate_down",
    "fault_type": "stuck",
    "value": 0.0,
    "start_time": 0.0
  }
}
```

### 5. 参数估计

#### 获取参数估计值
```
GET /parameters/estimate
```

**响应示例**:
```json
[
  {
    "parameter_name": "manning_n",
    "value": 0.025,
    "uncertainty": 0.001,
    "timestamp": 1640995200.0
  },
  {
    "parameter_name": "gate_coefficient",
    "value": 0.65,
    "uncertainty": 0.05,
    "timestamp": 1640995200.0
  }
]
```

### 6. 控制命令

#### 发送控制命令
```
POST /control/command
```

**请求体**:
```json
{
  "command": "reset",
  "parameters": {}
}
```

**支持的命令**:
- `reset`: 重置仿真状态
- `start_data_generation`: 启动数据生成场景
- `update_gate_opening`: 更新闸门开度

**响应示例**:
```json
{
  "status": "success",
  "command": "reset",
  "timestamp": 1640995200.0,
  "message": "系统已重置"
}
```

## WebSocket接口

### 实时系统状态推送
```
WebSocket /ws/system_status
```

连接后，服务器会每秒推送系统状态信息。

### 实时传感器数据推送
```
WebSocket /ws/sensor_data
```

连接后，服务器会每0.5秒推送传感器数据。

## 健康检查

#### 系统健康检查
```
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2021-12-31T00:00:00",
  "system_modules": true,
  "components": {
    "simulation_manager": true,
    "ml_fault_detector": true,
    "predictive_maintenance": true
  }
}
```

## 使用示例

### Python示例

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000"

# 获取系统状态
response = requests.get(f"{BASE_URL}/system/status")
if response.status_code == 200:
    status = response.json()
    print(f"系统状态: {status['status']}")

# 启动仿真
config = {
    "duration": 3600.0,
    "timestep": 1.0,
    "upstream_inflow": 50.0,
    "gate_opening": 1.815
}
response = requests.post(f"{BASE_URL}/simulation/start", json=config)
if response.status_code == 200:
    result = response.json()
    print(f"仿真启动: {result['message']}")
```

### JavaScript示例

```javascript
// 获取传感器数据
async function getSensorData() {
    try {
        const response = await fetch('/sensors/data');
        const data = await response.json();
        console.log('传感器数据:', data);
        return data;
    } catch (error) {
        console.error('获取传感器数据失败:', error);
    }
}

// WebSocket连接示例
const ws = new WebSocket('ws://localhost:8000/ws/sensor_data');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('实时传感器数据:', data);
};
```

## 限流和配额

当前版本API没有实施限流措施。在生产环境中，建议实施以下限流策略：
- 每个IP每分钟最多1000次请求
- WebSocket连接数限制为10个/IP
- 大文件上传限制为10MB

## 版本管理

API版本通过URL路径管理：
- `v1`: 当前稳定版本
- `v2`: 开发中版本（如有）

## 变更日志

### v1.0.0 (2024-12-31)
- 初始版本发布
- 实现基础仿真控制API
- 实现传感器数据接口
- 实现故障注入功能
- 实现参数估计接口
- 实现WebSocket实时推送

## 支持和反馈

如有问题或建议，请联系技术支持团队：
- 邮箱: support@digital-twin-system.com
- 电话: +86-123-4567-8900