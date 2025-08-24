# 12 Web界面开发

## 概述

本示例展示如何为数字孪生水力系统开发现代化的Web界面，包括实时数据可视化、交互式控制面板、系统监控仪表板等功能。

## 学习目标

- 掌握Web界面架构设计
- 学会实时数据可视化技术
- 实现用户交互和系统控制
- 构建响应式和现代化的用户界面

## 技术栈

### 后端技术
- **Flask/FastAPI**: Python Web框架
- **WebSocket**: 实时数据通信
- **SQLite/PostgreSQL**: 数据存储
- **Redis**: 缓存和会话管理

### 前端技术
- **HTML5/CSS3**: 基础结构和样式
- **JavaScript/TypeScript**: 交互逻辑
- **Chart.js/D3.js**: 数据可视化
- **Bootstrap/Tailwind**: UI框架

## 文件结构

```
examples/12_web_interface/
├── README.md                    # 本文档
├── app.py                      # Flask主应用
├── api/                        # API接口
│   ├── __init__.py
│   ├── data_api.py            # 数据API
│   ├── control_api.py         # 控制API
│   └── system_api.py          # 系统状态API
├── static/                     # 静态资源
│   ├── css/
│   │   ├── dashboard.css
│   │   ├── charts.css
│   │   └── responsive.css
│   ├── js/
│   │   ├── dashboard.js
│   │   ├── charts.js
│   │   ├── websocket.js
│   │   └── controls.js
│   └── images/
├── templates/                  # HTML模板
│   ├── base.html
│   ├── dashboard.html
│   ├── monitoring.html
│   ├── control_panel.html
│   └── system_status.html
├── components/                 # Web组件
│   ├── real_time_chart.py
│   ├── data_table.py
│   ├── control_widgets.py
│   └── alert_system.py
├── websocket_handler.py        # WebSocket处理器
├── database.py                 # 数据库接口
├── config_web.py              # Web配置
└── run_server.py              # 服务器启动脚本
```

## 主要功能模块

### 1. 实时仪表板
- **系统概览**: 关键指标一览
- **实时图表**: 传感器数据时间序列
- **状态指示器**: 系统健康状态
- **报警面板**: 故障和报警信息

### 2. 数据监控
- **传感器监控**: 所有传感器实时数据
- **历史数据查询**: 可选择时间范围
- **数据导出**: CSV/Excel格式导出
- **数据质量评估**: 数据完整性和准确性

### 3. 系统控制
- **参数调整**: 在线修改系统参数
- **仿真控制**: 启动/停止/重置仿真
- **场景切换**: 不同仿真场景选择
- **故障注入**: 手动注入测试故障

### 4. 诊断分析
- **故障检测结果**: 实时故障状态
- **参数辨识**: 参数收敛过程
- **性能指标**: 系统性能评估
- **报告生成**: 自动生成分析报告

## 核心代码示例

### Flask应用主框架
```python
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'digital_twin_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量存储系统状态
system_state = {
    "status": "running",
    "sensor_data": {},
    "fault_status": {},
    "parameters": {}
}

@app.route('/')
def dashboard():
    """主仪表板"""
    return render_template('dashboard.html')

@app.route('/monitoring')
def monitoring():
    """监控页面"""
    return render_template('monitoring.html')

@app.route('/control')
def control_panel():
    """控制面板"""
    return render_template('control_panel.html')
```

### WebSocket实时数据推送
```python
class DataStreamer:
    """实时数据流处理器"""
    
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
        self.running = False
        self.thread = None
    
    def start_streaming(self):
        """开始数据流推送"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._stream_data)
            self.thread.daemon = True
            self.thread.start()
    
    def _stream_data(self):
        """数据流推送线程"""
        while self.running:
            # 获取最新数据
            current_data = get_current_system_data()
            
            # 推送到所有连接的客户端
            self.socketio.emit('sensor_data_update', {
                'timestamp': time.time(),
                'data': current_data
            })
            
            time.sleep(1)  # 1秒更新一次

@socketio.on('connect')
def handle_connect():
    """客户端连接处理"""
    print('Client connected')
    emit('connection_established', {'status': 'connected'})

@socketio.on('request_data')
def handle_data_request(data):
    """处理数据请求"""
    sensor_type = data.get('sensor_type', 'all')
    time_range = data.get('time_range', '1h')
    
    # 获取请求的数据
    response_data = get_historical_data(sensor_type, time_range)
    emit('data_response', response_data)
```

