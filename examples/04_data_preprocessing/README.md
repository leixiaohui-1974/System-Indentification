# 04 数据预处理详解

## 概述

本示例深入介绍数字孪生系统中的数据预处理技术，包括滤波算法、噪声处理、异常值检测和数据质量评估。

## 学习目标

- 理解数据预处理在数字孪生系统中的重要性
- 掌握滑动平均、卡尔曼滤波等滤波技术
- 学会检测和处理传感器数据异常
- 评估数据质量和处理效果

## 文件结构

```
examples/04_data_preprocessing/
├── README.md                    # 本文档
├── preprocessing_demo.py        # 预处理演示主程序
├── filter_algorithms.py        # 滤波算法实现
├── noise_analysis.py           # 噪声分析工具
├── outlier_detection.py        # 异常值检测
├── data_quality_assessment.py  # 数据质量评估
├── real_time_processor.py      # 实时数据处理器
├── config_preprocessing.py     # 预处理配置
├── test_data/                  # 测试数据
│   ├── noisy_sensor_data.csv
│   ├── clean_reference_data.csv
│   └── fault_data_samples.csv
└── output/                     # 输出结果
    ├── filter_comparison.png
    ├── noise_analysis_report.png
    └── data_quality_metrics.json
```

## 主要内容

### 1. 滤波算法对比
- **滑动平均滤波**: 简单、快速，适用于平稳信号
- **指数平滑**: 对新数据敏感，适用于趋势信号
- **卡尔曼滤波**: 最优估计，适用于动态系统
- **中值滤波**: 去除脉冲噪声，保持边缘特征

### 2. 噪声特性分析
- 噪声类型识别（白噪声、有色噪声）
- 噪声功率谱分析
- 信噪比计算
- 噪声统计特性

### 3. 异常值检测
- 基于统计的方法（3-sigma、IQR）
- 基于模型的方法（残差分析）
- 在线异常检测算法
- 异常值处理策略

### 4. 数据质量评估
- 完整性评估
- 一致性检查
- 准确性验证
- 及时性分析

## 运行示例

### 基础演示
```bash
python preprocessing_demo.py
```

### 滤波算法对比
```bash
python preprocessing_demo.py --mode filter_comparison
```

### 噪声分析
```bash
python preprocessing_demo.py --mode noise_analysis
```

### 实时处理演示
```bash
python preprocessing_demo.py --mode real_time
```

## 核心算法

### 滑动平均滤波
```python
def moving_average_filter(data, window_size):
    """滑动平均滤波"""
    filtered_data = []
    buffer = deque(maxlen=window_size)
    
    for value in data:
        buffer.append(value)
        filtered_data.append(np.mean(buffer))
    
    return filtered_data
```

### 卡尔曼滤波
```python
class KalmanFilter:
    def __init__(self, process_noise, measurement_noise):
        self.Q = process_noise  # 过程噪声
        self.R = measurement_noise  # 观测噪声
        # ... 其他参数初始化
    
    def update(self, measurement):
        # 预测步骤
        # 更新步骤
        return filtered_value
```

### 异常值检测
```python
def detect_outliers_zscore(data, threshold=3.0):
    """基于Z-score的异常值检测"""
    mean_val = np.mean(data)
    std_val = np.std(data)
    z_scores = np.abs((data - mean_val) / std_val)
    return z_scores > threshold
```

## 配置参数

### 滤波参数
```python
FILTER_CONFIG = {
    "moving_average": {
        "window_size": 5
    },
    "exponential": {
        "alpha": 0.3
    },
    "kalman": {
        "process_noise": 0.01,
        "measurement_noise": 0.1
    }
}
```

### 异常检测参数
```python
OUTLIER_CONFIG = {
    "zscore_threshold": 3.0,
    "iqr_multiplier": 1.5,
    "rolling_window": 20
}
```

## 性能评估指标

### 滤波效果评估
- **噪声减少率**: (原始噪声 - 滤波后噪声) / 原始噪声
- **信号延迟**: 滤波引入的时间延迟
- **信号保真度**: 滤波后信号与真实信号的相似度

### 异常检测性能
- **检测率**: 正确检测的异常值比例
- **误报率**: 误报的正常值比例
- **F1分数**: 检测率和精确率的调和平均

## 实际应用案例

### 案例1: 水位传感器噪声处理
```python
# 场景：水位传感器受电磁干扰产生高频噪声
# 解决方案：滑动平均 + 卡尔曼滤波组合
water_level_processor = WaterLevelProcessor(
    primary_filter="moving_average",
    secondary_filter="kalman",
    window_size=3,
    kalman_q=0.001,
    kalman_r=0.01
)
```

### 案例2: 流量计异常值检测
```python
# 场景：流量计偶发性读数异常
# 解决方案：滑动窗口 + 统计检验
flow_outlier_detector = FlowOutlierDetector(
    method="modified_zscore",
    window_size=10,
    threshold=3.5
)
```

## 常见问题与解决方案

### Q1: 滤波后信号延迟过大？
**A**: 
- 减小滤波窗口大小
- 使用前向-后向滤波
- 采用实时性更好的滤波算法

### Q2: 异常值检测误报率高？
**A**:
- 调整检测阈值
- 结合多种检测方法
- 考虑信号的动态特性

### Q3: 实时处理性能不足？
**A**:
- 优化算法实现
- 使用增量式计算
- 考虑硬件加速

## 进阶学习

完成本示例后，建议继续学习：

1. [05_fault_detection](../05_fault_detection/) - 故障检测算法
2. [06_system_identification](../06_system_identification/) - 系统辨识
3. [13_performance_optimization](../13_performance_optimization/) - 性能优化

## 参考资料

- Kalman滤波理论与应用
- 数字信号处理基础
- 异常检测算法综述
- 实时系统设计原理