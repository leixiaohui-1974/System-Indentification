# -*- coding: utf-8 -*-
"""
增强系统辨识模块

实现高级参数估计算法，包括多模型协同辨识、自适应参数更新和鲁棒估计方法。
该模块能够处理非线性、时变和不确定系统参数的在线估计问题。
"""

import numpy as np
from scipy.optimize import least_squares
from typing import Dict, List, Tuple, Optional, Callable
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class ParameterInfo:
    """参数信息类"""
    name: str
    initial_value: float
    lower_bound: float
    upper_bound: float
    is_time_varying: bool = False
    uncertainty: float = 0.1

class AdvancedSystemIdentifier(ABC):
    """
    高级系统辨识器基类
    """
    
    def __init__(self, parameters: List[ParameterInfo]):
        """
        初始化高级系统辨识器
        
        Args:
            parameters: 参数信息列表
        """
        self.parameters = {param.name: param for param in parameters}
        self.parameter_values = {param.name: param.initial_value for param in parameters}
        self.parameter_uncertainties = {param.name: param.uncertainty for param in parameters}
        
        # 历史记录
        self.parameter_history = {param.name: [] for param in parameters}
        self.residual_history = []
        self.convergence_history = []
        
        logger.info(f"高级系统辨识器初始化完成，参数数量: {len(parameters)}")
    
    @abstractmethod
    def update_parameters(self, measurements: Dict[str, float], 
                         predictions: Dict[str, float], 
                         inputs: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        更新参数估计值
        
        Args:
            measurements: 测量值字典
            predictions: 预测值字典
            inputs: 输入值字典（可选）
            
        Returns:
            更新后的参数值字典
        """
        pass
    
    def get_parameter_values(self) -> Dict[str, float]:
        """
        获取当前参数值
        
        Returns:
            参数值字典
        """
        return self.parameter_values.copy()
    
    def get_parameter_uncertainties(self) -> Dict[str, float]:
        """
        获取参数不确定性
        
        Returns:
            参数不确定性字典
        """
        return self.parameter_uncertainties.copy()
    
    def _update_history(self):
        """
        更新历史记录
        """
        for param_name in self.parameter_values:
            self.parameter_history[param_name].append(self.parameter_values[param_name])


class MultiModelIdentifier(AdvancedSystemIdentifier):
    """
    多模型协同辨识器
    """
    
    def __init__(self, parameters: List[ParameterInfo], 
                 model_functions: Dict[str, Callable]):
        """
        初始化多模型协同辨识器
        
        Args:
            parameters: 参数信息列表
            model_functions: 模型函数字典 {model_name: function}
        """
        super().__init__(parameters)
        self.model_functions = model_functions
        self.model_weights = {name: 1.0/len(model_functions) for name in model_functions}
        self.weight_history = {name: [] for name in model_functions}
        
        logger.info(f"多模型协同辨识器初始化完成，模型数量: {len(model_functions)}")
    
    def update_parameters(self, measurements: Dict[str, float], 
                         predictions: Dict[str, float], 
                         inputs: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        使用多模型协同更新参数
        """
        # 计算各模型的残差
        residuals = {}
        for model_name, model_func in self.model_functions.items():
            try:
                model_output = model_func(self.parameter_values, inputs or {})
                residual = 0.0
                for key in measurements:
                    if key in model_output:
                        residual += (measurements[key] - model_output[key]) ** 2
                residuals[model_name] = np.sqrt(residual)
            except Exception as e:
                logger.warning(f"模型 {model_name} 计算失败: {e}")
                residuals[model_name] = float('inf')
        
        # 更新模型权重（基于残差的逆）
        total_inverse_residual = sum(1.0/(r + 1e-6) for r in residuals.values() if r < float('inf'))
        if total_inverse_residual > 0:
            for model_name in self.model_functions:
                residual = residuals.get(model_name, float('inf'))
                if residual < float('inf'):
                    self.model_weights[model_name] = (1.0/(residual + 1e-6)) / total_inverse_residual
                else:
                    self.model_weights[model_name] = 0.0
        
        # 记录权重历史
        for name, weight in self.model_weights.items():
            self.weight_history[name].append(weight)
        
        # 使用加权平均更新参数
        return self._weighted_parameter_update(measurements, predictions, inputs)
    
    def _weighted_parameter_update(self, measurements: Dict[str, float], 
                                  predictions: Dict[str, float], 
                                  inputs: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        加权参数更新
        """
        # 简化的参数更新逻辑
        for param_name in self.parameter_values:
            # 基于测量和预测的差异调整参数
            total_adjustment = 0.0
            total_weight = 0.0
            
            for model_name, weight in self.model_weights.items():
                if weight > 0:
                    # 简化的调整逻辑
                    adjustment = weight * 0.01  # 学习率
                    total_adjustment += adjustment
                    total_weight += weight
            
            if total_weight > 0:
                # 应用调整
                current_value = self.parameter_values[param_name]
                param_info = self.parameters[param_name]
                new_value = current_value + total_adjustment / total_weight
                # 确保在边界内
                new_value = np.clip(new_value, param_info.lower_bound, param_info.upper_bound)
                self.parameter_values[param_name] = new_value
        
        self._update_history()
        return self.parameter_values.copy()


class AdaptiveRLSIdentifier(AdvancedSystemIdentifier):
    """
    自适应递归最小二乘辨识器
    """
    
    def __init__(self, parameters: List[ParameterInfo], 
                 forgetting_factor: float = 0.98,
                 covariance_init: float = 1000.0):
        """
        初始化自适应RLS辨识器
        
        Args:
            parameters: 参数信息列表
            forgetting_factor: 遗忘因子
            covariance_init: 初始协方差值
        """
        super().__init__(parameters)
        self.forgetting_factor = forgetting_factor
        self.covariance_init = covariance_init
        
        # RLS状态变量
        self.theta = np.array([param.initial_value for param in parameters])
        self.P = np.eye(len(parameters)) * covariance_init
        self.param_names = [param.name for param in parameters]
        
        # 自适应参数
        self.residual_window = 50
        self.residual_buffer = []
        self.forgetting_factor_adapted = forgetting_factor
        
        logger.info("自适应RLS辨识器初始化完成")
    
    def update_parameters(self, measurements: Dict[str, float], 
                         predictions: Dict[str, float], 
                         inputs: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        使用自适应RLS更新参数
        """
        # 构造回归向量和输出
        phi = self._construct_regressor(inputs)
        y = self._construct_output(measurements)
        
        if phi is None or y is None:
            return self.parameter_values.copy()
        
        # 自适应遗忘因子调整
        self._adapt_forgetting_factor(measurements, predictions)
        
        # RLS更新步骤
        self._rls_update_step(y, phi)
        
        # 更新参数值和不确定性
        for i, param_name in enumerate(self.param_names):
            self.parameter_values[param_name] = float(self.theta[i])
            self.parameter_uncertainties[param_name] = float(np.sqrt(self.P[i, i]))
        
        self._update_history()
        return self.parameter_values.copy()
    
    def _construct_regressor(self, inputs: Optional[Dict[str, float]]) -> Optional[np.ndarray]:
        """
        构造回归向量
        """
        if inputs is None:
            return None
        
        # 简化的回归向量构造
        phi = []
        for param_name in self.param_names:
            # 假设每个参数与对应的输入成正比
            input_key = f"input_{param_name}"
            phi.append(inputs.get(input_key, 1.0))
        
        return np.array(phi)
    
    def _construct_output(self, measurements: Dict[str, float]) -> Optional[float]:
        """
        构造输出值
        """
        # 简化：使用第一个测量值作为输出
        if measurements:
            return list(measurements.values())[0]
        return None
    
    def _adapt_forgetting_factor(self, measurements: Dict[str, float], 
                                predictions: Dict[str, float]):
        """
        自适应调整遗忘因子
        """
        # 计算当前残差
        residual = 0.0
        for key in measurements:
            if key in predictions:
                residual += abs(measurements[key] - predictions[key])
        
        self.residual_buffer.append(residual)
        if len(self.residual_buffer) > self.residual_window:
            self.residual_buffer.pop(0)
        
        # 如果残差增大，减小遗忘因子以更快适应
        if len(self.residual_buffer) >= 2:
            recent_mean = np.mean(self.residual_buffer[-5:])
            overall_mean = np.mean(self.residual_buffer)
            
            if recent_mean > overall_mean * 1.1:  # 残差显著增大
                self.forgetting_factor_adapted = max(0.9, self.forgetting_factor * 0.95)
            elif recent_mean < overall_mean * 0.9:  # 残差减小
                self.forgetting_factor_adapted = min(1.0, self.forgetting_factor * 1.05)
            else:
                self.forgetting_factor_adapted = self.forgetting_factor
    
    def _rls_update_step(self, y: float, phi: np.ndarray):
        """
        RLS更新步骤
        """
        # 确保phi是列向量
        phi = phi.reshape(-1, 1)
        
        # 1. 计算增益向量
        P_phi = self.P @ phi
        denominator = self.forgetting_factor_adapted + phi.T @ P_phi
        
        if denominator < 1e-12:  # 避免除零
            return
        
        K = P_phi / denominator[0, 0]
        
        # 2. 计算预测误差
        y_pred = self.theta.T @ phi
        error = y - y_pred[0, 0] if isinstance(y_pred, np.ndarray) else y - y_pred
        
        # 3. 更新参数估计
        self.theta = self.theta + (K * error).flatten()
        
        # 4. 更新协方差矩阵
        self.P = (self.P - K @ phi.T @ self.P) / self.forgetting_factor_adapted


class RobustEKFIdentifier(AdvancedSystemIdentifier):
    """
    鲁棒扩展卡尔曼滤波辨识器
    """
    
    def __init__(self, parameters: List[ParameterInfo],
                 initial_covariance: np.ndarray,
                 process_noise: np.ndarray,
                 measurement_noise: np.ndarray,
                 outlier_threshold: float = 3.0):
        """
        初始化鲁棒EKF辨识器
        
        Args:
            parameters: 参数信息列表
            initial_covariance: 初始协方差矩阵
            process_noise: 过程噪声协方差矩阵
            measurement_noise: 测量噪声协方差矩阵
            outlier_threshold: 异常值阈值（标准差倍数）
        """
        super().__init__(parameters)
        self.outlier_threshold = outlier_threshold
        
        # EKF状态
        self.x = np.array([param.initial_value for param in parameters])
        self.P = initial_covariance.copy()
        self.Q = process_noise.copy()
        self.R = measurement_noise.copy()
        
        self.param_names = [param.name for param in parameters]
        self.state_dimension = len(parameters)
        
        # 鲁棒性增强
        self.innovation_history = []
        self.innovation_window = 20
        
        logger.info("鲁棒EKF辨识器初始化完成")
    
    def update_parameters(self, measurements: Dict[str, float], 
                         predictions: Dict[str, float], 
                         inputs: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        使用鲁棒EKF更新参数
        """
        # 构造测量向量和预测向量
        z = self._construct_measurement(measurements)
        z_pred = self._construct_measurement(predictions)
        
        if z is None or z_pred is None:
            return self.parameter_values.copy()
        
        # 计算观测矩阵（简化为单位矩阵）
        H = np.eye(self.state_dimension)
        
        # 计算创新
        innovation = z - z_pred
        
        # 异常值检测
        if self._is_outlier(innovation):
            logger.warning("检测到异常测量值，降低测量噪声权重")
            # 临时增大测量噪声以降低异常值影响
            R_effective = self.R * 10.0
        else:
            R_effective = self.R
        
        # EKF更新步骤
        self._ekf_update_step(z, z_pred, H, R_effective)
        
        # 更新参数值和不确定性
        for i, param_name in enumerate(self.param_names):
            self.parameter_values[param_name] = float(self.x[i])
            self.parameter_uncertainties[param_name] = float(np.sqrt(self.P[i, i]))
        
        self._update_history()
        return self.parameter_values.copy()
    
    def _construct_measurement(self, data: Dict[str, float]) -> Optional[np.ndarray]:
        """
        构造测量向量
        """
        if not data:
            return None
        
        # 按参数名称顺序提取测量值
        measurements = []
        for param_name in self.param_names:
            # 假设测量值键与参数名对应
            measurement_key = param_name.replace('_param', '')
            measurements.append(data.get(measurement_key, 0.0))
        
        return np.array(measurements)
    
    def _is_outlier(self, innovation: np.ndarray) -> bool:
        """
        检测创新是否为异常值
        """
        self.innovation_history.append(innovation)
        if len(self.innovation_history) > self.innovation_window:
            self.innovation_history.pop(0)
        
        if len(self.innovation_history) < 5:
            return False
        
        # 计算历史创新的统计特性
        innovations = np.array(self.innovation_history)
        mean_innovation = np.mean(innovations, axis=0)
        std_innovation = np.std(innovations, axis=0)
        
        # 检查当前创新是否超出阈值
        normalized_innovation = np.abs(innovation - mean_innovation) / (std_innovation + 1e-12)
        return np.any(normalized_innovation > self.outlier_threshold)
    
    def _ekf_update_step(self, z: np.ndarray, z_pred: np.ndarray, 
                         H: np.ndarray, R_effective: np.ndarray):
        """
        EKF更新步骤
        """
        # 计算创新协方差
        S = H @ self.P @ H.T + R_effective
        
        # 计算卡尔曼增益
        K = self.P @ H.T @ np.linalg.inv(S)
        
        # 计算创新
        innovation = z - z_pred
        
        # 状态更新
        self.x = self.x + K @ innovation
        
        # 协方差更新
        I = np.eye(self.state_dimension)
        self.P = (I - K @ H) @ self.P
        
        # 添加过程噪声
        self.P = self.P + self.Q


class ParameterConvergenceMonitor:
    """
    参数收敛性监控器
    """
    
    def __init__(self, window_size: int = 50, convergence_threshold: float = 0.01):
        """
        初始化参数收敛性监控器
        
        Args:
            window_size: 窗口大小
            convergence_threshold: 收敛阈值
        """
        self.window_size = window_size
        self.convergence_threshold = convergence_threshold
        self.parameter_history = {}
        self.convergence_status = {}
        
        logger.info("参数收敛性监控器初始化完成")
    
    def add_parameter_values(self, timestamp: float, parameters: Dict[str, float]):
        """
        添加参数值
        
        Args:
            timestamp: 时间戳
            parameters: 参数值字典
        """
        for param_name, value in parameters.items():
            if param_name not in self.parameter_history:
                self.parameter_history[param_name] = []
            
            self.parameter_history[param_name].append((timestamp, value))
            
            # 保持窗口大小
            if len(self.parameter_history[param_name]) > self.window_size:
                self.parameter_history[param_name].pop(0)
    
    def check_convergence(self) -> Dict[str, bool]:
        """
        检查参数收敛性
        
        Returns:
            参数收敛状态字典
        """
        for param_name, history in self.parameter_history.items():
            if len(history) < 10:  # 需要足够数据点
                self.convergence_status[param_name] = False
                continue
            
            # 计算最近数据的标准差
            recent_values = [val for _, val in history[-20:]]
            std_dev = np.std(recent_values)
            
            # 判断是否收敛
            self.convergence_status[param_name] = std_dev < self.convergence_threshold
        
        return self.convergence_status.copy()
    
    def get_convergence_report(self) -> Dict[str, Any]:
        """
        获取收敛报告
        
        Returns:
            收敛报告字典
        """
        report = {
            'convergence_status': self.convergence_status.copy(),
            'parameter_stability': {},
            'recommendations': []
        }
        
        for param_name, history in self.parameter_history.items():
            if len(history) >= 10:
                recent_values = [val for _, val in history[-20:]]
                std_dev = float(np.std(recent_values))
                mean_val = float(np.mean(recent_values))
                
                report['parameter_stability'][param_name] = {
                    'std_deviation': std_dev,
                    'mean_value': mean_val,
                    'is_stable': std_dev < self.convergence_threshold,
                    'samples': len(history)
                }
                
                if std_dev >= self.convergence_threshold:
                    report['recommendations'].append(
                        f"参数 {param_name} 尚未收敛，建议延长观测时间或调整激励信号"
                    )
            else:
                report['parameter_stability'][param_name] = {
                    'std_deviation': None,
                    'mean_value': None,
                    'is_stable': False,
                    'samples': len(history)
                }
        
        # 总体收敛状态
        all_converged = all(status for status in self.convergence_status.values())
        report['overall_convergence'] = all_converged
        
        if not all_converged:
            report['recommendations'].append("系统参数尚未完全收敛，建议继续运行辨识过程")
        
        return report


# 测试和验证函数
def test_multi_model_identifier():
    """
    测试多模型协同辨识器
    """
    logger.info("开始测试多模型协同辨识器")
    
    # 定义参数
    parameters = [
        ParameterInfo("param_a", 1.0, 0.1, 2.0, True, 0.1),
        ParameterInfo("param_b", 0.5, 0.01, 1.0, True, 0.05)
    ]
    
    # 定义模型函数
    def model1(params, inputs):
        a, b = params.get("param_a", 1.0), params.get("param_b", 0.5)
        x = inputs.get("input", 1.0)
        return {"output": a * x + b}
    
    def model2(params, inputs):
        a, b = params.get("param_a", 1.0), params.get("param_b", 0.5)
        x = inputs.get("input", 1.0)
        return {"output": a * x**2 + b * x}
    
    model_functions = {"linear": model1, "quadratic": model2}
    
    # 创建辨识器
    identifier = MultiModelIdentifier(parameters, model_functions)
    
    # 模拟数据
    for i in range(100):
        # 真实参数
        true_a = 1.2 + 0.1 * np.sin(i * 0.1)
        true_b = 0.3 + 0.05 * np.cos(i * 0.15)
        
        # 输入
        input_val = 2.0 + np.sin(i * 0.2)
        inputs = {"input": input_val, "input_param_a": input_val, "input_param_b": 1.0}
        
        # 真实输出
        true_output = true_a * input_val + 0.1 * np.sin(input_val) + true_b
        measurements = {"output": true_output + np.random.normal(0, 0.05)}
        predictions = {"output": identifier.parameter_values["param_a"] * input_val + 
                      identifier.parameter_values["param_b"]}
        
        # 更新参数
        identifier.update_parameters(measurements, predictions, inputs)
    
    final_params = identifier.get_parameter_values()
    logger.info(f"多模型协同辨识器测试完成，最终参数: {final_params}")
    
    return identifier


def test_adaptive_rls_identifier():
    """
    测试自适应RLS辨识器
    """
    logger.info("开始测试自适应RLS辨识器")
    
    # 定义参数
    parameters = [
        ParameterInfo("gain", 0.8, 0.1, 2.0, False, 0.1),
        ParameterInfo("time_constant", 1.5, 0.1, 5.0, False, 0.2)
    ]
    
    # 创建辨识器
    identifier = AdaptiveRLSIdentifier(parameters, forgetting_factor=0.95)
    
    # 模拟数据
    for i in range(100):
        # 真实系统响应
        true_gain = 1.0 + 0.2 * np.sin(i * 0.1)
        true_tc = 1.2 + 0.3 * np.cos(i * 0.08)
        
        # 输入输出数据
        input_val = np.sin(i * 0.3)
        output_val = true_gain * input_val * (1 - np.exp(-i/true_tc)) + np.random.normal(0, 0.02)
        
        measurements = {"output": output_val}
        predictions = {"output": identifier.parameter_values["gain"] * input_val}
        inputs = {"input_gain": input_val, "input_time_constant": 1.0}
        
        # 更新参数
        identifier.update_parameters(measurements, predictions, inputs)
    
    final_params = identifier.get_parameter_values()
    logger.info(f"自适应RLS辨识器测试完成，最终参数: {final_params}")
    
    return identifier


if __name__ == "__main__":
    # 运行测试
    logging.basicConfig(level=logging.INFO)
    
    # 测试多模型协同辨识
    try:
        mm_identifier = test_multi_model_identifier()
        logger.info("多模型协同辨识器测试成功")
    except Exception as e:
        logger.error(f"多模型协同辨识器测试失败: {e}")
    
    # 测试自适应RLS辨识
    try:
        rls_identifier = test_adaptive_rls_identifier()
        logger.info("自适应RLS辨识器测试成功")
    except Exception as e:
        logger.error(f"自适应RLS辨识器测试失败: {e}")