### 实时图表组件
```javascript
class RealTimeChart {
    constructor(containerId, config) {
        this.container = document.getElementById(containerId);
        this.config = config;
        this.chart = null;
        this.maxDataPoints = config.maxDataPoints || 100;
        this.data = [];
        
        this.initChart();
    }
    
    initChart() {
        const ctx = this.container.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: this.config.label,
                    data: [],
                    borderColor: this.config.color || 'blue',
                    backgroundColor: 'transparent',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                second: 'HH:mm:ss'
                            }
                        }
                    },
                    y: {
                        beginAtZero: false
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }
    
    addDataPoint(timestamp, value) {
        // 添加新数据点
        this.data.push({ x: timestamp, y: value });
        
        // 限制数据点数量
        if (this.data.length > this.maxDataPoints) {
            this.data.shift();
        }
        
        // 更新图表
        this.chart.data.datasets[0].data = this.data;
        this.chart.update('none'); // 不使用动画以提高性能
    }
    
    updateThreshold(min, max) {
        // 更新阈值线
        if (!this.chart.options.plugins.annotation) {
            this.chart.options.plugins.annotation = { annotations: {} };
        }
        
        this.chart.options.plugins.annotation.annotations = {
            maxLine: {
                type: 'line',
                yMin: max,
                yMax: max,
                borderColor: 'red',
                borderWidth: 2,
                label: {
                    content: `最大值: ${max}`,
                    enabled: true
                }
            },
            minLine: {
                type: 'line',
                yMin: min,
                yMax: min,
                borderColor: 'orange',
                borderWidth: 2,
                label: {
                    content: `最小值: ${min}`,
                    enabled: true
                }
            }
        };
        
        this.chart.update();
    }
}
```

### WebSocket客户端管理
```javascript
class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000;
        this.eventHandlers = {};
        
        this.connect();
    }
    
    connect() {
        try {
            this.socket = io(this.url);
            this.setupEventHandlers();
            console.log('WebSocket连接已建立');
        } catch (error) {
            console.error('WebSocket连接失败:', error);
            this.handleReconnect();
        }
    }
    
    setupEventHandlers() {
        this.socket.on('connect', () => {
            console.log('连接到服务器');
            this.reconnectAttempts = 0;
            this.emit('connection_established');
        });
        
        this.socket.on('disconnect', () => {
            console.log('与服务器断开连接');
            this.handleReconnect();
        });
        
        this.socket.on('sensor_data_update', (data) => {
            this.handleSensorDataUpdate(data);
        });
        
        this.socket.on('system_alert', (alert) => {
            this.handleSystemAlert(alert);
        });
    }
    
    handleSensorDataUpdate(data) {
        // 更新所有图表
        for (const [sensorId, value] of Object.entries(data.data)) {
            const chart = window.chartManager.getChart(sensorId);
            if (chart) {
                chart.addDataPoint(data.timestamp, value);
            }
        }
        
        // 更新数值显示
        this.updateSensorValues(data.data);
    }
    
    handleSystemAlert(alert) {
        // 显示系统报警
        const alertContainer = document.getElementById('alert-container');
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${alert.level}`;
        alertElement.innerHTML = `
            <strong>${alert.title}</strong>
            <p>${alert.message}</p>
            <small>${new Date(alert.timestamp).toLocaleString()}</small>
        `;
        alertContainer.insertBefore(alertElement, alertContainer.firstChild);
        
        // 自动移除较老的报警
        const alerts = alertContainer.querySelectorAll('.alert');
        if (alerts.length > 10) {
            alerts[alerts.length - 1].remove();
        }
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval);
        } else {
            console.error('重连失败，请刷新页面');
            this.showConnectionError();
        }
    }
    
    requestHistoricalData(sensorType, timeRange) {
        this.socket.emit('request_data', {
            sensor_type: sensorType,
            time_range: timeRange
        });
    }
    
    sendControlCommand(command, parameters) {
        this.socket.emit('control_command', {
            command: command,
            parameters: parameters,
            timestamp: Date.now()
        });
    }
}
```

### 响应式仪表板布局
```css
/* 仪表板主要样式 */
.dashboard-container {
    display: grid;
    grid-template-columns: 250px 1fr;
    grid-template-rows: 60px 1fr;
    grid-template-areas:
        "sidebar header"
        "sidebar main";
    height: 100vh;
    background-color: #f5f7fa;
}

