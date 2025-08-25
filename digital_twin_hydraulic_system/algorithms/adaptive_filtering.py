# -*- coding: utf-8 -*-
"""
自适应滤波算法模块

实现高级滤波技术，包括自适应卡尔曼滤波、粒子滤波和多传感器数据融合算法。
这些算法将提高系统在复杂环境下的数据处理能力和鲁棒性。
"""

import numpy as np
from scipy.linalg import sqrtm
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class AdaptiveKalmanFilter:
    """
    自适应卡尔曼滤波器，能够根据系统噪声特性自动调整滤波参数
    """
    
    def __init__(self, initial_state: np.ndarray, initial_covariance: np.ndarray, 
                 process_noise_base: np.ndarray, measurement_noise_base: np.ndarray):
        """
        初始化自适应卡尔曼滤波器
        
        Args:
            initial_state: 初始状态向量
            initial_covariance: 初始协方差矩阵
            process_noise_base: 基础过程噪声协方差矩阵
            measurement_noise_base: 基础测量噪声协方差矩阵
        """
        self.state = initial_state.copy()
        self.covariance = initial_covariance.copy()
        self.process_noise_base = process_noise_base.copy()
        self.measurement_noise_base = measurement_noise_base.copy()
        
        # 自适应参数
        self.adaptation_window = 50  # 用于噪声估计的窗口大小
        self.innovation_history = []
        self.residual_history = []
        
        # 噪声估计参数
        self.process_noise_scale = 1.0
        self.measurement_noise_scale = 1.0
        
        logger.info("自适应卡尔曼滤波器初始化完成")
    
    def predict(self, transition_matrix: np.ndarray, control_matrix: Optional[np.ndarray] = None, 
                control_input: Optional[np.ndarray] = None):
        """
        预测步骤
        
        Args:
            transition_matrix: 状态转移矩阵
            control_matrix: 控制矩阵（可选）
            control_input: 控制输入（可选）
        """
        # 状态预测
        self.state = transition_matrix @ self.state
        if control_matrix is not None and control_input is not None:
            self.state += control_matrix @ control_input
        
        # 协方差预测
        self.covariance = transition_matrix @ self.covariance @ transition_matrix.T + \
                         self.process_noise_scale * self.process_noise_base
    
    def update(self, measurement: np.ndarray, observation_matrix: np.ndarray, 
               measurement_noise_override: Optional[np.ndarray] = None):
        """
        更新步骤
        
        Args:
            measurement: 测量值
            observation_matrix: 观测矩阵
            measurement_noise_override: 测量噪声协方差矩阵覆盖（可选）
        """
        # 计算卡尔曼增益
        measurement_noise = measurement_noise_override if measurement_noise_override is not None \
                           else self.measurement_noise_scale * self.measurement_noise_base
                           
        innovation_covariance = observation_matrix @ self.covariance @ observation_matrix.T + measurement_noise
        kalman_gain = self.covariance @ observation_matrix.T @ np.linalg.inv(innovation_covariance)
        
        # 状态更新
        predicted_measurement = observation_matrix @ self.state
        innovation = measurement - predicted_measurement
        self.state = self.state + kalman_gain @ innovation
        
        # 协方差更新
        identity = np.eye(self.covariance.shape[0])
        self.covariance = (identity - kalman_gain @ observation_matrix) @ self.covariance
        
        # 存储创新用于自适应调整
        self.innovation_history.append(innovation)
        if len(self.innovation_history) > self.adaptation_window:
            self.innovation_history.pop(0)
        
        # 自适应调整噪声参数
        self._adapt_noise_parameters()
    
    def _adapt_noise_parameters(self):
        """
        根据创新序列自适应调整噪声参数
        """
        if len(self.innovation_history) < self.adaptation_window:
            return
        
        # 计算创新协方差
        innovations = np.array(self.innovation_history)
        empirical_covariance = np.cov(innovations.T)
        
        # 计算理论创新协方差
        # 这里简化处理，实际应用中需要根据具体的观测矩阵计算
        theoretical_covariance = self.measurement_noise_scale * self.measurement_noise_base
        
        # 计算噪声比例因子
        if np.linalg.det(theoretical_covariance) > 1e-12:
            # 使用协方差矩阵的迹来估计比例因子
            trace_empirical = np.trace(empirical_covariance)
            trace_theoretical = np.trace(theoretical_covariance)
            
            if trace_theoretical > 1e-12:
                ratio = trace_empirical / trace_theoretical
                # 限制调整范围，避免过度调整
                self.measurement_noise_scale = np.clip(ratio, 0.1, 10.0)
    
    def get_state(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取当前状态和协方差
        
        Returns:
            (state, covariance): 状态向量和协方差矩阵
        """
        return self.state.copy(), self.covariance.copy()


class ParticleFilter:
    """
    粒子滤波器，适用于非线性非高斯系统的状态估计
    """
    
    def __init__(self, num_particles: int, state_dimension: int, 
                 initial_state_mean: np.ndarray, initial_state_cov: np.ndarray):
        """
        初始化粒子滤波器
        
        Args:
            num_particles: 粒子数量
            state_dimension: 状态维度
            initial_state_mean: 初始状态均值
            initial_state_cov: 初始状态协方差
        """
        self.num_particles = num_particles
        self.state_dimension = state_dimension
        
        # 初始化粒子
        self.particles = np.random.multivariate_normal(
            initial_state_mean, initial_state_cov, num_particles
        )
        
        # 初始化权重（均匀分布）
        self.weights = np.ones(num_particles) / num_particles
        
        logger.info(f"粒子滤波器初始化完成，粒子数: {num_particles}")
    
    def predict(self, process_model, process_noise_cov: np.ndarray):
        """
        预测步骤
        
        Args:
            process_model: 状态转移函数，接受状态和噪声作为参数
            process_noise_cov: 过程噪声协方差矩阵
        """
        # 为每个粒子添加过程噪声
        noise = np.random.multivariate_normal(
            np.zeros(self.state_dimension), process_noise_cov, self.num_particles
        )
        
        # 应用状态转移模型
        for i in range(self.num_particles):
            self.particles[i] = process_model(self.particles[i]) + noise[i]
    
    def update(self, measurement: np.ndarray, measurement_model, 
               measurement_noise_cov: np.ndarray):
        """
        更新步骤
        
        Args:
            measurement: 测量值
            measurement_model: 观测函数
            measurement_noise_cov: 测量噪声协方差矩阵
        """
        # 计算每个粒子的权重
        for i in range(self.num_particles):
            predicted_measurement = measurement_model(self.particles[i])
            innovation = measurement - predicted_measurement
            
            # 计算似然（假设高斯噪声）
            likelihood = self._multivariate_gaussian(
                innovation, np.zeros_like(innovation), measurement_noise_cov
            )
            self.weights[i] *= likelihood
        
        # 归一化权重
        weight_sum = np.sum(self.weights)
        if weight_sum > 1e-12:
            self.weights /= weight_sum
        else:
            # 如果所有权重都很小，重新初始化
            self.weights = np.ones(self.num_particles) / self.num_particles
    
    def _multivariate_gaussian(self, x: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> float:
        """
        计算多维高斯分布的概率密度
        
        Args:
            x: 输入向量
            mean: 均值向量
            cov: 协方差矩阵
            
        Returns:
            概率密度值
        """
        d = len(x)
        cov_inv = np.linalg.inv(cov)
        cov_det = np.linalg.det(cov)
        
        if cov_det <= 0:
            return 0.0
        
        diff = x - mean
        exponent = -0.5 * diff.T @ cov_inv @ diff
        coefficient = 1.0 / np.sqrt((2 * np.pi) ** d * cov_det)
        
        return coefficient * np.exp(exponent)
    
    def resample(self):
        """
        重采样步骤，防止粒子退化
        """
        # 计算有效粒子数
        effective_particles = 1.0 / np.sum(self.weights ** 2)
        
        # 如果有效粒子数过少，进行重采样
        if effective_particles < self.num_particles / 2:
            # 使用系统重采样方法
            indices = self._systematic_resample()
            
            # 重采样粒子
            self.particles = self.particles[indices]
            
            # 重置权重
            self.weights = np.ones(self.num_particles) / self.num_particles
    
    def _systematic_resample(self) -> np.ndarray:
        """
        系统重采样方法
        
        Returns:
            重采样索引数组
        """
        # 生成累积权重
        cumulative_weights = np.cumsum(self.weights)
        
        # 生成随机起始点
        u = np.random.uniform(0, 1 / self.num_particles)
        
        # 生成均匀间隔的采样点
        samples = u + np.arange(self.num_particles) / self.num_particles
        
        # 选择粒子
        indices = np.zeros(self.num_particles, dtype=int)
        i, j = 0, 0
        while i < self.num_particles:
            while cumulative_weights[j] < samples[i]:
                j += 1
            indices[i] = j
            i += 1
        
        return indices
    
    def get_estimate(self) -> np.ndarray:
        """
        获取状态估计值（加权平均）
        
        Returns:
            状态估计值
        """
        return np.average(self.particles, weights=self.weights, axis=0)


class MultiSensorFusion:
    """
    多传感器数据融合器，融合来自不同传感器的信息
    """
    
    def __init__(self, sensor_weights: Dict[str, float]):
        """
        初始化多传感器融合器
        
        Args:
            sensor_weights: 传感器权重字典
        """
        self.sensor_weights = sensor_weights
        self.measurements = {}
        logger.info("多传感器融合器初始化完成")
    
    def add_measurement(self, sensor_id: str, measurement: float, timestamp: float):
        """
        添加传感器测量值
        
        Args:
            sensor_id: 传感器ID
            measurement: 测量值
            timestamp: 时间戳
        """
        if sensor_id not in self.sensor_weights:
            logger.warning(f"未知传感器 {sensor_id}，忽略测量值")
            return
        
        self.measurements[sensor_id] = {
            'value': measurement,
            'timestamp': timestamp
        }
    
    def get_fused_measurement(self) -> Tuple[float, float]:
        """
        获取融合后的测量值和不确定性
        
        Returns:
            (fused_value, uncertainty): 融合值和不确定性
        """
        if not self.measurements:
            return 0.0, float('inf')
        
        # 计算加权平均
        weighted_sum = 0.0
        weight_sum = 0.0
        weighted_squared_sum = 0.0
        
        for sensor_id, data in self.measurements.items():
            weight = self.sensor_weights.get(sensor_id, 0.0)
            if weight > 0:
                weighted_sum += weight * data['value']
                weight_sum += weight
                weighted_squared_sum += weight * (data['value'] ** 2)
        
        if weight_sum <= 0:
            return 0.0, float('inf')
        
        fused_value = weighted_sum / weight_sum
        
        # 计算融合值的方差
        if len(self.measurements) > 1:
            variance = (weighted_squared_sum / weight_sum) - (fused_value ** 2)
            uncertainty = np.sqrt(max(variance, 0)) / np.sqrt(len(self.measurements))
        else:
            uncertainty = 0.1  # 默认不确定性
        
        return fused_value, uncertainty
    
    def clear_measurements(self):
        """
        清除所有测量值
        """
        self.measurements.clear()


# 测试和验证函数
def test_adaptive_kalman_filter():
    """
    测试自适应卡尔曼滤波器
    """
    logger.info("开始测试自适应卡尔曼滤波器")
    
    # 初始化参数
    initial_state = np.array([0.0, 1.0])  # 位置和速度
    initial_covariance = np.eye(2) * 0.1
    process_noise = np.eye(2) * 0.01
    measurement_noise = np.eye(1) * 0.1
    
    # 创建滤波器
    akf = AdaptiveKalmanFilter(initial_state, initial_covariance, process_noise, measurement_noise)
    
    # 状态转移矩阵（匀速模型）
    dt = 1.0
    transition_matrix = np.array([[1, dt], [0, 1]])
    
    # 观测矩阵（只能观测位置）
    observation_matrix = np.array([[1, 0]])
    
    # 模拟数据
    true_positions = []
    measurements = []
    estimates = []
    
    # 真实轨迹
    position = 0.0
    velocity = 1.0
    
    for i in range(100):
        # 真实状态更新
        position += velocity * dt
        true_positions.append(position)
        
        # 生成测量值（带噪声）
        measurement = position + np.random.normal(0, 0.1)
        measurements.append(measurement)
        
        # 滤波器步骤
        akf.predict(transition_matrix)
        akf.update(np.array([measurement]), observation_matrix)
        
        # 获取估计值
        state, _ = akf.get_state()
        estimates.append(state[0])
    
    logger.info("自适应卡尔曼滤波器测试完成")
    return true_positions, measurements, estimates


def test_particle_filter():
    """
    测试粒子滤波器
    """
    logger.info("开始测试粒子滤波器")
    
    # 初始化参数
    num_particles = 100
    state_dimension = 2
    initial_mean = np.array([0.0, 1.0])
    initial_cov = np.eye(2) * 0.1
    
    # 创建粒子滤波器
    pf = ParticleFilter(num_particles, state_dimension, initial_mean, initial_cov)
    
    # 定义状态转移模型（非线性）
    def process_model(state):
        x, v = state
        # 非线性状态转移：x_k = x_{k-1} + v_{k-1}*dt + 0.1*sin(x_{k-1})
        dt = 1.0
        new_x = x + v * dt + 0.1 * np.sin(x)
        new_v = v + np.random.normal(0, 0.01)  # 速度随机变化
        return np.array([new_x, new_v])
    
    # 定义观测模型
    def measurement_model(state):
        x, v = state
        # 观测模型：z = x + 0.2*cos(x) + noise
        return x + 0.2 * np.cos(x)
    
    # 模拟数据
    true_states = []
    measurements = []
    estimates = []
    
    # 初始状态
    true_state = np.array([0.0, 1.0])
    
    for i in range(50):
        # 真实状态更新
        true_state = process_model(true_state)
        true_states.append(true_state.copy())
        
        # 生成测量值
        true_measurement = measurement_model(true_state)
        measurement = true_measurement + np.random.normal(0, 0.1)
        measurements.append(measurement)
        
        # 粒子滤波器步骤
        pf.predict(process_model, np.eye(2) * 0.01)
        pf.update(np.array([measurement]), measurement_model, np.eye(1) * 0.1)
        pf.resample()
        
        # 获取估计值
        estimate = pf.get_estimate()
        estimates.append(estimate.copy())
    
    logger.info("粒子滤波器测试完成")
    return true_states, measurements, estimates


if __name__ == "__main__":
    # 运行测试
    logging.basicConfig(level=logging.INFO)
    
    # 测试自适应卡尔曼滤波
    try:
        true_pos, meas, est = test_adaptive_kalman_filter()
        logger.info(f"自适应卡尔曼滤波测试结果 - 真实值: {true_pos[-1]:.3f}, 估计值: {est[-1]:.3f}")
    except Exception as e:
        logger.error(f"自适应卡尔曼滤波测试失败: {e}")
    
    # 测试粒子滤波
    try:
        true_states, meas, est = test_particle_filter()
        logger.info(f"粒子滤波测试结果 - 真实位置: {true_states[-1][0]:.3f}, 估计位置: {est[-1][0]:.3f}")
    except Exception as e:
        logger.error(f"粒子滤波测试失败: {e}")