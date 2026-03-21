"""
代码生成优化

提供代码生成缓存和模板预加载功能。
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OptimizationConfig:
    """优化配置"""
    enable_cache: bool = True  # 启用缓存
    cache_ttl: int = 3600  # 缓存存活时间（秒）
    preload_templates: bool = True  # 预加载模板
    max_cache_size: int = 1000  # 最大缓存条目数


@dataclass
class OptimizationStats:
    """优化统计"""
    cache_hits: int = 0
    cache_misses: int = 0
    templates_loaded: int = 0
    total_generations: int = 0
    avg_generation_time: float = 0.0
    _total_time: float = field(default=0.0, repr=False)


class CodeGenOptimizer:
    """
    代码生成优化器
    
    提供代码生成缓存、模板预加载等优化功能。
    
    使用示例:
        config = OptimizationConfig(enable_cache=True)
        optimizer = CodeGenOptimizer(config)
        
        # 生成代码（带缓存）
        code = optimizer.generate_with_cache(
            template="event_listener",
            params={"event_name": "OnJoinServer"},
            template_manager=template_manager
        )
    """
    
    def __init__(self, config: OptimizationConfig | None = None):
        """
        初始化优化器
        
        Args:
            config: 优化配置
        """
        self.config = config or OptimizationConfig()
        self._stats = OptimizationStats()
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (value, timestamp)
    
    def generate_with_cache(
        self,
        template: str,
        params: dict[str, Any],
        generate_fn: callable,
    ) -> Any:
        """
        带缓存的代码生成
        
        Args:
            template: 模板名称
            params: 模板参数
            generate_fn: 生成函数
            
        Returns:
            生成的代码
        """
        if not self.config.enable_cache:
            start = time.time()
            result = generate_fn()
            self._record_generation(time.time() - start)
            return result
        
        # 生成缓存键
        key = self._generate_cache_key(template, params)
        
        # 尝试从缓存获取
        if key in self._cache:
            value, timestamp = self._cache[key]
            if (time.time() - timestamp) < self.config.cache_ttl:
                self._stats.cache_hits += 1
                return value
        
        # 缓存未命中，生成并缓存
        self._stats.cache_misses += 1
        
        start = time.time()
        result = generate_fn()
        generation_time = time.time() - start
        
        # 检查缓存大小
        if len(self._cache) >= self.config.max_cache_size:
            self._evict_oldest()
        
        # 存入缓存
        self._cache[key] = (result, time.time())
        
        self._record_generation(generation_time)
        
        return result
    
    def preload_templates(self, template_manager: Any) -> int:
        """
        预加载模板到内存
        
        Args:
            template_manager: 模板管理器实例
            
        Returns:
            预加载的模板数量
        """
        if not self.config.preload_templates:
            return 0
        
        try:
            # 获取所有模板
            templates = template_manager.list_templates()
            
            # 预加载每个模板
            for template_name in templates:
                template_manager.get_template(template_name)
                self._stats.templates_loaded += 1
            
            return self._stats.templates_loaded
        except Exception:
            return 0
    
    def invalidate_cache(self, template: str | None = None) -> int:
        """
        使缓存失效
        
        Args:
            template: 模板名称，None 表示清空所有
            
        Returns:
            清除的缓存条目数
        """
        if template is None:
            count = len(self._cache)
            self._cache.clear()
            return count
        
        # 清除特定模板的缓存
        prefix = f"{template}:"
        keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        return len(keys_to_remove)
    
    def stats(self) -> dict[str, Any]:
        """
        获取优化统计
        
        Returns:
            统计信息
        """
        hit_rate = (
            self._stats.cache_hits / (self._stats.cache_hits + self._stats.cache_misses)
            if (self._stats.cache_hits + self._stats.cache_misses) > 0
            else 0
        )
        
        return {
            "cache_hits": self._stats.cache_hits,
            "cache_misses": self._stats.cache_misses,
            "cache_hit_rate": hit_rate,
            "cache_size": len(self._cache),
            "templates_loaded": self._stats.templates_loaded,
            "total_generations": self._stats.total_generations,
            "avg_generation_time_ms": self._stats.avg_generation_time * 1000,
        }
    
    def _generate_cache_key(self, template: str, params: dict[str, Any]) -> str:
        """生成缓存键"""
        # 对参数排序以保证一致性
        params_str = str(sorted(params.items()))
        key_input = f"{template}:{params_str}"
        return hashlib.md5(key_input.encode()).hexdigest()
    
    def _evict_oldest(self) -> None:
        """淘汰最旧的缓存条目"""
        if not self._cache:
            return
        
        # 找到最旧的条目
        oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]
    
    def _record_generation(self, duration: float) -> None:
        """记录生成统计"""
        self._stats.total_generations += 1
        self._stats._total_time += duration
        self._stats.avg_generation_time = (
            self._stats._total_time / self._stats.total_generations
        )


class TemplatePool:
    """
    模板池
    
    预加载和缓存常用模板，加速代码生成。
    
    使用示例:
        pool = TemplatePool()
        pool.warmup(template_manager, ["event_listener", "api_call"])
        
        # 快速获取模板
        template = pool.get("event_listener")
    """
    
    def __init__(self, max_size: int = 50):
        """
        初始化模板池
        
        Args:
            max_size: 最大模板数量
        """
        self.max_size = max_size
        self._templates: dict[str, Any] = {}
        self._access_order: list[str] = []
    
    def warmup(self, template_manager: Any, template_names: list[str]) -> int:
        """
        预热模板池
        
        Args:
            template_manager: 模板管理器
            template_names: 模板名称列表
            
        Returns:
            成功加载的模板数量
        """
        loaded = 0
        
        for name in template_names:
            try:
                template = template_manager.get_template(name)
                self._templates[name] = template
                self._access_order.append(name)
                loaded += 1
            except Exception:
                pass
        
        return loaded
    
    def get(self, name: str) -> Any | None:
        """
        获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            模板对象，不存在返回 None
        """
        if name not in self._templates:
            return None
        
        # 更新访问顺序
        if name in self._access_order:
            self._access_order.remove(name)
        self._access_order.append(name)
        
        return self._templates[name]
    
    def put(self, name: str, template: Any) -> None:
        """
        添加模板到池
        
        Args:
            name: 模板名称
            template: 模板对象
        """
        # 检查是否需要淘汰
        if name not in self._templates and len(self._templates) >= self.max_size:
            self._evict()
        
        self._templates[name] = template
        
        if name in self._access_order:
            self._access_order.remove(name)
        self._access_order.append(name)
    
    def clear(self) -> None:
        """清空模板池"""
        self._templates.clear()
        self._access_order.clear()
    
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "size": len(self._templates),
            "max_size": self.max_size,
            "templates": list(self._templates.keys()),
        }
    
    def _evict(self) -> None:
        """淘汰最久未使用的模板"""
        if self._access_order:
            oldest = self._access_order.pop(0)
            if oldest in self._templates:
                del self._templates[oldest]
