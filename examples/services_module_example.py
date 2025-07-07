"""
重构后的服务使用示例
展示从 doraemon.services 模块导入和使用服务的方法
"""

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional

# 从 services 模块导入
from doraemon.services import (  # 基础服务; 增强同步服务; 异步服务; 配置管理
    AsyncServiceRegistry,
    BaseService,
    ServiceConfigManager,
    ServiceRegistry,
    async_service_call,
    create_async_service,
    create_service,
    get_async_service,
    get_service,
    global_monitor,
    service_call,
)


# 数据结构定义
@dataclass
class InputProto:
    question: str
    classifyIds: List
    count: int


@dataclass
class GeneralRemoteResponseIntentInfo:
    intentQuestionId: int
    intentQuestion: str
    intentQuestionVector: List
    intentId: str
    intentName: str
    intentDescription: Optional[str]
    distance: float


@dataclass
class OutputProto:
    intentQuestions: List[GeneralRemoteResponseIntentInfo]
    msg: str


def basic_service_example():
    """基础服务示例（向后兼容）"""
    print("=== 基础服务示例 ===")
    
    # 使用原有的 BaseService 类
    service = BaseService(
        name="basic_service",
        service_url="http://10.170.138.185:8097/question/filter/intent",
        service_method="post",
        input_proto=InputProto,
        output_proto=OutputProto
    )
    
    inputs = {
        "question": "基础服务测试",
        "classifyIds": [],
        "count": 1
    }
    
    result = service(
        json=inputs,
        timeout=30,
        headers={"traceId": "basic_test"}
    )
    
    if result:
        print(f"基础服务调用成功: {result.msg}")
    else:
        print("基础服务调用失败")


def enhanced_service_example():
    """增强服务示例"""
    print("\n=== 增强服务示例 ===")
    
    # 创建增强服务
    service = create_service(
        name="enhanced_service",
        service_url="http://10.170.138.185:8097/question/filter/intent",
        service_method="post",
        input_proto=InputProto,
        output_proto=OutputProto,
        timeout=30.0,
        max_retries=3,
        pool_connections=10,
        pool_maxsize=20
    )
    
    print(f"增强服务创建完成: {service.config.name}")
    
    inputs = {
        "question": "增强服务测试",
        "classifyIds": [],
        "count": 1
    }
    
    # 使用缓存
    result = service(
        json_data=inputs,
        headers={"traceId": "enhanced_test"},
        use_cache=True,
        cache_ttl=300
    )
    
    if result:
        print(f"增强服务调用成功: {result.msg}")
    else:
        print("增强服务调用失败")
    
    # 从注册表获取服务
    registered_service = get_service("enhanced_service")
    if registered_service:
        print(f"从注册表获取服务成功: {registered_service.config.name}")
    
    # 查看所有已注册服务
    all_services = ServiceRegistry.list_services()
    print(f"已注册服务: {list(all_services.keys())}")


async def async_service_example():
    """异步服务示例"""
    print("\n=== 异步服务示例 ===")
    
    # 创建异步服务
    async_service = create_async_service(
        name="async_enhanced_service",
        service_url="http://10.170.138.185:8097/question/filter/intent",
        service_method="post",
        input_proto=InputProto,
        output_proto=OutputProto,
        timeout=30.0,
        connector_limit=100
    )
    
    print(f"异步服务创建完成: {async_service.config.name}")
    
    inputs = {
        "question": "异步服务测试",
        "classifyIds": [],
        "count": 1
    }
    
    # 单个异步调用
    result = await async_service(
        json_data=inputs,
        headers={"traceId": "async_test"}
    )
    
    if result:
        print(f"异步服务调用成功: {result.msg}")
    else:
        print("异步服务调用失败")
    
    # 批量异步调用
    print("\n--- 批量异步调用 ---")
    batch_requests = [
        {
            "json_data": {
                "question": f"批量问题 {i}",
                "classifyIds": [],
                "count": 1
            },
            "headers": {"traceId": f"batch_{i}"}
        }
        for i in range(3)
    ]
    
    start_time = time.time()
    batch_results = await async_service.batch_call(
        requests=batch_requests,
        max_concurrent=2
    )
    end_time = time.time()
    
    success_count = len([r for r in batch_results if r is not None])
    print(f"批量调用完成: {success_count}/{len(batch_requests)} 成功, 耗时 {end_time - start_time:.2f}秒")
    
    # 清理异步资源
    await async_service.close()


def decorator_example():
    """装饰器使用示例"""
    print("\n=== 装饰器示例 ===")
    
    # 确保有注册的服务
    if not get_service("enhanced_service"):
        print("未发现注册服务，进行注册")
        create_service(
            name="enhanced_service",
            service_url="http://10.170.138.185:8097/question/filter/intent",
            service_method="post",
            input_proto=InputProto,
            output_proto=OutputProto
        )
    
    @service_call("enhanced_service", use_cache=True, cache_ttl=300)
    def query_with_decorator(question: str):
        """使用装饰器的查询函数"""
        return {
            "json_data": {
                "question": question,
                "classifyIds": [],
                "count": 1
            },
            "headers": {"traceId": "decorator_test"}
        }
    
    try:
        result = query_with_decorator("装饰器测试问题")
        if result:
            print(f"装饰器调用成功: {result.msg}")
        else:
            print("装饰器调用失败")
    except Exception as e:
        print(f"装饰器调用出错: {e}")


def monitoring_example():
    """监控示例"""
    print("\n=== 监控示例 ===")
    
    # 记录一些模拟请求
    global_monitor.record_request("test_service", True, 0.123)
    global_monitor.record_request("test_service", True, 0.156)
    global_monitor.record_request("test_service", False, 0.200)
    
    # 获取监控指标
    metrics = global_monitor.get_metrics("test_service")
    print(f"测试服务监控指标: {metrics}")
    
    # 获取所有服务指标
    all_metrics = global_monitor.get_all_metrics()
    print(f"所有服务监控指标: {all_metrics}")


def config_example():
    """配置管理示例"""
    print("\n=== 配置管理示例 ===")
    
    # 注意：这里只是演示API，实际使用需要安装PyYAML
    try:
        # 从配置文件加载服务
        config_path = "./services_config.yaml"
        # services = ServiceConfigManager.load_from_yaml(config_path)
        # print(f"从配置文件加载了 {len(services)} 个服务")
    except Exception as e:
        print(f"配置加载示例: {e}")


def main():
    """主函数"""
    print("=== Doraemon Services 模块使用示例 ===")
    
    # 基础服务示例
    basic_service_example()
    
    # 增强服务示例
    enhanced_service_example()
    
    # 装饰器示例
    decorator_example()
    
    # 监控示例
    monitoring_example()
    
    # 配置管理示例
    config_example()
    
    print("\n=== 同步部分完成 ===")


async def async_main():
    """异步主函数"""
    print("\n=== 异步服务示例 ===")
    
    # 异步服务示例
    await async_service_example()
    
    print("\n=== 异步部分完成 ===")


if __name__ == "__main__":
    # 运行同步示例
    main()
    
    # 运行异步示例
    asyncio.run(async_main())
    
    print("\n=== 所有示例完成 ===")
    print("如需运行异步示例，请取消注释 asyncio.run(async_main()) 行")
