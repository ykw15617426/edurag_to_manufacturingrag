"""
    目的：创建collection和index
"""
from pymilvus import MilvusClient, DataType


def operate_collection():
    # 1. 建立连接，使用数据库
    client = MilvusClient(uri="http://localhost:19530")
    client.using_database(db_name="milvus_demo")
    # 2. 指定字段
    schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
    schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=10, description="向量字段")
    schema.add_field(field_name="scalar1", datatype=DataType.VARCHAR, max_length=100, description="标题字段")
    # 3. 创建集合
    client.create_collection(collection_name="demo_v1", schema=schema)
    # 4. 创建向量索引
    index_params = client.prepare_index_params()
    index_params.add_index(field_name="vector", index_type="IVF_FLAT", metric_type="COSINE", index_name="vector_index", params={ "nlist": 128 })
    client.create_index(collection_name="demo_v1", index_params=index_params)
    # 5. 查询标量索引
    lists = client.list_indexes(collection_name="demo_v1")
    print(f"索引列表：{lists}")
    res = client.describe_index(collection_name="demo_v1", index_name="vector_index")
    print(f'vector_index:{res}')
    # 6. 创建标量索引
    index_params1 = client.prepare_index_params()
    index_params1.add_index(field_name="scalar1", index_type="", index_name="scalar1_index")
    client.create_index(collection_name="demo_v1", index_params=index_params1)
    # 5. 查询标量索引
    lists = client.list_indexes(collection_name="demo_v1")
    print(f"索引列表：{lists}")
    res = client.describe_index(collection_name="demo_v1", index_name="scalar1_index")
    print(f'scalar1_index:{res}')


# 测试
if __name__ == '__main__':
    operate_collection()