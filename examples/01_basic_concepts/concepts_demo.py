#!/usr/bin/env python3
"""
数字孪生水力系统 - 基础概念演示

本脚本演示了数字孪生系统的核心概念和组件关系。
通过可视化的方式展示系统架构和数据流。

作者: 数字孪生团队
日期: 2024
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConceptsDemo:
    """基础概念演示类"""
    
    def __init__(self):
        """初始化演示器"""
        self.demo_title = "数字孪生水力系统 - 基础概念演示"
        logger.info(f"启动 {self.demo_title}")
    
    def demonstrate_dual_model_concept(self):
        """演示双模型概念"""
        print("\n" + "="*60)
        print("双模型架构概念演示")
        print("="*60)
        
        # 模拟时间序列
        time_steps = np.linspace(0, 10, 100)
        
        # 模型A（高保真）- 复杂但精确
        model_a_data = np.sin(time_steps) + 0.1*np.sin(5*time_steps) + 0.05*np.random.normal(0, 1, len(time_steps))
        
        # 模型B（简化）- 快速但近似
        model_b_data = np.sin(time_steps) + 0.02*np.random.normal(0, 1, len(time_steps))
        
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(time_steps, model_a_data, 'b-', label='模型A (高保真FVM)', linewidth=2)
        plt.title('模型A - 高保真物理模型 (基于FVM)')
        plt.ylabel('水位 (m)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 1, 2)
        plt.plot(time_steps, model_b_data, 'r-', label='模型B (轻量化ID)', linewidth=2)
        plt.title('模型B - 轻量化孪生模型 (基于ID)')
        plt.xlabel('时间 (s)')
        plt.ylabel('水位 (m)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('dual_model_concept.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✓ 双模型概念图已保存为 'dual_model_concept.png'")
        print(f"  模型A计算精度: 高 | 计算速度: 慢")
        print(f"  模型B计算精度: 中 | 计算速度: 快")
    
    def demonstrate_system_layers(self):
        """演示系统层次结构"""
        print("\n" + "="*60)
        print("系统层次结构演示")
        print("="*60)
        
        layers = [
            ("可视化层", "visualization.py", "实时图表、Web界面"),
            ("控制与管理层", "simulation_manager.py", "仿真控制、流程管理"),
            ("诊断与辨识层", "diagnostics/", "故障检测、系统辨识"),
            ("模型层", "models/", "物理模型、数学模型"),
            ("数据生成层", "sensor_simulator.py", "传感器仿真、数据模拟")
        ]
        
        print("系统分层架构:")
        for i, (layer, file, desc) in enumerate(layers):
            print(f"  {i+1}. {layer:15} -> {file:25} | {desc}")
        
        # 数据流演示
        print("\n数据流向:")
        flow_steps = [
            "传感器数据生成",
            "数据预处理与清洗", 
            "故障检测与诊断",
            "系统辨识与参数更新",
            "模型预测与仿真",
            "结果可视化与展示"
        ]
        
        for i, step in enumerate(flow_steps):
            if i < len(flow_steps) - 1:
                print(f"  {step} -> ")
            else:
                print(f"  {step}")
    
    def demonstrate_component_interactions(self):
        """演示组件交互关系"""
        print("\n" + "="*60)
        print("组件交互关系演示")
        print("="*60)
        
        components = {
            "SensorSimulator": "生成传感器数据",
            "DataPreprocessor": "数据清洗和滤波",
            "FaultDetector": "故障检测和诊断",
            "SystemIdentifier": "在线参数辨识",
            "FVMChannelModel": "高保真物理模型",
            "IDChannelModel": "轻量化孪生模型",
            "SimulationManager": "仿真流程管理",
            "Visualizer": "结果可视化"
        }
        
        print("核心组件及功能:")
        for comp, func in components.items():
            print(f"  • {comp:20} : {func}")
        
        print("\n组件交互流程:")
        interactions = [
            "SensorSimulator -> DataPreprocessor (原始数据)",
            "DataPreprocessor -> FaultDetector (清洗数据)",
            "FaultDetector -> SystemIdentifier (可靠数据)",
            "SystemIdentifier -> IDChannelModel (参数更新)",
            "FVMChannelModel -> SensorSimulator (真值参考)",
            "SimulationManager -> 所有组件 (流程控制)",
            "所有组件 -> Visualizer (状态数据)"
        ]
        
        for interaction in interactions:
            print(f"  {interaction}")
    
    def demonstrate_key_algorithms(self):
        """演示关键算法概念"""
        print("\n" + "="*60)
        print("关键算法概念演示")
        print("="*60)
        
        algorithms = {
            "滑动平均滤波": {
                "用途": "数据预处理，去除噪声",
                "原理": "对固定窗口内的数据求平均值",
                "参数": "窗口大小 (window_size)"
            },
            "递归最小二乘法 (RLS)": {
                "用途": "在线参数辨识",
                "原理": "递归更新模型参数以最小化误差",
                "参数": "遗忘因子 (forgetting_factor)"
            },
            "扩展卡尔曼滤波 (EKF)": {
                "用途": "非线性系统状态估计",
                "原理": "基于线性化的贝叶斯滤波",
                "参数": "过程噪声、观测噪声协方差"
            },
            "指数移动平均 (EMA)": {
                "用途": "故障检测中的残差平滑",
                "原理": "指数加权的历史数据平均",
                "参数": "平滑因子 (alpha)"
            }
        }
        
        for alg_name, details in algorithms.items():
            print(f"\n{alg_name}:")
            for key, value in details.items():
                print(f"  {key}: {value}")
    
    def run_complete_demo(self):
        """运行完整演示"""
        print(f"\n🚀 {self.demo_title}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.demonstrate_dual_model_concept()
            self.demonstrate_system_layers()
            self.demonstrate_component_interactions()
            self.demonstrate_key_algorithms()
            
            print("\n" + "="*60)
            print("演示完成!")
            print("="*60)
            print("📚 建议下一步学习: examples/02_quick_start/")
            print("💡 提示: 查看生成的图像文件了解双模型概念")
            
        except Exception as e:
            logger.error(f"演示过程中出现错误: {e}")
            raise

def main():
    """主函数"""
    demo = ConceptsDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()