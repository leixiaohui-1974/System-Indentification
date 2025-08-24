# 05 故障检测实现

## 概述

本示例详细介绍数字孪生水力系统中的故障检测技术，包括传感器故障类型、检测算法、诊断策略和容错机制。

## 学习目标

- 理解传感器故障的类型和特征
- 掌握多种故障检测算法的原理和实现
- 学会设计多层次的故障诊断系统
- 实现实时故障检测和报警机制

## 文件结构

```
examples/05_fault_detection/
├── README.md                     # 本文档
├── fault_detection_demo.py       # 故障检测演示主程序
├── fault_types.py                # 故障类型定义和模拟
├── detection_algorithms.py       # 检测算法实现
├── diagnostic_system.py          # 诊断系统框架
├── fault_injection.py            # 故障注入工具
├── alarm_system.py               # 报警系统
├── redundancy_manager.py         # 冗余管理器
├── config_fault_detection.py     # 故障检测配置
├── test_scenarios/               # 测试场景
│   ├── drift_scenario.json
│   ├── noise_scenario.json
│   ├── stuck_scenario.json
│   └── multiple_faults.json
└── output/                       # 输出结果
    ├── fault_detection_report.html
    ├── detection_performance.png
    └── fault_timeline.json
```

## 传感器故障类型

### 1. 硬故障 (Hard Faults)
- **完全失效**: 传感器停止工作，无数据输出
- **卡死故障**: 输出固定值，不随真实物理量变化
- **短路/断路**: 输出极值（0或最大值）

### 2. 软故障 (Soft Faults)
- **漂移故障**: 输出逐渐偏离真实值
- **增益故障**: 输出幅值异常（过大或过小）
- **偏置故障**: 输出存在固定偏差
- **噪声增大**: 测量精度下降，随机误差增大

### 3. 间歇性故障
- **周期性故障**: 按一定周期出现的故障
- **随机故障**: 随机出现的瞬时故障
- **环境相关故障**: 与环境条件相关的故障

## 检测算法分类

### 1. 基于模型的方法
```python
class ModelBasedDetector:
    """基于模型的故障检测器"""
    
    def __init__(self, model, threshold):
        self.model = model
        self.threshold = threshold
    
    def detect(self, measurement, predicted_value):
        residual = abs(measurement - predicted_value)
        return residual > self.threshold
```

### 2. 基于统计的方法
```python
class StatisticalDetector:
    """基于统计的故障检测器"""
    
    def __init__(self, window_size=20, z_threshold=3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.data_buffer = deque(maxlen=window_size)
    
    def detect(self, measurement):
        self.data_buffer.append(measurement)
        if len(self.data_buffer) < self.window_size:
            return False
        
        mean_val = np.mean(self.data_buffer)
        std_val = np.std(self.data_buffer)
        z_score = abs(measurement - mean_val) / std_val
        
        return z_score > self.z_threshold
```

### 3. 基于信号处理的方法
```python
class SignalBasedDetector:
    """基于信号处理的故障检测器"""
    
    def __init__(self, method="wavelet"):
        self.method = method
        self.baseline_spectrum = None
    
    def detect(self, signal_segment):
        if self.method == "fft":
            return self._fft_based_detection(signal_segment)
        elif self.method == "wavelet":
            return self._wavelet_based_detection(signal_segment)
```

### 4. 基于机器学习的方法
```python
class MLBasedDetector:
    """基于机器学习的故障检测器"""
    
    def __init__(self, model_type="isolation_forest"):
        self.model_type = model_type
        self.model = None
        self.is_trained = False
    
    def train(self, normal_data):
        if self.model_type == "isolation_forest":
            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(contamination=0.1)
            self.model.fit(normal_data)
        self.is_trained = True
    
    def detect(self, measurement):
        if not self.is_trained:
            return False
        prediction = self.model.predict([[measurement]])
        return prediction[0] == -1  # -1 表示异常
```

## 多层次诊断架构

### 第一层：单传感器检测
- 统计阈值检测
- 趋势分析
- 频域分析

### 第二层：多传感器关联
- 传感器间一致性检查
- 物理约束验证
- 冗余信息利用

### 第三层：系统级诊断
- 模型残差分析
- 状态估计器
- 专家系统规则

## 核心算法实现

### CUSUM算法（累积和）
```python
class CUSUMDetector:
    """CUSUM累积和检测算法"""
    
    def __init__(self, threshold=5.0, drift=0.5):
        self.threshold = threshold
        self.drift = drift
        self.cumsum_pos = 0.0
        self.cumsum_neg = 0.0
    
    def detect(self, measurement, reference=0.0):
        deviation = measurement - reference
        
        # 正向累积和
        self.cumsum_pos = max(0, self.cumsum_pos + deviation - self.drift)
        
        # 负向累积和
        self.cumsum_neg = max(0, self.cumsum_neg - deviation - self.drift)
        
        # 检测阈值
        if self.cumsum_pos > self.threshold:
            return "positive_drift"
        elif self.cumsum_neg > self.threshold:
            return "negative_drift"
        else:
            return "normal"
```

