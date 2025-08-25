# -*- coding: utf-8 -*-
"""
性能优化模块

提供系统性能优化功能，包括计算加速、内存管理和并行处理优化。
该模块旨在提升数字孪生系统的计算效率和实时响应能力。
"""

import numpy as np
from numba import jit, njit, prange
from typing import Dict, List, Tuple, Optional, Callable
import logging
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
import functools

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    cpu_usage: float
    memory_usage: float
    execution_time: float
    throughput: float
    cache_hit_rate: float

class ComputationAccelerator:
    """
    计算加速器，使用Numba JIT编译优化数值计算
    """
    
    def __init__(self, parallel: bool = True, cache: bool = True):
        """
        初始化计算加速器
        
        Args:
            parallel: 是否启用并行计算
            cache: 是否缓存编译结果
        """
        self.parallel = parallel
        self.cache = cache
        self.compilation_cache = {}
        logger.info(f"计算加速器初始化完成 - 并行: {parallel}, 缓存: {cache}")
    
    @staticmethod
    @njit(fastmath=True, cache=True)
    def accelerated_area_calculation(h: float, bottom_width: float, side_slope: float) -> float:
        """
        加速的截面积计算
        
        Args:
            h: 水深
            bottom_width: 渠道底宽
            side_slope: 边坡系数
            
        Returns:
            截面积
        """
        return (bottom_width + side_slope * h) * h
    
    @staticmethod
    @njit(fastmath=True, cache=True)
    def accelerated_wetted_perimeter(h: float, bottom_width: float, side_slope: float) -> float:
        """
        加速的湿周计算
        
        Args:
            h: 水深
            bottom_width: 渠道底宽
            side_slope: 边坡系数
            
        Returns:
            湿周
        """
        return bottom_width + 2 * h * np.sqrt(1 + side_slope**2)
    
    @staticmethod
    @njit(fastmath=True, parallel=True, cache=True)
    def accelerated_vector_operations(vectors: np.ndarray) -> np.ndarray:
        """
        加速的向量运算
        
        Args:
            vectors: 输入向量数组 (n, m)
            
        Returns:
            运算结果向量 (n,)
        """
        result = np.empty(vectors.shape[0])
        for i in prange(vectors.shape[0]):
            # 复杂的向量运算示例
            result[i] = np.sum(vectors[i] * np.sin(vectors[i])) + np.prod(vectors[i])
        return result
    
    def compile_function(self, func: Callable, *args) -> Callable:
        """
        编译函数以提高执行速度
        
        Args:
            func: 要编译的函数
            *args: 函数参数类型注解
            
        Returns:
            编译后的函数
        """
        # 创建唯一的缓存键
        cache_key = f"{func.__name__}_{hash(args)}"
        
        if cache_key in self.compilation_cache:
            return self.compilation_cache[cache_key]
        
        # 应用JIT装饰器
        if self.parallel:
            compiled_func = njit(func, fastmath=True, parallel=True, cache=self.cache)
        else:
            compiled_func = njit(func, fastmath=True, cache=self.cache)
        
        self.compilation_cache[cache_key] = compiled_func
        logger.debug(f"函数 {func.__name__} 已编译并缓存")
        return compiled_func


