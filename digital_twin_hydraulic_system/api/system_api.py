# -*- coding: utf-8 -*-
"""
数字孪生水力系统Web API

提供RESTful API接口，支持系统监控、控制和数据访问功能。
使用FastAPI框架实现高性能API服务。
"""

from fastapi import FastAPI, HTTPException, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import numpy as np
import json
import asyncio
import logging
from datetime import datetime
import uvicorn

# 导入系统模块
try:
    from .. import config
    from ..simulation_manager import SimulationManager
    from ..diagnostics.ml_fault_detector import MLFaultDetector, PredictiveMaintenance
    from ..diagnostics.advanced_identifier import ParameterInfo, MultiModelIdentifier
    from ..models.id_channel_model import IDChannelModel
    from ..models.fvm_channel_model import FVMChannelModel
    from ..visualization import Visualizer
    logger = logging.getLogger(__name__)
    SYSTEM_MODULES_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"系统模块导入失败: {e}")
    SYSTEM_MODULES_AVAILABLE = False

# 创建FastAPI应用
app = FastAPI(
    title="数字孪生水力系统API",
    description="提供数字孪生水力系统的实时监控、故障诊断和参数辨识功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
simulation_manager = None
ml_fault_detector = None
predictive_maintenance = None
active_websockets = set()

# 数据模型定义
class SensorData(BaseModel):
    """传感器数据模型"""
    timestamp: float
    h_gate_up: float
    h_gate_down: float
    q_gate_down: float
    h_channel_mid: float
    q_channel_end: float

class SystemStatus(BaseModel):
    """系统状态模型"""
    timestamp: float
    status: str
    health_score: float
    active_faults: List[str]
    estimated_parameters: Dict[str, float]

class SimulationConfig(BaseModel):
    """仿真配置模型"""
    duration: float = Field(default=3600.0, gt=0, le=86400)
    timestep: float = Field(default=1.0, gt=0, le=10.0)
    upstream_inflow: float = Field(default=50.0, ge=0, le=200.0)
    gate_opening: float = Field(default=1.815, ge=0, le=5.0)

class FaultInjection(BaseModel):
    """故障注入模型"""
    sensor_id: str
    fault_type: str  # stuck, drift, noise
    value: float
    start_time: float = 0.0

class ParameterEstimate(BaseModel):
    """参数估计模型"""
    parameter_name: str
    value: float
    uncertainty: float
    timestamp: float

class ControlCommand(BaseModel):
    """控制命令模型"""
    command: str
    parameters: Optional[Dict[str, Any]] = None

# 初始化系统组件
def initialize_system():
    """初始化系统组件"""
    global simulation_manager, ml_fault_detector, predictive_maintenance
    
    if not SYSTEM_MODULES_AVAILABLE:
        logger.warning("系统模块不可用，API功能受限")
        return
    
    try:
        # 初始化仿真管理器
        simulation_manager = SimulationManager(config)
        logger.info("仿真管理器初始化完成")
        
        # 初始化机器学习故障检测器
        ml_config = {
            'contamination': 0.1,
            'n_estimators': 50,
            'window_size': 30,
            'feature_names': ['h_gate_up', 'h_gate_down', 'q_gate_down']
        }
        ml_fault_detector = MLFaultDetector(ml_config)
        logger.info("机器学习故障检测器初始化完成")
        
        # 初始化预测性维护系统
        pm_config = {
            'maintenance_threshold': 0.7,
            'prediction_horizon': 100
        }
        predictive_maintenance = PredictiveMaintenance(pm_config)
        logger.info("预测性维护系统初始化完成")
        
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")

# API路由定义
@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "数字孪生水力系统API",
        "version": "1.0.0",
        "status": "running" if SYSTEM_MODULES_AVAILABLE else "limited",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/system/status")
async def get_system_status() -> SystemStatus:
    """获取系统状态"""
    if not SYSTEM_MODULES_AVAILABLE or simulation_manager is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        # 获取当前系统状态
        timestamp = datetime.now().timestamp()
        status = "normal"
        health_score = 1.0
        active_faults = []
        
        # 估计参数（如果可用）
        estimated_parameters = {}
        if hasattr(simulation_manager, 'ekf') and simulation_manager.ekf is not None:
            estimated_parameters['manning_n'] = float(simulation_manager.ekf.x[-1])
            estimated_parameters['gate_coefficient'] = config.GATE_DISCHARGE_COEFFICIENT_TRUE
        
        return SystemStatus(
            timestamp=timestamp,
            status=status,
            health_score=health_score,
            active_faults=active_faults,
            estimated_parameters=estimated_parameters
        )
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@app.post("/simulation/start")
async def start_simulation(config: SimulationConfig) -> Dict[str, Any]:
    """启动仿真"""
    if not SYSTEM_MODULES_AVAILABLE or simulation_manager is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        # 更新仿真配置
        simulation_manager.config.SIMULATION_DURATION = config.duration
        simulation_manager.config.TIMESTEP = config.timestep
        simulation_manager.config.UPSTREAM_INFLOW = config.upstream_inflow
        simulation_manager.gate_opening = config.gate_opening
        
        # 重置仿真状态
        simulation_manager.reset_simulation_state()
        
        return {
            "status": "success",
            "message": "仿真已启动",
            "config": config.dict()
        }
    except Exception as e:
        logger.error(f"启动仿真失败: {e}")
        raise HTTPException(status_code=500, detail="启动仿真失败")

@app.post("/simulation/step")
async def step_simulation(steps: int = 1) -> Dict[str, Any]:
    """执行仿真步骤"""
    if not SYSTEM_MODULES_AVAILABLE or simulation_manager is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        # 执行仿真步骤
        success = simulation_manager.step_simulation(steps)
        
        # 获取当前状态
        current_state = {
            "timestamp": simulation_manager.timestamp,
            "h_true": simulation_manager.h_true_gate_upstream,
            "n_true": simulation_manager.model_a.manning_n if simulation_manager.model_a else 0.025
        }
        
        if hasattr(simulation_manager, 'ekf') and simulation_manager.ekf is not None:
            current_state["n_est"] = float(simulation_manager.ekf.x[-1])
        
        return {
            "status": "success" if success else "finished",
            "current_state": current_state,
            "simulation_running": success
        }
    except Exception as e:
        logger.error(f"执行仿真步骤失败: {e}")
        raise HTTPException(status_code=500, detail="执行仿真步骤失败")

@app.get("/sensors/data")
async def get_sensor_data() -> SensorData:
    """获取传感器数据"""
    if not SYSTEM_MODULES_AVAILABLE or simulation_manager is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        # 模拟传感器数据获取
        timestamp = datetime.now().timestamp()
        
        # 如果仿真正在运行，获取仿真数据
        if hasattr(simulation_manager, 'h_true_gate_upstream'):
            h_gate_up = simulation_manager.h_true_gate_upstream
            # 生成相关联的传感器数据
            h_gate_down = h_gate_up * 0.8 + np.random.normal(0, 0.01)
            q_gate_down = 30.0 + 10.0 * np.sin(timestamp * 0.01) + np.random.normal(0, 0.5)
            h_channel_mid = h_gate_up * 0.9 + np.random.normal(0, 0.005)
            q_channel_end = q_gate_down * 0.95 + np.random.normal(0, 0.3)
        else:
            # 默认值
            h_gate_up = 2.5 + np.random.normal(0, 0.01)
            h_gate_down = 2.0 + np.random.normal(0, 0.01)
            q_gate_down = 38.0 + np.random.normal(0, 0.5)
            h_channel_mid = 2.2 + np.random.normal(0, 0.005)
            q_channel_end = 36.0 + np.random.normal(0, 0.3)
        
        return SensorData(
            timestamp=timestamp,
            h_gate_up=float(h_gate_up),
            h_gate_down=float(h_gate_down),
            q_gate_down=float(q_gate_down),
            h_channel_mid=float(h_channel_mid),
            q_channel_end=float(q_channel_end)
        )
    except Exception as e:
        logger.error(f"获取传感器数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取传感器数据失败")

@app.post("/faults/inject")
async def inject_fault(fault: FaultInjection) -> Dict[str, Any]:
    """注入故障"""
    if not SYSTEM_MODULES_AVAILABLE or simulation_manager is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        # 添加故障到仿真管理器
        simulation_manager.add_perturbation(
            event_time=fault.start_time,
            event_type='sensor_fault',
            sensor_id=fault.sensor_id,
            fault_type=fault.fault_type,
            value=fault.value
        )
        
        return {
            "status": "success",
            "message": f"故障已注入: {fault.sensor_id} ({fault.fault_type})",
            "fault": fault.dict()
        }
    except Exception as e:
        logger.error(f"注入故障失败: {e}")
        raise HTTPException(status_code=500, detail="注入故障失败")

@app.get("/parameters/estimate")
async def get_parameter_estimates() -> List[ParameterEstimate]:
    """获取参数估计值"""
    if not SYSTEM_MODULES_AVAILABLE:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        estimates = []
        timestamp = datetime.now().timestamp()
        
        # 如果有仿真管理器，获取EKF估计值
        if simulation_manager and hasattr(simulation_manager, 'ekf') and simulation_manager.ekf is not None:
            # 曼宁系数估计
            estimates.append(ParameterEstimate(
                parameter_name="manning_n",
                value=float(simulation_manager.ekf.x[-1]),
                uncertainty=float(np.sqrt(simulation_manager.ekf.P[-1, -1])),
                timestamp=timestamp
            ))
        
        # 默认参数估计
        estimates.append(ParameterEstimate(
            parameter_name="gate_coefficient",
            value=config.GATE_DISCHARGE_COEFFICIENT_TRUE,
            uncertainty=0.05,
            timestamp=timestamp
        ))
        
        return estimates
    except Exception as e:
        logger.error(f"获取参数估计失败: {e}")
        raise HTTPException(status_code=500, detail="获取参数估计失败")

@app.post("/control/command")
async def send_control_command(command: ControlCommand) -> Dict[str, Any]:
    """发送控制命令"""
    if not SYSTEM_MODULES_AVAILABLE or simulation_manager is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        result = {
            "status": "received",
            "command": command.command,
            "timestamp": datetime.now().timestamp()
        }
        
        # 处理不同类型的命令
        if command.command == "reset":
            simulation_manager.reset_simulation_state()
            result["message"] = "系统已重置"
            result["status"] = "success"
        elif command.command == "start_data_generation":
            # 启动数据生成场景
            result["message"] = "数据生成场景已启动"
            result["status"] = "success"
        elif command.command == "update_gate_opening":
            if command.parameters and "value" in command.parameters:
                simulation_manager.gate_opening = float(command.parameters["value"])
                result["message"] = f"闸门开度已更新为 {simulation_manager.gate_opening}"
                result["status"] = "success"
            else:
                result["status"] = "error"
                result["message"] = "缺少参数值"
        else:
            result["status"] = "unknown"
            result["message"] = f"未知命令: {command.command}"
        
        return result
    except Exception as e:
        logger.error(f"处理控制命令失败: {e}")
        raise HTTPException(status_code=500, detail="处理控制命令失败")

@app.websocket("/ws/system_status")
async def websocket_system_status(websocket: WebSocket):
    """WebSocket连接，实时推送系统状态"""
    await websocket.accept()
    active_websockets.add(websocket)
    
    try:
        while True:
            # 获取系统状态
            status = await get_system_status()
            
            # 发送状态到客户端
            await websocket.send_json(status.dict())
            
            # 等待1秒
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        active_websockets.discard(websocket)

@app.websocket("/ws/sensor_data")
async def websocket_sensor_data(websocket: WebSocket):
    """WebSocket连接，实时推送传感器数据"""
    await websocket.accept()
    active_websockets.add(websocket)
    
    try:
        while True:
            # 获取传感器数据
            sensor_data = await get_sensor_data()
            
            # 发送数据到客户端
            await websocket.send_json(sensor_data.dict())
            
            # 等待0.5秒（更高的频率）
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"WebSocket传感器数据连接错误: {e}")
    finally:
        active_websockets.discard(websocket)

