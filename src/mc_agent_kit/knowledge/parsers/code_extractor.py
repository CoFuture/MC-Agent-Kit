"""
代码示例提取器

从文档中提取和分析代码示例。
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeExample:
    """代码示例"""
    id: str
    code: str
    language: str
    source: str
    description: str = ""
    api_names: list[str] = field(default_factory=list)
    event_names: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "language": self.language,
            "source": self.source,
            "description": self.description,
            "api_names": self.api_names,
            "event_names": self.event_names,
            "tags": self.tags,
        }


class CodeExtractor:
    """
    代码示例提取器

    从文档中提取代码示例，并识别其中使用的 API 和事件。

    使用示例:
        extractor = CodeExtractor()
        examples = extractor.extract_from_file("/path/to/doc.md")
        for ex in examples:
            print(ex.api_names, ex.event_names)
    """

    # 常用 API 模式
    API_PATTERNS = [
        # 服务端 API
        r"server\.GetConfig\(\)",
        r"server\.GetPlayer\(([^)]+)\)",
        r"server\.CreateEngineEntity\(([^)]+)\)",
        r"server\.GetEngineActor\(([^)]+)\)",
        r"server\.GetGameLoopInfo\(\)",
        r"server\.NotifyToClient\(([^)]+)\)",
        r"server\.BroadcastToAllClient\(([^)]+)\)",
        # 客户端 API
        r"client\.GetConfig\(\)",
        r"client\.GetPlayer\(([^)]+)\)",
        r"client\.NotifyToServer\(([^)]+)\)",
        # 常用函数
        r"GetEngineType\(\)",
        r"GetAttr\(([^)]+)\)",
        r"SetAttr\(([^)]+)\)",
        r"GetPos\(\)",
        r"SetPos\(([^)]+)\)",
        r"GetRot\(\)",
        r"SetRot\(([^)]+)\)",
        r"GetFootPos\(\)",
        r"SetFootPos\(([^)]+)\)",
        r"CreateEntity\(([^)]+)\)",
        r"DestroyEntity\(([^)]+)\)",
        r"SpawnToPlayer\(([^)]+)\)",
        r"Destroy\(\)",
        # 配置相关
        r"GetConfigByKey\(([^)]+)\)",
        r"SetConfigByKey\(([^)]+)\)",
    ]

    # 事件模式
    EVENT_PATTERNS = [
        r"(\w+Event)",  # 如 ServerPlayerJoinedEvent
        r"ListenForEvent\s*\(\s*[\"'](\w+)[\"']",  # 监听事件
        r"On(\w+)",  # 回调事件
    ]

    def __init__(self):
        """初始化提取器"""
        self.code_block_pattern = re.compile(
            r"```(\w*)\n(.*?)```",
            re.DOTALL
        )

        # 编译 API 和事件模式
        self._api_regexes = [
            (re.compile(p), self._extract_api_name(p))
            for p in self.API_PATTERNS
        ]

        self._event_regexes = [
            re.compile(p) for p in self.EVENT_PATTERNS
        ]

    def extract_from_content(
        self,
        content: str,
        source: str = "",
    ) -> list[CodeExample]:
        """
        从内容中提取代码示例

        Args:
            content: 文档内容
            source: 来源标识

        Returns:
            代码示例列表
        """
        examples = []

        for i, match in enumerate(self.code_block_pattern.finditer(content)):
            language = match.group(1) or "text"
            code = match.group(2).strip()

            if not code or len(code) < 10:
                continue

            # 生成 ID
            example_id = self._generate_id(source, i)

            # 提取 API 和事件
            api_names = self._extract_apis(code)
            event_names = self._extract_events(code)

            # 提取描述（代码块前的文本）
            description = self._extract_description(content, match.start())

            # 生成标签
            tags = self._generate_tags(code, api_names, event_names)

            examples.append(CodeExample(
                id=example_id,
                code=code,
                language=language,
                source=source,
                description=description,
                api_names=api_names,
                event_names=event_names,
                tags=tags,
            ))

        return examples

    def extract_from_file(self, path: str) -> list[CodeExample]:
        """
        从文件中提取代码示例

        Args:
            path: 文件路径

        Returns:
            代码示例列表
        """
        with open(path, encoding="utf-8") as f:
            content = f.read()

        return self.extract_from_content(content, source=path)

    def extract_from_directory(
        self,
        dir_path: str,
        recursive: bool = True,
    ) -> list[CodeExample]:
        """
        从目录中提取代码示例

        Args:
            dir_path: 目录路径
            recursive: 是否递归搜索

        Returns:
            代码示例列表
        """
        from pathlib import Path

        examples = []
        path = Path(dir_path)

        pattern = "**/*.md" if recursive else "*.md"

        for fp in path.glob(pattern):
            try:
                file_examples = self.extract_from_file(str(fp))
                examples.extend(file_examples)
            except Exception:
                continue

        return examples

    def find_examples_by_api(
        self,
        examples: list[CodeExample],
        api_name: str,
    ) -> list[CodeExample]:
        """
        查找使用特定 API 的代码示例

        Args:
            examples: 代码示例列表
            api_name: API 名称

        Returns:
            匹配的代码示例列表
        """
        return [
            ex for ex in examples
            if api_name in ex.api_names or api_name.lower() in ex.code.lower()
        ]

    def find_examples_by_event(
        self,
        examples: list[CodeExample],
        event_name: str,
    ) -> list[CodeExample]:
        """
        查找使用特定事件的代码示例

        Args:
            examples: 代码示例列表
            event_name: 事件名称

        Returns:
            匹配的代码示例列表
        """
        return [
            ex for ex in examples
            if event_name in ex.event_names or event_name.lower() in ex.code.lower()
        ]

    def find_examples_by_tag(
        self,
        examples: list[CodeExample],
        tag: str,
    ) -> list[CodeExample]:
        """
        按标签查找代码示例

        Args:
            examples: 代码示例列表
            tag: 标签

        Returns:
            匹配的代码示例列表
        """
        return [ex for ex in examples if tag.lower() in [t.lower() for t in ex.tags]]

    def _generate_id(self, source: str, index: int) -> str:
        """生成示例 ID"""
        import hashlib
        hash_input = f"{source}:{index}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _extract_api_name(self, pattern: str) -> str:
        """从模式提取 API 名称"""
        # 简单提取函数名
        match = re.search(r"\.(\w+)\(", pattern)
        if match:
            return match.group(1)
        match = re.search(r"(\w+)\(", pattern)
        if match:
            return match.group(1)
        return ""

    def _extract_apis(self, code: str) -> list[str]:
        """从代码中提取使用的 API"""
        apis = set()

        for pattern, api_name in self._api_regexes:
            if pattern.search(code):
                if api_name:
                    apis.add(api_name)

        # 直接搜索函数调用
        api_calls = re.findall(r"(?:server|client)\.(\w+)", code)
        apis.update(api_calls)

        # 搜索直接函数调用
        direct_calls = re.findall(r"(?<![.\w])(\w+)\s*\(", code)
        for call in direct_calls:
            if call[0].isupper() or call in ["GetConfig", "SetConfig", "GetAttr", "SetAttr"]:
                apis.add(call)

        return sorted(apis)

    def _extract_events(self, code: str) -> list[str]:
        """从代码中提取事件名称"""
        events = set()

        for regex in self._event_regexes:
            matches = regex.findall(code)
            events.update(matches)

        # 特殊处理 ListenForEvent
        listen_matches = re.findall(r"ListenForEvent\s*\(\s*[\"']([^\"']+)[\"']", code)
        events.update(listen_matches)

        return sorted(events)

    def _extract_description(self, content: str, code_start: int) -> str:
        """提取代码块前的描述文本"""
        # 找到代码块前的文本
        before_code = content[:code_start].strip()

        # 取最后几行作为描述
        lines = before_code.split("\n")
        desc_lines = []

        for line in reversed(lines):
            line = line.strip()
            if not line:
                break
            if line.startswith("#"):
                desc_lines.insert(0, line.lstrip("# "))
                break
            if len(desc_lines) < 2:
                desc_lines.insert(0, line)

        return " ".join(desc_lines).strip()[:200]

    def _generate_tags(
        self,
        code: str,
        api_names: list[str],
        event_names: list[str],
    ) -> list[str]:
        """生成代码标签"""
        tags = set()

        # 根据代码内容生成标签
        if "entity" in code.lower() or "Entity" in code:
            tags.add("entity")
        if "player" in code.lower() or "Player" in code:
            tags.add("player")
        if "item" in code.lower() or "Item" in code:
            tags.add("item")
        if "block" in code.lower() or "Block" in code:
            tags.add("block")
        if "ui" in code.lower() or "UI" in code:
            tags.add("ui")
        if "server" in code:
            tags.add("server")
        if "client" in code:
            tags.add("client")
        if "event" in code.lower():
            tags.add("event")
        if "config" in code.lower():
            tags.add("config")

        # 根据事件名称生成标签
        for event in event_names:
            if "Player" in event:
                tags.add("player")
            if "Entity" in event:
                tags.add("entity")
            if "Item" in event:
                tags.add("item")
            if "Block" in event:
                tags.add("block")
            if "Chat" in event:
                tags.add("chat")

        return sorted(tags)