# 02 快速开始指南

## 概述

本示例提供了数字孪生水力系统的快速入门指南，让您能够在几分钟内运行完整的仿真系统并查看结果。

## 前置要求

- Python 3.8+
- 必要的依赖包（见 requirements.txt）
- 基础概念了解（建议先完成 01_basic_concepts）

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行基础仿真
```bash
python quick_start_demo.py
```

### 3. 查看结果
程序会生成：
- 实时仿真输出
- 可视化图表文件
- 系统状态报告

## 文件结构

```
examples/02_quick_start/
├── README.md                # 本文档
├── quick_start_demo.py      # 快速开始主程序
├── simple_simulator.py     # 简化的仿真器
├── basic_analysis.py       # 基础数据分析
├── requirements.txt        # 依赖包列表
├── config_quickstart.py    # 快速开始配置
└── output/                 # 输出文件目录
    ├── simulation_results.png
    ├── system_status.json
    └── simulation_log.txt
```

## 示例功能

### 1. 基础仿真运行
- 启动简化的数字孪生系统
- 运行 30 秒的仿真时间
- 实时显示系统状态

### 2. 数据生成与处理
- 模拟 5 个传感器的数据
- 应用滑动平均滤波
- 检测潜在的传感器故障

### 3. 模型预测
- 使用简化的物理模型
- 在线参数辨识
- 预测结果对比

### 4. 可视化输出
- 传感器数据时间序列
- 故障检测状态
- 参数收敛过程
- 系统性能指标

## 运行结果解读

### 控制台输出
```
🚀 数字孪生水力系统快速开始
================================
⏱️  仿真时间: 30.0 秒
📊 传感器数量: 5
🔧 启用故障检测: 是
📈 启用参数辨识: 是

[00:01] 系统初始化完成
[00:02] 开始数据采集...
[00:05] 检测到正常运行状态
[00:10] 参数更新: manning_coeff = 0.0251
...
[00:30] 仿真完成
```

### 生成的图表
1. **simulation_results.png** - 完整仿真结果
2. **sensor_trends.png** - 传感器数据趋势
3. **fault_detection.png** - 故障检测状态
4. **parameter_evolution.png** - 参数演化过程

### 状态文件
- **system_status.json** - 系统最终状态
- **simulation_log.txt** - 详细仿真日志

## 定制化选项

### 修改仿真参数
编辑 `config_quickstart.py`：
```python
# 仿真时长
SIMULATION_TIME = 60.0  # 改为60秒

# 传感器噪声
NOISE_LEVEL = 0.01  # 增加噪声水平

# 故障注入
INJECT_FAULT = True  # 启用故障注入
FAULT_START_TIME = 15.0  # 15秒后注入故障
```

### 选择不同场景
```bash
# 正常运行场景
python quick_start_demo.py --scenario normal

# 带故障的场景
python quick_start_demo.py --scenario fault

# 高噪声场景
python quick_start_demo.py --scenario noisy
```

## 常见问题

### Q: 仿真运行很慢？
A: 这是正常的，因为包含了完整的物理模型计算。可以减少仿真时间或降低输出频率。

### Q: 图表无法显示？
A: 确保安装了 matplotlib，或查看 output/ 目录中的图片文件。

### Q: 参数不收敛？
A: 调整 RLS 遗忘因子或增加仿真时间长度。

## 下一步学习

完成快速开始后，建议继续学习：

1. [03_basic_simulation](../03_basic_simulation/) - 详细仿真过程
2. [04_data_preprocessing](../04_data_preprocessing/) - 数据预处理技术
3. [05_fault_detection](../05_fault_detection/) - 故障检测算法

## 技术支持

如遇到问题，请：
1. 检查依赖包是否正确安装
2. 查看 simulation_log.txt 的错误信息
3. 参考项目主文档
4. 提交 Issue 或联系开发团队