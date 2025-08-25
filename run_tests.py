#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本

用于运行项目中的所有测试，并生成测试报告。
"""

import subprocess
import sys
import os

def run_tests():
    """运行所有测试"""
    print("开始运行测试...")
    
    # 测试文件列表
    test_files = [
        "digital_twin_hydraulic_system/tests/test_performance_optimizer.py",
        "digital_twin_hydraulic_system/tests/test_integration.py",
        "digital_twin_hydraulic_system/tests/test_performance.py",
        "digital_twin_hydraulic_system/tests/test_security.py",
        "digital_twin_hydraulic_system/tests/test_deployment.py",
        "tests/test_fault_detector.py",
        "tests/test_gate_model.py",
        "tests/test_system_identifier.py"
    ]
    
    # 运行每个测试文件
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n运行测试: {test_file}")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", test_file, "-v"
                ], capture_output=True, text=True)
                
                print(result.stdout)
                if result.stderr:
                    print("错误输出:")
                    print(result.stderr)
                    
                if result.returncode != 0:
                    print(f"测试 {test_file} 失败")
                else:
                    print(f"测试 {test_file} 通过")
            except Exception as e:
                print(f"运行测试 {test_file} 时出错: {e}")
        else:
            print(f"测试文件不存在: {test_file}")
    
    print("\n所有测试运行完成")

def run_coverage():
    """运行测试并生成覆盖率报告"""
    print("运行测试并生成覆盖率报告...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "--cov=digital_twin_hydraulic_system",
            "--cov-report=html:coverage_report",
            "--cov-report=term-missing"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
            
        print("\n覆盖率报告已生成到 coverage_report 目录")
    except Exception as e:
        print(f"生成覆盖率报告时出错: {e}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "coverage":
            run_coverage()
        else:
            print("用法: python run_tests.py [coverage]")
    else:
        run_tests()

if __name__ == "__main__":
    main()