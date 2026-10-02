"""
    文档向量化与存储：core/vector_store.py
"""
from base.config import config
from base.logger import logger
import os
# 导入 BGE-M3 嵌入函数，用于生成文档和查询的向量表示
from milvus_model.hybrid import BGEM3EmbeddingFunction
# 导入 Milvus 相关类，用于操作向量数据库
from pymilvus import MilvusClient, DataType, AnnSearchRequest, WeightedRanker
# 导入 Document 类，用于创建文档对象
from langchain_core.documents import Document
# 导入 CrossEncoder，用于重排序和 NLI 判断
from sentence_transformers import CrossEncoder
# 导入 hashlib 模块，用于生成唯一ID 的哈希值
import hashlib
import json
from rag_qa.core.milvus_schema import HASH_PATTERN
from rag_qa.core.milvus_schema import (
    select_collection, ensure_manufacturing_collection,
    validate_manufacturing_document, build_manufacturing_row,
)


# # 定义 VectorStore 类，封装向量存储和检索功能
class VectorStore:
    # 初始化方法，设置向量存储的基本参数
    def __init__(self,
                 collection_name=None,
                 host=config.MILVUS_HOST,
                 port=config.MILVUS_PORT,
                 database=config.MILVUS_DATABASE_NAME,
                 *, schema_mode="legacy"):
        # 设置 Milvus 集合名称
        self.schema_mode = schema_mode
        self.collection_name = select_collection(
            schema_mode, collection_name, config.MILVUS_COLLECTION_NAME,
            config.MILVUS_MANUFACTURING_COLLECTION_NAME)
        # 设置 Milvus 主机地址
        self.host = host
        # 设置 Milvus 端口号
        self.port = port
        # 设置 Milvus 数据库名称
        self.database = database
        # 重排序 模型路径
        rerank_model_path = os.path.join(config.MODELS_DIR, 'bge-reranker-large')
        # TODO device代表设备： mps:m1系列的mac/ cpu: cpu / cuda: nvidia的gpu。和操作系统无关
        # 初始化 BGE-Reranker 模型，用于重排序检索结果
        self.reranker = CrossEncoder(rerank_model_path, device='cpu')
        # bge-m3 模型路径
        bge_m3_model_path = os.path.join(config.MODELS_DIR, 'bge-m3')
        # 初始化 BGE-M3 嵌入函数，使用 CPU 设备，不启用 FP16
        self.embedding_function = BGEM3EmbeddingFunction(
            model_name_or_path=bge_m3_model_path,
            # 在CPU上，FP32往往更稳定、兼容性更好。关闭FP16以保证检索和排序的准确性。
            use_f16=False,
            device='cpu'
        )
        # 获取稠密向量的维度 1024
        self.dense_dim = self.embedding_function.dim["dense"]
        # 初始化 Milvus 客户端，连接到指定主机和数据库
        self.client = MilvusClient(uri=f'http://{self.host}:{self.port}', db_name=self.database)
        # 调用方法创建或加载 Milvus 集合
        self._create_or_load_collection()

    # 定义私有方法，创建或加载 Milvus 集合
    def _create_or_load_collection(self):
        if self.schema_mode == "manufacturing":
            ensure_manufacturing_collection(self.client, self.collection_name, self.dense_dim)
            return
        # 检查指定集合是否已存在
        if not self.client.has_collection(self.collection_name):
            # 创建集合 Schema，禁用自动 ID，启用动态字段
            schema = self.client.create_schema(auto_id=False, enable_dynamic_field=True)
            # 添加 ID 字段，作为主键，VARCHAR 类型，最大长度 100
            schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=100)
            # 添加文本字段，VARCHAR 类型，最大长度 65535
            schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
            # 添加稠密向量字段，FLOAT_VECTOR 类型，维度由嵌入函数指定
            schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=self.dense_dim)
            # 添加稀疏向量字段，SPARSE_FLOAT_VECTOR 类型
            schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
            # 添加子块 ID 字段，VARCHAR 类型，最大长度 100
            schema.add_field(field_name="child_id", datatype=DataType.VARCHAR, max_length=100)
            # 添加父块 ID 字段，VARCHAR 类型，最大长度 100
            schema.add_field(field_name="parent_id", datatype=DataType.VARCHAR, max_length=100)
            # 添加父块内容字段，VARCHAR 类型，最大长度 65535
            schema.add_field(field_name="parent_content", datatype=DataType.VARCHAR, max_length=65535)
            # 添加学科类别字段，VARCHAR 类型，最大长度 50
            schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=50)
            # 添加时间戳字段，VARCHAR 类型，最大长度 50
            schema.add_field(field_name="timestamp", datatype=DataType.VARCHAR, max_length=50)

            # 创建索引参数对象
            index_params = self.client.prepare_index_params()
            # 为稠密向量字段添加 IVF_FLAT 索引，度量类型为内积 (IP)
            index_params.add_index(
                field_name="dense_vector",
                index_name="dense_index",
                index_type="IVF_FLAT",
                metric_type="IP",
                params={"nlist": 128}
            )
            # 为稀疏向量字段添加 SPARSE_INVERTED_INDEX 索引，度量类型为内积 (IP)
            index_params.add_index(
                field_name="sparse_vector",
                index_name="sparse_index",
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="IP",
                # 丢弃权值最小的 20% 的维度（只保留权值较大的 80%）
                params={"drop_ratio_build": 0.2}
            )
            # 创建 Milvus 集合，应用定义的 Schema 和索引参数
            self.client.create_collection(collection_name=self.collection_name, schema=schema,
                                          index_params=index_params)
            # 记录创建集合的日志
            logger.info(f"已创建集合 {self.collection_name}")
        # 如果集合已存在
        else:
            # 记录加载集合的日志
            logger.info(f"已加载集合 {self.collection_name}")
        # 将集合加载到内存，确保可立即查询
        self.client.load_collection(self.collection_name)

    # 定义方法，存储文档到向量数据库
    def add_documents(self, documents):
        if self.schema_mode == "manufacturing":
            # Validate the entire batch before embedding/upsert; no partial invalid writes.
            for doc in documents:
                validate_manufacturing_document(doc)
            if not documents:
                logger.error("没有数据存储到向量数据库")
                return
            embeddings = self.embedding_function([doc.page_content for doc in documents])
            rows = [build_manufacturing_row(
                doc, embeddings["dense"][i], self.get_sparse_dict(embeddings, i), self.dense_dim)
                for i, doc in enumerate(documents)]
            self.client.upsert(collection_name=self.collection_name, data=rows)
            logger.info(f"已存储 {len(rows)} 个制造业文档到向量数据库")
            return
        data = []
        # 向量化
        texts = [doc.page_content for doc in documents]
        embeddings = self.embedding_function(texts)
        for i, doc in enumerate(documents):
            print(f'11--->doc:{doc}')
            # 处理稀疏向量
            sparse_vector = self.get_sparse_dict(embeddings, i)
            # id md5
            id_md5 = hashlib.md5(doc.metadata['id'].encode("utf-8")).hexdigest()
            # 封装数据
            data.append({
                "id": id_md5,
                "text": doc.page_content,
                "dense_vector": embeddings["dense"][i],
                "sparse_vector": sparse_vector,
                "child_id": doc.metadata["id"],
                "parent_id": doc.metadata["parent_id"],
                "parent_content": doc.metadata["parent_content"],
                "source": doc.metadata.get("source", ""),
                "timestamp": doc.metadata.get("timestamp", "")
            })
        if data:
            self.client.upsert(collection_name=self.collection_name, data=data)
            logger.info(f"已存储 {len(data)} 个文档到向量数据库")
        else:
            logger.error("没有数据存储到向量数据库")

    def _require_manufacturing_admin(self):
        if self.schema_mode != "manufacturing":
            raise ValueError("ingestion administration is forbidden for Legacy collections")

    def list_document_child_ids(self, document_id):
        """Full document snapshot; this is ingestion administration, not online filtering."""
        self._require_manufacturing_admin()
        if (not isinstance(document_id, str) or not document_id.strip()
                or len(document_id.encode("utf-8")) > 256):
            raise ValueError("document_id: nonempty VARCHAR(256) required")
        iterator = self.client.query_iterator(
            collection_name=self.collection_name, batch_size=1000, limit=-1,
            filter="document_id == " + json.dumps(document_id, ensure_ascii=False),
            output_fields=["id", "child_id", "document_id"], consistency_level="Strong")
        ids = []
        try:
            while True:
                rows = iterator.next()
                if not rows:
                    break
                for row in rows:
                    identifier = row.get("id")
                    if (row.get("document_id") != document_id or row.get("child_id") != identifier
                            or not isinstance(identifier, str) or not HASH_PATTERN.fullmatch(identifier)):
                        raise ValueError("invalid manufacturing document snapshot; deletion forbidden")
                    ids.append(identifier)
        finally:
            iterator.close()
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate PK in document snapshot")
        return sorted(ids)

    def delete_child_ids(self, ids):
        self._require_manufacturing_admin()
        ids = list(ids)
        if any(not isinstance(i, str) or not HASH_PATTERN.fullmatch(i) for i in ids):
            raise ValueError("delete requires stable lowercase SHA256 PKs")
        ids = sorted(set(ids))
        for start in range(0, len(ids), 1000):
            self.client.delete(collection_name=self.collection_name, ids=ids[start:start + 1000])

    def verify_document_snapshot(self, document_id, desired_ids):
        self._require_manufacturing_admin()
        return set(self.list_document_child_ids(document_id)) == set(desired_ids)

    # 定义方法，处理稀疏向量 选中代码，ctrl+alt+M --> 提取函数
    def get_sparse_dict(self, embeddings, i):
        if self.schema_mode == "manufacturing":
            # Select a 2-D CSR row for both scipy sparse matrices and sparse arrays.
            row = embeddings["sparse"].tocsr()[[i], :]
            return dict(zip(row.indices, row.data))
        # 初始化稀疏向量字典
        sparse_vector = {}
        try:
            # 新版本 milvus-model 使用 coo_array 格式
            row = embeddings["sparse"][i]
            print('i-->', i, "row-->", row)
            # 获取非零元素的列索引数组
            if hasattr(row, 'col'):  # coo_array 格式，新版Milvus
                indices = row.col
            else:  # csr_matrix 格式
                indices = row.indices
        except Exception as e:
            # 兼容旧版本 milvus-model
            row = embeddings["sparse"].getrow(0)
            indices = row.indices
        # 获取稀疏向量的非零值
        values = row.data
        # logger.info(f"稀疏向量的非零索引：{indices}:{values}")
        # logger.info("=" * 100)
        for idx, value in zip(indices, values):
            sparse_vector[idx] = value  # 稀疏向量的非零元素
        return sparse_vector

    # 定义方法，执行混合检索并重排序
    def hybrid_search_with_rerank(self, query, k=config.RETRIEVAL_K, source_filter=None):
        logger.info(f"hybrid_search_with_rerank 执行混合检索并重排序...query:{query}, k:{k}, source_filter:{source_filter}")
        embeddings = self.embedding_function([query])
        # 稠密向量
        dense_query_vector = embeddings["dense"][0]
        # 稀疏向量
        sparse_query_vector = self.get_sparse_dict(embeddings, 0)
        # 条件 source == 'ai'
        expr_filter = f"source == '{source_filter}'" if source_filter else ""
        # 稠密向量搜索构建
        dense_request = AnnSearchRequest(
            data=[dense_query_vector],
            anns_field="dense_vector",
            param={"metric_type": "IP", "nprobe": 10},
            limit=k,
            expr=expr_filter
        )
        # 稠疏向量搜索构建
        sparse_request = AnnSearchRequest(
            data=[sparse_query_vector],
            anns_field="sparse_vector",
            param={"metric_type": "IP"},
            limit=k,
            expr=expr_filter
        )
        results = self.client.hybrid_search(
            collection_name=self.collection_name,
            reqs=[dense_request, sparse_request],
            ranker=WeightedRanker(0.8, 0.3),
            limit=k,
            output_fields=["id", "text", "child_id", "parent_id", "parent_content", "source", "timestamp"],
        )[0]
        logger.info(f"混合检索并重排序结果：{results}")
        # 判断如果搜索的结果为空
        if not results or len(results) == 0:
            logger.info("没有找到相关文档")
            return []
        # 将查询结果转换成 Document 对象
        child_docs = [self._doc_from_hit(hit['entity']) for hit in results]
        logger.info(f"11-->去重前的父文档数量：{len(child_docs)}")
        # 获取得去重后的父文档，父块内容在 doc.page_content 中
        parent_docs = self._get_unique_parent_docs(child_docs)
        logger.info(f"22-->去重前的父文档数量：{len(parent_docs)}")
        # 只有一个文档，直接返回
        if len(parent_docs) < 2:
            return parent_docs[:config.CANDIDATE_M]

        # 获取得分
        pairs = [[query, doc.page_content] for doc in parent_docs]
        scores = self.reranker.predict(pairs)  # [0.00365302    0.33621186    0.999556  ]
        ranker_parent_docs = [doc for _, doc in sorted(zip(scores, parent_docs), reverse=True)]
        logger.info(f"33-->重排序结果：{ranker_parent_docs}")
        return ranker_parent_docs[:config.CANDIDATE_M]

    # 定义私有方法，从 Milvus 查询结果转换成创建 Document 对象
    def _doc_from_hit(self, hit):
        return Document(
            page_content=hit["text"],   # 子块内容
            metadata={
                "id": hit["id"],
                "parent_id": hit["parent_id"],
                "parent_content": hit["parent_content"],   # 父块内容必需有，将来用于拼接提示词
                "source": hit["source"],
                "timestamp": hit["timestamp"]
            }
        )

    # 定义私有方法，从子块中提取去重的父文档，里面只有内容
    def _get_unique_parent_docs(self, child_docs):
        parent_contents = set()
        for doc in child_docs:
            # 对父块内容去重
            parent_contents.add(doc.metadata.get('parent_content', doc.page_content))
        return [Document(page_content=content) for content in parent_contents]


# 测试
if __name__ == '__main__':
    vector_store = VectorStore()
    # from document_processor import process_documents
    # docs = process_documents(config.DATA_DIR + "/ai_data")
    # vector_store.add_documents(docs)

    docs = vector_store.hybrid_search_with_rerank(query="语⾔模型发展⾛过了哪三个阶段?", k=10, source_filter='ai')
    # vector_store.hybrid_search_with_rerank(query="语⾔模型发展⾛过了哪三个阶段?", k=3, source_filter='java')
    # 遍历元组
    for doc in docs:
        print(doc.page_content)
        print("*" * 80)
