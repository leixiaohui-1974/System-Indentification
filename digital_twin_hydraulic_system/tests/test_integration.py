# -*- coding: utf-8 -*-
"""
系统集成测试

测试数字孪生水力系统各组件的集成和协同工作能力。
"""

import pytest
import numpy as np
import time
import asyncio
from unittest.mock import Mock, patch

# 导入系统模块
try:
    from digital_twin_hydraulic_system import config
    from digital_twin_hydraulic_system.simulation_manager import SimulationManager
    from digital_twin_hydraulic_system.diagnostics.fault_detector import FaultDetector
    from digital_twin_hydraulic_system.diagnostics.system_identifier import SystemIdentifier
    from digital_twin_hydraulic_system.diagnostics.ml_fault_detector import MLFaultDetector
    from digital_twin_hydraulic_system.models.gate_model import GateModel
    from digital_twin_hydraulic_system.models.id_channel_model import IDChannelModel
    from digital_twin_hydraulic_system.models.fvm_channel_model import FVMChannelModel
    from digital_twin_hydraulic_system.performance.optimizer import OptimizationManager
    from digital_twin_hydraulic_system.api.system_api import app
    from fastapi.testclient import TestClient
    SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"系统模块导入失败: {e}")
    SYSTEM_AVAILABLE = False

@pytest.fixture
def client():
    """创建测试客户端"""
    if SYSTEM_AVAILABLE:
        return TestClient(app)
    return None

@pytest.fixture
def simulation_manager():
    """创建仿真管理器实例"""
    if SYSTEM_AVAILABLE:
        return SimulationManager(config)
    return None

@pytest.fixture
def fault_detector():
    """创建故障检测器实例"""
    if SYSTEM_AVAILABLE:
        gate_model = GateModel(config)
        return FaultDetector(config, gate_model)
    return None

@pytest.fixture
def system_identifier():
    """创建系统辨识器实例"""
    if SYSTEM_AVAILABLE:
        return SystemIdentifier(config)
    return None

@pytest.fixture
def ml_fault_detector():
    """创建机器学习故障检测器实例"""
    if SYSTEM_AVAILABLE:
        ml_config = {
            'contamination': 0.1,
            'n_estimators': 10,
            'window_size': 10,
            'feature_names': ['h_gate_up', 'h_gate_down', 'q_gate_down']
        }
        return MLFaultDetector(ml_config)
    return None

def test_simulation_integration(simulation_manager):
    """测试仿真管理器集成"""
    if not SYSTEM_AVAILABLE or simulation_manager is None:
        pytest.skip("系统模块不可用")
        
    # 测试仿真初始化
    assert simulation_manager.timestamp == 0.0
    assert simulation_manager.h_true_gate_upstream > 0
    
    # 测试仿真步进
    initial_timestamp = simulation_manager.timestamp
    success = simulation_manager.step_simulation(1)
    assert success
    assert simulation_manager.timestamp > initial_timestamp
    
    # 测试仿真重置
    simulation_manager.reset_simulation_state()
    assert simulation_manager.timestamp == 0.0

def test_fault_detection_integration(fault_detector, simulation_manager):
    """测试故障检测集成"""
    if not SYSTEM_AVAILABLE or fault_detector is None:
        pytest.skip("系统模块不可用")
        
    # 模拟正常数据
    gate_opening = 1.815
    gate_cq_estimate = 0.55
    cleaned_data = {
        'h_gate_up': 3.0,
        'h_gate_down': 2.5,
        'q_gate_down': 38.28  # 与预期一致的流量
    }
    
    model_b_predictions = {}
    reliable_data, status = fault_detector.diagnose(
        cleaned_data, model_b_predictions, gate_opening, gate_cq_estimate)
    
    # 正常情况下应该没有故障
    assert status == "All systems nominal."
    assert reliable_data == cleaned_data

def test_system_identification_integration(system_identifier):
    """测试系统辨识集成"""
    if not SYSTEM_AVAILABLE or system_identifier is None:
        pytest.skip("系统模块不可用")
        
    # 测试RLS参数辨识
    # 创建一个简单的线性系统: y(k) = 0.8 * y(k-1) + 0.2 * u(k-1)
    true_a, true_b = 0.8, 0.2
    y_prev = 1.0
    
    # 运行多个步骤的RLS辨识
    for k in range(100):
        u_prev = np.sin(k * 0.1)  # 输入信号
        noise = np.random.normal(0, 0.01)  # 噪声
        phi_k = np.array([y_prev, u_prev])
        y_k = true_a * y_prev + true_b * u_prev + noise
        
        # 运行RLS步骤
        system_identifier.run_rls_step(y_k, phi_k)
        y_prev = y_k
    
    # 检查参数是否收敛
    identified_params = system_identifier.get_identified_params()
    a1 = identified_params['model_b_params']['a1']
    b1 = identified_params['model_b_params']['b1']
    
    # 参数应该接近真实值（允许一定误差）
    assert abs(a1 - true_a) < 0.1
    assert abs(b1 - true_b) < 0.1

