#!/usr/bin/env python3
"""
快速开始配置文件

为快速开始示例提供的配置参数，支持不同的仿真场景。

作者: 数字孪生团队
日期: 2024
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class QuickStartConfig:
    """快速开始配置类"""
    
    def __init__(self, scenario: str = "normal"):
        self.scenario = scenario
        self._setup_basic_config()
        self._setup_scenario_config(scenario)
    
    def _setup_basic_config(self):
        """设置基础配置"""
        # ============ 仿真基础参数 ============
        self.TIME_STEP: float = 1.0  # 时间步长 (秒)
        self.OUTPUT_INTERVAL: int = 1  # 输出间隔
        
        # ============ 传感器配置 ============
        self.SENSOR_LIST: List[str] = [
            "h_gate_up",      # 闸门上游水位
            "h_gate_down",    # 闸门下游水位
            "q_gate_down",    # 闸门下游流量
            "h_channel_mid",  # 渠道中段水位
            "q_channel_end"   # 渠道末端流量
        ]
        
        # 传感器噪声水平
        self.NOISE_LEVEL_H: float = 0.005  # 水位传感器噪声 (m)
        self.NOISE_LEVEL_Q: float = 0.01   # 流量传感器噪声 (m³/s)
        
        # ============ 数据预处理参数 ============
        self.FILTER_WINDOW_SIZE: int = 5  # 滑动窗口大小
        
        # ============ 故障检测参数 ============
        self.ENABLE_FAULT_DETECTION: bool = True
        self.NOISE_FACTOR_THRESHOLD: float = 3.0  # 噪声检测阈值倍数
        self.DRIFT_THRESHOLD_H: float = 0.1       # 水位漂移阈值 (m)
        self.DRIFT_THRESHOLD_Q: float = 1.0       # 流量漂移阈值 (m³/s)
        self.STUCK_THRESHOLD_H: float = 0.01      # 水位卡死阈值 (m)
        self.STUCK_THRESHOLD_Q: float = 0.1       # 流量卡死阈值 (m³/s)
        self.EMA_ALPHA: float = 0.05              # 指数移动平均因子
        
        # ============ 系统辨识参数 ============
        self.ENABLE_SYSTEM_ID: bool = True
        self.RLS_FORGETTING_FACTOR: float = 0.95     # RLS遗忘因子
        self.RLS_INITIAL_COVARIANCE: float = 1000.0  # 初始协方差
        
        # ============ 物理模型参数 ============
        self.MANNING_INITIAL: float = 0.025  # 初始曼宁系数
        self.GATE_COEFF_INITIAL: float = 0.65  # 初始闸门系数
        
        # ============ 故障注入参数 ============
        self.INJECT_FAULT: bool = False
        self.FAULT_INJECTION_TIME: float = 15.0  # 故障注入时间 (秒)
        self.FAULT_TYPE: str = "noise"            # 故障类型
        self.FAULT_TARGET_SENSOR: str = "h_gate_up"  # 目标传感器
        self.FAULT_NOISE_MULTIPLIER: float = 5.0     # 噪声放大倍数
        self.FAULT_DRIFT_RATE: float = 0.01          # 漂移速率
    
    def _setup_scenario_config(self, scenario: str):
        """根据场景设置特定配置"""
        if scenario == "normal":
            # 正常运行场景 - 使用默认配置
            pass
            
        elif scenario == "fault":
            # 故障注入场景
            self.INJECT_FAULT = True
            self.FAULT_TYPE = "drift"
            self.FAULT_INJECTION_TIME = 10.0
            self.FAULT_TARGET_SENSOR = "h_gate_up"
            self.FAULT_DRIFT_RATE = 0.02
            
        elif scenario == "noisy":
            # 高噪声场景
            self.NOISE_LEVEL_H *= 3.0  # 增加水位噪声
            self.NOISE_LEVEL_Q *= 3.0  # 增加流量噪声
            self.INJECT_FAULT = True
            self.FAULT_TYPE = "noise"
            self.FAULT_INJECTION_TIME = 5.0
            self.FAULT_NOISE_MULTIPLIER = 10.0
            
        else:
            print(f"⚠️  未知场景 '{scenario}'，使用默认配置")
    
    def get_scenario_description(self) -> str:
        """获取场景描述"""
        descriptions = {
            "normal": "正常运行场景 - 所有组件正常工作",
            "fault": "故障注入场景 - 模拟传感器漂移故障",
            "noisy": "高噪声场景 - 传感器噪声显著增加"
        }
        return descriptions.get(self.scenario, "自定义场景")
    
    def print_config_summary(self):
        """打印配置摘要"""
        print(f"\n配置摘要 - {self.scenario.upper()} 场景")
        print("="*50)
        print(f"场景描述: {self.get_scenario_description()}")
        print(f"时间步长: {self.TIME_STEP} 秒")
        print(f"传感器数量: {len(self.SENSOR_LIST)}")
        print(f"故障检测: {'启用' if self.ENABLE_FAULT_DETECTION else '禁用'}")
        print(f"系统辨识: {'启用' if self.ENABLE_SYSTEM_ID else '禁用'}")
        
        if self.INJECT_FAULT:
            print(f"故障注入: 启用")
            print(f"  类型: {self.FAULT_TYPE}")
            print(f"  时间: {self.FAULT_INJECTION_TIME} 秒")
            print(f"  目标: {self.FAULT_TARGET_SENSOR}")
        else:
            print(f"故障注入: 禁用")
        
        print("="*50)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "scenario": self.scenario,
            "time_step": self.TIME_STEP,
            "sensor_list": self.SENSOR_LIST,
            "noise_levels": {
                "water_level": self.NOISE_LEVEL_H,
                "flow_rate": self.NOISE_LEVEL_Q
            },
            "fault_detection": {
                "enabled": self.ENABLE_FAULT_DETECTION,
                "thresholds": {
                    "noise_factor": self.NOISE_FACTOR_THRESHOLD,
                    "drift_h": self.DRIFT_THRESHOLD_H,
                    "drift_q": self.DRIFT_THRESHOLD_Q
                }
            },
            "system_identification": {
                "enabled": self.ENABLE_SYSTEM_ID,
                "rls_forgetting_factor": self.RLS_FORGETTING_FACTOR
            },
            "fault_injection": {
                "enabled": self.INJECT_FAULT,
                "type": self.FAULT_TYPE,
                "time": self.FAULT_INJECTION_TIME,
                "target": self.FAULT_TARGET_SENSOR
            }
        }

# ============ 预定义配置 ============
def get_normal_config() -> QuickStartConfig:
    """获取正常运行配置"""
    return QuickStartConfig("normal")

def get_fault_config() -> QuickStartConfig:
    """获取故障场景配置"""
    return QuickStartConfig("fault")

def get_noisy_config() -> QuickStartConfig:
    """获取噪声场景配置"""
    return QuickStartConfig("noisy")

def get_custom_config(**kwargs) -> QuickStartConfig:
    """获取自定义配置"""
    config = QuickStartConfig("normal")
    
    # 应用自定义参数
    for key, value in kwargs.items():
        if hasattr(config, key.upper()):
            setattr(config, key.upper(), value)
        else:
            print(f"⚠️  未知配置参数: {key}")
    
    return config

# ============ 配置验证 ============
def validate_config(config: QuickStartConfig) -> bool:
    """验证配置的有效性"""
    errors = []
    
    # 检查基础参数
    if config.TIME_STEP <= 0:
        errors.append("时间步长必须大于0")
    
    if not config.SENSOR_LIST:
        errors.append("传感器列表不能为空")
    
    if config.NOISE_LEVEL_H < 0 or config.NOISE_LEVEL_Q < 0:
        errors.append("噪声水平不能为负数")
    
    # 检查故障注入参数
    if config.INJECT_FAULT:
        if config.FAULT_INJECTION_TIME < 0:
            errors.append("故障注入时间不能为负数")
        
        if config.FAULT_TARGET_SENSOR not in config.SENSOR_LIST:
            errors.append("故障目标传感器不在传感器列表中")
        
        valid_fault_types = ["noise", "drift", "stuck"]
        if config.FAULT_TYPE not in valid_fault_types:
            errors.append(f"故障类型必须是 {valid_fault_types} 之一")
    
    # 检查系统辨识参数
    if config.ENABLE_SYSTEM_ID:
        if not (0 < config.RLS_FORGETTING_FACTOR <= 1):
            errors.append("RLS遗忘因子必须在(0,1]范围内")
    
    # 输出错误信息
    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"  • {error}")
        return False
    
    print("✅ 配置验证通过")
    return True

if __name__ == "__main__":
    # 演示不同配置
    print("快速开始配置演示")
    print("="*60)
    
    scenarios = ["normal", "fault", "noisy"]
    
    for scenario in scenarios:
        config = QuickStartConfig(scenario)
        config.print_config_summary()
        
        # 验证配置
        is_valid = validate_config(config)
        print(f"配置有效性: {'✅ 有效' if is_valid else '❌ 无效'}")
        print()
    
    # 自定义配置示例
    print("自定义配置示例:")
    custom_config = get_custom_config(
        time_step=0.5,
        noise_level_h=0.01,
        inject_fault=True,
        fault_type="stuck"
    )
    custom_config.print_config_summary()