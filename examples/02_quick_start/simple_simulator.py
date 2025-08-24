#!/usr/bin/env python3
"""
简化的数字孪生仿真器

为快速开始示例提供的简化版本数字孪生系统实现。
包含核心功能但简化了复杂的物理模型计算。

作者: 数字孪生团队
日期: 2024
"""

import numpy as np
from typing import Dict, Any, List
from collections import deque
import logging

logger = logging.getLogger(__name__)

class SimpleSensorSimulator:
    """简化的传感器仿真器"""
    
    def __init__(self, config):
        self.config = config
        self.time = 0.0
        
        # 基础值设定
        self.base_values = {
            "h_gate_up": 5.0,
            "h_gate_down": 3.0,
            "q_gate_down": 10.0,
            "h_channel_mid": 4.0,
            "q_channel_end": 9.5
        }
        
        # 故障状态
        self.fault_injected = False
        self.fault_start_time = getattr(config, 'FAULT_INJECTION_TIME', 15.0)
        self.fault_type = getattr(config, 'FAULT_TYPE', 'noise')
        
    def generate_sensor_data(self, current_time: float) -> Dict[str, float]:
        """生成传感器数据"""
        self.time = current_time
        sensor_data = {}
        
        # 检查是否需要注入故障
        inject_fault = (hasattr(self.config, 'INJECT_FAULT') and 
                       self.config.INJECT_FAULT and 
                       current_time >= self.fault_start_time)
        
        for sensor in self.config.SENSOR_LIST:
            base_value = self.base_values.get(sensor, 1.0)
            
            # 基础动态变化
            dynamic_component = self._get_dynamic_component(sensor, current_time)
            
            # 噪声
            noise_level = self._get_noise_level(sensor, inject_fault)
            noise = np.random.normal(0, noise_level)
            
            # 故障模拟
            fault_component = self._get_fault_component(sensor, current_time, inject_fault)
            
            # 组合最终值
            final_value = base_value + dynamic_component + noise + fault_component
            
            # 确保物理合理性
            final_value = self._apply_physical_constraints(sensor, final_value)
            
            sensor_data[sensor] = final_value
        
        return sensor_data
    
    def _get_dynamic_component(self, sensor: str, t: float) -> float:
        """获取动态变化分量"""
        # 不同传感器的动态特性
        if 'h' in sensor:  # 水位传感器
            return 0.5 * np.sin(0.1 * t) + 0.2 * np.sin(0.3 * t)
        else:  # 流量传感器
            return 2.0 * np.sin(0.08 * t) + 1.0 * np.sin(0.25 * t)
    
    def _get_noise_level(self, sensor: str, amplify: bool = False) -> float:
        """获取噪声水平"""
        base_noise = (self.config.NOISE_LEVEL_H if 'h' in sensor 
                     else self.config.NOISE_LEVEL_Q)
        
        if amplify and self.fault_type == 'noise':
            return base_noise * self.config.FAULT_NOISE_MULTIPLIER
        
        return base_noise
    
    def _get_fault_component(self, sensor: str, t: float, inject_fault: bool) -> float:
        """获取故障分量"""
        if not inject_fault:
            return 0.0
        
        fault_duration = t - self.fault_start_time
        
        if self.fault_type == 'drift':
            # 漂移故障：线性增长的偏差
            drift_rate = getattr(self.config, 'FAULT_DRIFT_RATE', 0.01)
            return drift_rate * fault_duration
            
        elif self.fault_type == 'stuck':
            # 卡死故障：固定值
            if sensor == self.config.FAULT_TARGET_SENSOR:
                return -self._get_dynamic_component(sensor, t)  # 抵消动态变化
        
        return 0.0
    
    def _apply_physical_constraints(self, sensor: str, value: float) -> float:
        """应用物理约束"""
        if 'h' in sensor:  # 水位不能为负
            return max(0.1, value)
        else:  # 流量不能为负
            return max(0.0, value)

class SimpleDataPreprocessor:
    """简化的数据预处理器"""
    
    def __init__(self, config):
        self.config = config
        self.buffers = {}
        self.window_size = getattr(config, 'FILTER_WINDOW_SIZE', 5)
    
    def process_data(self, raw_data: Dict[str, float]) -> Dict[str, float]:
        """处理数据"""
        processed_data = {}
        
        for sensor, value in raw_data.items():
            # 初始化缓冲区
            if sensor not in self.buffers:
                self.buffers[sensor] = deque(maxlen=self.window_size)
            
            # 添加新数据
            self.buffers[sensor].append(value)
            
            # 应用滑动平均滤波
            if len(self.buffers[sensor]) >= 3:  # 至少3个点才开始滤波
                processed_data[sensor] = np.mean(self.buffers[sensor])
            else:
                processed_data[sensor] = value
        
        return processed_data

