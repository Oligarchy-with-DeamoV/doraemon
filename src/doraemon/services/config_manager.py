"""
服务配置管理器
支持从配置文件加载服务配置
"""

import importlib
import json
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    yaml = None

from .enhanced_service import EnhancedService, ServiceConfig, ServiceRegistry


class ServiceConfigManager:
    """服务配置管理器"""
    
    @staticmethod
    def load_from_yaml(config_path: str) -> Dict[str, EnhancedService]:
        """从YAML文件加载服务配置"""
        if yaml is None:
            raise ImportError("PyYAML is required for YAML config loading. Install with: pip install PyYAML")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return ServiceConfigManager._create_services_from_config(config_data)
    
    @staticmethod
    def load_from_json(config_path: str) -> Dict[str, EnhancedService]:
        """从JSON文件加载服务配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return ServiceConfigManager._create_services_from_config(config_data)
    
    @staticmethod
    def _create_services_from_config(config_data: Dict[str, Any]) -> Dict[str, EnhancedService]:
        """从配置数据创建服务"""
        services = {}
        
        for service_name, service_config in config_data.get('services', {}).items():
            try:
                # 动态导入proto类
                input_proto = ServiceConfigManager._import_class(
                    service_config['input_proto']
                )
                output_proto = ServiceConfigManager._import_class(
                    service_config['output_proto']
                )
                
                # 创建服务配置
                config = ServiceConfig(
                    name=service_name,
                    service_url=service_config['service_url'],
                    service_method=service_config['service_method'],
                    input_proto=input_proto,
                    output_proto=output_proto,
                    timeout=service_config.get('timeout', 30.0),
                    max_retries=service_config.get('max_retries', 3),
                    pool_connections=service_config.get('pool_connections', 10),
                    pool_maxsize=service_config.get('pool_maxsize', 20),
                    verify=service_config.get('verify', True),
                    headers=service_config.get('headers', {})
                )
                
                # 注册服务
                service = ServiceRegistry.register(config)
                services[service_name] = service
                
            except Exception as e:
                print(f"Failed to create service {service_name}: {e}")
        
        return services
    
    @staticmethod
    def _import_class(class_path: str):
        """动态导入类"""
        module_name, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    
    @staticmethod
    def export_to_yaml(services: Dict[str, EnhancedService], output_path: str):
        """导出服务配置到YAML文件"""
        config_data = {
            'services': {}
        }
        
        for service_name, service in services.items():
            config = service.config
            config_data['services'][service_name] = {
                'service_url': config.service_url,
                'service_method': config.service_method,
                'input_proto': f"{config.input_proto.__module__}.{config.input_proto.__name__}",
                'output_proto': f"{config.output_proto.__module__}.{config.output_proto.__name__}",
                'timeout': config.timeout,
                'max_retries': config.max_retries,
                'pool_connections': config.pool_connections,
                'pool_maxsize': config.pool_maxsize,
                'verify': config.verify,
                'headers': config.headers or {}
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)


class ServiceMonitor:
    """服务监控器"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_request(self, service_name: str, success: bool, response_time: float):
        """记录请求指标"""
        if service_name not in self.metrics:
            self.metrics[service_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_response_time': 0.0,
                'max_response_time': 0.0,
                'min_response_time': float('inf')
            }
        
        metrics = self.metrics[service_name]
        metrics['total_requests'] += 1
        metrics['total_response_time'] += response_time
        metrics['max_response_time'] = max(metrics['max_response_time'], response_time)
        metrics['min_response_time'] = min(metrics['min_response_time'], response_time)
        
        if success:
            metrics['successful_requests'] += 1
        else:
            metrics['failed_requests'] += 1
    
    def get_metrics(self, service_name: str) -> Dict[str, Any]:
        """获取服务指标"""
        if service_name not in self.metrics:
            return {}
        
        metrics = self.metrics[service_name]
        avg_response_time = (
            metrics['total_response_time'] / metrics['total_requests']
            if metrics['total_requests'] > 0 else 0
        )
        success_rate = (
            metrics['successful_requests'] / metrics['total_requests'] * 100
            if metrics['total_requests'] > 0 else 0
        )
        
        return {
            'total_requests': metrics['total_requests'],
            'successful_requests': metrics['successful_requests'],
            'failed_requests': metrics['failed_requests'],
            'success_rate': f"{success_rate:.2f}%",
            'avg_response_time': f"{avg_response_time:.3f}s",
            'max_response_time': f"{metrics['max_response_time']:.3f}s",
            'min_response_time': f"{metrics['min_response_time']:.3f}s"
        }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务指标"""
        return {
            service_name: self.get_metrics(service_name)
            for service_name in self.metrics.keys()
        }


# 全局监控器实例
global_monitor = ServiceMonitor()
