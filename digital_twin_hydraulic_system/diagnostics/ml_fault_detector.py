# -*- coding: utf-8 -*-
"""
机器学习故障诊断模块

集成多种机器学习算法，实现智能故障检测、分类和预测性维护功能。
该模块能够自动学习正常工况下的数据模式，并检测异常行为。
"""

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging
from collections import deque
import json
import joblib

logger = logging.getLogger(__name__)

class MLFaultDetector:
    """
    基于机器学习的故障检测器
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化机器学习故障检测器
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        
        # 算法配置
        self.contamination = self.config.get('contamination', 0.1)  # 异常比例
        self.n_estimators = self.config.get('n_estimators', 100)   # 随机森林树数
        self.window_size = self.config.get('window_size', 50)      # 滑动窗口大小
        self.feature_names = self.config.get('feature_names', [])   # 特征名称
        
        # 初始化算法模型
        self.isolation_forest = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=42
        )
        
        self.one_class_svm = OneClassSVM(
            nu=self.contamination,
            kernel='rbf',
            gamma='scale'
        )
        
        self.random_forest = RandomForestClassifier(
            n_estimators=self.n_estimators,
            random_state=42
        )
        
        # 数据预处理
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # 数据缓冲区
        self.data_buffer = deque(maxlen=self.window_size)
        self.label_buffer = deque(maxlen=self.window_size)
        
        # 特征重要性
        self.feature_importance = {}
        
        logger.info("机器学习故障检测器初始化完成")
    
    def add_data(self, features: Dict[str, float], label: Optional[int] = None):
        """
        添加训练或检测数据
        
        Args:
            features: 特征字典
            label: 标签（0=正常，1=异常，None=未知）
        """
        # 将特征转换为数组
        if not self.feature_names:
            self.feature_names = list(features.keys())
        
        feature_vector = [features.get(name, 0.0) for name in self.feature_names]
        self.data_buffer.append(feature_vector)
        
        if label is not None:
            self.label_buffer.append(label)
    
    def fit_normal_behavior(self, normal_data: Optional[np.ndarray] = None):
        """
        训练正常行为模型
        
        Args:
            normal_data: 正常数据数组 (n_samples, n_features)
        """
        if normal_data is None:
            if len(self.data_buffer) == 0:
                logger.warning("没有数据可用于训练")
                return
            
            normal_data = np.array(self.data_buffer)
        
        # 数据标准化
        normalized_data = self.scaler.fit_transform(normal_data)
        
        # 训练无监督模型
        self.isolation_forest.fit(normalized_data)
        self.one_class_svm.fit(normalized_data)
        
        self.is_fitted = True
        logger.info(f"正常行为模型训练完成，使用 {len(normal_data)} 个样本")
    
    def fit_fault_classifier(self, labeled_data: Optional[Tuple[np.ndarray, np.ndarray]] = None):
        """
        训练故障分类器
        
        Args:
            labeled_data: (特征数组, 标签数组) 的元组
        """
        if labeled_data is None:
            if len(self.data_buffer) == 0 or len(self.label_buffer) == 0:
                logger.warning("没有标记数据可用于训练分类器")
                return
            
            features = np.array(self.data_buffer)
            labels = np.array(self.label_buffer)
        else:
            features, labels = labeled_data
        
        # 数据标准化
        normalized_features = self.scaler.fit_transform(features)
        
        # 训练分类器
        self.random_forest.fit(normalized_features, labels)
        
        # 计算特征重要性
        importances = self.random_forest.feature_importances_
        self.feature_importance = dict(zip(self.feature_names, importances))
        
        self.is_fitted = True
        logger.info(f"故障分类器训练完成，使用 {len(features)} 个样本")
    
    def detect_anomalies(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        检测异常
        
        Args:
            features: 特征字典
            
        Returns:
            检测结果字典
        """
        if not self.is_fitted:
            logger.warning("模型未训练，无法进行异常检测")
            return {'anomaly': False, 'confidence': 0.0}
        
        # 准备特征向量
        feature_vector = np.array([[features.get(name, 0.0) for name in self.feature_names]])
        normalized_vector = self.scaler.transform(feature_vector)
        
        # 使用多种算法进行检测
        iso_pred = self.isolation_forest.predict(normalized_vector)[0]
        svm_pred = self.one_class_svm.predict(normalized_vector)[0]
        
        # 计算异常分数
        iso_score = self.isolation_forest.decision_function(normalized_vector)[0]
        svm_score = self.one_class_svm.decision_function(normalized_vector)[0]
        
        # 综合判断
        is_anomaly = (iso_pred == -1) or (svm_pred == -1)
        confidence = (iso_score + svm_score) / 2  # 简单平均
        
        # 标准化置信度到0-1范围
        confidence = 1 / (1 + np.exp(-confidence))  # Sigmoid函数
        
        result = {
            'anomaly': is_anomaly,
            'confidence': float(confidence),
            'iso_prediction': int(iso_pred),
            'svm_prediction': int(svm_pred),
            'iso_score': float(iso_score),
            'svm_score': float(svm_score)
        }
        
        return result
    
    def classify_fault(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        故障分类
        
        Args:
            features: 特征字典
            
        Returns:
            分类结果字典
        """
        if not self.is_fitted:
            logger.warning("分类器未训练，无法进行故障分类")
            return {'fault_type': 'unknown', 'probability': 0.0}
        
        # 准备特征向量
        feature_vector = np.array([[features.get(name, 0.0) for name in self.feature_names]])
        normalized_vector = self.scaler.transform(feature_vector)
        
        # 预测类别和概率
        prediction = self.random_forest.predict(normalized_vector)[0]
        probabilities = self.random_forest.predict_proba(normalized_vector)[0]
        max_prob = np.max(probabilities)
        
        # 获取类别名称
        class_names = self.random_forest.classes_
        fault_type = class_names[prediction] if len(class_names) > prediction else f"class_{prediction}"
        
        result = {
            'fault_type': str(fault_type),
            'probability': float(max_prob),
            'all_probabilities': dict(zip(map(str, class_names), map(float, probabilities)))
        }
        
        return result
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        获取特征重要性
        
        Returns:
            特征重要性字典
        """
        return self.feature_importance.copy()
    
    def save_model(self, filepath: str):
        """
        保存模型到文件
        
        Args:
            filepath: 文件路径
        """
        model_data = {
            'isolation_forest': self.isolation_forest,
            'one_class_svm': self.one_class_svm,
            'random_forest': self.random_forest,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'config': self.config
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"模型已保存到 {filepath}")
    
    def load_model(self, filepath: str):
        """
        从文件加载模型
        
        Args:
            filepath: 文件路径
        """
        model_data = joblib.load(filepath)
        
        self.isolation_forest = model_data['isolation_forest']
        self.one_class_svm = model_data['one_class_svm']
        self.random_forest = model_data['random_forest']
        self.scaler = model_data['scaler']
        self.is_fitted = model_data['is_fitted']
        self.feature_names = model_data['feature_names']
        self.feature_importance = model_data['feature_importance']
        self.config = model_data['config']
        
        logger.info(f"模型已从 {filepath} 加载")


class PredictiveMaintenance:
    """
    预测性维护系统
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化预测性维护系统
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.maintenance_threshold = self.config.get('maintenance_threshold', 0.7)
        self.prediction_horizon = self.config.get('prediction_horizon', 100)  # 预测时间窗口
        
        # 健康指标历史
        self.health_history = deque(maxlen=1000)
        self.maintenance_records = []
        
        logger.info("预测性维护系统初始化完成")
    
    def update_health_indicator(self, timestamp: float, health_score: float, 
                              features: Dict[str, float]):
        """
        更新健康指标
        
        Args:
            timestamp: 时间戳
            health_score: 健康分数 (0-1, 1表示完全健康)
            features: 相关特征
        """
        health_record = {
            'timestamp': timestamp,
            'health_score': health_score,
            'features': features.copy()
        }
        
        self.health_history.append(health_record)
    
    def predict_maintenance_need(self) -> Dict[str, Any]:
        """
        预测维护需求
        
        Returns:
            预测结果字典
        """
        if len(self.health_history) < 10:
            return {'need_maintenance': False, 'urgency': 0.0, 'predicted_time': None}
        
        # 使用简单的线性趋势预测
        recent_records = list(self.health_history)[-20:]  # 最近20个记录
        timestamps = np.array([r['timestamp'] for r in recent_records])
        health_scores = np.array([r['health_score'] for r in recent_records])
        
        # 计算健康趋势
        if len(timestamps) >= 2:
            # 线性回归计算趋势
            A = np.vstack([timestamps, np.ones(len(timestamps))]).T
            slope, intercept = np.linalg.lstsq(A, health_scores, rcond=None)[0]
            
            # 预测何时达到维护阈值
            if slope < 0:  # 健康状况在下降
                predicted_time = (self.maintenance_threshold - intercept) / slope
                time_to_maintenance = max(0, predicted_time - timestamps[-1])
                
                # 计算紧急程度
                urgency = min(1.0, (health_scores[-1] - self.maintenance_threshold) / 
                             (1.0 - self.maintenance_threshold))
                urgency = max(0.0, urgency)
                
                need_maintenance = health_scores[-1] <= self.maintenance_threshold or \
                                 time_to_maintenance <= self.prediction_horizon
                
                return {
                    'need_maintenance': bool(need_maintenance),
                    'urgency': float(urgency),
                    'predicted_time': float(predicted_time),
                    'time_to_maintenance': float(time_to_maintenance),
                    'health_trend': float(slope)
                }
        
        # 默认情况
        current_health = health_scores[-1] if len(health_scores) > 0 else 1.0
        urgency = max(0.0, min(1.0, (1.0 - current_health) / (1.0 - self.maintenance_threshold)))
        
        return {
            'need_maintenance': current_health <= self.maintenance_threshold,
            'urgency': float(urgency),
            'predicted_time': None,
            'time_to_maintenance': None,
            'health_trend': 0.0
        }
    
    def record_maintenance(self, timestamp: float, maintenance_type: str, 
                          description: str = ""):
        """
        记录维护事件
        
        Args:
            timestamp: 时间戳
            maintenance_type: 维护类型
            description: 描述
        """
        record = {
            'timestamp': timestamp,
            'type': maintenance_type,
            'description': description
        }
        
        self.maintenance_records.append(record)
        logger.info(f"维护记录已添加: {maintenance_type} at {timestamp}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        获取健康报告
        
        Returns:
            健康报告字典
        """
        if len(self.health_history) == 0:
            return {'status': 'no_data', 'health_score': 1.0}
        
        latest_health = self.health_history[-1]['health_score']
        avg_health = np.mean([r['health_score'] for r in self.health_history])
        
        # 计算健康趋势
        if len(self.health_history) >= 2:
            scores = [r['health_score'] for r in self.health_history]
            trend = np.mean(np.diff(scores[-min(10, len(scores)):]))  # 最近10个点的趋势
        else:
            trend = 0.0
        
        status = 'healthy' if latest_health > 0.8 else \
                'degraded' if latest_health > 0.5 else 'critical'
        
        return {
            'status': status,
            'latest_health_score': float(latest_health),
            'average_health_score': float(avg_health),
            'health_trend': float(trend),
            'total_records': len(self.health_history),
            'maintenance_records': len(self.maintenance_records)
        }


class FaultPatternAnalyzer:
    """
    故障模式分析器
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化故障模式分析器
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.pattern_window = self.config.get('pattern_window', 100)  # 模式分析窗口
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)
        
        # 故障模式库
        self.fault_patterns = {}
        self.pattern_counter = 0
        
        logger.info("故障模式分析器初始化完成")
    
    def extract_features(self, data_window: List[Dict[str, float]]) -> Dict[str, float]:
        """
        从数据窗口中提取特征
        
        Args:
            data_window: 数据窗口列表
            
        Returns:
            特征字典
        """
        if not data_window:
            return {}
        
        features = {}
        df = pd.DataFrame(data_window)
        
        # 统计特征
        for column in df.columns:
            if df[column].dtype in ['int64', 'float64']:
                features[f'{column}_mean'] = float(df[column].mean())
                features[f'{column}_std'] = float(df[column].std())
                features[f'{column}_min'] = float(df[column].min())
                features[f'{column}_max'] = float(df[column].max())
                features[f'{column}_range'] = float(df[column].max() - df[column].min())
                
                # 趋势特征
                if len(df[column]) >= 2:
                    features[f'{column}_trend'] = float(np.polyfit(range(len(df[column])), df[column], 1)[0])
        
        return features
    
    def identify_pattern(self, features: Dict[str, float], pattern_id: Optional[str] = None) -> str:
        """
        识别或创建故障模式
        
        Args:
            features: 特征字典
            pattern_id: 模式ID（如果已知）
            
        Returns:
            模式ID
        """
        if pattern_id is None:
            # 创建新模式ID
            pattern_id = f"pattern_{self.pattern_counter}"
            self.pattern_counter += 1
        
        # 存储模式
        self.fault_patterns[pattern_id] = {
            'features': features.copy(),
            'timestamp': pd.Timestamp.now(),
            'occurrences': self.fault_patterns.get(pattern_id, {}).get('occurrences', 0) + 1
        }
        
        logger.info(f"识别到故障模式: {pattern_id}")
        return pattern_id
    
    def find_similar_patterns(self, features: Dict[str, float]) -> List[Tuple[str, float]]:
        """
        查找相似的故障模式
        
        Args:
            features: 特征字典
            
        Returns:
            相似模式列表 [(pattern_id, similarity_score), ...]
        """
        if not self.fault_patterns:
            return []
        
        similarities = []
        feature_vector = np.array(list(features.values()))
        
        for pattern_id, pattern_data in self.fault_patterns.items():
            pattern_features = pattern_data['features']
            pattern_vector = np.array([pattern_features.get(k, 0) for k in features.keys()])
            
            # 计算余弦相似度
            dot_product = np.dot(feature_vector, pattern_vector)
            norm_product = np.linalg.norm(feature_vector) * np.linalg.norm(pattern_vector)
            
            if norm_product > 0:
                similarity = dot_product / norm_product
                similarities.append((pattern_id, float(similarity)))
        
        # 按相似度排序并过滤
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [(pid, score) for pid, score in similarities if score >= self.similarity_threshold]
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        获取模式统计信息
        
        Returns:
            统计信息字典
        """
        if not self.fault_patterns:
            return {'total_patterns': 0}
        
        total_occurrences = sum(p['occurrences'] for p in self.fault_patterns.values())
        most_common = max(self.fault_patterns.items(), key=lambda x: x[1]['occurrences'])
        
        return {
            'total_patterns': len(self.fault_patterns),
            'total_occurrences': total_occurrences,
            'most_common_pattern': most_common[0],
            'most_common_count': most_common[1]['occurrences'],
            'average_occurrences': total_occurrences / len(self.fault_patterns)
        }


# 测试和验证函数
def test_ml_fault_detector():
    """
    测试机器学习故障检测器
    """
    logger.info("开始测试机器学习故障检测器")
    
    # 配置参数
    config = {
        'contamination': 0.1,
        'n_estimators': 50,
        'window_size': 30,
        'feature_names': ['temperature', 'pressure', 'vibration']
    }
    
    # 创建检测器
    detector = MLFaultDetector(config)
    
    # 生成正常数据
    np.random.seed(42)
    normal_data = []
    for _ in range(200):
        temp = np.random.normal(25, 2)  # 温度
        pressure = np.random.normal(100, 5)  # 压力
        vibration = np.random.normal(0.1, 0.02)  # 振动
        normal_data.append([temp, pressure, vibration])
    
    # 训练正常行为模型
    detector.fit_normal_behavior(np.array(normal_data))
    
    # 测试正常数据
    normal_features = {'temperature': 24.5, 'pressure': 99.8, 'vibration': 0.09}
    result = detector.detect_anomalies(normal_features)
    logger.info(f"正常数据检测结果: {result}")
    
    # 测试异常数据
    anomaly_features = {'temperature': 50.0, 'pressure': 150.0, 'vibration': 0.5}
    result = detector.detect_anomalies(anomaly_features)
    logger.info(f"异常数据检测结果: {result}")
    
    logger.info("机器学习故障检测器测试完成")


def test_predictive_maintenance():
    """
    测试预测性维护系统
    """
    logger.info("开始测试预测性维护系统")
    
    # 创建系统
    pm = PredictiveMaintenance({'maintenance_threshold': 0.7, 'prediction_horizon': 50})
    
    # 模拟健康数据下降
    for i in range(100):
        timestamp = i * 10  # 每10秒一个记录
        health_score = max(0.5, 1.0 - i * 0.005)  # 逐渐下降的健康分数
        features = {'temp': 25 + i * 0.1, 'pressure': 100 + i * 0.2}
        
        pm.update_health_indicator(timestamp, health_score, features)
    
    # 预测维护需求
    prediction = pm.predict_maintenance_need()
    logger.info(f"维护预测结果: {prediction}")
    
    # 获取健康报告
    report = pm.get_health_report()
    logger.info(f"健康报告: {report}")
    
    logger.info("预测性维护系统测试完成")


if __name__ == "__main__":
    # 运行测试
    logging.basicConfig(level=logging.INFO)
    
    # 测试机器学习故障检测
    try:
        test_ml_fault_detector()
    except Exception as e:
        logger.error(f"机器学习故障检测测试失败: {e}")
    
    # 测试预测性维护
    try:
        test_predictive_maintenance()
    except Exception as e:
        logger.error(f"预测性维护测试失败: {e}")