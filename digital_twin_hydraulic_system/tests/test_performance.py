# -*- coding: utf-8 -*-
"""
性能测试模块

测试系统的性能表现，包括计算速度、内存使用和并发处理能力。
"""

import pytest
import time
import numpy as np
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import asyncio

# 导入系统模块
try:
    from digital_twin_hydraulic_system import config
    from digital_twin_hydraulic_system.simulation_manager import SimulationManager
    from digital_twin_hydraulic_system.models.fvm_channel_model import FVMChannelModel
    from digital_twin_hydraulic_system.models.id_channel_model import IDChannelModel
    from digital_twin_hydraulic_system.performance.optimizer import (
        ComputationAccelerator, 
        MemoryManager, 
        ParallelProcessor,
        OptimizationManager
    )
    from digital_twin_hydraulic_system.diagnostics.system_identifier import SystemIdentifier
    SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"系统模块导入失败: {e}")
    SYSTEM_AVAILABLE = False

def measure_execution_time(func, *args, **kwargs):
    """测量函数执行时间"""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    return result, execution_time

def get_memory_usage():
    """获取当前内存使用量（MB）"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_fvm_model_performance():
    """测试FVM模型性能"""
    # 创建FVM模型实例
    fvm_model = FVMChannelModel(config)
    
    # 准备测试数据
    initial_conditions = np.array([2.5, 2.4, 2.3, 2.2, 2.1])  # 5个网格点的初始水深
    boundary_conditions = (2.5, 2.0)  # 上游和下游边界条件
    dt = 1.0
    dx = 100.0
    
    # 测试单步计算性能
    result, exec_time = measure_execution_time(
        fvm_model.compute_next_step,
        initial_conditions, boundary_conditions, dt, dx
    )
    
    print(f"FVM单步计算时间: {exec_time:.6f}秒")
    assert exec_time < 1.0  # 应该在1秒内完成
    assert isinstance(result, np.ndarray)
    assert result.shape == initial_conditions.shape

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_id_model_performance():
    """测试ID模型性能"""
    # 创建ID模型实例
    id_model = IDChannelModel(config)
    
    # 准备测试数据
    h_upstream = 2.5
    gate_opening = 1.815
    dt = 1.0
    
    # 测试单步计算性能
    result, exec_time = measure_execution_time(
        id_model.compute_next_step,
        h_upstream, gate_opening, dt
    )
    
    print(f"ID单步计算时间: {exec_time:.6f}秒")
    assert exec_time < 0.1  # 应该在0.1秒内完成
    assert isinstance(result, tuple)
    assert len(result) == 2  # 应该返回(h_downstream, q_downstream)

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_rls_identification_performance():
    """测试RLS参数辨识性能"""
    # 创建系统辨识器实例
    identifier = SystemIdentifier(config)
    
    # 准备测试数据
    y_k = 1.5
    phi_k = np.array([1.2, 0.8])
    
    # 测试RLS步骤性能
    result, exec_time = measure_execution_time(
        identifier.run_rls_step,
        y_k, phi_k
    )
    
    print(f"RLS单步计算时间: {exec_time:.6f}秒")
    assert exec_time < 0.01  # 应该在0.01秒内完成

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_computation_accelerator_performance():
    """测试计算加速器性能"""
    # 创建计算加速器实例
    accelerator = ComputationAccelerator(parallel=True, cache=True)
    
    # 测试向量运算性能
    vectors = np.random.random((10000, 10))
    
    # 原始计算
    def original_computation(vectors):
        result = np.empty(vectors.shape[0])
        for i in range(vectors.shape[0]):
            result[i] = np.sum(vectors[i] * np.sin(vectors[i])) + np.prod(vectors[i])
        return result
    
    original_result, original_time = measure_execution_time(original_computation, vectors)
    
    # 加速计算
    accelerated_result, accelerated_time = measure_execution_time(
        accelerator.accelerated_vector_operations, vectors
    )
    
    print(f"原始计算时间: {original_time:.6f}秒")
    print(f"加速计算时间: {accelerated_time:.6f}秒")
    print(f"加速比: {original_time/accelerated_time:.2f}x")
    
    # 验证结果一致性
    assert np.allclose(original_result, accelerated_result, rtol=1e-10)
    
    # 应该有显著的性能提升
    assert accelerated_time < original_time

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_memory_management_performance():
    """测试内存管理性能"""
    # 创建内存管理器实例
    memory_manager = MemoryManager(max_cache_size=100)
    
    # 测试内存使用情况
    initial_memory = get_memory_usage()
    
    # 分配大量数组
    arrays = []
    for i in range(1000):
        shape = (100, 100)
        array = memory_manager.get_cached_array(shape)
        arrays.append(array)
    
    # 检查内存使用
    peak_memory = get_memory_usage()
    memory_increase = peak_memory - initial_memory
    print(f"内存增加: {memory_increase:.2f} MB")
    
    # 由于使用了缓存，内存增加应该有限
    # （具体限制取决于系统，但我们检查没有异常增长）
    assert memory_increase < 100  # 假设不超过100MB增长

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_parallel_processing_performance():
    """测试并行处理性能"""
    # 创建并行处理器实例
    parallel_processor = ParallelProcessor(max_threads=4)
    
    # 定义计算密集型任务
    def compute_task(n):
        # 模拟计算密集型工作
        result = 0
        for i in range(n):
            result += np.sin(i * 0.01) * np.cos(i * 0.01)
        return result
    
    # 测试数据
    test_data = [10000] * 100  # 100个任务，每个计算10000次
    
    # 串行执行
    start_time = time.perf_counter()
    serial_results = [compute_task(n) for n in test_data]
    serial_time = time.perf_counter() - start_time
    
    # 并行执行
    start_time = time.perf_counter()
    parallel_results = parallel_processor.parallel_map(compute_task, test_data)
    parallel_time = time.perf_counter() - start_time
    
    print(f"串行执行时间: {serial_time:.4f}秒")
    print(f"并行执行时间: {parallel_time:.4f}秒")
    if parallel_time > 0:
        print(f"加速比: {serial_time/parallel_time:.2f}x")
    
    # 验证结果一致性
    assert len(serial_results) == len(parallel_results)
    for s, p in zip(serial_results, parallel_results):
        assert abs(s - p) < 1e-10
    
    # 并行执行应该更快（在多核系统上）
    # 注意：在某些系统上可能不会更快，所以我们不做强制断言
    # 但我们会报告性能数据
    
    # 清理资源
    parallel_processor.close()

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_simulation_manager_performance():
    """测试仿真管理器性能"""
    # 创建仿真管理器实例
    sim_manager = SimulationManager(config)
    
    # 测试仿真步进性能
    num_steps = 1000
    start_time = time.perf_counter()
    
    for _ in range(num_steps):
        success = sim_manager.step_simulation(1)
        if not success:
            break
    
    total_time = time.perf_counter() - start_time
    steps_per_second = num_steps / total_time if total_time > 0 else 0
    
    print(f"仿真步进性能: {steps_per_second:.2f} 步/秒")
    print(f"平均每步时间: {1000*total_time/num_steps:.4f} 毫秒")
    
    # 应该能够维持一定的仿真速度
    assert steps_per_second > 10  # 每秒至少10步

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_concurrent_access_performance():
    """测试并发访问性能"""
    # 创建共享资源
    sim_manager = SimulationManager(config)
    
    # 定义并发任务
    def simulation_task(task_id):
        results = []
        for i in range(10):
            success = sim_manager.step_simulation(1)
            results.append((task_id, i, success, sim_manager.timestamp))
            time.sleep(0.001)  # 短暂延迟
        return results
    
    # 使用线程池执行并发任务
    with ThreadPoolExecutor(max_workers=4) as executor:
        start_time = time.perf_counter()
        futures = [executor.submit(simulation_task, i) for i in range(4)]
        results = [future.result() for future in futures]
        total_time = time.perf_counter() - start_time
    
    print(f"并发执行时间: {total_time:.4f}秒")
    
    # 验证所有任务都完成了
    assert len(results) == 4
    for task_results in results:
        assert len(task_results) == 10

@pytest.mark.skipif(not SYSTEM_AVAILABLE, reason="系统模块不可用")
def test_optimization_manager_performance():
    """测试优化管理器性能"""
    # 创建优化管理器实例
    opt_manager = OptimizationManager()
    
    # 测试性能监控开销
    start_time = time.perf_counter()
    opt_manager.start_performance_monitoring()
    time.sleep(0.5)  # 监控0.5秒
    opt_manager.stop_performance_monitoring()
    monitoring_time = time.perf_counter() - start_time
    
    print(f"性能监控开销: {monitoring_time:.4f}秒")
    
    # 获取性能报告
    report = opt_manager.get_performance_report()
    assert isinstance(report, dict)
    assert 'optimization_config' in report
    
    # 清理资源
    opt_manager.cleanup()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])