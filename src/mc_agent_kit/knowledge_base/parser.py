"""
文档解析器

解析 ModSDK Markdown 文档，提取结构化信息。
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path

from .models import (
    APIEntry,
    APIParameter,
    CodeExample,
    EnumEntry,
    EnumValue,
    EventEntry,
    EventParameter,
    Scope,
)


class DocumentParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    def parse(self, content: str, source_path: str) -> list:
        """解析文档内容，返回条目列表"""
        pass


class MarkdownParser(DocumentParser):
    """Markdown 文档解析器

    解析 ModSDK 的 Markdown 格式文档，提取 API、事件、枚举等信息。

    文档格式示例：
    - 事件文档：包含事件名称、描述、参数、返回值、示例代码
    - API 文档：包含接口名称、描述、参数、返回值、示例代码
    - 枚举文档：包含枚举名称、值列表
    """

    # 作用域标记正则
    SCOPE_SERVER_PATTERN = re.compile(r"服务端")
    SCOPE_CLIENT_PATTERN = re.compile(r"客户端")

    # 代码块正则
    CODE_BLOCK_PATTERN = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)

    # 表格行正则 - 匹配 | cell | cell | 格式
    TABLE_ROW_PATTERN = re.compile(r"\|([^|\n]+)")

    # 标题正则
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    # 方法路径正则（如：method in mod.server.component.itemCompServer.ItemCompServer）
    METHOD_PATH_PATTERN = re.compile(r"method in ([\w.]+)")

    def parse(self, content: str, source_path: str) -> list:
        """解析文档内容

        Args:
            content: Markdown 文档内容
            source_path: 文档源路径

        Returns:
            解析出的条目列表
        """
        # 移除 YAML frontmatter
        content = self._remove_frontmatter(content)

        # 根据文档类型选择解析方法
        if "事件" in source_path or self._is_event_document(content):
            return self._parse_events(content, source_path)
        elif "枚举" in source_path:
            return self._parse_enums(content, source_path)
        elif "接口" in source_path or self._is_api_document(content):
            return self._parse_apis(content, source_path)

        return []

    def _remove_frontmatter(self, content: str) -> str:
        """移除 YAML frontmatter"""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content

    def _is_event_document(self, content: str) -> bool:
        """判断是否为事件文档"""
        # 事件文档通常包含"触发时机"或"监听"等关键词
        return bool(re.search(r"触发时机|监听|ListenForEvent", content))

    def _is_api_document(self, content: str) -> bool:
        """判断是否为 API 文档"""
        # API 文档通常包含"method in"标记
        return bool(self.METHOD_PATH_PATTERN.search(content))

    def _parse_scope(self, text: str) -> Scope:
        """解析作用域（客户端/服务端）"""
        has_server = bool(self.SCOPE_SERVER_PATTERN.search(text))
        has_client = bool(self.SCOPE_CLIENT_PATTERN.search(text))

        if has_server and has_client:
            return Scope.BOTH
        elif has_server:
            return Scope.SERVER
        elif has_client:
            return Scope.CLIENT
        return Scope.UNKNOWN

    def _parse_table(self, table_text: str) -> list[dict]:
        """解析 Markdown 表格

        Args:
            table_text: 表格文本

        Returns:
            表格行列表，每行为字典 {列名: 值}
        """
        lines = table_text.strip().split("\n")
        if len(lines) < 2:
            return []

        # 解析表头
        header_cells = self.TABLE_ROW_PATTERN.findall(lines[0])
        if not header_cells:
            return []

        headers = [h.strip() for h in header_cells]

        # 跳过分隔行（如 | --- | --- |）
        data_lines = lines[2:] if len(lines) > 2 else []

        rows = []
        for line in data_lines:
            cells = self.TABLE_ROW_PATTERN.findall(line)
            if len(cells) >= len(headers):
                row = {headers[i]: cells[i].strip() for i in range(len(headers))}
                rows.append(row)

        return rows

    def _extract_code_blocks(self, text: str) -> list[CodeExample]:
        """提取代码块"""
        examples = []
        for match in self.CODE_BLOCK_PATTERN.finditer(text):
            language = match.group(1)
            code = match.group(2).strip()
            examples.append(CodeExample(code=code, language=language))
        return examples

    def _parse_events(self, content: str, source_path: str) -> list[EventEntry]:
        """解析事件文档

        事件文档格式：
        ## EventName
        <span>服务端/客户端</span>

        - 描述
            描述文本

        - 参数
            | 参数名 | 数据类型 | 说明 |
            | --- | --- | --- |
            | id | str | 实体id |

        - 返回值
            无

        - 备注
            备注内容

        - 示例
            ```python
            代码
            ```
        """
        events = []

        # 获取模块名（从文件路径推断）
        module = self._extract_module_from_path(source_path)

        # 按 ## 分割文档（每个事件一个章节）
        sections = re.split(r"\n## (?=[A-Z])", content)

        for section in sections:
            if not section.strip():
                continue

            # 提取事件名称（第一个非空行）
            lines = section.strip().split("\n")
            if not lines:
                continue

            event_name = lines[0].strip()
            if not event_name or not event_name[0].isupper():
                continue

            # 解析作用域
            scope = self._parse_scope(section)

            # 解析描述
            description = self._extract_description(section)

            # 解析参数
            parameters = self._extract_event_parameters(section)

            # 解析返回值
            return_value = self._extract_return_value(section)

            # 解析备注
            remarks = self._extract_remarks(section)

            # 提取代码示例
            examples = self._extract_code_blocks(section)

            event = EventEntry(
                name=event_name,
                module=module,
                description=description,
                scope=scope,
                parameters=parameters,
                return_value=return_value,
                examples=examples,
                remarks=remarks,
                source_path=source_path,
            )
            events.append(event)

        return events

    def _parse_apis(self, content: str, source_path: str) -> list[APIEntry]:
        """解析 API 文档

        API 文档格式：
        ## ApiName
        <span>服务端/客户端</span>

        method in mod.server.component.xxx.XxxComp

        - 描述
            描述文本

        - 参数
            | 参数名 | 数据类型 | 说明 |
            | --- | --- | --- |
            | entityId | str | 实体id |

        - 返回值
            | 数据类型 | 说明 |
            | --- | --- |
            | bool | 是否成功 |

        - 示例
            ```python
            代码
            ```
        """
        apis = []

        # 获取模块名
        module = self._extract_module_from_path(source_path)

        # 按 ## 分割文档
        sections = re.split(r"\n## (?=[A-Z])", content)

        for section in sections:
            if not section.strip():
                continue

            lines = section.strip().split("\n")
            if not lines:
                continue

            api_name = lines[0].strip()
            if not api_name or not api_name[0].isupper():
                continue

            # 解析作用域
            scope = self._parse_scope(section)

            # 解析方法路径
            method_path = self._extract_method_path(section)

            # 解析描述
            description = self._extract_description(section)

            # 解析参数
            parameters = self._extract_api_parameters(section)

            # 解析返回值
            return_type, return_description = self._extract_return_type(section)

            # 解析备注
            remarks = self._extract_remarks(section)

            # 提取代码示例
            examples = self._extract_code_blocks(section)

            api = APIEntry(
                name=api_name,
                module=module,
                description=description,
                method_path=method_path,
                scope=scope,
                parameters=parameters,
                return_type=return_type,
                return_description=return_description,
                examples=examples,
                remarks=remarks,
                source_path=source_path,
            )
            apis.append(api)

        return apis

    def _parse_enums(self, content: str, source_path: str) -> list[EnumEntry]:
        """解析枚举文档"""
        enums = []

        # 获取枚举名称（从文件名）
        enum_name = Path(source_path).stem

        # 解析表格获取枚举值
        # 查找表格
        table_match = re.search(r"\|.+\|\n\|.+\|\n([\s\S]+?)(?=\n#|\n##|\Z)", content)
        if table_match:
            table_text = table_match.group(0)
            rows = self._parse_table(table_text)

            values = []
            for row in rows:
                # 尝试不同的列名
                name = row.get("名称") or row.get("枚举名") or row.get("Key") or row.get("名", "")
                value = row.get("值") or row.get("Value") or name
                desc = row.get("说明") or row.get("描述") or row.get("Description") or ""

                if name:
                    values.append(EnumValue(name=name, value=value, description=desc))

            if values:
                # 提取描述
                description = self._extract_description(content)

                enums.append(
                    EnumEntry(
                        name=enum_name,
                        values=values,
                        description=description,
                        source_path=source_path,
                    )
                )

        return enums

    def _extract_module_from_path(self, path: str) -> str:
        """从文件路径提取模块名"""
        parts = Path(path).parts

        # 查找 "接口" 或 "事件" 目录
        for i, part in enumerate(parts):
            if part in ("接口", "事件", "枚举值"):
                # 获取下一级目录作为模块名
                if i + 1 < len(parts):
                    return parts[i + 1]
                return part

        # 默认返回最后一个目录名
        if len(parts) > 1:
            return parts[-2]
        return "unknown"

    def _extract_description(self, text: str) -> str:
        """提取描述文本"""
        # 查找 "- 描述" 后的内容
        desc_match = re.search(r"- 描述\s*\n\s*(.+?)(?=\n-|\n#|\Z)", text, re.DOTALL)
        if desc_match:
            desc = desc_match.group(1).strip()
            # 清理换行和多余空白
            desc = re.sub(r"\s+", " ", desc)
            return desc
        return ""

    def _extract_method_path(self, text: str) -> str:
        """提取方法路径"""
        match = self.METHOD_PATH_PATTERN.search(text)
        if match:
            return match.group(1)
        return ""

    def _extract_event_parameters(self, text: str) -> list[EventParameter]:
        """提取事件参数"""
        parameters = []

        # 查找 "- 参数" 后的表格
        param_match = re.search(r"- 参数\s*\n([\s\S]+?)(?=\n-|\n#|\Z)", text)
        if param_match:
            table_text = param_match.group(1)
            rows = self._parse_table(table_text)

            for row in rows:
                name = row.get("参数名", "")
                data_type = row.get("数据类型", "")
                description = row.get("说明", "")

                # 检查是否可修改
                mutable = "修改" in description or "设置为" in description

                if name:
                    parameters.append(
                        EventParameter(
                            name=name,
                            data_type=data_type,
                            description=description,
                            mutable=mutable,
                        )
                    )

        return parameters

    def _extract_api_parameters(self, text: str) -> list[APIParameter]:
        """提取 API 参数"""
        parameters = []

        # 查找 "- 参数" 后的表格
        param_match = re.search(r"- 参数\s*\n([\s\S]+?)(?=\n-|\n#|\Z)", text)
        if param_match:
            table_text = param_match.group(1)
            rows = self._parse_table(table_text)

            for row in rows:
                name = row.get("参数名", "")
                data_type = row.get("数据类型", "")
                description = row.get("说明", "")

                # 检查是否可选
                optional = "可选" in description or "默认" in description

                if name:
                    parameters.append(
                        APIParameter(
                            name=name,
                            data_type=data_type,
                            description=description,
                            optional=optional,
                        )
                    )

        return parameters

    def _extract_return_value(self, text: str) -> str | None:
        """提取事件返回值"""
        ret_match = re.search(r"- 返回值\s*\n\s*(.+?)(?=\n-|\n#|\Z)", text, re.DOTALL)
        if ret_match:
            ret = ret_match.group(1).strip()
            if ret == "无":
                return None
            return ret
        return None

    def _extract_return_type(self, text: str) -> tuple[str | None, str | None]:
        """提取 API 返回值类型和描述"""
        ret_match = re.search(r"- 返回值\s*\n([\s\S]+?)(?=\n-|\n#|\Z)", text)
        if ret_match:
            table_text = ret_match.group(1)
            rows = self._parse_table(table_text)

            if rows:
                row = rows[0]
                return_type = row.get("数据类型", "")
                return_desc = row.get("说明", "")
                return return_type, return_desc

        return None, None

    def _extract_remarks(self, text: str) -> list[str]:
        """提取备注"""
        remarks = []

        # 查找 "- 备注" 后的内容
        remarks_match = re.search(r"- 备注\s*\n([\s\S]+?)(?=\n-|\n#|\Z)", text)
        if remarks_match:
            remarks_text = remarks_match.group(1).strip()
            # 按行分割，每条备注一行
            for line in remarks_text.split("\n"):
                line = line.strip()
                if line and not line.startswith("|"):  # 排除表格
                    # 清理开头的 "- "
                    line = re.sub(r"^-\s*", "", line)
                    remarks.append(line)

        return remarks


def parse_document(file_path: str) -> list:
    """解析单个文档文件

    Args:
        file_path: 文档文件路径

    Returns:
        解析出的条目列表
    """
    path = Path(file_path)
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    parser = MarkdownParser()
    return parser.parse(content, file_path)