class SimpleFaultDetector:
    """简化的故障检测器"""
    
    def __init__(self, config):
        self.config = config
        self.detection_history = {}
        self.smoothed_residuals = {}
        self.ema_alpha = getattr(config, 'EMA_ALPHA', 0.05)
    
    def detect_faults(self, processed_data: Dict[str, float], 
                     model_predictions: Dict[str, float]) -> Dict[str, str]:
        """检测故障"""
        fault_status = {}
        
        for sensor in processed_data:
            # 初始化历史记录
            if sensor not in self.detection_history:
                self.detection_history[sensor] = deque(maxlen=10)
            
            self.detection_history[sensor].append(processed_data[sensor])
            
            # 执行故障检测
            fault_type = self._check_sensor_faults(sensor, processed_data[sensor], 
                                                  model_predictions.get(sensor, processed_data[sensor]))
            
            fault_status[sensor] = fault_type if fault_type else "正常"
        
        return fault_status
    
    def _check_sensor_faults(self, sensor: str, current_value: float, 
                           predicted_value: float) -> str:
        """检查单个传感器的故障"""
        # 1. 噪声检测
        if len(self.detection_history[sensor]) >= 5:
            recent_values = list(self.detection_history[sensor])[-5:]
            noise_level = np.std(recent_values)
            
            base_noise = (self.config.NOISE_LEVEL_H if 'h' in sensor 
                         else self.config.NOISE_LEVEL_Q)
            noise_threshold = base_noise * getattr(self.config, 'NOISE_FACTOR_THRESHOLD', 3.0)
            
            if noise_level > noise_threshold:
                return f"噪声增大 ({noise_level:.4f})"
        
        # 2. 漂移检测
        residual = current_value - predicted_value
        
        # 更新平滑残差
        if sensor not in self.smoothed_residuals:
            self.smoothed_residuals[sensor] = 0.0
        
        self.smoothed_residuals[sensor] = (self.ema_alpha * residual + 
                                         (1 - self.ema_alpha) * self.smoothed_residuals[sensor])
        
        drift_threshold = (getattr(self.config, 'DRIFT_THRESHOLD_H', 0.1) if 'h' in sensor 
                          else getattr(self.config, 'DRIFT_THRESHOLD_Q', 1.0))
        
        if abs(self.smoothed_residuals[sensor]) > drift_threshold:
            return f"漂移 ({self.smoothed_residuals[sensor]:.3f})"
        
        # 3. 卡死检测
        if len(self.detection_history[sensor]) >= 5:
            recent_values = list(self.detection_history[sensor])[-5:]
            value_range = max(recent_values) - min(recent_values)
            
            stuck_threshold = (getattr(self.config, 'STUCK_THRESHOLD_H', 0.01) if 'h' in sensor 
                             else getattr(self.config, 'STUCK_THRESHOLD_Q', 0.1))
            
            if value_range < stuck_threshold:
                return f"疑似卡死 (变化:{value_range:.4f})"
        
        return None

class SimpleSystemIdentifier:
    """简化的系统辨识器"""
    
    def __init__(self, config):
        self.config = config
        
        # 初始参数
        self.parameters = {
            "manning_coefficient": getattr(config, 'MANNING_INITIAL', 0.025),
            "gate_coefficient": getattr(config, 'GATE_COEFF_INITIAL', 0.65)
        }
        
        # RLS参数
        self.forgetting_factor = getattr(config, 'RLS_FORGETTING_FACTOR', 0.95)
        self.covariance_matrix = np.eye(2) * getattr(config, 'RLS_INITIAL_COVARIANCE', 1000.0)
        
        # 历史数据
        self.data_history = deque(maxlen=20)
    
    def update_parameters(self, sensor_data: Dict[str, float], 
                         model_predictions: Dict[str, float]) -> Dict[str, float]:
        """更新模型参数"""
        # 存储数据
        self.data_history.append({
            'sensor_data': sensor_data.copy(),
            'predictions': model_predictions.copy()
        })
        
        # 需要足够的数据才开始辨识
        if len(self.data_history) < 5:
            return self.parameters.copy()
        
        # 简化的RLS更新
        self._update_with_rls()
        
        return self.parameters.copy()
    
    def _update_with_rls(self):
        """使用RLS更新参数"""
        try:
            # 获取最近的观测数据
            recent_data = list(self.data_history)[-5:]
            
            # 构造观测向量和预测向量
            observations = []
            predictions = []
            
            for data_point in recent_data:
                # 使用水位和流量数据
                obs = [data_point['sensor_data'].get('h_gate_up', 5.0),
                      data_point['sensor_data'].get('q_gate_down', 10.0)]
                pred = [data_point['predictions'].get('h_gate_up', 5.0),
                       data_point['predictions'].get('q_gate_down', 10.0)]
                
                observations.extend(obs)
                predictions.extend(pred)
            
            # 计算误差
            error = np.array(observations) - np.array(predictions)
            mean_error = np.mean(error)
            
            # 简化的参数更新
            learning_rate = 0.001 * self.forgetting_factor
            
            # 更新曼宁系数
            if abs(mean_error) > 0.01:
                self.parameters["manning_coefficient"] += learning_rate * mean_error * 0.1
                self.parameters["manning_coefficient"] = np.clip(
                    self.parameters["manning_coefficient"], 0.01, 0.05)
            
            # 更新闸门系数（较慢的变化）
            if abs(mean_error) > 0.05:
                self.parameters["gate_coefficient"] += learning_rate * mean_error * 0.05
                self.parameters["gate_coefficient"] = np.clip(
                    self.parameters["gate_coefficient"], 0.5, 0.8)
                
        except Exception as e:
            logger.warning(f"参数更新失败: {e}")

