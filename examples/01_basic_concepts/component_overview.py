#!/usr/bin/env python3
"""
数字孪生水力系统 - 组件概览

本脚本详细展示系统中各个核心组件的功能、接口和使用方法。
通过模拟组件演示实际系统的工作原理。

作者: 数字孪生团队
日期: 2024
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Tuple
from collections import deque
import logging

logger = logging.getLogger(__name__)

class ComponentOverview:
    """组件概览演示类"""
    
    def __init__(self):
        self.demo_title = "数字孪生系统组件概览"
        
    def demonstrate_sensor_simulator(self):
        """演示传感器仿真器"""
        print("\n" + "="*50)
        print("1. 传感器仿真器 (SensorSimulator)")
        print("="*50)
        
        print("功能: 模拟真实水力系统中的传感器数据")
        print("输出: 水位、流量等传感器读数")
        
        # 模拟传感器数据生成
        time_steps = 20
        sensor_data = {
            "h_gate_up": [],
            "h_gate_down": [],
            "q_gate_down": [],
            "h_channel_mid": [],
            "q_channel_end": []
        }
        
        for t in range(time_steps):
            # 基础值 + 动态变化 + 噪声
            base_values = {
                "h_gate_up": 5.0 + 0.5*np.sin(t*0.3),
                "h_gate_down": 3.0 + 0.3*np.sin(t*0.3),
                "q_gate_down": 10.0 + 2.0*np.sin(t*0.2),
                "h_channel_mid": 4.0 + 0.4*np.sin(t*0.25),
                "q_channel_end": 9.5 + 1.8*np.sin(t*0.2)
            }
            
            for sensor, base_val in base_values.items():
                noise = 0.02 * np.random.normal()  # 2% 噪声
                sensor_data[sensor].append(base_val + noise)
        
        # 显示传感器配置
        sensor_config = {
            "h_gate_up": {"类型": "水位", "位置": "闸门上游", "单位": "m"},
            "h_gate_down": {"类型": "水位", "位置": "闸门下游", "单位": "m"},
            "q_gate_down": {"类型": "流量", "位置": "闸门下游", "单位": "m³/s"},
            "h_channel_mid": {"类型": "水位", "位置": "渠道中段", "单位": "m"},
            "q_channel_end": {"类型": "流量", "位置": "渠道末端", "单位": "m³/s"}
        }
        
        print("\n传感器配置:")
        for sensor, config in sensor_config.items():
            print(f"  {sensor:15}: {config['类型']} | {config['位置']} | {config['单位']}")
        
        print(f"\n✓ 生成了 {time_steps} 个时间步的传感器数据")
        return sensor_data
    
    def demonstrate_data_preprocessor(self, sensor_data: Dict[str, List[float]]):
        """演示数据预处理器"""
        print("\n" + "="*50)
        print("2. 数据预处理器 (DataPreprocessor)")
        print("="*50)
        
        print("功能: 对原始传感器数据进行清洗和滤波")
        print("算法: 滑动平均滤波")
        
        # 模拟滑动平均滤波
        window_size = 5
        filtered_data = {}
        
        for sensor, values in sensor_data.items():
            filtered_values = []
            buffer = deque(maxlen=window_size)
            
            for value in values:
                buffer.append(value)
                filtered_value = np.mean(buffer)
                filtered_values.append(filtered_value)
            
            filtered_data[sensor] = filtered_values
        
        # 计算滤波效果
        print(f"\n滤波参数:")
        print(f"  窗口大小: {window_size}")
        print(f"  滤波类型: 滑动平均")
        
        # 计算噪声减少效果
        original_noise = np.std(sensor_data["h_gate_up"])
        filtered_noise = np.std(filtered_data["h_gate_up"])
        noise_reduction = (1 - filtered_noise/original_noise) * 100
        
        print(f"\n滤波效果 (以h_gate_up为例):")
        print(f"  原始噪声标准差: {original_noise:.4f}")
        print(f"  滤波后噪声标准差: {filtered_noise:.4f}")
        print(f"  噪声减少: {noise_reduction:.1f}%")
        
        return filtered_data
    
    def demonstrate_fault_detector(self, clean_data: Dict[str, List[float]]):
        """演示故障检测器"""
        print("\n" + "="*50)
        print("3. 故障检测器 (FaultDetector)")
        print("="*50)
        
        print("功能: 检测传感器故障和异常")
        print("检测类型: 噪声增大、漂移、卡死")
        
        fault_detection_results = {}
        
        for sensor, values in clean_data.items():
            # 模拟故障检测逻辑
            recent_values = values[-10:]  # 最近10个值
            
            # 1. 噪声检测
            noise_level = np.std(recent_values)
            base_noise = 0.005 if 'h' in sensor else 0.01
            noise_threshold = base_noise * 3.0
            
            # 2. 漂移检测 (模拟模型预测比较)
            predicted_value = np.mean(values)  # 简化的预测值
            current_value = values[-1]
            drift = abs(current_value - predicted_value)
            drift_threshold = 0.1 if 'h' in sensor else 1.0
            
            # 3. 卡死检测 (变化率检测)
            recent_change = abs(max(recent_values) - min(recent_values))
            stuck_threshold = 0.01 if 'h' in sensor else 0.1
            
            # 故障判断
            faults = []
            if noise_level > noise_threshold:
                faults.append(f"噪声增大 ({noise_level:.4f} > {noise_threshold:.4f})")
            if drift > drift_threshold:
                faults.append(f"漂移 ({drift:.4f} > {drift_threshold:.4f})")
            if recent_change < stuck_threshold:
                faults.append(f"疑似卡死 (变化量: {recent_change:.4f})")
            
            fault_detection_results[sensor] = faults if faults else ["正常"]
        
        print("\n故障检测结果:")
        for sensor, faults in fault_detection_results.items():
            status = ", ".join(faults)
            print(f"  {sensor:15}: {status}")
        
        return fault_detection_results
    
    def demonstrate_system_identifier(self, clean_data: Dict[str, List[float]]):
        """演示系统辨识器"""
        print("\n" + "="*50)
        print("4. 系统辨识器 (SystemIdentifier)")
        print("="*50)
        
        print("功能: 在线辨识和更新模型参数")
        print("算法: 递归最小二乘法 (RLS) + 扩展卡尔曼滤波 (EKF)")
        
        # 模拟参数辨识
        initial_params = {
            "manning_coefficient": 0.025,
            "gate_coefficient": 0.65,
            "channel_slope": 0.001
        }
        
        # 模拟RLS参数更新
        rls_params = initial_params.copy()
        forgetting_factor = 0.95
        
        print(f"\nRLS参数辨识:")
        print(f"  遗忘因子: {forgetting_factor}")
        print(f"  初始参数:")
        for param, value in initial_params.items():
            print(f"    {param}: {value}")
        
        # 模拟参数收敛过程
        param_history = {param: [value] for param, value in initial_params.items()}
        
        for step in range(10):
            # 模拟参数更新 (简化版本)
            for param in rls_params:
                error = 0.001 * np.random.normal()  # 模拟估计误差
                update = 0.1 * error * forgetting_factor**step
                rls_params[param] += update
                param_history[param].append(rls_params[param])
        
        print(f"\n  经过 10 步迭代后的参数:")
        for param, value in rls_params.items():
            change = abs(value - initial_params[param])
            print(f"    {param}: {value:.6f} (变化: {change:.6f})")
        
        # 模拟EKF状态估计
        print(f"\nEKF状态估计:")
        ekf_states = {
            "water_level_1": 5.0,
            "water_level_2": 3.0,
            "flow_rate": 10.0
        }
        
        state_uncertainty = {
            "water_level_1": 0.01,
            "water_level_2": 0.01,
            "flow_rate": 0.1
        }
        
        print(f"  估计状态:")
        for state, value in ekf_states.items():
            uncertainty = state_uncertainty[state]
            print(f"    {state}: {value:.3f} ± {uncertainty:.3f}")
        
        return {
            "rls_params": rls_params,
            "param_history": param_history,
            "ekf_states": ekf_states
        }
    
    def demonstrate_models(self):
        """演示物理模型"""
        print("\n" + "="*50)
        print("5. 物理模型层")
        print("="*50)
        
        models = {
            "FVMChannelModel": {
                "类型": "高保真有限体积法模型",
                "用途": "精确物理仿真",
                "特点": "计算精度高，速度慢",
                "方程": "一维圣维南方程"
            },
            "IDChannelModel": {
                "类型": "轻量化积分时滞模型",
                "用途": "实时预测控制",
                "特点": "计算速度快，精度中等",
                "方程": "简化水力学方程"
            },
            "GateModel": {
                "类型": "闸门水力模型",
                "用途": "闸门流量计算",
                "特点": "经验公式，计算快速",
                "方程": "闸门流量公式"
            }
        }
        
        print("模型概览:")
        for model_name, details in models.items():
            print(f"\n  {model_name}:")
            for key, value in details.items():
                print(f"    {key}: {value}")
        
        # 模拟模型计算性能比较
        print(f"\n模型性能比较 (模拟数据):")
        performance_data = {
            "FVMChannelModel": {"计算时间": "100ms", "精度": "99%", "适用场景": "离线分析"},
            "IDChannelModel": {"计算时间": "5ms", "精度": "95%", "适用场景": "实时控制"},
            "GateModel": {"计算时间": "1ms", "精度": "90%", "适用场景": "快速估算"}
        }
        
        for model, perf in performance_data.items():
            print(f"  {model}:")
            for metric, value in perf.items():
                print(f"    {metric}: {value}")
    
    def demonstrate_visualization(self, sensor_data: Dict[str, List[float]]):
        """演示可视化组件"""
        print("\n" + "="*50)
        print("6. 可视化组件 (Visualizer)")
        print("="*50)
        
        print("功能: 实时显示系统状态和数据")
        print("输出: 图表、仪表板、状态面板")
        
        # 创建示例图表
        time_steps = list(range(len(sensor_data["h_gate_up"])))
        
        plt.figure(figsize=(12, 8))
        
        # 水位数据子图
        plt.subplot(2, 2, 1)
        plt.plot(time_steps, sensor_data["h_gate_up"], 'b-', label='闸门上游')
        plt.plot(time_steps, sensor_data["h_gate_down"], 'r-', label='闸门下游')
        plt.plot(time_steps, sensor_data["h_channel_mid"], 'g-', label='渠道中段')
        plt.title('水位监测')
        plt.xlabel('时间步')
        plt.ylabel('水位 (m)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 流量数据子图
        plt.subplot(2, 2, 2)
        plt.plot(time_steps, sensor_data["q_gate_down"], 'r-', label='闸门下游')
        plt.plot(time_steps, sensor_data["q_channel_end"], 'b-', label='渠道末端')
        plt.title('流量监测')
        plt.xlabel('时间步')
        plt.ylabel('流量 (m³/s)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 系统状态图
        plt.subplot(2, 2, 3)
        components = ['传感器', '预处理', '故障检测', '系统辨识', '模型']
        status = [1, 1, 1, 1, 1]  # 1表示正常
        colors = ['green' if s == 1 else 'red' for s in status]
        plt.bar(components, status, color=colors, alpha=0.7)
        plt.title('组件状态')
        plt.ylabel('状态 (1=正常, 0=异常)')
        plt.xticks(rotation=45)
        
        # 参数趋势图 (模拟)
        plt.subplot(2, 2, 4)
        param_values = [0.025 + 0.001*np.sin(t*0.1) for t in time_steps]
        plt.plot(time_steps, param_values, 'purple', linewidth=2)
        plt.title('参数辨识趋势')
        plt.xlabel('时间步')
        plt.ylabel('曼宁系数')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('component_overview_dashboard.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"\n✓ 生成可视化仪表板: 'component_overview_dashboard.png'")
        
        # 输出统计信息
        stats = {
            "数据点总数": len(sensor_data["h_gate_up"]) * len(sensor_data),
            "传感器数量": len(sensor_data),
            "监测时长": f"{len(sensor_data['h_gate_up'])} 时间步",
            "数据更新频率": "1Hz (模拟)"
        }
        
        print(f"\n系统统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    def run_complete_overview(self):
        """运行完整的组件概览演示"""
        print(f"🔍 {self.demo_title}")
        print(f"时间: {os.popen('date').read().strip()}")
        
        try:
            # 1. 传感器仿真
            sensor_data = self.demonstrate_sensor_simulator()
            
            # 2. 数据预处理
            clean_data = self.demonstrate_data_preprocessor(sensor_data)
            
            # 3. 故障检测
            fault_results = self.demonstrate_fault_detector(clean_data)
            
            # 4. 系统辨识
            identification_results = self.demonstrate_system_identifier(clean_data)
            
            # 5. 物理模型
            self.demonstrate_models()
            
            # 6. 可视化
            self.demonstrate_visualization(sensor_data)
            
            print("\n" + "="*60)
            print("组件概览演示完成!")
            print("="*60)
            print("📈 生成的文件:")
            print("  • component_overview_dashboard.png - 系统仪表板")
            print("\n📚 下一步学习建议:")
            print("  • 进入 02_quick_start 学习快速启动")
            print("  • 查看实际代码文件了解详细实现")
            
        except Exception as e:
            logger.error(f"演示过程中出现错误: {e}")
            raise

def main():
    """主函数"""
    overview = ComponentOverview()
    overview.run_complete_overview()

if __name__ == "__main__":
    main()