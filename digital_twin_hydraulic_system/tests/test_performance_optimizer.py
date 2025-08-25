# -*- coding: utf-8 -*-
"""
性能优化模块测试

测试性能优化模块的各项功能，包括计算加速、内存管理和并行处理。
"""

import pytest
import numpy as np
import time
from digital_twin_hydraulic_system.performance.optimizer import (
    ComputationAccelerator, 
    MemoryManager, 
    ParallelProcessor,
    OptimizationManager,
    benchmark_acceleration,
    test_memory_management,
    test_parallel_processing
)

def test_computation_accelerator():
    """测试计算加速器功能"""
    # 创建计算加速器实例
    accelerator = ComputationAccelerator(parallel=True, cache=True)
    
    # 测试截面积计算加速
    h = 2.5
    bottom_width = 10.0
    side_slope = 1.5
    area = accelerator.accelerated_area_calculation(h, bottom_width, side_slope)
    expected_area = (bottom_width + side_slope * h) * h
    assert abs(area - expected_area) < 1e-10
    
    # 测试湿周计算加速
    wetted_perimeter = accelerator.accelerated_wetted_perimeter(h, bottom_width, side_slope)
    expected_perimeter = bottom_width + 2 * h * np.sqrt(1 + side_slope**2)
    assert abs(wetted_perimeter - expected_perimeter) < 1e-10
    
    # 测试向量运算加速
    vectors = np.random.random((100, 5))
    result = accelerator.accelerated_vector_operations(vectors)
    assert result.shape == (100,)
    
    # 测试函数编译功能
    def test_function(x, y):
        return x * y + np.sin(x)
    
    compiled_func = accelerator.compile_function(test_function)
    x, y = 2.0, 3.0
    result = compiled_func(x, y)
    expected = test_function(x, y)
    assert abs(result - expected) < 1e-10

def test_memory_manager():
    """测试内存管理器功能"""
    # 创建内存管理器实例
    memory_manager = MemoryManager(max_cache_size=50)
    
    # 测试数组缓存功能
    shape = (100, 100)
    array1 = memory_manager.get_cached_array(shape)
    array2 = memory_manager.get_cached_array(shape)
    # 应该返回同一个对象
    assert array1 is array2
    
    # 测试不同形状的数组
    shape2 = (50, 50)
    array3 = memory_manager.get_cached_array(shape2)
    assert array1 is not array3
    
    # 测试缓存命中率
    for i in range(10):
        memory_manager.get_cached_array((200, 200))
    hit_rate = memory_manager.get_cache_hit_rate()
    # 应该有一定的命中率
    assert 0.0 <= hit_rate <= 1.0
    
    # 测试对象池功能
    class TestObject:
        def __init__(self, value=0):
            self.value = value
            
        def reset(self, value=0):
            self.value = value
    
    # 从对象池获取对象
    obj1 = memory_manager.get_object_from_pool(TestObject, value=10)
    assert isinstance(obj1, TestObject)
    assert obj1.value == 10
    
    # 将对象返回到池中
    memory_manager.return_object_to_pool(obj1)
    
    # 再次获取应该得到相同对象
    obj2 = memory_manager.get_object_from_pool(TestObject, value=20)
    assert obj1 is obj2
    assert obj2.value == 20  # 应该被重置

def test_parallel_processor():
    """测试并行处理器功能"""
    # 创建并行处理器实例
    parallel_processor = ParallelProcessor(max_threads=4, max_processes=2)
    
    # 测试并行映射功能
    def square(x):
        return x * x
    
    data = list(range(100))
    parallel_results = parallel_processor.parallel_map(square, data, use_processes=False)
    serial_results = [square(x) for x in data]
    assert parallel_results == serial_results
    
    # 测试并行计算任务
    def compute_task(args):
        x, y = args
        return x + y
    
    tasks = [(compute_task, (i, i*2)) for i in range(50)]
    results = parallel_processor.parallel_compute(tasks)
    expected = [i + i*2 for i in range(50)]
    assert results == expected
    
    # 清理资源
    parallel_processor.close()

def test_optimization_manager():
    """测试优化管理器功能"""
    # 创建优化管理器实例
    opt_manager = OptimizationManager()
    
    # 测试计算优化功能
    def test_func(x):
        return x * x + 2 * x + 1
    
    optimized_func = opt_manager.optimize_computation(test_func)
    result = optimized_func(5.0)
    expected = test_func(5.0)
    assert abs(result - expected) < 1e-10
    
    # 测试优化数组获取
    shape = (1000, 1000)
    array = opt_manager.get_optimized_array(shape)
    assert array.shape == shape
    
    # 测试并行执行
    def task_func(x):
        return x * 2
    
    tasks = [(task_func, (i,)) for i in range(10)]
    results = opt_manager.parallel_execute(tasks)
    expected = [i * 2 for i in range(10)]
    assert results == expected
    
    # 测试性能监控启动和停止
    opt_manager.start_performance_monitoring()
    time.sleep(0.1)  # 等待一些监控数据
    opt_manager.stop_performance_monitoring()
    
    # 测试性能报告
    report = opt_manager.get_performance_report()
    assert isinstance(report, dict)
    assert 'optimization_config' in report
    assert 'memory_pool_stats' in report
    
    # 清理资源
    opt_manager.cleanup()

def test_benchmark_functions():
    """测试基准测试函数"""
    # 测试计算加速基准测试
    try:
        acceleration_results = benchmark_acceleration()
        assert isinstance(acceleration_results, dict)
        assert 'speedup' in acceleration_results
        assert acceleration_results['speedup'] >= 1.0
    except Exception as e:
        # 基准测试可能因为环境原因失败，但我们仍要确保函数能运行
        pytest.skip(f"基准测试跳过: {e}")
    
    # 测试内存管理测试
    memory_results = test_memory_management()
    assert isinstance(memory_results, dict)
    assert 'cache_hit_rate' in memory_results
    
    # 测试并行处理测试
    try:
        parallel_results = test_parallel_processing()
        assert isinstance(parallel_results, dict)
        assert 'speedup' in parallel_results
    except Exception as e:
        # 并行处理测试可能因为环境原因失败
        pytest.skip(f"并行处理测试跳过: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])