class SimplePhysicalModel:
    """简化的物理模型"""
    
    def __init__(self, config):
        self.config = config
        self.current_parameters = {
            "manning_coefficient": getattr(config, 'MANNING_INITIAL', 0.025),
            "gate_coefficient": getattr(config, 'GATE_COEFF_INITIAL', 0.65)
        }
    
    def update_parameters(self, new_parameters: Dict[str, float]):
        """更新模型参数"""
        self.current_parameters.update(new_parameters)
    
    def predict(self, sensor_data: Dict[str, float]) -> Dict[str, float]:
        """模型预测"""
        predictions = {}
        
        # 简化的水力学模型
        for sensor in sensor_data:
            if 'h' in sensor:  # 水位预测
                # 基于连续性方程的简化预测
                base_prediction = sensor_data[sensor] * 0.98  # 轻微的水位衰减
                predictions[sensor] = base_prediction
                
            else:  # 流量预测
                # 基于曼宁公式的简化预测
                manning_effect = 1.0 + 0.1 * (self.current_parameters["manning_coefficient"] - 0.025)
                gate_effect = self.current_parameters["gate_coefficient"] / 0.65
                
                base_prediction = sensor_data[sensor] * manning_effect * gate_effect
                predictions[sensor] = base_prediction
        
        return predictions

class SimpleDigitalTwin:
    """简化的数字孪生系统"""
    
    def __init__(self, config):
        self.config = config
        
        # 组件初始化
        self.sensor_simulator = SimpleSensorSimulator(config)
        self.data_preprocessor = SimpleDataPreprocessor(config)
        self.fault_detector = SimpleFaultDetector(config) if config.ENABLE_FAULT_DETECTION else None
        self.system_identifier = SimpleSystemIdentifier(config) if config.ENABLE_SYSTEM_ID else None
        self.physical_model = SimplePhysicalModel(config)
        
        self.initialized = False
        
    def initialize(self) -> bool:
        """初始化系统"""
        try:
            logger.info("简化数字孪生系统初始化开始")
            
            # 验证配置
            if not hasattr(self.config, 'SENSOR_LIST') or not self.config.SENSOR_LIST:
                raise ValueError("传感器列表为空")
            
            # 初始化各组件
            logger.info(f"传感器数量: {len(self.config.SENSOR_LIST)}")
            logger.info(f"故障检测: {'启用' if self.fault_detector else '禁用'}")
            logger.info(f"系统辨识: {'启用' if self.system_identifier else '禁用'}")
            
            self.initialized = True
            logger.info("简化数字孪生系统初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False
    
    def run_step(self, current_time: float) -> Dict[str, Any]:
        """运行一个仿真步骤"""
        if not self.initialized:
            raise RuntimeError("系统未初始化")
        
        try:
            # 1. 生成传感器数据
            raw_sensor_data = self.sensor_simulator.generate_sensor_data(current_time)
            
            # 2. 数据预处理
            processed_data = self.data_preprocessor.process_data(raw_sensor_data)
            
            # 3. 模型预测
            model_predictions = self.physical_model.predict(processed_data)
            
            # 4. 故障检测
            fault_status = {}
            if self.fault_detector:
                fault_status = self.fault_detector.detect_faults(processed_data, model_predictions)
            else:
                fault_status = {sensor: "正常" for sensor in processed_data}
            
            # 5. 系统辨识
            identified_params = {}
            if self.system_identifier:
                identified_params = self.system_identifier.update_parameters(
                    processed_data, model_predictions)
                self.physical_model.update_parameters(identified_params)
            else:
                identified_params = self.physical_model.current_parameters.copy()
            
            # 返回步骤结果
            return {
                "raw_sensor_data": raw_sensor_data,
                "processed_data": processed_data,
                "model_predictions": model_predictions,
                "fault_status": fault_status,
                "identified_params": identified_params,
                "timestamp": current_time
            }
            
        except Exception as e:
            logger.error(f"仿真步骤执行失败 (t={current_time}): {e}")
            raise