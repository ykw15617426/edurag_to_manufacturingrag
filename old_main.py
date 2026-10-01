"""
    系统入口：旧版
"""
# 导入 MySQL 系统组件
from mysql_qa.db.mysql_client import MySQLClient
from mysql_qa.cache.redis_client import RedisClient
from mysql_qa.retrieval.bm25_search import BM25Search
# 导入 RAG 系统组件
from rag_qa.core.vector_store import VectorStore
from rag_qa.core.rag_system import RAGSystem
# 导入配置和日志
from base.logger import logger
from base.config import config
# 导入 OpenAI
from openai import OpenAI
# 导入时间库
import time

class IntegratedQASystem:
    def __init__(self):
        # 初始化 MySQL 客户端
        self.mysql_client = MySQLClient()
        # 初始化 Redis 客户端
        self.redis_client = RedisClient()
        # 初始化 BM25 搜索
        # 1.将原始列表存入到Redis。2.将原始问题进行Jieba分词后存入到Redis 3.将原始问题进行Jieba分词后初始化一个BM25
        self.bm25_search = BM25Search(self.redis_client, self.mysql_client)
        try:
            # 初始化 OpenAI 客户端
            self.client = OpenAI(api_key=config.DASHSCOPE_API_KEY, base_url=config.DASHSCOPE_BASE_URL)
        except Exception as e:
            # 记录 OpenAI 初始化失败
            logger.error(f"OpenAI 客户端初始化失败: {e}")
            raise
        # 初始化向量存储
        self.vector_store = VectorStore()
        # 初始化 RAG 系统
        # 传入一个函数对象 self.call_dashscope
        self.rag_system = RAGSystem(self.vector_store, self.call_dashscope)

    def call_dashscope(self, prompt):
        # 调用 DashScope API
        try:
            # 创建聊天完成请求
            completion = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt},
                ]
            )
            # 返回完成结果
            res = completion.choices[0].message.content if completion.choices else "错误：无效的 LLM 响应"
            # print(f'call_dashscope res-->{res}')
            return res
        except Exception as e:
            # 记录 LLM 调用失败
            logger.error(f"LLM 调用失败: {e}")
            # 返回错误信息
            return f"错误：LLM 调用失败 - {e}"

    def query(self, query, source_filter=None):
        # 查询集成系统
        start_time = time.time()
        # 记录查询信息
        logger.info(f"处理查询: '{query}', 过滤条件:'{source_filter}")
        # 首先尝试 MySQL 搜索
        answer, need_rag = self.bm25_search.search(query, threshold=0.85)
        if answer:
            # 记录 MySQL 答案
            logger.info(f"MySQL 答案: {answer}")
            # 计算处理时间
            processing_time = time.time() - start_time
            # 记录处理时间
            logger.info(f"查询处理耗时 {processing_time:.2f}秒")
            # 返回答案
            return answer
        elif need_rag:
            # 记录需要 RAG
            logger.info("无可靠 MySQL 答案，回退到 RAG")
            # 调用 RAG 系统
            answer = self.rag_system.generate_answer(query, source_filter)
            # 记录 RAG 答案
            logger.info(f"RAG 答案: {answer}")
            # 计算处理时间
            processing_time = time.time() - start_time
            # 记录处理时间
            logger.info(f"查询处理耗时 {processing_time:.2f}秒")
            # 返回答案
            return answer
        else:
            # 记录无答案
            logger.info("未找到答案")
            # 计算处理时间
            processing_time = time.time() - start_time
            # 记录处理时间
            logger.info(f"查询处理耗时 {processing_time:.2f}秒")
            # 返回默认答案
            return "未找到答案"

def main():
    # 初始化集成系统
    qa_system = IntegratedQASystem()
    try:
        # 打印欢迎信息
        print("\n欢迎使用集成问答系统！")
        print(f"支持的来源: {config.VALID_SOURCES}")
        print("输入查询进行问答，输入 'exit' 退出。")
        while True:
            # 获取用户输入
            query = input("\n输入查询: ").strip()
            if query.lower() == "exit":
                # 记录退出日志
                logger.info("退出系统")
                # 打印退出信息
                print("再见！")
                break
            # 获取来源过滤
            source_filter = input(f"输入来源过滤 ({'/'.join(config.VALID_SOURCES)}) (按 Enter 跳过): ").strip()
            if source_filter and source_filter not in config.VALID_SOURCES:
                # 记录无效来源
                logger.warning(f"无效来源 '{source_filter}'，忽略过滤")
                # 打印无效来源信息
                print(f"无效来源 '{source_filter}'，继续无过滤。")
                source_filter = None
            # 执行查询
            answer = qa_system.query(query, source_filter)
            # 打印答案
            answer = "".join(answer)
            print(f"\n答案: {answer}")

    except Exception as e:
        # 记录系统错误
        logger.error(f"系统错误: {e}")
        # 打印错误信息
        print(f"发生错误: {e}")
    finally:
        # 关闭 MySQL 连接
        qa_system.mysql_client.close()


if __name__ == "__main__":
    # 运行主程序
    main()