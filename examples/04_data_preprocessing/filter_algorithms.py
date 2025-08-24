#!/usr/bin/env python3
"""
滤波算法实现

实现多种滤波算法，用于数字孪生系统中的传感器数据预处理。
包括滑动平均、指数平滑、卡尔曼滤波、中值滤波等。

作者: 数字孪生团队
日期: 2024
"""

import numpy as np
from collections import deque
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class FilterBase(ABC):
    """滤波器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_initialized = False
        self.filter_history = []
    
    @abstractmethod
    def filter_single(self, value: float) -> float:
        """滤波单个数值"""
        pass
    
    def filter_batch(self, data: List[float]) -> List[float]:
        """批量滤波"""
        return [self.filter_single(value) for value in data]
    
    def reset(self):
        """重置滤波器状态"""
        self.is_initialized = False
        self.filter_history.clear()
    
    def get_filter_info(self) -> Dict[str, Any]:
        """获取滤波器信息"""
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "history_length": len(self.filter_history)
        }

class MovingAverageFilter(FilterBase):
    """滑动平均滤波器"""
    
    def __init__(self, window_size: int = 5):
        super().__init__("MovingAverage")
        self.window_size = window_size
        self.buffer = deque(maxlen=window_size)
        
    def filter_single(self, value: float) -> float:
        """滤波单个数值"""
        self.buffer.append(value)
        filtered_value = np.mean(self.buffer)
        
        if not self.is_initialized and len(self.buffer) >= self.window_size:
            self.is_initialized = True
        
        self.filter_history.append(filtered_value)
        return filtered_value
    
    def get_filter_info(self) -> Dict[str, Any]:
        info = super().get_filter_info()
        info.update({
            "window_size": self.window_size,
            "buffer_length": len(self.buffer)
        })
        return info

class ExponentialSmoothingFilter(FilterBase):
    """指数平滑滤波器"""
    
    def __init__(self, alpha: float = 0.3):
        super().__init__("ExponentialSmoothing")
        self.alpha = alpha
        self.previous_value = None
        
        if not (0 < alpha <= 1):
            raise ValueError("Alpha must be in range (0, 1]")
    
    def filter_single(self, value: float) -> float:
        """滤波单个数值"""
        if self.previous_value is None:
            # 第一个值直接使用
            filtered_value = value
            self.is_initialized = True
        else:
            # 指数加权平均
            filtered_value = self.alpha * value + (1 - self.alpha) * self.previous_value
        
        self.previous_value = filtered_value
        self.filter_history.append(filtered_value)
        return filtered_value
    
    def reset(self):
        super().reset()
        self.previous_value = None
    
    def get_filter_info(self) -> Dict[str, Any]:
        info = super().get_filter_info()
        info.update({
            "alpha": self.alpha,
            "previous_value": self.previous_value
        })
        return info

class KalmanFilter(FilterBase):
    """卡尔曼滤波器"""
    
    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1, 
                 initial_estimate: float = 0.0, initial_error: float = 1.0):
        super().__init__("Kalman")
        
        # 卡尔曼滤波参数
        self.Q = process_noise      # 过程噪声协方差
        self.R = measurement_noise  # 观测噪声协方差
        
        # 状态变量
        self.x_hat = initial_estimate  # 状态估计
        self.P = initial_error         # 估计误差协方差
        
        # 历史记录
        self.x_hat_history = []
        self.P_history = []
        
    def filter_single(self, measurement: float) -> float:
        """卡尔曼滤波更新"""
        if not self.is_initialized:
            # 第一次测量，初始化状态
            self.x_hat = measurement
            self.is_initialized = True
        else:
            # 预测步骤
            # x_hat_minus = x_hat (假设状态转移矩阵为1)
            # P_minus = P + Q
            x_hat_minus = self.x_hat
            P_minus = self.P + self.Q
            
            # 更新步骤
            # 卡尔曼增益
            K = P_minus / (P_minus + self.R)
            
            # 状态更新
            self.x_hat = x_hat_minus + K * (measurement - x_hat_minus)
            
            # 误差协方差更新
            self.P = (1 - K) * P_minus
        
        # 记录历史
        self.x_hat_history.append(self.x_hat)
        self.P_history.append(self.P)
        self.filter_history.append(self.x_hat)
        
        return self.x_hat
    
    def reset(self):
        super().reset()
        self.x_hat = 0.0
        self.P = 1.0
        self.x_hat_history.clear()
        self.P_history.clear()
    
    def get_filter_info(self) -> Dict[str, Any]:
        info = super().get_filter_info()
        info.update({
            "process_noise_Q": self.Q,
            "measurement_noise_R": self.R,
            "current_estimate": self.x_hat,
            "current_error_covariance": self.P
        })
        return info
    
    def get_confidence_interval(self, confidence_level: float = 0.95) -> Tuple[float, float]:
        """获取置信区间"""
        if not self.is_initialized:
            return (0.0, 0.0)
        
        # 基于正态分布的置信区间
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        error_std = np.sqrt(self.P)
        
        lower_bound = self.x_hat - z_score * error_std
        upper_bound = self.x_hat + z_score * error_std
        
        return (lower_bound, upper_bound)

class MedianFilter(FilterBase):
    """中值滤波器"""
    
    def __init__(self, window_size: int = 5):
        super().__init__("Median")
        if window_size % 2 == 0:
            window_size += 1  # 确保窗口大小为奇数
        self.window_size = window_size
        self.buffer = deque(maxlen=window_size)
    
    def filter_single(self, value: float) -> float:
        """滤波单个数值"""
        self.buffer.append(value)
        
        if len(self.buffer) >= 3:  # 至少需要3个点才能进行中值滤波
            filtered_value = np.median(list(self.buffer))
        else:
            filtered_value = value
        
        if not self.is_initialized and len(self.buffer) >= self.window_size:
            self.is_initialized = True
        
        self.filter_history.append(filtered_value)
        return filtered_value
    
    def get_filter_info(self) -> Dict[str, Any]:
        info = super().get_filter_info()
        info.update({
            "window_size": self.window_size,
            "buffer_length": len(self.buffer)
        })
        return info

class AdaptiveFilter(FilterBase):
    """自适应滤波器"""
    
    def __init__(self, min_alpha: float = 0.1, max_alpha: float = 0.9, 
                 adaptation_rate: float = 0.1):
        super().__init__("Adaptive")
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.adaptation_rate = adaptation_rate
        
        self.current_alpha = (min_alpha + max_alpha) / 2
        self.previous_value = None
        self.prediction_errors = deque(maxlen=10)
        
    def filter_single(self, value: float) -> float:
        """自适应滤波"""
        if self.previous_value is None:
            filtered_value = value
            self.is_initialized = True
        else:
            # 计算预测误差
            prediction_error = abs(value - self.previous_value)
            self.prediction_errors.append(prediction_error)
            
            # 自适应调整alpha
            if len(self.prediction_errors) >= 3:
                recent_error = np.mean(list(self.prediction_errors)[-3:])
                overall_error = np.mean(self.prediction_errors)
                
                if recent_error > overall_error:
                    # 误差增大，提高响应速度
                    self.current_alpha = min(self.max_alpha, 
                                           self.current_alpha + self.adaptation_rate)
                else:
                    # 误差减小，降低响应速度
                    self.current_alpha = max(self.min_alpha, 
                                           self.current_alpha - self.adaptation_rate)
            
            # 指数平滑
            filtered_value = (self.current_alpha * value + 
                            (1 - self.current_alpha) * self.previous_value)
        
        self.previous_value = filtered_value
        self.filter_history.append(filtered_value)
        return filtered_value
    
    def reset(self):
        super().reset()
        self.previous_value = None
        self.current_alpha = (self.min_alpha + self.max_alpha) / 2
        self.prediction_errors.clear()
    
    def get_filter_info(self) -> Dict[str, Any]:
        info = super().get_filter_info()
        info.update({
            "current_alpha": self.current_alpha,
            "min_alpha": self.min_alpha,
            "max_alpha": self.max_alpha,
            "recent_errors": list(self.prediction_errors)[-5:] if self.prediction_errors else []
        })
        return info

class CombinedFilter(FilterBase):
    """组合滤波器 - 多种滤波器串联"""
    
    def __init__(self, filters: List[FilterBase]):
        super().__init__("Combined")
        self.filters = filters
        
    def filter_single(self, value: float) -> float:
        """依次通过所有滤波器"""
        current_value = value
        
        for filter_obj in self.filters:
            current_value = filter_obj.filter_single(current_value)
        
        if not self.is_initialized:
            self.is_initialized = all(f.is_initialized for f in self.filters)
        
        self.filter_history.append(current_value)
        return current_value
    
    def reset(self):
        super().reset()
        for filter_obj in self.filters:
            filter_obj.reset()
    
    def get_filter_info(self) -> Dict[str, Any]:
        info = super().get_filter_info()
        info.update({
            "sub_filters": [f.get_filter_info() for f in self.filters]
        })
        return info

class FilterManager:
    """滤波器管理器"""
    
    def __init__(self):
        self.filters = {}
        self.performance_metrics = {}
    
    def add_filter(self, name: str, filter_obj: FilterBase):
        """添加滤波器"""
        self.filters[name] = filter_obj
        logger.info(f"添加滤波器: {name} ({filter_obj.__class__.__name__})")
    
    def remove_filter(self, name: str):
        """移除滤波器"""
        if name in self.filters:
            del self.filters[name]
            logger.info(f"移除滤波器: {name}")
    
    def filter_data(self, name: str, data: List[float]) -> List[float]:
        """使用指定滤波器处理数据"""
        if name not in self.filters:
            raise ValueError(f"滤波器 '{name}' 不存在")
        
        return self.filters[name].filter_batch(data)
    
    def compare_filters(self, data: List[float], 
                       reference_data: Optional[List[float]] = None) -> Dict[str, Any]:
        """比较所有滤波器的性能"""
        results = {}
        
        for name, filter_obj in self.filters.items():
            # 重置滤波器
            filter_obj.reset()
            
            # 滤波数据
            filtered_data = filter_obj.filter_batch(data)
            
            # 计算性能指标
            metrics = self._calculate_performance_metrics(
                original_data=data,
                filtered_data=filtered_data,
                reference_data=reference_data
            )
            
            results[name] = {
                "filtered_data": filtered_data,
                "metrics": metrics,
                "filter_info": filter_obj.get_filter_info()
            }
        
        return results
    
    def _calculate_performance_metrics(self, original_data: List[float], 
                                     filtered_data: List[float],
                                     reference_data: Optional[List[float]] = None) -> Dict[str, float]:
        """计算性能指标"""
        metrics = {}
        
        # 噪声减少率
        original_noise = np.std(np.diff(original_data))
        filtered_noise = np.std(np.diff(filtered_data))
        noise_reduction = (1 - filtered_noise / original_noise) * 100 if original_noise > 0 else 0
        metrics["noise_reduction_percent"] = noise_reduction
        
        # 信号保真度 (与原始数据的相关系数)
        if len(original_data) == len(filtered_data):
            correlation = np.corrcoef(original_data, filtered_data)[0, 1]
            metrics["signal_fidelity"] = correlation
        
        # 与参考数据的比较 (如果提供)
        if reference_data and len(reference_data) == len(filtered_data):
            mse = np.mean((np.array(filtered_data) - np.array(reference_data)) ** 2)
            mae = np.mean(np.abs(np.array(filtered_data) - np.array(reference_data)))
            metrics["mse_vs_reference"] = mse
            metrics["mae_vs_reference"] = mae
        
        # 延迟估计 (通过互相关)
        if len(original_data) == len(filtered_data) and len(original_data) > 10:
            cross_corr = np.correlate(original_data, filtered_data, mode='full')
            delay = np.argmax(cross_corr) - len(original_data) + 1
            metrics["estimated_delay"] = abs(delay)
        
        return metrics
    
    def get_all_filter_info(self) -> Dict[str, Any]:
        """获取所有滤波器信息"""
        return {name: filter_obj.get_filter_info() 
                for name, filter_obj in self.filters.items()}

# 工厂函数
def create_filter(filter_type: str, **kwargs) -> FilterBase:
    """创建滤波器的工厂函数"""
    filter_classes = {
        "moving_average": MovingAverageFilter,
        "exponential": ExponentialSmoothingFilter,
        "kalman": KalmanFilter,
        "median": MedianFilter,
        "adaptive": AdaptiveFilter
    }
    
    if filter_type not in filter_classes:
        raise ValueError(f"不支持的滤波器类型: {filter_type}")
    
    return filter_classes[filter_type](**kwargs)

def create_standard_filter_set() -> FilterManager:
    """创建标准滤波器集合"""
    manager = FilterManager()
    
    # 添加各种滤波器
    manager.add_filter("ma_3", create_filter("moving_average", window_size=3))
    manager.add_filter("ma_5", create_filter("moving_average", window_size=5))
    manager.add_filter("ma_10", create_filter("moving_average", window_size=10))
    
    manager.add_filter("exp_01", create_filter("exponential", alpha=0.1))
    manager.add_filter("exp_03", create_filter("exponential", alpha=0.3))
    manager.add_filter("exp_05", create_filter("exponential", alpha=0.5))
    
    manager.add_filter("kalman_low", create_filter("kalman", process_noise=0.001, measurement_noise=0.1))
    manager.add_filter("kalman_med", create_filter("kalman", process_noise=0.01, measurement_noise=0.1))
    manager.add_filter("kalman_high", create_filter("kalman", process_noise=0.1, measurement_noise=0.1))
    
    manager.add_filter("median_3", create_filter("median", window_size=3))
    manager.add_filter("median_5", create_filter("median", window_size=5))
    
    manager.add_filter("adaptive", create_filter("adaptive"))
    
    return manager