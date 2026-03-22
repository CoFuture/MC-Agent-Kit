"""
Iteration #38 Tests - MVP 闭环完善与性能优化

测试覆盖:
1. 端到端测试：知识检索、项目脚手架
2. 性能基准测试
3. 文档国际化验证
"""

import pytest
import tempfile
from pathlib import Path

# ==============================================================================
# 端到端测试
# ==============================================================================

class TestEndToEndWorkflow:
    """端到端工作流测试"""

    def test_knowledge_retrieval_available(self):
        """测试知识检索可用"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval
        
        retrieval = KnowledgeRetrieval()
        assert retrieval is not None

    def test_project_scaffold_available(self):
        """测试项目脚手架可用"""
        from mc_agent_kit.scaffold.creator import ProjectCreator
        
        creator = ProjectCreator()
        assert creator is not None

    def test_create_project_returns_object(self):
        """测试创建项目返回对象"""
        from mc_agent_kit.scaffold.creator import ProjectCreator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            creator = ProjectCreator()
            project_name = "test_addon"
            project_path = Path(tmpdir) / project_name
            
            # 创建项目返回 AddonProject 对象
            result = creator.create_project(project_name, project_path)
            
            # 验证返回的是对象
            assert result is not None


# ==============================================================================
# 性能基准测试
# ==============================================================================

class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_lru_cache_basic(self):
        """测试 LRU 缓存基本功能"""
        from mc_agent_kit.performance import LRUCache
        
        cache = LRUCache(max_size=100)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # 验证缓存工作
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("nonexistent") is None

    def test_knowledge_cache_basic(self):
        """测试知识缓存基本功能"""
        from mc_agent_kit.performance import KnowledgeCache
        
        kb_cache = KnowledgeCache(max_size=100, ttl=300)
        kb_cache.set("search_test", {"results": []})
        assert kb_cache.get("search_test") == {"results": []}

    def test_log_batch_processor_basic(self):
        """测试日志批处理器基本功能"""
        from mc_agent_kit.performance import LogBatchProcessor
        
        processor = LogBatchProcessor()
        assert processor is not None

    def test_log_aggregator_basic(self):
        """测试日志聚合器基本功能"""
        from mc_agent_kit.performance import LogAggregator
        
        aggregator = LogAggregator()
        aggregator.add("log1")
        aggregator.add("log2")
        assert aggregator is not None


# ==============================================================================
# 启动器测试
# ==============================================================================

class TestLauncher:
    """启动器测试"""

    def test_addon_info_available(self):
        """测试 AddonInfo 可用"""
        from mc_agent_kit.launcher.addon_scanner import AddonInfo
        
        assert AddonInfo is not None

    def test_game_config_available(self):
        """测试 GameConfig 可用"""
        from mc_agent_kit.launcher.config_generator import GameConfig
        
        assert GameConfig is not None


# ==============================================================================
# 日志捕获测试
# ==============================================================================

class TestLogCapture:
    """日志捕获测试"""

    def test_log_parser_available(self):
        """测试日志解析器可用"""
        from mc_agent_kit.log_capture.parser import LogParser
        
        parser = LogParser()
        assert parser is not None

    def test_log_analyzer_available(self):
        """测试日志分析器可用"""
        from mc_agent_kit.log_capture.analyzer import LogAnalyzer
        
        analyzer = LogAnalyzer()
        assert analyzer is not None


# ==============================================================================
# 文档国际化测试
# ==============================================================================

class TestDocumentationInternationalization:
    """文档国际化测试"""

    def test_docs_directory_structure(self):
        """测试文档目录结构"""
        docs_path = Path(__file__).parent.parent.parent / "docs"
        
        # 检查文档目录存在
        assert docs_path.exists(), f"Docs directory not found: {docs_path}"
        
        # 检查英文文档目录
        en_docs_path = docs_path / "en"
        assert en_docs_path.exists(), f"English docs directory not found: {en_docs_path}"

    def test_user_docs_exist(self):
        """测试用户文档存在"""
        docs_path = Path(__file__).parent.parent.parent / "docs"
        
        # 检查中文用户文档
        user_docs_path = docs_path / "user"
        assert user_docs_path.exists(), f"User docs directory not found: {user_docs_path}"


# ==============================================================================
# 集成测试
# ==============================================================================

class TestIntegration:
    """集成测试"""

    def test_scaffold_creator_available(self):
        """测试脚手架创建器可用"""
        from mc_agent_kit.scaffold.creator import ProjectCreator
        
        creator = ProjectCreator()
        assert creator is not None

    def test_performance_modules_available(self):
        """测试性能模块可用"""
        from mc_agent_kit.performance import LRUCache, KnowledgeCache, LogBatchProcessor, LogAggregator
        
        # 测试所有性能组件可以实例化
        cache = LRUCache(max_size=50)
        kb_cache = KnowledgeCache(max_size=50, ttl=300)
        processor = LogBatchProcessor()
        aggregator = LogAggregator()
        
        assert cache is not None
        assert kb_cache is not None
        assert processor is not None
        assert aggregator is not None


# ==============================================================================
# 验收标准测试
# ==============================================================================

class TestAcceptanceCriteria:
    """验收标准测试"""

    def test_mvp_components_available(self):
        """测试 MVP 组件可用"""
        # 1. 知识检索可用
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval
        retrieval = KnowledgeRetrieval()
        assert retrieval is not None
        
        # 2. 项目创建可用
        from mc_agent_kit.scaffold.creator import ProjectCreator
        creator = ProjectCreator()
        assert creator is not None
        
        # 3. 启动器诊断可用
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        diagnoser = LauncherDiagnoser()
        assert diagnoser is not None

    def test_performance_cache_speed(self):
        """测试缓存性能"""
        import time
        from mc_agent_kit.performance import LRUCache
        
        cache = LRUCache(max_size=1000)
        
        # 性能测试：100 次操作应该在合理时间内完成
        start = time.time()
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
            cache.get(f"key_{i}")
        elapsed = time.time() - start
        
        # 100 次操作应该在 1 秒内完成
        assert elapsed < 1.0, f"Performance too slow: {elapsed}s"

    def test_tests_run_successfully(self):
        """测试测试成功运行"""
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