.dashboard-header {
    grid-area: header;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
}

.dashboard-sidebar {
    grid-area: sidebar;
    background: #2c3e50;
    color: white;
    padding: 1rem;
}

.dashboard-main {
    grid-area: main;
    padding: 2rem;
    overflow-y: auto;
}

/* 卡片样式 */
.metric-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 0.5rem;
}

.metric-label {
    font-size: 0.9rem;
    color: #7f8c8d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* 图表容器 */
.chart-container {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #ecf0f1;
}

.chart-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #2c3e50;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .dashboard-container {
        grid-template-columns: 1fr;
        grid-template-rows: 60px auto 1fr;
        grid-template-areas:
            "header"
            "sidebar"
            "main";
    }
    
    .dashboard-sidebar {
        display: none;
    }
    
    .dashboard-sidebar.mobile-open {
        display: block;
        position: fixed;
        top: 60px;
        left: 0;
        right: 0;
        z-index: 1000;
    }
    
    .dashboard-main {
        padding: 1rem;
    }
}

/* 状态指示器 */
.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}

.status-normal { background-color: #27ae60; }
.status-warning { background-color: #f39c12; }
.status-error { background-color: #e74c3c; }
.status-offline { background-color: #95a5a6; }

/* 报警样式 */
.alert-container {
    position: fixed;
    top: 80px;
    right: 20px;
    width: 350px;
    z-index: 1000;
}

.alert {
    background: white;
    border-left: 4px solid;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    animation: slideInRight 0.3s ease-out;
}

.alert-info { border-left-color: #3498db; }
.alert-warning { border-left-color: #f39c12; }
.alert-error { border-left-color: #e74c3c; }

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

## 部署和配置

### 开发环境启动
```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python run_server.py
```

### 生产环境部署
```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 --worker-class eventlet app:app
```

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--worker-class", "eventlet", "app:app"]
```

## 性能优化

### 前端优化
- **代码分割**: 按需加载JavaScript模块
- **缓存策略**: 合理利用浏览器缓存
- **压缩优化**: CSS/JS文件压缩
- **CDN加速**: 静态资源CDN分发

### 后端优化
- **数据缓存**: Redis缓存频繁查询数据
- **连接池**: 数据库连接池管理
- **异步处理**: 使用异步框架提高并发
- **负载均衡**: 多实例部署和负载均衡

## 安全考虑

### 身份认证
```python
from flask_login import LoginManager, login_required

@app.route('/admin')
@login_required
def admin_panel():
    return render_template('admin.html')
```

### 数据验证
```python
from flask_wtf import FlaskForm
from wtforms import FloatField, validators

class ParameterForm(FlaskForm):
    manning_coefficient = FloatField('曼宁系数', 
        [validators.NumberRange(min=0.01, max=0.1)])
```

### CSRF保护
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

## 下一步学习

完成本示例后，建议继续学习：

1. [13_performance_optimization](../13_performance_optimization/) - 性能优化
2. [18_deployment](../18_deployment/) - 系统部署
3. [16_logging_debugging](../16_logging_debugging/) - 日志和调试

## 演示地址

本地开发服务器: http://localhost:5000
- 仪表板: http://localhost:5000/
- 监控页面: http://localhost:5000/monitoring  
- 控制面板: http://localhost:5000/control