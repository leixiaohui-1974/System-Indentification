#!/usr/bin/env python3
"""
数字孪生水力系统 - 基础配置

本配置文件包含了用于基础概念演示的参数设置。
为演示目的，参数已简化并添加了详细注释。

作者: 数字孪生团队
日期: 2024
"""

import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class BasicDemoConfig:
    """基础演示配置类"""
    
    # ============ 仿真基础参数 ============
    SIMULATION_TIME_STEP: float = 1.0  # 仿真时间步长 (秒)
    TOTAL_SIMULATION_TIME: float = 100.0  # 总仿真时间 (秒)
    OUTPUT_INTERVAL: int = 1  # 输出间隔 (步)
    
    # ============ 传感器配置 ============
    # 传感器噪声水平
    NOISE_LEVEL_WATER_LEVEL: float = 0.005  # 水位传感器噪声标准差 (m)
    NOISE_LEVEL_FLOW: float = 0.01  # 流量传感器噪声标准差 (m³/s)
    
    # 传感器位置信息
    SENSOR_LOCATIONS: Dict[str, str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.SENSOR_LOCATIONS is None:
            self.SENSOR_LOCATIONS = {
                "h_gate_up": "闸门上游水位",
                "h_gate_down": "闸门下游水位", 
                "q_gate_down": "闸门下游流量",
                "h_channel_mid": "渠道中段水位",
                "q_channel_end": "渠道末端流量"
            }
    
    # ============ 数据预处理参数 ============
    FILTER_TYPE: str = "moving_average"  # 滤波器类型
    FILTER_WINDOW_SIZE: int = 5  # 滑动窗口大小
    
    # ============ 故障检测参数 ============
    # 噪声检测
    NOISE_FACTOR_THRESHOLD: float = 3.0  # 噪声检测阈值倍数
    
    # 漂移检测
    DRIFT_THRESHOLD_H: float = 0.1  # 水位传感器漂移阈值 (m)
    DRIFT_THRESHOLD_Q: float = 1.0  # 流量传感器漂移阈值 (m³/s)
    EMA_ALPHA: float = 0.05  # 指数移动平均平滑因子
    
    # 卡死检测
    STUCK_THRESHOLD_H: float = 0.01  # 水位变化阈值 (m)
    STUCK_THRESHOLD_Q: float = 0.1   # 流量变化阈值 (m³/s)
    
    # ============ 系统辨识参数 ============
    # RLS参数
    RLS_FORGETTING_FACTOR: float = 0.95  # 遗忘因子
    RLS_INITIAL_COVARIANCE: float = 1000.0  # 初始协方差
    
    # EKF参数
    EKF_PROCESS_NOISE_Q: float = 0.01  # 过程噪声协方差
    EKF_MEASUREMENT_NOISE_R: float = 0.1  # 观测噪声协方差
    
    # ============ 模型参数 ============
    # 物理参数初始值
    MANNING_COEFFICIENT_INITIAL: float = 0.025  # 曼宁糙率系数
    GATE_COEFFICIENT_INITIAL: float = 0.65     # 闸门流量系数
    CHANNEL_SLOPE: float = 0.001               # 渠道坡度
    
    # 几何参数
    CHANNEL_LENGTH: float = 1000.0  # 渠道长度 (m)
    CHANNEL_WIDTH: float = 10.0     # 渠道宽度 (m)
    GATE_WIDTH: float = 8.0         # 闸门宽度 (m)
    
    # ============ 可视化参数 ============
    PLOT_STYLE: str = "seaborn"  # 绘图风格
    FIGURE_SIZE: tuple = (12, 8)  # 图像尺寸
    DPI: int = 300               # 图像分辨率
    
    # 颜色配置
    COLOR_SCHEME: Dict[str, str] = None
    
    def __post_init_colors__(self):
        """初始化颜色方案"""
        if self.COLOR_SCHEME is None:
            self.COLOR_SCHEME = {
                "water_level": "#2E86AB",  # 蓝色
                "flow_rate": "#A23B72",    # 紫红色
                "normal": "#43AA8B",       # 绿色
                "warning": "#F18F01",      # 橙色
                "error": "#C73E1D"         # 红色
            }
    
    # ============ 文件路径配置 ============
    def get_output_dir(self) -> str:
        """获取输出目录"""
        return os.path.join(os.path.dirname(__file__), "output")
    
    def get_data_dir(self) -> str:
        """获取数据目录"""
        return os.path.join(os.path.dirname(__file__), "data")
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        for dir_path in [self.get_output_dir(), self.get_data_dir()]:
            os.makedirs(dir_path, exist_ok=True)

# ============ 演示场景配置 ============
class DemoScenarios:
    """演示场景配置"""
    
    @staticmethod
    def get_normal_scenario() -> Dict[str, Any]:
        """正常运行场景"""
        return {
            "name": "正常运行",
            "description": "所有组件正常工作",
            "sensor_noise_multiplier": 1.0,
            "fault_injection": False,
            "parameter_drift": False
        }
    
    @staticmethod
    def get_noisy_scenario() -> Dict[str, Any]:
        """噪声增大场景"""
        return {
            "name": "噪声增大",
            "description": "传感器噪声显著增加",
            "sensor_noise_multiplier": 5.0,
            "fault_injection": True,
            "fault_type": "noise"
        }
    
    @staticmethod
    def get_drift_scenario() -> Dict[str, Any]:
        """传感器漂移场景"""
        return {
            "name": "传感器漂移",
            "description": "传感器读数逐渐偏离真值",
            "sensor_noise_multiplier": 1.0,
            "fault_injection": True,
            "fault_type": "drift",
            "drift_rate": 0.01  # m/step 或 m³/s/step
        }
    
    @staticmethod
    def get_stuck_scenario() -> Dict[str, Any]:
        """传感器卡死场景"""
        return {
            "name": "传感器卡死",
            "description": "传感器读数停止变化",
            "sensor_noise_multiplier": 0.1,
            "fault_injection": True,
            "fault_type": "stuck"
        }

# ============ 全局配置实例 ============
# 创建默认配置实例
demo_config = BasicDemoConfig()
demo_config.__post_init__()
demo_config.__post_init_colors__()

# ============ 辅助函数 ============
def print_config_summary():
    """打印配置摘要"""
    print("="*50)
    print("基础演示配置摘要")
    print("="*50)
    
    print(f"仿真时间步长: {demo_config.SIMULATION_TIME_STEP} 秒")
    print(f"总仿真时间: {demo_config.TOTAL_SIMULATION_TIME} 秒")
    print(f"传感器数量: {len(demo_config.SENSOR_LOCATIONS)}")
    print(f"滤波窗口大小: {demo_config.FILTER_WINDOW_SIZE}")
    print(f"噪声检测阈值: {demo_config.NOISE_FACTOR_THRESHOLD}x")
    
    print(f"\n物理参数:")
    print(f"  曼宁系数: {demo_config.MANNING_COEFFICIENT_INITIAL}")
    print(f"  闸门系数: {demo_config.GATE_COEFFICIENT_INITIAL}")
    print(f"  渠道坡度: {demo_config.CHANNEL_SLOPE}")
    
    print(f"\n传感器位置:")
    for sensor, location in demo_config.SENSOR_LOCATIONS.items():
        print(f"  {sensor}: {location}")

def get_demo_scenario(scenario_name: str) -> Dict[str, Any]:
    """获取演示场景配置"""
    scenarios = {
        "normal": DemoScenarios.get_normal_scenario(),
        "noisy": DemoScenarios.get_noisy_scenario(),
        "drift": DemoScenarios.get_drift_scenario(),
        "stuck": DemoScenarios.get_stuck_scenario()
    }
    
    return scenarios.get(scenario_name, scenarios["normal"])

if __name__ == "__main__":
    # 演示配置使用
    print_config_summary()
    
    print(f"\n可用演示场景:")
    for scenario_name in ["normal", "noisy", "drift", "stuck"]:
        scenario = get_demo_scenario(scenario_name)
        print(f"  {scenario_name}: {scenario['description']}")
    
    # 确保输出目录存在
    demo_config.ensure_directories()
    print(f"\n✓ 输出目录已创建: {demo_config.get_output_dir()}")
    print(f"✓ 数据目录已创建: {demo_config.get_data_dir()}")