class MemoryManager:
    """
    内存管理器，优化内存使用和分配
    """
    
    def __init__(self, max_cache_size: int = 100):
        """
        初始化内存管理器
        
        Args:
            max_cache_size: 最大缓存大小
        """
        self.max_cache_size = max_cache_size
        self.object_pool = {}
        self.memory_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        logger.info(f"内存管理器初始化完成 - 最大缓存: {max_cache_size}")
    
    def get_cached_array(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> np.ndarray:
        """
        获取缓存的数组对象，避免重复分配
        
        Args:
            shape: 数组形状
            dtype: 数据类型
            
        Returns:
            数组对象
        """
        cache_key = f"array_{shape}_{dtype}"
        
        if cache_key in self.memory_cache:
            self.cache_stats['hits'] += 1
            return self.memory_cache[cache_key]
        
        self.cache_stats['misses'] += 1
        # 创建新数组
        array = np.empty(shape, dtype=dtype)
        self.memory_cache[cache_key] = array
        
        # 维护缓存大小
        if len(self.memory_cache) > self.max_cache_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        return array
    
    def get_object_from_pool(self, obj_type: type, **kwargs) -> object:
        """
        从对象池获取对象
        
        Args:
            obj_type: 对象类型
            **kwargs: 对象初始化参数
            
        Returns:
            对象实例
        """
        pool_key = f"{obj_type.__name__}_{hash(frozenset(kwargs.items()))}"
        
        if pool_key not in self.object_pool:
            self.object_pool[pool_key] = []
        
        pool = self.object_pool[pool_key]
        if pool:
            obj = pool.pop()
            # 重置对象状态
            if hasattr(obj, 'reset'):
                obj.reset(**kwargs)
            return obj
        else:
            # 创建新对象
            return obj_type(**kwargs)
    
    def return_object_to_pool(self, obj: object):
        """
        将对象返回到对象池
        
        Args:
            obj: 对象实例
        """
        obj_type = type(obj)
        pool_key = f"{obj_type.__name__}_{id(obj)}"  # 简化处理
        
        if pool_key not in self.object_pool:
            self.object_pool[pool_key] = []
        
        pool = self.object_pool[pool_key]
        if len(pool) < 10:  # 限制池大小
            pool.append(obj)
    
    def get_cache_hit_rate(self) -> float:
        """
        获取缓存命中率
        
        Returns:
            缓存命中率
        """
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        if total == 0:
            return 0.0
        return self.cache_stats['hits'] / total


class ParallelProcessor:
    """
    并行处理器，管理多线程和多进程计算
    """
    
    def __init__(self, max_threads: Optional[int] = None, max_processes: Optional[int] = None):
        """
        初始化并行处理器
        
        Args:
            max_threads: 最大线程数
            max_processes: 最大进程数
        """
        self.max_threads = max_threads or min(32, (psutil.cpu_count() or 1) + 4)
        self.max_processes = max_processes or psutil.cpu_count()
        
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_threads)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_processes)
        
        logger.info(f"并行处理器初始化完成 - 线程: {self.max_threads}, 进程: {self.max_processes}")
    
    def parallel_map(self, func: Callable, data: List, use_processes: bool = False) -> List:
        """
        并行映射函数到数据列表
        
        Args:
            func: 要应用的函数
            data: 数据列表
            use_processes: 是否使用进程（否则使用线程）
            
        Returns:
            结果列表
        """
        if use_processes:
            return list(self.process_pool.map(func, data))
        else:
            return list(self.thread_pool.map(func, data))
    
    def parallel_compute(self, tasks: List[Tuple[Callable, Tuple]]) -> List:
        """
        并行执行计算任务
        
        Args:
            tasks: 任务列表 [(function, args), ...]
            
        Returns:
            结果列表
        """
        futures = []
        for func, args in tasks:
            future = self.thread_pool.submit(func, *args)
            futures.append(future)
        
        # 收集结果
        results = []
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"并行计算任务失败: {e}")
                results.append(None)
        
        return results
    
    def close(self):
        """关闭线程池和进程池"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)


class PerformanceMonitor:
    """
    性能监控器，实时监控系统性能指标
    """
    
    def __init__(self, sampling_interval: float = 1.0):
        """
        初始化性能监控器
        
        Args:
            sampling_interval: 采样间隔（秒）
        """
        self.sampling_interval = sampling_interval
        self.metrics_history = []
        self.monitoring = False
        self.monitor_thread = None
        logger.info(f"性能监控器初始化完成 - 采样间隔: {sampling_interval}s")
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 保持历史记录大小
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)
                
                time.sleep(self.sampling_interval)
            except Exception as e:
                logger.error(f"性能监控循环错误: {e}")
                time.sleep(self.sampling_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 内存使用率
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent
        
        # 简化的执行时间（模拟）
        execution_time = np.random.exponential(0.01)  # 毫秒
        
        # 吞吐量（模拟）
        throughput = np.random.normal(1000, 100)  # 操作/秒
        
        # 缓存命中率（模拟）
        cache_hit_rate = np.random.beta(9, 1)  # 90%命中率
        
        return PerformanceMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory_percent,
            execution_time=execution_time,
            throughput=throughput,
            cache_hit_rate=cache_hit_rate
        )
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_average_metrics(self, window_size: int = 10) -> Optional[PerformanceMetrics]:
        """获取平均性能指标"""
        if len(self.metrics_history) < window_size:
            return None
        
        recent_metrics = self.metrics_history[-window_size:]
        
        avg_cpu = np.mean([m.cpu_usage for m in recent_metrics])
        avg_memory = np.mean([m.memory_usage for m in recent_metrics])
        avg_execution = np.mean([m.execution_time for m in recent_metrics])
        avg_throughput = np.mean([m.throughput for m in recent_metrics])
        avg_cache = np.mean([m.cache_hit_rate for m in recent_metrics])
        
        return PerformanceMetrics(
            cpu_usage=avg_cpu,
            memory_usage=avg_memory,
            execution_time=avg_execution,
            throughput=avg_throughput,
            cache_hit_rate=avg_cache
        )


class OptimizationManager:
    """
    优化管理器，协调各种优化策略
    """
    
    def __init__(self):
        """初始化优化管理器"""
        self.accelerator = ComputationAccelerator()
        self.memory_manager = MemoryManager()
        self.parallel_processor = ParallelProcessor()
        self.performance_monitor = PerformanceMonitor()
        
        # 优化配置
        self.optimization_config = {
            'use_jit_compilation': True,
            'enable_memory_pooling': True,
            'parallel_processing': True,
            'cache_results': True
        }
        
        logger.info("优化管理器初始化完成")
    
    def optimize_computation(self, func: Callable) -> Callable:
        """
        优化计算函数
        
        Args:
            func: 要优化的函数
            
        Returns:
            优化后的函数
        """
        if self.optimization_config['use_jit_compilation']:
            # 使用JIT编译优化
            return self.accelerator.compile_function(func)
        return func
    
    def get_optimized_array(self, shape: Tuple[int, ...], dtype: np.dtype = np.float64) -> np.ndarray:
        """
        获取优化的数组
        
        Args:
            shape: 数组形状
            dtype: 数据类型
            
        Returns:
            优化的数组
        """
        if self.optimization_config['enable_memory_pooling']:
            return self.memory_manager.get_cached_array(shape, dtype)
        return np.empty(shape, dtype=dtype)
    
    def parallel_execute(self, tasks: List[Tuple[Callable, Tuple]]) -> List:
        """
        并行执行任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            执行结果
        """
        if self.optimization_config['parallel_processing']:
            return self.parallel_processor.parallel_compute(tasks)
        else:
            # 串行执行
            results = []
            for func, args in tasks:
                try:
                    result = func(*args)
                    results.append(result)
                except Exception as e:
                    logger.error(f"任务执行失败: {e}")
                    results.append(None)
            return results
    
    def start_performance_monitoring(self):
        """启动性能监控"""
        self.performance_monitor.start_monitoring()
    
    def stop_performance_monitoring(self):
        """停止性能监控"""
        self.performance_monitor.stop_monitoring()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        获取性能报告
        
        Returns:
            性能报告字典
        """
        current_metrics = self.performance_monitor.get_current_metrics()
        avg_metrics = self.performance_monitor.get_average_metrics()
        cache_hit_rate = self.memory_manager.get_cache_hit_rate()
        
        return {
            'current_metrics': current_metrics.__dict__ if current_metrics else {},
            'average_metrics': avg_metrics.__dict__ if avg_metrics else {},
            'cache_hit_rate': cache_hit_rate,
            'optimization_config': self.optimization_config,
            'memory_pool_stats': {
                'pools': len(self.memory_manager.object_pool),
                'cached_arrays': len(self.memory_manager.memory_cache)
            }
        }
    
    def cleanup(self):
        """清理资源"""
        self.stop_performance_monitoring()
        self.parallel_processor.close()


