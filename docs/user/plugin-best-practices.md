# 插件最佳实践

本文档介绍开发 MC-Agent-Kit 插件的最佳实践，包括代码质量、性能优化、安全性和可维护性。

## 目录

1. [插件结构](#插件结构)
2. [代码质量](#代码质量)
3. [性能优化](#性能优化)
4. [安全性](#安全性)
5. [错误处理](#错误处理)
6. [测试策略](#测试策略)
7. [版本管理](#版本管理)

---

## 插件结构

### 标准目录结构

```
my_plugin/
├── plugin.json        # 插件清单（必需）
├── __init__.py        # 插件入口
├── my_plugin.py       # 主要实现
├── config.py          # 配置管理
├── utils.py           # 工具函数
├── tests/
│   ├── __init__.py
│   └── test_my_plugin.py
└── README.md          # 文档
```

### plugin.json 清单

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "插件描述",
  "author": "作者名",
  "main": "my_plugin.py",
  "dependencies": {
    "python": ">=3.10",
    "packages": ["requests>=2.28.0"]
  },
  "compatibility": {
    "mc_agent_kit": ">=1.0.0"
  },
  "config": {
    "default": {
      "enabled": true,
      "debug": false
    }
  }
}
```

### 插件入口点

```python
# my_plugin.py
from mc_agent_kit.plugin import PluginBase, PluginMetadata, PluginResult

class MyPlugin(PluginBase):
    """我的插件"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="插件描述",
            author="作者名",
            dependencies=["requests>=2.28.0"],
            capabilities=["feature1", "feature2"]
        )
    
    def initialize(self, config: dict) -> None:
        """初始化插件"""
        self.config = config
        # 初始化逻辑
    
    def execute(self, params: dict) -> PluginResult:
        """执行插件功能"""
        try:
            # 执行逻辑
            return PluginResult(
                success=True,
                data={"result": "ok"}
            )
        except Exception as e:
            return PluginResult(
                success=False,
                error=str(e)
            )
    
    def shutdown(self) -> None:
        """清理资源"""
        # 清理逻辑
```

---

## 代码质量

### 类型注解

始终使用类型注解：

```python
from typing import Any

def process_data(
    data: dict[str, Any],
    options: list[str] | None = None
) -> dict[str, Any]:
    """处理数据"""
    options = options or []
    # ...
    return result
```

### 文档字符串

为公共 API 编写文档字符串：

```python
def calculate_score(
    metrics: dict[str, float],
    weights: dict[str, float] | None = None
) -> float:
    """计算综合分数。
    
    Args:
        metrics: 指标字典，键为指标名，值为指标值
        weights: 可选的权重字典，默认等权重
    
    Returns:
        综合分数，范围 0-100
    
    Raises:
        ValueError: 如果指标值为负数
    
    Example:
        >>> metrics = {"speed": 80, "accuracy": 90}
        >>> calculate_score(metrics)
        85.0
    """
    # ...
```

### 代码复杂度

保持函数简单：

```python
# 不推荐：复杂嵌套
def process_complex(data):
    result = []
    for item in data:
        if item.valid:
            if item.type == "A":
                for sub in item.children:
                    if sub.active:
                        result.append(sub.value)
    return result

# 推荐：提前返回
def process_better(data):
    result = []
    for item in data:
        if not item.valid:
            continue
        if item.type != "A":
            continue
        for sub in item.children:
            if sub.active:
                result.append(sub.value)
    return result

# 推荐：提取函数
def process_best(data):
    return [
        sub.value
        for item in data
        if item.valid and item.type == "A"
        for sub in item.children
        if sub.active
    ]
```

### 使用 Code Smell 检测

```python
from mc_agent_kit.completion import SmellDetector

detector = SmellDetector()
smells = detector.detect(code)
for smell in smells:
    print(f"{smell.type}: {smell.message} (行 {smell.line})")
```

---

## 性能优化

### 1. 缓存计算结果

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(key: str) -> Any:
    """缓存昂贵计算的结果"""
    # 复杂计算
    return result
```

### 2. 批量处理

```python
from mc_agent_kit.performance import LogBatchProcessor

processor = LogBatchProcessor(
    batch_size=100,
    flush_interval_ms=1000
)

# 批量添加日志
for log in logs:
    processor.add(log)

# 自动或手动刷新
processor.flush()
```

### 3. 延迟加载

```python
class LazyLoader:
    """延迟加载资源"""
    
    def __init__(self):
        self._resource = None
    
    @property
    def resource(self):
        if self._resource is None:
            self._resource = self._load_resource()
        return self._resource
    
    def _load_resource(self):
        # 加载资源
        return resource
```

### 4. 使用性能分析

```python
from mc_agent_kit.execution import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
result = analyzer.profile(lambda: my_function())

print(f"执行时间: {result.total_time_ms}ms")
print(f"热点函数: {result.hotspots}")
```

---

## 安全性

### 1. 输入验证

```python
def process_user_input(data: dict) -> PluginResult:
    """处理用户输入，先验证"""
    
    # 验证必需字段
    required_fields = ["name", "value"]
    for field in required_fields:
        if field not in data:
            return PluginResult(
                success=False,
                error=f"缺少必需字段: {field}"
            )
    
    # 验证字段类型
    if not isinstance(data["name"], str):
        return PluginResult(
            success=False,
            error="name 必须是字符串"
        )
    
    if not isinstance(data["value"], (int, float)):
        return PluginResult(
            success=False,
            error="value 必须是数字"
        )
    
    # 验证范围
    if data["value"] < 0:
        return PluginResult(
            success=False,
            error="value 不能为负数"
        )
    
    # 处理验证后的数据
    return process_validated(data)
```

### 2. 使用沙箱

```python
from mc_agent_kit.plugin import PluginSandbox, SandboxConfig

# 创建沙箱配置
config = SandboxConfig(
    permission_level="RESTRICTED",
    allowed_modules=["json", "re"],
    blocked_modules=["os", "subprocess", "sys"],
    allowed_paths=["/data"],
    network_access=False
)

sandbox = PluginSandbox(config)

# 验证代码
violations = sandbox.validate_code(plugin_code)
for violation in violations:
    print(f"违规: {violation}")

# 在沙箱中执行
result = sandbox.execute(plugin_code)
```

### 3. 避免危险操作

```python
# 不推荐：直接执行用户输入
def unsafe(user_input):
    eval(user_input)  # 危险！

# 推荐：使用安全的替代方案
def safe(user_input):
    allowed_functions = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
    }
    
    parts = user_input.split()
    if parts[0] in allowed_functions:
        return allowed_functions[parts[0]](int(parts[1]), int(parts[2]))
    raise ValueError(f"未知操作: {parts[0]}")
```

---

## 错误处理

### 1. 具体异常

```python
# 不推荐：裸 except
try:
    do_something()
except:
    pass

# 推荐：捕获具体异常
try:
    do_something()
except FileNotFoundError as e:
    logger.error(f"文件未找到: {e}")
except PermissionError as e:
    logger.error(f"权限不足: {e}")
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise
```

### 2. 自定义异常

```python
class PluginError(Exception):
    """插件基础异常"""
    pass

class ConfigurationError(PluginError):
    """配置错误"""
    pass

class ValidationError(PluginError):
    """验证错误"""
    pass

def load_config(path: str) -> dict:
    """加载配置"""
    if not Path(path).exists():
        raise ConfigurationError(f"配置文件不存在: {path}")
    # ...
```

### 3. 错误恢复

```python
def execute_with_retry(
    func,
    max_retries: int = 3,
    delay: float = 1.0
) -> Any:
    """带重试的执行"""
    import time
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"尝试 {attempt + 1} 失败: {e}，等待重试...")
            time.sleep(delay)
```

---

## 测试策略

### 1. 单元测试

```python
# tests/test_my_plugin.py
import pytest
from my_plugin import MyPlugin

class TestMyPlugin:
    """MyPlugin 单元测试"""
    
    @pytest.fixture
    def plugin(self):
        return MyPlugin()
    
    def test_metadata(self, plugin):
        """测试元数据"""
        assert plugin.metadata.name == "my_plugin"
        assert plugin.metadata.version == "1.0.0"
    
    def test_execute_success(self, plugin):
        """测试成功执行"""
        result = plugin.execute({"action": "test"})
        assert result.success is True
    
    def test_execute_invalid_action(self, plugin):
        """测试无效操作"""
        result = plugin.execute({"action": "invalid"})
        assert result.success is False
```

### 2. 集成测试

```python
# tests/test_integration.py
import pytest
from mc_agent_kit.plugin import PluginManager, PluginLoader

class TestIntegration:
    """集成测试"""
    
    def test_load_and_execute(self, tmp_path):
        """测试加载和执行"""
        # 创建测试插件
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()
        # ... 创建插件文件
        
        # 加载插件
        manager = PluginManager()
        manager.load_from_path(plugin_dir)
        
        # 执行插件
        result = manager.execute("test_plugin", {"action": "test"})
        assert result.success is True
```

### 3. 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest tests/ --cov=my_plugin --cov-report=html
```

---

## 版本管理

### 语义化版本

使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

### 版本兼容性

```python
# plugin.json
{
  "version": "1.2.0",
  "compatibility": {
    "mc_agent_kit": ">=1.0.0,<2.0.0"
  }
}
```

### 版本检查

```python
from mc_agent_kit.plugin import VersionChecker, VersionCompatibility

checker = VersionChecker()
report = checker.check_compatibility("1.2.0", ">=1.0.0,<2.0.0")

if report.level == VersionCompatibility.INCOMPATIBLE:
    print(f"版本不兼容: {report.message}")
```

---

## 检查清单

### 发布前检查

- [ ] 所有测试通过
- [ ] 测试覆盖率 >= 80%
- [ ] 文档完整更新
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] 无安全漏洞
- [ ] 代码通过 ruff 检查
- [ ] 类型检查通过（mypy）

### 代码质量检查

```bash
# 代码格式检查
ruff check src/

# 类型检查
mypy src/

# 测试覆盖率
pytest --cov=src/ --cov-report=term-missing
```

---

## 相关文档

- [插件开发指南](plugin-development.md)
- [热重载功能](hot-reload.md)
- [插件调试指南](plugin-debugging.md)
- [常见问题](faq.md)

---

*文档版本: v1.0.0*
*最后更新: 2026-03-22*