### SPRT算法（序贯概率比检验）
```python
class SPRTDetector:
    """序贯概率比检验"""
    
    def __init__(self, alpha=0.01, beta=0.01, delta=1.0):
        self.alpha = alpha  # 虚警概率
        self.beta = beta    # 漏检概率
        self.delta = delta  # 检测的最小变化
        
        self.A = (1 - beta) / alpha
        self.B = beta / (1 - alpha)
        self.log_likelihood_ratio = 0.0
    
    def detect(self, measurement, normal_mean, normal_std):
        # 计算似然比
        fault_mean = normal_mean + self.delta
        
        # 正常情况下的似然
        normal_likelihood = self._gaussian_likelihood(measurement, normal_mean, normal_std)
        
        # 故障情况下的似然
        fault_likelihood = self._gaussian_likelihood(measurement, fault_mean, normal_std)
        
        # 更新对数似然比
        if normal_likelihood > 0:
            self.log_likelihood_ratio += np.log(fault_likelihood / normal_likelihood)
        
        # 决策
        if self.log_likelihood_ratio >= np.log(self.A):
            return "fault_detected"
        elif self.log_likelihood_ratio <= np.log(self.B):
            return "normal"
        else:
            return "continue_testing"
```

## 冗余和容错机制

### 硬件冗余
```python
class HardwareRedundancy:
    """硬件冗余管理"""
    
    def __init__(self, sensor_groups):
        self.sensor_groups = sensor_groups  # 每组包含冗余传感器
    
    def vote(self, measurements):
        """多数表决"""
        if len(measurements) >= 3:
            return np.median(measurements)
        elif len(measurements) == 2:
            # 简单平均或选择可信度高的
            return np.mean(measurements)
        else:
            return measurements[0] if measurements else None
```

### 分析冗余
```python
class AnalyticalRedundancy:
    """分析冗余 - 基于物理模型"""
    
    def __init__(self, physical_model):
        self.model = physical_model
    
    def estimate_sensor_value(self, other_sensor_data):
        """基于其他传感器数据估计目标传感器值"""
        return self.model.predict(other_sensor_data)
    
    def detect_inconsistency(self, measured_value, estimated_value, threshold):
        """检测不一致性"""
        return abs(measured_value - estimated_value) > threshold
```

## 性能评估指标

### 检测性能
- **检测率 (Detection Rate)**: TP / (TP + FN)
- **误报率 (False Alarm Rate)**: FP / (FP + TN)
- **准确率 (Accuracy)**: (TP + TN) / (TP + TN + FP + FN)
- **F1分数**: 2 * (Precision * Recall) / (Precision + Recall)

### 实时性能
- **检测延迟**: 从故障发生到检测出的时间
- **处理时间**: 单次检测所需的计算时间
- **内存消耗**: 算法运行时的内存占用

## 运行示例

### 基础故障检测演示
```bash
python fault_detection_demo.py
```

### 特定故障类型测试
```bash
python fault_detection_demo.py --fault_type drift
python fault_detection_demo.py --fault_type stuck
python fault_detection_demo.py --fault_type noise
```

### 多传感器场景测试
```bash
python fault_detection_demo.py --scenario multi_sensor
```

### 实时检测演示
```bash
python fault_detection_demo.py --mode real_time
```

## 配置参数

### 检测器配置
```python
DETECTOR_CONFIG = {
    "statistical": {
        "window_size": 20,
        "z_threshold": 3.0,
        "use_robust_statistics": True
    },
    "model_based": {
        "residual_threshold": 0.1,
        "consecutive_violations": 3
    },
    "cusum": {
        "drift_threshold": 0.5,
        "detection_threshold": 5.0
    }
}
```

### 传感器配置
```python
SENSOR_CONFIG = {
    "h_gate_up": {
        "normal_range": [2.0, 8.0],
        "noise_threshold": 0.02,
        "drift_threshold": 0.05,
        "stuck_threshold": 0.001
    },
    "q_gate_down": {
        "normal_range": [0.0, 50.0],
        "noise_threshold": 0.5,
        "drift_threshold": 1.0,
        "stuck_threshold": 0.1
    }
}
```

## 实际应用案例

### 案例1: 水位传感器漂移检测
**场景**: 水位传感器由于沉积物积累导致缓慢漂移
**解决方案**: CUSUM + 模型残差双重检测

### 案例2: 流量计间歇性故障
**场景**: 流量计受水中杂物影响偶发性读数异常
**解决方案**: 统计检测 + 时间窗口过滤

### 案例3: 多传感器协同诊断
**场景**: 利用水位-流量物理关系进行交叉验证
**解决方案**: 分析冗余 + 一致性检查

## 常见问题

### Q1: 如何降低误报率？
**A**: 
- 调整检测阈值
- 增加确认机制
- 结合多种检测方法

### Q2: 如何提高检测敏感性？
**A**:
- 降低检测阈值
- 使用更敏感的算法
- 增加传感器冗余

### Q3: 实时性能如何优化？
**A**:
- 简化算法实现
- 使用增量计算
- 优化数据结构

## 下一步学习

完成本示例后，建议继续学习：

1. [06_system_identification](../06_system_identification/) - 系统辨识
2. [10_advanced_diagnostics](../10_advanced_diagnostics/) - 高级诊断
3. [16_logging_debugging](../16_logging_debugging/) - 日志和调试