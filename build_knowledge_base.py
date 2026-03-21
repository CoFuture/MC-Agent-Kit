"""
构建知识库脚本

扫描 ModSDK 文档目录，解析所有文档，生成知识库索引文件。
"""

import sys
from pathlib import Path

# 添加 src 到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from mc_agent_kit.knowledge_base import KnowledgeIndexer, KnowledgeRetriever


def main():
    # 配置路径
    docs_dir = Path(__file__).parent / "resources" / "docs" / "mcdocs"
    output_path = Path(__file__).parent / "data" / "knowledge_base.json"

    print(f"文档目录: {docs_dir}")
    print(f"输出文件: {output_path}")

    # 构建知识库
    print("\n开始构建知识库...")
    indexer = KnowledgeIndexer()

    try:
        kb = indexer.build(str(docs_dir), str(output_path))
        stats = kb.stats()

        print("\n知识库统计:")
        print(f"  API 数量: {stats['total_apis']}")
        print(f"  事件数量: {stats['total_events']}")
        print(f"  枚举数量: {stats['total_enums']}")
        print(f"  API 模块: {', '.join(stats['api_modules'][:5])}{'...' if len(stats['api_modules']) > 5 else ''}")
        print(f"  事件模块: {', '.join(stats['event_modules'][:5])}{'...' if len(stats['event_modules']) > 5 else ''}")

        # 测试检索器
        print("\n测试检索器...")
        retriever = KnowledgeRetriever(kb)

        # 搜索测试
        results = retriever.search_api("entity")
        print(f"  搜索 'entity' API: {len(results)} 条结果")

        results = retriever.search_event("hurt")
        print(f"  搜索 'hurt' 事件: {len(results)} 条结果")

        # 模块列表
        modules = retriever.list_modules()
        print(f"  总模块数: {len(modules)}")

        print("\n知识库构建完成!")

    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请确保 resources/docs/mcdocs 目录存在")
        sys.exit(1)
    except Exception as e:
        print(f"构建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()