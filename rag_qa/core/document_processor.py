"""
    文档处理器：rag_qa/core/document_processor.py
"""
import os
from collections import Counter, defaultdict
from base.config import config
from base.logger import logger
from datetime import datetime
from rag_qa.edu_document_loaders.edu_docloader import OCRDOCLoader
from rag_qa.edu_document_loaders.edu_imgloader import OCRIMGLoader
from rag_qa.edu_document_loaders.edu_pdfloader import OCRPDFLoader
from rag_qa.edu_document_loaders.edu_pptloader import OCRPPTLoader

from rag_qa.edu_text_spliter.edu_chinese_recursive_text_splitter import ChineseRecursiveTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain_text_splitters import MarkdownTextSplitter
from rag_qa.ingestion.metadata_loader import load_with_metadata
from rag_qa.ingestion.fingerprints import sha256_content, build_parent_id, build_child_id

# 定义支持的文件类型及其对应的加载器字典
document_loaders = {
    # 文本文件使用 TextLoader
    ".txt": TextLoader,
    # PDF 文件使用 OCRPDFLoader
    ".pdf": OCRPDFLoader,
    # Word 文件使用 OCRDOCLoader
    ".docx": OCRDOCLoader,
    # PPT 文件使用 OCRPPTLoader
    ".ppt": OCRPPTLoader,
    # PPTX 文件使用 OCRPPTLoader
    ".pptx": OCRPPTLoader,
    # JPG 文件使用 OCRIMGLoader
    ".jpg": OCRIMGLoader,
    # PNG 文件使用 OCRIMGLoader
    ".png": OCRIMGLoader,
    # Markdown 文件使用 UnstructuredMarkdownLoader
    ".md": UnstructuredMarkdownLoader
}



# 加载文档，参数是一个目录
def load_documents_from_directory(directory_path, *, metadata_mode="legacy"):
    if metadata_mode not in {"legacy", "manufacturing"}:
        raise ValueError("metadata_mode must be legacy or manufacturing")
    # 初始化空列表，用于存储加载后的文档
    documents = []
    supported_extensions = document_loaders.keys()
    source = os.path.basename(directory_path).replace("_data", "")
    logger.info(f"source:{source}")
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            # 获取文件扩展名
            file_extension = os.path.splitext(file)[1].lower()
            if file_extension not in supported_extensions:
                logger.warning(f"不支持该格式{file_extension}的文件")
                continue
            else:
                logger.info(f"支持该格式{file_extension}的文件正在加载....")
                load_class = document_loaders[file_extension]
                def load_file(loader_path):
                    if ".txt" == file_extension:
                        loader = load_class(loader_path, encoding='utf-8')
                    else:
                        loader = load_class(loader_path)
                    return loader.load()

                load_docs = (load_with_metadata(file_path, load_file)
                             if metadata_mode == "manufacturing" else load_file(file_path))
                # 遍历加载到的文档列表
                for doc in load_docs:
                    doc.metadata['source'] = source
                    doc.metadata['file_path'] = file_path
                    doc.metadata['timestamp'] = datetime.now().isoformat()
                    # documents.append(doc)
                documents.extend(load_docs)
                logger.info(f'文件{file_path}加载成功....')
    return documents


# 处理文档并进行分层分割，返回子块结果
def process_documents(directory_path,
                      parent_chunk_size=config.PARENT_CHUNK_SIZE,
                      child_chunk_size=config.CHILD_CHUNK_SIZE,
                      parent_chunk_overlap=config.PARENT_CHUNK_OVERLAP,
                      child_chunk_overlap=config.CHILD_CHUNK_OVERLAP,
                      *, metadata_mode="legacy"):
    # 子块文档列表
    child_chunks = []
    # 加载指定目录下所有的文档
    documents = load_documents_from_directory(directory_path, metadata_mode=metadata_mode)
    parent_splitter = ChineseRecursiveTextSplitter(chunk_size=parent_chunk_size, chunk_overlap=parent_chunk_overlap)
    child_splitter = ChineseRecursiveTextSplitter(chunk_size=child_chunk_size, chunk_overlap=child_chunk_overlap)
    markdown_parent_splitter = MarkdownTextSplitter(chunk_size=parent_chunk_size, chunk_overlap=parent_chunk_overlap)
    markdown_child_splitter = MarkdownTextSplitter(chunk_size=child_chunk_size, chunk_overlap=child_chunk_overlap)
    # Span all Loader outputs for the same business document (e.g. multiple pages).
    parent_occurrences = defaultdict(Counter)

    for i, doc in enumerate(documents):
        # 获取文档的扩展名
        file_extension = os.path.splitext(doc.metadata["file_path"])[1].lower()
        # 选择分割器
        is_markdown = file_extension == ".md"
        parent_splitter_to_use = markdown_parent_splitter if is_markdown else parent_splitter
        child_splitter_to_use = markdown_child_splitter if is_markdown else child_splitter
        # 获取所有的父块文档
        parent_docs = parent_splitter_to_use.split_documents([doc])
        for j, parent_doc in enumerate(parent_docs):
            # 为父块文档添加元数据
            # Legacy 保留位置 ID；Manufacturing 使用业务 namespace + 内容指纹。
            if metadata_mode == "manufacturing":
                document_id = parent_doc.metadata["document_id"]
                parent_hash = sha256_content(parent_doc.page_content)
                occurrence = parent_occurrences[document_id][parent_hash]
                parent_occurrences[document_id][parent_hash] += 1
                parent_doc.metadata["parent_content_sha256"] = parent_hash
                parent_doc.metadata["id"] = build_parent_id(document_id, parent_hash, occurrence)
            else:
                parent_doc.metadata["id"] = f'doc_{i}_parent_{j}'
            parent_doc.metadata["parent_content"] = parent_doc.page_content
            # 获取所有的子块文档
            child_docs = child_splitter_to_use.split_documents([parent_doc])
            child_occurrences = Counter()
            # 遍历子块文档
            for k, child_doc in enumerate(child_docs):
                # 为子块文档添加元数据
                child_doc.metadata["parent_id"] = parent_doc.metadata["id"]
                child_doc.metadata["parent_content"] = parent_doc.page_content
                # Child occurrence 只在当前 Parent 的相同内容中计数。
                if metadata_mode == "manufacturing":
                    child_hash = sha256_content(child_doc.page_content)
                    occurrence = child_occurrences[child_hash]
                    child_occurrences[child_hash] += 1
                    child_doc.metadata["child_content_sha256"] = child_hash
                    child_doc.metadata["id"] = build_child_id(
                        document_id, parent_doc.metadata["id"], child_hash, occurrence)
                    child_doc.metadata["child_id"] = child_doc.metadata["id"]
                else:
                    child_doc.metadata["id"] = parent_doc.metadata["id"] + f'_child_{k}'
                child_chunks.append(child_doc)
                logger.info(f"处理文档成功:父块{parent_doc.metadata['id']}:子块:{child_doc.metadata['id']}")
                logger.warning('=' * 100)
        print("\n\n")
    # 返回所有子块列表
    return child_chunks


if __name__ == "__main__":
    chunks = load_documents_from_directory(f"{config.DATA_DIR}/ai_data")
    print(f"--->{len(chunks)}")
    # chunks = process_documents(f"{config.DATA_DIR}/ai_data")
    print(chunks)
