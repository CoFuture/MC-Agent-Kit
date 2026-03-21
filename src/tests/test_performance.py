"""
性能优化模块测试
"""

import time
import pytest
from mc_agent_kit.performance import (
    KnowledgeCache,
    LRUCache,
    LogBatchProcessor,
    BatchConfig,
    CodeGenOptimizer,
    OptimizationConfig,
)


class TestLRUCache:
    """LRU 缓存测试"""
    
    def test_basic_set_get(self):
        """测试基本的设置和获取"""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = LRUCache(max_size=10)
        assert cache.get("nonexistent") is None
    
    def test_max_size_eviction(self):
        """测试最大容量淘汰"""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # 应该淘汰 key1
        
        assert cache.get("key1") is None  # 已淘汰
        assert cache.get("key2") == "value2"
        assert cache.get("key4") == "value4"
    
    def test_lru_order(self):
        """测试 LRU 顺序"""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # 访问 key1，使其变为最近使用
        cache.get("key1")
        
        # 添加 key4，应该淘汰 key2（最久未使用）
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None  # 已淘汰
        assert cache.get("key4") == "value4"
    
    def test_ttl_expiration(self):
        """测试 TTL 过期"""
        cache = LRUCache(max_size=10, ttl_seconds=1)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        time.sleep(1.1)  # 等待过期
        
        assert cache.get("key1") is None  # 已过期
    
    def test_update_existing(self):
        """测试更新已有条目"""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        
        assert cache.get("key1") == "value2"
    
    def test_delete(self):
        """测试删除"""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("key1") is False  # 已不存在
    
    def test_clear(self):
        """测试清空"""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_stats(self):
        """测试统计信息"""
        cache = LRUCache(max_size=10)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")
        cache.get("key1")
        
        stats = cache.stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert stats["total_hits"] == 2
        assert stats["avg_hits"] == 1.0


class TestKnowledgeCache:
    """知识库缓存测试"""
    
    def test_get_or_set_cache_hit(self):
        """测试缓存命中"""
        cache = KnowledgeCache(max_size=10)
        
        call_count = [0]
        
        def compute_fn():
            call_count[0] += 1
            return "computed_value"
        
        # 第一次调用，缓存未命中
        result1 = cache.get_or_set("query1", compute_fn)
        assert result1 == "computed_value"
        assert call_count[0] == 1
        
        # 第二次调用，缓存命中
        result2 = cache.get_or_set("query1", compute_fn)
        assert result2 == "computed_value"
        assert call_count[0] == 1  # 未再次调用
    
    def test_get_or_set_cache_miss(self):
        """测试缓存未命中"""
        cache = KnowledgeCache(max_size=10)
        
        results = []
        
        def compute_fn():
            results.append(len(results))
            return f"value_{len(results)}"
        
        cache.get_or_set("query1", compute_fn)
        cache.get_or_set("query2", compute_fn)
        
        assert results == [0, 1]
    
    def test_invalidate(self):
        """测试使缓存失效"""
        cache = KnowledgeCache(max_size=10)
        
        cache.get_or_set("query1", lambda: "value1")
        assert cache.get_or_set("query1", lambda: "value2") == "value1"
        
        cache.invalidate("query1")
        assert cache.get_or_set("query1", lambda: "value2") == "value2"
    
    def test_stats_hit_rate(self):
        """测试命中率统计"""
        cache = KnowledgeCache(max_size=10)
        
        # 2 次未命中，3 次命中
        cache.get_or_set("q1", lambda: "v1")  # miss
        cache.get_or_set("q2", lambda: "v2")  # miss
        cache.get_or_set("q1", lambda: "v1")  # hit
        cache.get_or_set("q2", lambda: "v2")  # hit
        cache.get_or_set("q1", lambda: "v1")  # hit
        
        stats = cache.stats()
        
        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.6  # 60%
    
    def test_clear(self):
        """测试清空"""
        cache = KnowledgeCache(max_size=10)
        
        cache.get_or_set("q1", lambda: "v1")
        cache.get_or_set("q2", lambda: "v2")
        cache.clear()
        
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0