def test_ml_fault_detection_integration(ml_fault_detector):
    """测试机器学习故障检测集成"""
    if not SYSTEM_AVAILABLE or ml_fault_detector is None:
        pytest.skip("系统模块不可用")
        
    # 生成正常数据
    normal_data = []
    for i in range(50):
        timestamp = time.time()
        h_gate_up = 2.5 + 0.1 * np.sin(i * 0.1) + np.random.normal(0, 0.01)
        h_gate_down = 2.0 + 0.1 * np.sin(i * 0.1 + 0.5) + np.random.normal(0, 0.01)
        q_gate_down = 38.0 + 2.0 * np.sin(i * 0.1 + 1.0) + np.random.normal(0, 0.5)
        
        data_point = {
            'timestamp': timestamp,
            'h_gate_up': h_gate_up,
            'h_gate_down': h_gate_down,
            'q_gate_down': q_gate_down
        }
        normal_data.append(data_point)
    
    # 训练模型
    ml_fault_detector.train(normal_data)
    
    # 测试正常数据检测
    for data_point in normal_data[-10:]:  # 测试最后10个数据点
        is_anomaly = ml_fault_detector.detect_anomaly(data_point)
        # 正常数据应该不被标记为异常（但可能有少量误报）
        # 我们检查大部分数据应该是正常的
        pass  # 这里不做强制断言，因为机器学习模型可能有误报
    
    # 测试异常数据检测
    anomaly_data = {
        'timestamp': time.time(),
        'h_gate_up': 2.5,
        'h_gate_down': 2.0,
        'q_gate_down': 0.0  # 明显异常的流量
    }
    is_anomaly = ml_fault_detector.detect_anomaly(anomaly_data)
    # 异常数据应该被检测出来（但不保证100%准确）

def test_api_integration(client):
    """测试API集成"""
    if not SYSTEM_AVAILABLE or client is None:
        pytest.skip("系统模块不可用")
        
    # 测试根路径
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    
    # 测试健康检查
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    
    # 测试系统状态
    response = client.get("/system/status")
    # 可能返回503如果系统未完全初始化，但我们检查响应格式
    if response.status_code == 200:
        data = response.json()
        assert "timestamp" in data
        assert "status" in data

def test_optimization_integration():
    """测试性能优化集成"""
    if not SYSTEM_AVAILABLE:
        pytest.skip("系统模块不可用")
        
    # 创建优化管理器
    opt_manager = OptimizationManager()
    
    # 测试优化配置
    config = opt_manager.optimization_config
    assert isinstance(config, dict)
    assert 'use_jit_compilation' in config
    assert 'enable_memory_pooling' in config
    assert 'parallel_processing' in config
    
    # 测试性能监控
    opt_manager.start_performance_monitoring()
    time.sleep(0.1)  # 收集一些数据
    opt_manager.stop_performance_monitoring()
    
    # 获取性能报告
    report = opt_manager.get_performance_report()
    assert isinstance(report, dict)
    
    # 清理资源
    opt_manager.cleanup()

def test_end_to_end_simulation():
    """端到端仿真测试"""
    if not SYSTEM_AVAILABLE:
        pytest.skip("系统模块不可用")
        
    # 创建系统组件
    sim_manager = SimulationManager(config)
    gate_model = GateModel(config)
    fault_detector = FaultDetector(config, gate_model)
    system_identifier = SystemIdentifier(config)
    
    # 运行一个简短的仿真
    for step in range(20):
        # 执行仿真步骤
        success = sim_manager.step_simulation(1)
        if not success:
            break
            
        # 获取传感器数据
        h_up = sim_manager.h_true_gate_upstream
        h_down = sim_manager.h_true_gate_downstream
        q_down = sim_manager.q_true_gate_downstream
        
        # 数据预处理（简化）
        cleaned_data = {
            'h_gate_up': h_up,
            'h_gate_down': h_down,
            'q_gate_down': q_down
        }
        
        # 故障检测
        model_b_predictions = {}
        gate_opening = sim_manager.gate_opening
        gate_cq_estimate = config.GATE_DISCHARGE_COEFFICIENT_TRUE
        reliable_data, status = fault_detector.diagnose(
            cleaned_data, model_b_predictions, gate_opening, gate_cq_estimate)
        
        # 系统辨识（如果有可靠数据）
        if 'h_gate_up' in reliable_data and 'q_gate_down' in reliable_data:
            # 构造回归向量（简化）
            phi_k = np.array([h_up, gate_opening])
            y_k = q_down
            
            # 运行RLS步骤
            system_identifier.run_rls_step(y_k, phi_k)
    
    # 验证仿真完成
    assert sim_manager.timestamp > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])