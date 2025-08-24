#!/usr/bin/env python3
"""
基础数据分析模块

为快速开始示例提供数据分析功能，包括统计分析、性能评估和结果总结。

作者: 数字孪生团队
日期: 2024
"""

import numpy as np
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class BasicAnalyzer:
    """基础数据分析器"""
    
    def __init__(self, config):
        self.config = config
        
    def analyze_simulation_results(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析仿真结果"""
        try:
            analysis_results = {
                "total_data_points": len(simulation_data["time"]),
                "simulation_duration": simulation_data["time"][-1] if simulation_data["time"] else 0,
                "sensor_statistics": self._analyze_sensor_data(simulation_data),
                "fault_analysis": self._analyze_fault_detection(simulation_data),
                "parameter_analysis": self._analyze_parameter_identification(simulation_data),
                "model_performance": self._analyze_model_performance(simulation_data),
                "total_faults_detected": self._count_total_faults(simulation_data),
                "parameter_convergence": self._check_parameter_convergence(simulation_data),
                "average_prediction_error": self._calculate_prediction_error(simulation_data)
            }
            
            logger.info("仿真结果分析完成")
            return analysis_results
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return {}
    
    def _analyze_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """分析传感器数据统计特性"""
        sensor_stats = {}
        
        for sensor in self.config.SENSOR_LIST:
            if sensor in data["sensor_data"]:
                sensor_values = data["sensor_data"][sensor]
                processed_values = data["processed_data"][sensor]
                
                # 基础统计
                stats = {
                    "mean": float(np.mean(sensor_values)),
                    "std": float(np.std(sensor_values)),
                    "min": float(np.min(sensor_values)),
                    "max": float(np.max(sensor_values)),
                    "range": float(np.max(sensor_values) - np.min(sensor_values))
                }
                
                # 处理效果
                original_noise = np.std(sensor_values)
                filtered_noise = np.std(processed_values)
                noise_reduction = (1 - filtered_noise/original_noise) * 100 if original_noise > 0 else 0
                
                stats.update({
                    "original_noise": float(original_noise),
                    "filtered_noise": float(filtered_noise),
                    "noise_reduction_percent": float(noise_reduction)
                })
                
                # 故障率统计
                fault_count = sum(1 for fault_status in data["fault_status"] 
                                if fault_status.get(sensor, "正常") != "正常")
                fault_rate = (fault_count / len(data["fault_status"])) * 100 if data["fault_status"] else 0
                
                stats["fault_rate"] = float(fault_rate)
                
                sensor_stats[sensor] = stats
        
        return sensor_stats
    
    def _analyze_fault_detection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析故障检测结果"""
        if not data["fault_status"]:
            return {"fault_detection_enabled": False}
        
        fault_analysis = {
            "fault_detection_enabled": True,
            "total_time_steps": len(data["fault_status"]),
            "fault_types": {},
            "sensor_fault_summary": {},
            "fault_timeline": []
        }
        
        # 统计故障类型
        fault_type_counts = {}
        sensor_fault_counts = {sensor: 0 for sensor in self.config.SENSOR_LIST}
        
        for i, fault_status in enumerate(data["fault_status"]):
            step_faults = []
            for sensor, status in fault_status.items():
                if status != "正常":
                    sensor_fault_counts[sensor] += 1
                    fault_type = status.split("(")[0].strip()  # 提取故障类型
                    fault_type_counts[fault_type] = fault_type_counts.get(fault_type, 0) + 1
                    step_faults.append(f"{sensor}:{fault_type}")
            
            if step_faults:
                fault_analysis["fault_timeline"].append({
                    "time_step": i,
                    "time": data["time"][i] if i < len(data["time"]) else i,
                    "faults": step_faults
                })
        
        fault_analysis["fault_types"] = fault_type_counts
        fault_analysis["sensor_fault_summary"] = sensor_fault_counts
        
        return fault_analysis
    
    def _analyze_parameter_identification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析参数辨识结果"""
        if not data["identified_params"]:
            return {"parameter_identification_enabled": False}
        
        param_analysis = {
            "parameter_identification_enabled": True,
            "parameter_evolution": {},
            "convergence_metrics": {},
            "final_parameters": data["identified_params"][-1] if data["identified_params"] else {}
        }
        
        # 分析每个参数的演化
        if data["identified_params"]:
            param_names = data["identified_params"][0].keys()
            
            for param_name in param_names:
                param_values = [params.get(param_name, 0) for params in data["identified_params"]]
                
                param_analysis["parameter_evolution"][param_name] = {
                    "initial_value": float(param_values[0]) if param_values else 0,
                    "final_value": float(param_values[-1]) if param_values else 0,
                    "mean_value": float(np.mean(param_values)) if param_values else 0,
                    "std_deviation": float(np.std(param_values)) if param_values else 0,
                    "total_change": float(param_values[-1] - param_values[0]) if len(param_values) > 1 else 0
                }
                
                # 收敛性分析
                if len(param_values) > 10:
                    # 计算后半段的标准差作为收敛指标
                    latter_half = param_values[len(param_values)//2:]
                    convergence_std = np.std(latter_half)
                    
                    param_analysis["convergence_metrics"][param_name] = {
                        "convergence_std": float(convergence_std),
                        "is_converged": convergence_std < 0.001  # 收敛阈值
                    }
        
        return param_analysis
    
    def _analyze_model_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析模型性能"""
        if not data["model_predictions"]:
            return {"model_predictions_available": False}
        
        performance_analysis = {
            "model_predictions_available": True,
            "prediction_accuracy": {},
            "overall_performance": {}
        }
        
        # 计算每个传感器的预测精度
        total_error = 0
        total_points = 0
        
        for sensor in self.config.SENSOR_LIST:
            if sensor in data["processed_data"]:
                actual_values = data["processed_data"][sensor]
                predicted_values = [pred.get(sensor, actual_values[i]) 
                                  for i, pred in enumerate(data["model_predictions"]) 
                                  if i < len(actual_values)]
                
                if len(predicted_values) == len(actual_values):
                    # 计算误差指标
                    errors = np.array(actual_values) - np.array(predicted_values)
                    mae = np.mean(np.abs(errors))
                    rmse = np.sqrt(np.mean(errors**2))
                    mape = np.mean(np.abs(errors / np.array(actual_values))) * 100
                    
                    performance_analysis["prediction_accuracy"][sensor] = {
                        "mae": float(mae),
                        "rmse": float(rmse),
                        "mape": float(mape),
                        "correlation": float(np.corrcoef(actual_values, predicted_values)[0, 1])
                    }
                    
                    total_error += mae
                    total_points += 1
        
        # 整体性能
        if total_points > 0:
            performance_analysis["overall_performance"] = {
                "average_mae": float(total_error / total_points),
                "sensors_analyzed": total_points
            }
        
        return performance_analysis
    
    def _count_total_faults(self, data: Dict[str, Any]) -> int:
        """统计总故障数量"""
        total_faults = 0
        for fault_status in data["fault_status"]:
            total_faults += sum(1 for status in fault_status.values() if status != "正常")
        return total_faults
    
    def _check_parameter_convergence(self, data: Dict[str, Any]) -> str:
        """检查参数收敛状态"""
        if not data["identified_params"] or len(data["identified_params"]) < 10:
            return "数据不足"
        
        # 检查最后25%的数据的稳定性
        last_quarter_start = len(data["identified_params"]) * 3 // 4
        recent_params = data["identified_params"][last_quarter_start:]
        
        convergence_status = {}
        for param_name in recent_params[0].keys():
            param_values = [params[param_name] for params in recent_params]
            stability = np.std(param_values)
            convergence_status[param_name] = stability < 0.001
        
        if all(convergence_status.values()):
            return "已收敛"
        elif any(convergence_status.values()):
            return "部分收敛"
        else:
            return "未收敛"
    
    def _calculate_prediction_error(self, data: Dict[str, Any]) -> float:
        """计算平均预测误差"""
        if not data["model_predictions"] or not data["processed_data"]:
            return 0.0
        
        total_error = 0
        total_comparisons = 0
        
        for sensor in self.config.SENSOR_LIST:
            if sensor in data["processed_data"]:
                actual_values = data["processed_data"][sensor]
                
                for i, pred in enumerate(data["model_predictions"]):
                    if i < len(actual_values) and sensor in pred:
                        error = abs(actual_values[i] - pred[sensor])
                        total_error += error
                        total_comparisons += 1
        
        return total_error / total_comparisons if total_comparisons > 0 else 0.0

class PerformanceAnalyzer:
    """性能分析器"""
    
    @staticmethod
    def analyze_computational_performance(execution_times: List[float]) -> Dict[str, float]:
        """分析计算性能"""
        if not execution_times:
            return {}
        
        return {
            "mean_execution_time": float(np.mean(execution_times)),
            "max_execution_time": float(np.max(execution_times)),
            "min_execution_time": float(np.min(execution_times)),
            "std_execution_time": float(np.std(execution_times)),
            "total_execution_time": float(np.sum(execution_times))
        }
    
    @staticmethod
    def analyze_memory_usage(memory_snapshots: List[float]) -> Dict[str, float]:
        """分析内存使用"""
        if not memory_snapshots:
            return {}
        
        return {
            "peak_memory_mb": float(np.max(memory_snapshots)),
            "average_memory_mb": float(np.mean(memory_snapshots)),
            "memory_growth_mb": float(memory_snapshots[-1] - memory_snapshots[0]) if len(memory_snapshots) > 1 else 0
        }

class DataQualityAnalyzer:
    """数据质量分析器"""
    
    @staticmethod
    def analyze_data_quality(sensor_data: Dict[str, List[float]]) -> Dict[str, Dict[str, Any]]:
        """分析数据质量"""
        quality_analysis = {}
        
        for sensor, values in sensor_data.items():
            if not values:
                continue
            
            values_array = np.array(values)
            
            # 基础质量指标
            quality_metrics = {
                "completeness": 1.0 - np.sum(np.isnan(values_array)) / len(values_array),
                "outlier_ratio": DataQualityAnalyzer._detect_outliers(values_array),
                "consistency_score": DataQualityAnalyzer._calculate_consistency(values_array),
                "noise_level": float(np.std(np.diff(values_array))),  # 基于差分的噪声估计
                "data_points": len(values)
            }
            
            quality_analysis[sensor] = quality_metrics
        
        return quality_analysis
    
    @staticmethod
    def _detect_outliers(values: np.ndarray, threshold: float = 3.0) -> float:
        """检测异常值比例"""
        if len(values) < 3:
            return 0.0
        
        # 使用3-sigma规则检测异常值
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            return 0.0
        
        z_scores = np.abs((values - mean_val) / std_val)
        outliers = np.sum(z_scores > threshold)
        
        return outliers / len(values)
    
    @staticmethod
    def _calculate_consistency(values: np.ndarray) -> float:
        """计算数据一致性得分"""
        if len(values) < 2:
            return 1.0
        
        # 基于连续性的一致性评分
        differences = np.diff(values)
        mean_diff = np.mean(np.abs(differences))
        std_diff = np.std(differences)
        
        if mean_diff == 0:
            return 1.0
        
        # 一致性得分：变化率的稳定性
        consistency = 1.0 / (1.0 + std_diff / mean_diff)
        return min(1.0, consistency)

class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def generate_summary_report(analysis_results: Dict[str, Any]) -> str:
        """生成摘要报告"""
        report_lines = [
            "="*60,
            "数字孪生系统仿真分析报告",
            "="*60,
            "",
            f"📊 仿真概况:",
            f"  • 总数据点数: {analysis_results.get('total_data_points', 0)}",
            f"  • 仿真时长: {analysis_results.get('simulation_duration', 0):.1f} 秒",
            f"  • 检测故障数: {analysis_results.get('total_faults_detected', 0)}",
            f"  • 参数收敛状态: {analysis_results.get('parameter_convergence', '未知')}",
            f"  • 平均预测误差: {analysis_results.get('average_prediction_error', 0):.4f}",
            "",
        ]
        
        # 传感器统计
        if 'sensor_statistics' in analysis_results:
            report_lines.extend([
                "🔍 传感器数据统计:",
                ""
            ])
            
            for sensor, stats in analysis_results['sensor_statistics'].items():
                report_lines.extend([
                    f"  {sensor}:",
                    f"    均值: {stats['mean']:.3f}",
                    f"    标准差: {stats['std']:.4f}",
                    f"    噪声降低: {stats['noise_reduction_percent']:.1f}%",
                    f"    故障率: {stats['fault_rate']:.1f}%",
                    ""
                ])
        
        # 故障分析
        if analysis_results.get('fault_analysis', {}).get('fault_detection_enabled'):
            fault_info = analysis_results['fault_analysis']
            report_lines.extend([
                "⚠️  故障检测分析:",
                f"  • 故障类型数: {len(fault_info.get('fault_types', {}))}"
            ])
            
            for fault_type, count in fault_info.get('fault_types', {}).items():
                report_lines.append(f"    - {fault_type}: {count} 次")
            
            report_lines.append("")
        
        # 参数辨识
        if analysis_results.get('parameter_analysis', {}).get('parameter_identification_enabled'):
            param_info = analysis_results['parameter_analysis']
            report_lines.extend([
                "🎯 参数辨识结果:",
                ""
            ])
            
            for param, evolution in param_info.get('parameter_evolution', {}).items():
                report_lines.extend([
                    f"  {param}:",
                    f"    初始值: {evolution['initial_value']:.6f}",
                    f"    最终值: {evolution['final_value']:.6f}",
                    f"    总变化: {evolution['total_change']:.6f}",
                    ""
                ])
        
        report_lines.extend([
            "="*60,
            "报告生成完成",
            "="*60
        ])
        
        return "\n".join(report_lines)