class TestLogBatchProcessor:
    """日志批处理器测试"""
    
    def test_basic_add_flush(self):
        """测试基本的添加和刷新"""
        config = BatchConfig(batch_size=10)
        processor = LogBatchProcessor(config)
        
        processor.add("log1")
        processor.add("log2")
        
        result = processor.flush()
        
        assert result.processed_count == 2
        assert result.dropped_count == 0
    
    def test_auto_flush_on_batch_size(self):
        """测试达到批次大小自动刷新"""
        config = BatchConfig(batch_size=3)
        processed_logs = []
        
        def process_fn(logs):
            processed_logs.extend(logs)
        
        processor = LogBatchProcessor(config, process_fn=process_fn)
        
        processor.add("log1")
        processor.add("log2")
        processor.add("log3")  # 应该触发自动刷新
        
        assert len(processed_logs) == 3
    
    def test_max_queue_size(self):
        """测试最大队列大小"""
        config = BatchConfig(max_queue_size=5)
        processor = LogBatchProcessor(config)
        
        for i in range(10):
            processor.add(f"log{i}")
        
        stats = processor.stats()
        assert stats["total_dropped"] == 5  # 后 5 个被丢弃
    
    def test_should_flush(self):
        """测试是否应该刷新"""
        config = BatchConfig(batch_size=5, flush_interval=0.1)
        processor = LogBatchProcessor(config)
        
        # 队列未满，时间未到
        assert processor.should_flush() is False
        
        # 达到批次大小
        for _ in range(5):
            processor.add("log")
        assert processor.should_flush() is True
        
        # 刷新后
        processor.flush()
        assert processor.should_flush() is False
        
        # 等待时间到
        time.sleep(0.15)
        assert processor.should_flush() is True
    
    def test_stats(self):
        """测试统计信息"""
        config = BatchConfig(batch_size=10)
        processor = LogBatchProcessor(config)
        
        processor.add("log1")
        processor.add("log2")
        processor.flush()
        processor.flush()  # 空刷新
        
        stats = processor.stats()
        
        assert stats["total_added"] == 2
        assert stats["total_processed"] == 2
        assert stats["flush_count"] == 2
        assert stats["queue_size"] == 0


class TestCodeGenOptimizer:
    """代码生成优化器测试"""
    
    def test_generate_with_cache_hit(self):
        """测试带缓存的生成（命中）"""
        config = OptimizationConfig(enable_cache=True)
        optimizer = CodeGenOptimizer(config)
        
        call_count = [0]
        
        def generate_fn():
            call_count[0] += 1
            return "generated_code"
        
        # 第一次生成
        result1 = optimizer.generate_with_cache("template1", {"param": "value"}, generate_fn)
        assert result1 == "generated_code"
        assert call_count[0] == 1
        
        # 第二次生成（缓存命中）
        result2 = optimizer.generate_with_cache("template1", {"param": "value"}, generate_fn)
        assert result2 == "generated_code"
        assert call_count[0] == 1  # 未再次调用
    
    def test_generate_with_cache_miss(self):
        """测试带缓存的生成（未命中）"""
        config = OptimizationConfig(enable_cache=True)
        optimizer = CodeGenOptimizer(config)
        
        results = []
        
        def generate_fn():
            results.append(len(results))
            return f"code_{len(results)}"
        
        optimizer.generate_with_cache("template1", {"p": "v1"}, generate_fn)
        optimizer.generate_with_cache("template1", {"p": "v2"}, generate_fn)  # 不同参数
        
        assert results == [0, 1]  # 两次都未命中
    
    def test_cache_disabled(self):
        """测试缓存禁用"""
        config = OptimizationConfig(enable_cache=False)
        optimizer = CodeGenOptimizer(config)
        
        call_count = [0]
        
        def generate_fn():
            call_count[0] += 1
            return "code"
        
        optimizer.generate_with_cache("template", {}, generate_fn)
        optimizer.generate_with_cache("template", {}, generate_fn)
        
        assert call_count[0] == 2  # 每次都调用
    
    def test_invalidate_cache(self):
        """测试使缓存失效"""
        config = OptimizationConfig(enable_cache=True)
        optimizer = CodeGenOptimizer(config)
        
        optimizer.generate_with_cache("template1", {}, lambda: "code1")
        optimizer.generate_with_cache("template2", {}, lambda: "code2")
        
        # 使 template1 失效
        count = optimizer.invalidate_cache("template1")
        assert count == 1
        
        stats = optimizer.stats()
        assert stats["cache_size"] == 1
    
    def test_stats(self):
        """测试统计信息"""
        config = OptimizationConfig(enable_cache=True)
        optimizer = CodeGenOptimizer(config)
        
        optimizer.generate_with_cache("t1", {"p": "v1"}, lambda: "c1")  # miss
        optimizer.generate_with_cache("t1", {"p": "v1"}, lambda: "c1")  # hit
        optimizer.generate_with_cache("t2", {"p": "v2"}, lambda: "c2")  # miss
        
        stats = optimizer.stats()
        
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 2
        assert stats["total_generations"] == 3
        assert stats["cache_hit_rate"] == 1/3  # ~33%


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