# 性能测试和验证函数
def benchmark_acceleration():
    """
    基准测试：比较加速前后的性能
    """
    logger.info("开始计算加速基准测试")
    
    # 创建测试数据
    size = 1000000
    test_data = np.random.random((size, 3))
    
    # 原始计算函数
    def original_computation(data):
        result = np.empty(data.shape[0])
        for i in range(data.shape[0]):
            result[i] = np.sum(data[i] * np.sin(data[i])) + np.prod(data[i])
        return result
    
    # 加速版本
    accelerator = ComputationAccelerator()
    accelerated_computation = accelerator.compile_function(original_computation, test_data)
    
    # 测试原始版本
    start_time = time.time()
    original_result = original_computation(test_data)
    original_time = time.time() - start_time
    
    # 测试加速版本
    start_time = time.time()
    accelerated_result = accelerated_computation(test_data)
    accelerated_time = time.time() - start_time
    
    # 计算加速比
    speedup = original_time / accelerated_time if accelerated_time > 0 else 1.0
    
    logger.info(f"基准测试结果:")
    logger.info(f"  原始计算时间: {original_time:.4f}s")
    logger.info(f"  加速计算时间: {accelerated_time:.4f}s")
    logger.info(f"  加速比: {speedup:.2f}x")
    logger.info(f"  结果一致性: {np.allclose(original_result, accelerated_result)}")
    
    return {
        'original_time': original_time,
        'accelerated_time': accelerated_time,
        'speedup': speedup,
        'consistent': np.allclose(original_result, accelerated_result)
    }