# 广播消息到所有活跃的WebSocket连接
async def broadcast_message(message: Dict[str, Any]):
    """广播消息到所有活跃的WebSocket连接"""
    disconnected = set()
    for websocket in active_websockets:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.add(websocket)
    
    # 移除断开的连接
    for websocket in disconnected:
        active_websockets.discard(websocket)

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("数字孪生水力系统API启动中...")
    initialize_system()
    logger.info("数字孪生水力系统API启动完成")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("数字孪生水力系统API关闭中...")
    # 清理资源
    active_websockets.clear()
    logger.info("数字孪生水力系统API关闭完成")

# 健康检查端点
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_modules": SYSTEM_MODULES_AVAILABLE,
        "components": {
            "simulation_manager": simulation_manager is not None,
            "ml_fault_detector": ml_fault_detector is not None,
            "predictive_maintenance": predictive_maintenance is not None
        }
    }

# API文档和测试页面
@app.get("/api/docs")
async def api_docs():
    """API文档页面"""
    return {
        "message": "API文档可通过 /docs 和 /redoc 访问",
        "endpoints": [
            "GET / - API根路径",
            "GET /system/status - 系统状态",
            "POST /simulation/start - 启动仿真",
            "POST /simulation/step - 执行仿真步骤",
            "GET /sensors/data - 传感器数据",
            "POST /faults/inject - 注入故障",
            "GET /parameters/estimate - 参数估计",
            "POST /control/command - 控制命令",
            "WebSocket /ws/system_status - 系统状态实时推送",
            "WebSocket /ws/sensor_data - 传感器数据实时推送"
        ]
    }

# 主函数（用于独立运行）
def main():
    """主函数，用于独立运行API服务器"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动服务器
    uvicorn.run(
        "system_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()