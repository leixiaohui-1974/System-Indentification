#!/usr/bin/env python3
"""
数字孪生水力系统 - 快速开始演示

这是一个完整的快速开始示例，展示如何在几分钟内运行数字孪生系统。
包含数据生成、处理、故障检测、参数辨识和可视化的完整流程。

使用方法:
    python quick_start_demo.py [--scenario normal|fault|noisy] [--time 30]

作者: 数字孪生团队
日期: 2024
"""

import sys
import os
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# 添加项目根路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import numpy as np
import matplotlib.pyplot as plt
from simple_simulator import SimpleDigitalTwin
from basic_analysis import BasicAnalyzer
from config_quickstart import QuickStartConfig
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('output/simulation_log.txt', mode='w')
    ]
)
logger = logging.getLogger(__name__)

class QuickStartDemo:
    """快速开始演示类"""
    
    def __init__(self, scenario: str = "normal", simulation_time: float = 30.0):
        """
        初始化快速开始演示
        
        Args:
            scenario: 仿真场景 ('normal', 'fault', 'noisy')
            simulation_time: 仿真时间长度 (秒)
        """
        self.scenario = scenario
        self.simulation_time = simulation_time
        self.config = QuickStartConfig(scenario)
        self.digital_twin = None
        self.analyzer = None
        self.results = {}
        
        # 确保输出目录存在
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"快速开始演示初始化完成 - 场景: {scenario}, 时长: {simulation_time}s")
    
    def print_welcome_banner(self):
        """打印欢迎信息"""
        print("\n" + "="*60)
        print("🚀 数字孪生水力系统快速开始")
        print("="*60)
        print(f"⏱️  仿真时间: {self.simulation_time} 秒")
        print(f"📊 传感器数量: {len(self.config.SENSOR_LIST)}")
        print(f"🎯 仿真场景: {self.scenario}")
        print(f"🔧 启用故障检测: {'是' if self.config.ENABLE_FAULT_DETECTION else '否'}")
        print(f"📈 启用参数辨识: {'是' if self.config.ENABLE_SYSTEM_ID else '否'}")
        print(f"📁 输出目录: {self.output_dir.absolute()}")
        print("="*60)
    
    def initialize_system(self):
        """初始化数字孪生系统"""
        print("\n[初始化] 正在启动数字孪生系统...")
        
        try:
            # 创建数字孪生实例
            self.digital_twin = SimpleDigitalTwin(self.config)
            
            # 创建分析器
            self.analyzer = BasicAnalyzer(self.config)
            
            # 初始化系统
            init_success = self.digital_twin.initialize()
            
            if init_success:
                print("✅ [初始化] 系统初始化成功")
                logger.info("数字孪生系统初始化完成")
                return True
            else:
                print("❌ [初始化] 系统初始化失败")
                logger.error("数字孪生系统初始化失败")
                return False
                
        except Exception as e:
            print(f"❌ [初始化] 初始化过程中出现错误: {e}")
            logger.error(f"初始化错误: {e}")
            return False
    
    def run_simulation(self):
        """运行仿真"""
        print(f"\n[仿真] 开始运行 {self.simulation_time} 秒仿真...")
        
        # 仿真参数
        dt = self.config.TIME_STEP
        total_steps = int(self.simulation_time / dt)
        
        # 存储仿真数据
        simulation_data = {
            "time": [],
            "sensor_data": {sensor: [] for sensor in self.config.SENSOR_LIST},
            "processed_data": {sensor: [] for sensor in self.config.SENSOR_LIST},
            "fault_status": [],
            "identified_params": [],
            "model_predictions": []
        }
        
        print(f"📊 总仿真步数: {total_steps}")
        print(f"⏱️  时间步长: {dt} 秒")
        
        start_time = time.time()
        
        try:
            for step in range(total_steps):
                current_time = step * dt
                simulation_data["time"].append(current_time)
                
                # 运行一个仿真步骤
                step_results = self.digital_twin.run_step(current_time)
                
                # 存储数据
                for sensor in self.config.SENSOR_LIST:
                    simulation_data["sensor_data"][sensor].append(
                        step_results["raw_sensor_data"][sensor]
                    )
                    simulation_data["processed_data"][sensor].append(
                        step_results["processed_data"][sensor]
                    )
                
                simulation_data["fault_status"].append(step_results["fault_status"])
                simulation_data["identified_params"].append(step_results["identified_params"])
                simulation_data["model_predictions"].append(step_results["model_predictions"])
                
                # 显示进度（每5秒显示一次）
                if current_time % 5.0 < dt:
                    progress = (step + 1) / total_steps * 100
                    elapsed = time.time() - start_time
                    remaining = elapsed / (step + 1) * (total_steps - step - 1)
                    
                    print(f"[{current_time:05.1f}s] 进度: {progress:5.1f}% | "
                          f"剩余时间: {remaining:.1f}s | "
                          f"故障状态: {self._format_fault_status(step_results['fault_status'])}")
                
                # 检查是否有故障注入
                if self.scenario == "fault" and current_time >= self.config.FAULT_INJECTION_TIME:
                    if not hasattr(self, 'fault_injected'):
                        print(f"⚠️  [{current_time:05.1f}s] 注入故障: {self.config.FAULT_TYPE}")
                        self.fault_injected = True
            
            # 仿真完成
            elapsed_time = time.time() - start_time
            print(f"\n✅ [仿真] 仿真完成! 耗时: {elapsed_time:.2f} 秒")
            
            self.results = simulation_data
            return True
            
        except Exception as e:
            print(f"❌ [仿真] 仿真过程中出现错误: {e}")
            logger.error(f"仿真错误: {e}")
            return False
    
    def _format_fault_status(self, fault_status):
        """格式化故障状态显示"""
        normal_count = sum(1 for status in fault_status.values() if status == "正常")
        total_count = len(fault_status)
        
        if normal_count == total_count:
            return "全部正常"
        else:
            fault_count = total_count - normal_count
            return f"{fault_count}个故障"
    
    def analyze_results(self):
        """分析仿真结果"""
        print(f"\n[分析] 正在分析仿真结果...")
        
        try:
            # 使用分析器处理结果
            analysis_results = self.analyzer.analyze_simulation_results(self.results)
            
            # 显示关键统计信息
            print(f"📈 分析结果摘要:")
            print(f"  • 数据点总数: {analysis_results['total_data_points']}")
            print(f"  • 故障检出次数: {analysis_results['total_faults_detected']}")
            print(f"  • 参数收敛状态: {analysis_results['parameter_convergence']}")
            print(f"  • 平均预测误差: {analysis_results['average_prediction_error']:.4f}")
            
            # 传感器状态总结
            print(f"\n🔍 传感器状态总结:")
            for sensor, stats in analysis_results['sensor_statistics'].items():
                print(f"  • {sensor}: 均值={stats['mean']:.3f}, "
                      f"标准差={stats['std']:.4f}, "
                      f"故障率={stats['fault_rate']:.1f}%")
            
            # 保存分析结果
            analysis_file = self.output_dir / "analysis_results.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ [分析] 分析完成，结果保存到: {analysis_file}")
            return analysis_results
            
        except Exception as e:
            print(f"❌ [分析] 分析过程中出现错误: {e}")
            logger.error(f"分析错误: {e}")
            return None
    
    def generate_visualizations(self):
        """生成可视化图表"""
        print(f"\n[可视化] 正在生成图表...")
        
        try:
            # 创建主仪表板
            self._create_main_dashboard()
            
            # 创建传感器趋势图
            self._create_sensor_trends()
            
            # 创建故障检测图
            self._create_fault_detection_chart()
            
            # 创建参数演化图
            self._create_parameter_evolution_chart()
            
            print("✅ [可视化] 图表生成完成")
            print(f"📁 图表文件保存在: {self.output_dir}")
            
        except Exception as e:
            print(f"❌ [可视化] 图表生成过程中出现错误: {e}")
            logger.error(f"可视化错误: {e}")
    
    def _create_main_dashboard(self):
        """创建主仪表板"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'数字孪生系统仿真结果 - {self.scenario.upper()} 场景', fontsize=16)
        
        time_data = self.results["time"]
        
        # 水位数据
        ax1 = axes[0, 0]
        for sensor in ["h_gate_up", "h_gate_down", "h_channel_mid"]:
            if sensor in self.results["sensor_data"]:
                ax1.plot(time_data, self.results["sensor_data"][sensor], 
                        label=sensor, linewidth=2)
        ax1.set_title('水位监测')
        ax1.set_xlabel('时间 (s)')
        ax1.set_ylabel('水位 (m)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 流量数据
        ax2 = axes[0, 1]
        for sensor in ["q_gate_down", "q_channel_end"]:
            if sensor in self.results["sensor_data"]:
                ax2.plot(time_data, self.results["sensor_data"][sensor], 
                        label=sensor, linewidth=2)
        ax2.set_title('流量监测')
        ax2.set_xlabel('时间 (s)')
        ax2.set_ylabel('流量 (m³/s)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 故障状态热图
        ax3 = axes[1, 0]
        fault_matrix = self._create_fault_matrix()
        im = ax3.imshow(fault_matrix, aspect='auto', cmap='RdYlGn', interpolation='nearest')
        ax3.set_title('故障检测状态')
        ax3.set_xlabel('时间步')
        ax3.set_ylabel('传感器')
        ax3.set_yticks(range(len(self.config.SENSOR_LIST)))
        ax3.set_yticklabels(self.config.SENSOR_LIST)
        plt.colorbar(im, ax=ax3)
        
        # 参数演化
        ax4 = axes[1, 1]
        if self.results["identified_params"]:
            manning_values = [params.get("manning_coefficient", 0.025) 
                            for params in self.results["identified_params"]]
            ax4.plot(time_data, manning_values, 'purple', linewidth=2)
            ax4.set_title('曼宁系数辨识')
            ax4.set_xlabel('时间 (s)')
            ax4.set_ylabel('曼宁系数')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'simulation_results.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_fault_matrix(self):
        """创建故障状态矩阵"""
        n_sensors = len(self.config.SENSOR_LIST)
        n_steps = len(self.results["fault_status"])
        fault_matrix = np.ones((n_sensors, n_steps))  # 1 = 正常
        
        for t, fault_status in enumerate(self.results["fault_status"]):
            for i, sensor in enumerate(self.config.SENSOR_LIST):
                if sensor in fault_status and fault_status[sensor] != "正常":
                    fault_matrix[i, t] = 0  # 0 = 故障
        
        return fault_matrix
    
    def _create_sensor_trends(self):
        """创建传感器趋势图"""
        n_sensors = len(self.config.SENSOR_LIST)
        fig, axes = plt.subplots(n_sensors, 1, figsize=(12, 2*n_sensors))
        fig.suptitle('传感器数据趋势分析', fontsize=14)
        
        time_data = self.results["time"]
        
        for i, sensor in enumerate(self.config.SENSOR_LIST):
            ax = axes[i] if n_sensors > 1 else axes
            
            # 原始数据
            raw_data = self.results["sensor_data"][sensor]
            processed_data = self.results["processed_data"][sensor]
            
            ax.plot(time_data, raw_data, alpha=0.5, color='lightblue', label='原始数据')
            ax.plot(time_data, processed_data, color='blue', linewidth=2, label='处理后数据')
            
            ax.set_title(f'{sensor} - 数据趋势')
            ax.set_xlabel('时间 (s)')
            ax.set_ylabel('数值')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'sensor_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_fault_detection_chart(self):
        """创建故障检测图表"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        time_data = self.results["time"]
        
        # 统计每个时间点的故障数量
        fault_counts = []
        for fault_status in self.results["fault_status"]:
            fault_count = sum(1 for status in fault_status.values() if status != "正常")
            fault_counts.append(fault_count)
        
        ax.fill_between(time_data, fault_counts, alpha=0.6, color='red', label='故障数量')
        ax.plot(time_data, fault_counts, color='darkred', linewidth=2)
        
        ax.set_title('故障检测时间序列')
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('故障传感器数量')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'fault_detection.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_parameter_evolution_chart(self):
        """创建参数演化图表"""
        if not self.results["identified_params"]:
            return
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        time_data = self.results["time"]
        
        # 曼宁系数演化
        manning_values = [params.get("manning_coefficient", 0.025) 
                         for params in self.results["identified_params"]]
        axes[0].plot(time_data, manning_values, 'purple', linewidth=2)
        axes[0].axhline(y=0.025, color='gray', linestyle='--', alpha=0.7, label='初始值')
        axes[0].set_title('曼宁系数辨识过程')
        axes[0].set_ylabel('曼宁系数')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # 闸门系数演化
        gate_values = [params.get("gate_coefficient", 0.65) 
                      for params in self.results["identified_params"]]
        axes[1].plot(time_data, gate_values, 'green', linewidth=2)
        axes[1].axhline(y=0.65, color='gray', linestyle='--', alpha=0.7, label='初始值')
        axes[1].set_title('闸门系数辨识过程')
        axes[1].set_xlabel('时间 (s)')
        axes[1].set_ylabel('闸门系数')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'parameter_evolution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_final_report(self):
        """保存最终报告"""
        print(f"\n[报告] 正在生成最终报告...")
        
        try:
            report = {
                "simulation_info": {
                    "scenario": self.scenario,
                    "simulation_time": self.simulation_time,
                    "time_step": self.config.TIME_STEP,
                    "total_steps": len(self.results["time"]),
                    "completed_at": datetime.now().isoformat()
                },
                "system_status": {
                    "sensors_count": len(self.config.SENSOR_LIST),
                    "fault_detection_enabled": self.config.ENABLE_FAULT_DETECTION,
                    "system_identification_enabled": self.config.ENABLE_SYSTEM_ID
                },
                "performance_metrics": {
                    "total_faults_detected": sum(
                        sum(1 for status in fault_status.values() if status != "正常")
                        for fault_status in self.results["fault_status"]
                    ),
                    "final_parameters": self.results["identified_params"][-1] if self.results["identified_params"] else {}
                },
                "output_files": [
                    "simulation_results.png",
                    "sensor_trends.png", 
                    "fault_detection.png",
                    "parameter_evolution.png",
                    "analysis_results.json",
                    "simulation_log.txt"
                ]
            }
            
            report_file = self.output_dir / "final_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"✅ [报告] 最终报告已生成: {report_file}")
            
        except Exception as e:
            print(f"❌ [报告] 报告生成失败: {e}")
            logger.error(f"报告生成错误: {e}")
    
    def print_completion_summary(self):
        """打印完成总结"""
        print("\n" + "="*60)
        print("🎉 快速开始演示完成!")
        print("="*60)
        
        print(f"📊 仿真统计:")
        print(f"  • 场景类型: {self.scenario}")
        print(f"  • 仿真时长: {self.simulation_time} 秒")
        print(f"  • 数据点数: {len(self.results['time'])}")
        print(f"  • 传感器数: {len(self.config.SENSOR_LIST)}")
        
        print(f"\n📁 生成的文件:")
        output_files = list(self.output_dir.glob("*"))
        for file_path in sorted(output_files):
            print(f"  • {file_path.name}")
        
        print(f"\n🎯 下一步建议:")
        print(f"  1. 查看 output/ 目录中的可视化图表")
        print(f"  2. 阅读 final_report.json 了解详细结果")
        print(f"  3. 尝试其他场景: normal, fault, noisy")
        print(f"  4. 进入下一个示例: 03_basic_simulation")
        
        print("="*60)
    
    def run_complete_demo(self):
        """运行完整的快速开始演示"""
        try:
            # 1. 显示欢迎信息
            self.print_welcome_banner()
            
            # 2. 初始化系统
            if not self.initialize_system():
                return False
            
            # 3. 运行仿真
            if not self.run_simulation():
                return False
            
            # 4. 分析结果
            analysis_results = self.analyze_results()
            
            # 5. 生成可视化
            self.generate_visualizations()
            
            # 6. 保存最终报告
            self.save_final_report()
            
            # 7. 显示完成总结
            self.print_completion_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ 演示过程中出现未处理的错误: {e}")
            logger.error(f"未处理的错误: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数字孪生水力系统快速开始演示')
    parser.add_argument('--scenario', choices=['normal', 'fault', 'noisy'], 
                       default='normal', help='仿真场景')
    parser.add_argument('--time', type=float, default=30.0, 
                       help='仿真时间长度（秒）')
    
    args = parser.parse_args()
    
    # 创建并运行演示
    demo = QuickStartDemo(scenario=args.scenario, simulation_time=args.time)
    success = demo.run_complete_demo()
    
    # 退出代码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()