def test_memory_management():
    """
    测试内存管理功能
    """
    logger.info("开始内存管理测试")
    
    memory_manager = MemoryManager(max_cache_size=50)
    
    # 测试数组缓存
    shape1 = (1000, 1000)
    array1 = memory_manager.get_cached_array(shape1)
    array2 = memory_manager.get_cached_array(shape1)  # 应该返回同一对象
    
    logger.info(f"数组缓存测试 - 同一对象: {array1 is array2}")
    
    # 测试缓存命中率
    for i in range(100):
        shape = (i + 100, i + 100)
        memory_manager.get_cached_array(shape)
    
    hit_rate = memory_manager.get_cache_hit_rate()
    logger.info(f"缓存命中率: {hit_rate:.2%}")
    
    return {
        'same_object': array1 is array2,
        'cache_hit_rate': hit_rate,
        'cache_size': len(memory_manager.memory_cache)
    }


def test_parallel_processing():
    """
    测试并行处理功能
    """
    logger.info("开始并行处理测试")
    
    parallel_processor = ParallelProcessor()
    
    # 创建测试任务
    def compute_task(x):
        # 模拟计算密集型任务
        result = 0
        for i in range(100000):
            result += np.sin(x + i * 0.001)
        return result
    
    test_data = list(range(100))
    
    # 串行执行
    start_time = time.time()
    serial_results = [compute_task(x) for x in test_data]
    serial_time = time.time() - start_time
    
    # 并行执行
    start_time = time.time()
    parallel_results = parallel_processor.parallel_map(compute_task, test_data)
    parallel_time = time.time() - start_time
    
    # 计算加速比
    speedup = serial_time / parallel_time if parallel_time > 0 else 1.0
    consistency = np.allclose(serial_results, parallel_results, rtol=1e-10)
    
    logger.info(f"并行处理测试结果:")
    logger.info(f"  串行执行时间: {serial_time:.4f}s")
    logger.info(f"  并行执行时间: {parallel_time:.4f}s")
    logger.info(f"  加速比: {speedup:.2f}x")
    logger.info(f"  结果一致性: {consistency}")
    
    return {
        'serial_time': serial_time,
        'parallel_time': parallel_time,
        'speedup': speedup,
        'consistent': consistency
    }


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行性能测试
    try:
        # 测试计算加速
        acceleration_results = benchmark_acceleration()
        logger.info(f"计算加速测试完成: {acceleration_results}")
    except Exception as e:
        logger.error(f"计算加速测试失败: {e}")
    
    try:
        # 测试内存管理
        memory_results = test_memory_management()
        logger.info(f"内存管理测试完成: {memory_results}")
    except Exception as e:
        logger.error(f"内存管理测试失败: {e}")
    
    try:
        # 测试并行处理
        parallel_results = test_parallel_processing()
        logger.info(f"并行处理测试完成: {parallel_results}")
    except Exception as e:
        logger.error(f"并行处理测试失败: {e}")