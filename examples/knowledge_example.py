"""
知识库使用示例

展示如何构建和使用 MC ModSDK 知识库。
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mc_agent_kit.knowledge import KnowledgeBase


def main():
    """知识库使用示例"""
    
    # 初始化知识库
    docs_path = os.path.join(os.path.dirname(__file__), "..", "resources", "docs")
    persist_dir = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_db")
    
    kb = KnowledgeBase(
        docs_path=docs_path,
        persist_dir=persist_dir,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )
    
    print("=" * 60)
    print("MC-Agent-Kit 知识库")
    print("=" * 60)
    
    # 检查是否需要构建索引
    if not os.path.exists(os.path.join(persist_dir, "metadata.json")):
        print("\n首次运行，正在构建索引...")
        kb.build_index()
        print("索引构建完成！")
    else:
        print("\n加载已有索引...")
        kb = KnowledgeBase.load(persist_dir)
    
    # 交互式搜索
    print("\n输入问题进行搜索，输入 'q' 退出")
    print("-" * 60)
    
    while True:
        query = input("\n搜索: ").strip()
        
        if query.lower() == "q":
            break
        
        if not query:
            continue
        
        # 执行搜索
        results = kb.search(query, top_k=3)
        
        if not results:
            print("未找到相关内容")
            continue
        
        # 显示结果
        print(f"\n找到 {len(results)} 个相关结果:\n")
        
        for i, r in enumerate(results, 1):
            print(f"### 结果 {i}")
            print(f"来源: {r.source}")
            print(f"类型: {r.doc_type.value}")
            print(f"相关度: {r.score:.2f}")
            print(f"内容:\n{r.content[:400]}...")
            print("-" * 40)


def demo_api_queries():
    """API 查询示例"""
    
    persist_dir = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_db")
    
    if not os.path.exists(os.path.join(persist_dir, "metadata.json")):
        print("请先运行 main() 构建索引")
        return
    
    kb = KnowledgeBase.load(persist_dir)
    
    # API 查询示例
    queries = [
        "GetEngineType",
        "AddEntityClientEvent",
        "如何创建自定义物品",
        "自定义方块示例",
    ]
    
    print("\n" + "=" * 60)
    print("API 查询示例")
    print("=" * 60)
    
    for query in queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        
        result = kb.get_api(query)
        if result:
            print(f"名称: {result.name}")
            print(f"来源: {result.source}")
            print(f"内容:\n{result.content[:300]}...")
        else:
            print("未找到")


if __name__ == "__main__":
    main()