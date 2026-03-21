"""
MC-Agent-Kit 知识库模块

为 AI Agent 提供 MC ModSDK 开发知识的检索能力。
"""

from .base import Document, DocumentChunk, SearchResult
from .knowledge_base import KnowledgeBase

__all__ = [
    "KnowledgeBase",
    "Document",
    "DocumentChunk",
    "SearchResult",
]


def create_knowledge_tool(kb: KnowledgeBase):
    """
    创建 Agent 可调用的知识库工具函数
    
    Args:
        kb: KnowledgeBase 实例
        
    Returns:
        可供 Agent 调用的工具函数
    """
    def mc_knowledge_search(
        query: str,
        doc_type: str = "all",
        top_k: int = 5
    ) -> str:
        """
        搜索 MC ModSDK 知识库
        
        Args:
            query: 搜索关键词或问题
            doc_type: 文档类型 (api/guide/demo/all)
            top_k: 返回结果数量
            
        Returns:
            搜索结果文本
        """
        results = kb.search(query, doc_type=doc_type, top_k=top_k)

        if not results:
            return "未找到相关内容"

        output = []
        for i, r in enumerate(results, 1):
            output.append(f"## 结果 {i}")
            output.append(f"来源: {r.source}")
            output.append(f"类型: {r.doc_type}")
            output.append(f"相关度: {r.score:.2f}")
            output.append(f"内容:\n{r.content[:500]}...")
            output.append("")

        return "\n".join(output)

    return mc_knowledge_search
