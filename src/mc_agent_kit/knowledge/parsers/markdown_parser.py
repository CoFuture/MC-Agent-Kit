"""
Markdown 文档解析器

解析 ModSDK Markdown 文档，提取结构化信息。
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class APIParameter:
    """API 参数信息"""
    name: str
    type: str
    description: str
    required: bool = True
    default: str | None = None


@dataclass
class APIInfo:
    """API 接口信息"""
    name: str
    description: str
    module: str | None = None
    scope: str | None = None  # client/server/both
    parameters: list[APIParameter] = field(default_factory=list)
    return_type: str | None = None
    return_description: str | None = None
    code_examples: list[str] = field(default_factory=list)
    related_apis: list[str] = field(default_factory=list)
    related_events: list[str] = field(default_factory=list)


@dataclass
class EventInfo:
    """事件信息"""
    name: str
    description: str
    module: str | None = None
    scope: str | None = None
    parameters: list[APIParameter] = field(default_factory=list)
    code_examples: list[str] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """解析后的文档"""
    path: str
    title: str
    doc_type: str  # api/event/guide/demo
    content: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)
    api_info: APIInfo | None = None
    event_info: EventInfo | None = None
    code_blocks: list[str] = field(default_factory=list)


class MarkdownParser:
    """
    Markdown 文档解析器

    解析 ModSDK 的 Markdown 文档，提取结构化信息。

    使用示例:
        parser = MarkdownParser()
        doc = parser.parse("/path/to/api.md")
        print(doc.api_info)
    """

    def __init__(self) -> None:
        """初始化解析器"""
        self.code_block_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        self.table_pattern = re.compile(r"\|[^\n]+\|\n\|[-:| ]+\|\n((?:\|[^\n]+\|\n?)+)", re.MULTILINE)
        self.header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def parse(self, content: str, path: str = "") -> ParsedDocument:
        """
        解析 Markdown 文档

        Args:
            content: 文档内容
            path: 文档路径（用于推断类型）

        Returns:
            解析后的文档对象
        """
        # 提取 frontmatter
        frontmatter, content = self._parse_frontmatter(content)

        # 提取标题
        title = self._extract_title(content)

        # 提取代码块
        code_blocks = self._extract_code_blocks(content)

        # 提取章节
        sections = self._extract_sections(content)

        # 推断文档类型
        doc_type = self._infer_doc_type(path, content, frontmatter)

        # 创建文档对象
        doc = ParsedDocument(
            path=path,
            title=title,
            doc_type=doc_type,
            content=content,
            frontmatter=frontmatter,
            sections=sections,
            code_blocks=code_blocks,
        )

        # 根据类型解析详细信息
        if doc_type == "api":
            doc.api_info = self._parse_api_info(content, frontmatter, sections)
        elif doc_type == "event":
            doc.event_info = self._parse_event_info(content, frontmatter, sections)

        return doc

    def parse_file(self, path: str) -> ParsedDocument:
        """
        解析文件

        Args:
            path: 文件路径

        Returns:
            解析后的文档对象
        """
        with open(path, encoding="utf-8") as f:
            content = f.read()
        return self.parse(content, path)

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """解析 YAML frontmatter"""
        if not content.startswith("---"):
            return {}, content

        # 查找结束标记
        end_match = re.search(r"\n---\n", content[3:])
        if not end_match:
            return {}, content

        fm_content = content[3:end_match.end() + 2]
        remaining = content[end_match.end() + 3:]

        # 简单解析 YAML
        frontmatter: dict[str, Any] = {}
        for line in fm_content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip()

        return frontmatter, remaining

    def _extract_title(self, content: str) -> str:
        """提取文档标题"""
        match = self.header_pattern.search(content)
        if match:
            return str(match.group(2).strip())
        return ""

    def _extract_code_blocks(self, content: str) -> list[str]:
        """提取代码块"""
        blocks = []
        for match in self.code_block_pattern.finditer(content):
            match.group(1)
            code = match.group(2).strip()
            if code:
                blocks.append(code)
        return blocks

    def _extract_sections(self, content: str) -> dict[str, str]:
        """按标题提取章节"""
        sections: dict[str, str] = {}

        # 找到所有标题位置
        headers = []
        for match in self.header_pattern.finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append((level, title, match.start(), match.end()))

        # 提取每个标题下的内容
        for i, (level, title, start, end) in enumerate(headers):
            # 找到下一个同级或更高级标题
            section_end = len(content)
            for j in range(i + 1, len(headers)):
                if headers[j][0] <= level:
                    section_end = headers[j][2]
                    break

            section_content = content[end:section_end].strip()
            sections[title] = section_content

        return sections

    def _infer_doc_type(self, path: str, content: str, frontmatter: dict[str, Any]) -> str:
        """推断文档类型"""
        path_lower = path.lower().replace("\\", "/")

        # 根据路径推断
        if "/事件/" in path_lower or "event" in path_lower:
            return "event"
        if "/接口/" in path_lower or "api" in path_lower:
            return "api"
        if "guide" in path_lower or "教程" in path_lower:
            return "guide"
        if "demo" in path_lower:
            return "demo"

        # 根据内容推断
        if "事件名" in content or "eventName" in content:
            return "event"
        if "接口名" in content or "API" in content.upper():
            return "api"

        return "guide"

    def _parse_api_info(
        self,
        content: str,
        frontmatter: dict[str, Any],
        sections: dict[str, str],
    ) -> APIInfo:
        """解析 API 信息"""
        # 提取 API 名称
        name = frontmatter.get("名称", frontmatter.get("name", ""))
        if not name:
            # 从标题或内容提取
            name_match = re.search(r"`?(\w+)`\s*(?:接口|API)", content)
            if name_match:
                name = name_match.group(1)

        # 提取描述
        description = sections.get("描述", sections.get("简介", ""))

        # 提取模块
        module = frontmatter.get("模块", frontmatter.get("module", ""))

        # 提取作用域
        scope = self._extract_scope(content)

        # 提取参数
        parameters = self._extract_parameters(sections)

        # 提取返回值
        return_type, return_desc = self._extract_return_value(sections)

        # 提取代码示例
        code_examples = self._extract_code_blocks(content)

        return APIInfo(
            name=name,
            description=description,
            module=module,
            scope=scope,
            parameters=parameters,
            return_type=return_type,
            return_description=return_desc,
            code_examples=code_examples,
        )

    def _parse_event_info(
        self,
        content: str,
        frontmatter: dict[str, Any],
        sections: dict[str, str],
    ) -> EventInfo:
        """解析事件信息"""
        # 提取事件名称
        name = frontmatter.get("事件名", frontmatter.get("name", ""))
        if not name:
            name_match = re.search(r"`?(\w+)`\s*事件", content)
            if name_match:
                name = name_match.group(1)

        # 提取描述
        description = sections.get("描述", sections.get("简介", ""))

        # 提取模块
        module = frontmatter.get("模块", "")

        # 提取作用域
        scope = self._extract_scope(content)

        # 提取参数
        parameters = self._extract_parameters(sections)

        # 提取代码示例
        code_examples = self._extract_code_blocks(content)

        return EventInfo(
            name=name,
            description=description,
            module=module,
            scope=scope,
            parameters=parameters,
            code_examples=code_examples,
        )

    def _extract_scope(self, content: str) -> str | None:
        """提取作用域"""
        if "客户端" in content and "服务端" in content:
            return "both"
        if "客户端" in content:
            return "client"
        if "服务端" in content:
            return "server"
        return None

    def _extract_parameters(self, sections: dict[str, str]) -> list[APIParameter]:
        """从表格提取参数"""
        parameters: list[APIParameter] = []

        # 查找参数表
        param_section = sections.get("参数", sections.get("参数说明", ""))
        if not param_section:
            return parameters

        # 解析表格
        table_matches = self.table_pattern.findall(param_section)
        for table_content in table_matches:
            rows = table_content.strip().split("\n")
            for row in rows:
                cells = [c.strip() for c in row.split("|") if c.strip()]
                if len(cells) >= 3:
                    param_name = cells[0]
                    param_type = cells[1]
                    param_desc = cells[2] if len(cells) > 2 else ""

                    # 跳过表头
                    if param_name in ["参数名", "参数", "名称", "name"]:
                        continue

                    parameters.append(APIParameter(
                        name=param_name,
                        type=param_type,
                        description=param_desc,
                    ))

        return parameters

    def _extract_return_value(self, sections: dict[str, str]) -> tuple[str | None, str | None]:
        """提取返回值信息"""
        return_section = sections.get("返回值", "")
        if not return_section:
            return None, None

        # 简单提取
        lines = return_section.strip().split("\n")
        return_type = None
        return_desc = None

        for line in lines:
            line = line.strip()
            if line.startswith("类型") or line.startswith("type"):
                return_type = line.split(":", 1)[-1].strip() if ":" in line else None
            elif line.startswith("说明") or line.startswith("desc"):
                return_desc = line.split(":", 1)[-1].strip() if ":" in line else None

        return return_type, return_desc
