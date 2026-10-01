import os
from base.config import config
from base.logger import logger
from rag_qa.core.document_processor import process_documents  # 导入处理文档的函数
from rag_qa.core.vector_store import VectorStore
# 老的rag_system模块，该模块测试用它
from rag_qa.core.rag_system import RAGSystem
from openai import OpenAI  # 使用 OpenAI 接口

# RAG核心函数
def main(query_mode=True, directory_path="data"):
    """
        RAG核心函数
        :param query_mode: 查询模式   True：是查询    False：非查询（数据处理）
        :param directory_path: 操作目录
        :return: 无返回值，直接输出回答
    """
    try:
        # 初始化OpenAI客户端
        client = OpenAI(api_key=config.DASHSCOPE_API_KEY,
                        base_url=config.DASHSCOPE_BASE_URL)
    except Exception as e:
        logger.error(f"初始化 OpenAI 客户端失败 (请检查 API Key 和 Base URL): {e}")
        # 如果客户端初始化失败，可能无法继续，取决于模式
        if query_mode:  # 查询模式下必须要有 LLM
            print("错误：无法初始化语言模型客户端，无法进入查询模式。")
            return
        # 数据处理模式可能不需要 LLM，可以继续，但最好记录错误
        client = None  # 标记客户端不可用

    # 定义 LLM 调用函数 (仅在需要时定义和使用)
    def call_dashscope(prompt):
        if not client:  # 检查客户端是否可用
            logger.error("LLM 客户端未初始化，无法调用 call_dashscope")
            return f"错误: LLM客户端不可用"
        try:
            # 原生调用大模型
            completion = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手."},
                    {"role": "user", "content": prompt},
                ]
                # 可以添加 temperature 等参数
            )
            # 获取大模型的回复
            if completion.choices and completion.choices[0].message:
                return completion.choices[0].message.content
            else:
                logger.error("LLM API 调用返回无效响应或空消息")
                return "错误: LLM返回无效响应"
        except Exception as e:
            logger.error(f"LLM API (call_dashscope) 调用失败: {e}")
            return f"错误: 调用LLM失败 - {e}"

    try:
        # 初始化 VectorStore
        vector_store = VectorStore(
            collection_name=config.MILVUS_COLLECTION_NAME,
            host=config.MILVUS_HOST,
            port=config.MILVUS_PORT,
            database=config.MILVUS_DATABASE_NAME,
        )
    except Exception as e:
        logger.error(f"初始化 VectorStore 失败 (请检查 Milvus 连接配置): {e}")
        print("错误：无法连接到向量数据库，程序无法继续。")
        return

    # 根据模式执行不同操作
    if not query_mode:
        # --- 数据处理模式 --- 将 data 目录下所有学科的文档数据库写入到Milvus中
        logger.info("进入数据处理模式...")
        total_chunks_added = 0
        for source_dir in config.VALID_SOURCES:
            dir_path = os.path.join(directory_path, f"{source_dir}_data")
            if os.path.exists(dir_path):
                logger.info(f"开始处理目录: {dir_path}")
                try:
                    chunks = process_documents(
                        dir_path,
                        config.PARENT_CHUNK_SIZE,
                        config.CHILD_CHUNK_SIZE,
                        config.PARENT_CHUNK_OVERLAP,
                        config.CHILD_CHUNK_OVERLAP,
                    )
                    if chunks:
                        vector_store.add_documents(chunks)
                        total_chunks_added += len(chunks)
                        logger.info(f"成功处理目录 {dir_path}，添加了 {len(chunks)} 个文档块")
                    else:
                        logger.info(f"目录 {dir_path} 未发现有效文档或处理结果为空")
                except Exception as e:
                    logger.error(f"处理目录 {dir_path} 时出错: {e}")
            else:
                logger.warning(f"目录 {dir_path} 不存在，跳过处理")
        logger.info(f"数据处理完成，共添加了 {total_chunks_added} 个文档块到向量存储")
    else:
        # --- 交互式查询模式 ---
        if not client:  # 再次检查 LLM 客户端是否必须且可用
            print("错误：查询模式需要语言模型客户端，但初始化失败。")
            return

        logger.info("进入交互式查询模式...")
        try:
            # 初始化 RAG 系统
            rag_system = RAGSystem(vector_store, call_dashscope)
        except Exception as e:
            logger.error(f"初始化 RAGSystem 失败: {e}")
            print("错误：无法初始化 RAG 系统，无法进入查询模式。")
            return
        # ["ai", "java", "test", "ops", "bigdata"]
        valid_sources = config.VALID_SOURCES
        print("\n欢迎使用 EduRAG 交互式查询系统！")
        print(f"支持的学科类别：{valid_sources}")
        print("输入您的问题，或输入 'exit' 退出。")

        while True:
            # query 用户输入的问题
            query = input("\n请输入您的问题：")
            if query.lower() == "exit":
                logger.info("用户退出查询模式")
                print("再见！")
                break
            # source_filter_input 用户输入的学科过滤条件
            source_filter_input = input(f"请输入学科类别 ({'/'.join(valid_sources)}) (直接回车默认不过滤)：").strip()
            # 学科过滤条件
            source_filter = None  # 默认不过滤
            if source_filter_input:
                if source_filter_input in valid_sources:
                    source_filter = source_filter_input
                    logger.info(f"用户选择了学科过滤: {source_filter}")
                else:
                    logger.warning(
                        f"无效的学科类别 '{source_filter_input}'，将不过滤"
                    )
                    print(f"提示：输入的学科 '{source_filter_input}' 无效，将不过滤。")

            try:
                print("正在生成答案，请稍候...")
                # 走 rag_system.py 的 generate_answer 函数
                answer = rag_system.generate_answer(query, source_filter=source_filter)
                print("-" * 30)
                print(f"问题: {query}")
                print(f"回答: {answer}")
                print("-" * 30)
            except Exception as e:
                logger.error(f"处理查询 '{query}' 时失败: {str(e)}")
                print(f"抱歉，处理您的问题时遇到了错误，请稍后重试或联系管理员。\n")


if __name__ == "__main__":
    # 模式一：默认进入查询模式
    # 若要执行数据处理，可以修改调用方式，例如：
    # main(query_mode=False)
    # 或者通过命令行参数控制

    # # 模式二：查询模式
    import argparse
    parser = argparse.ArgumentParser(description="EduRAG System Main Entry Point")
    # store_true：表示存储bool值
    parser.add_argument('--data-processing', action='store_true',
                        help='Run in data processing mode instead of query mode.')
    # 字符串类型，默认值：./data/ai_data
    parser.add_argument('--data-dir', type=str, default='./data/ai_data',
                        help='Path to the data directory.')
    args = parser.parse_args()
    print('args-->', args)
    main(query_mode=(not args.data_processing), directory_path=args.data_dir)

    # main(query_mode=True)
