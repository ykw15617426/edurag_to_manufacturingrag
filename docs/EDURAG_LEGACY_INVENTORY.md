# EduRAG 教育遗留完整文本命中清单

审计日期：2026-10-01；main 基线 ff95920。范围：全部 99 个基线 tracked 文件，以及被忽略的 demo/langchain/models/*.py 本地源码。模型权重、.git、缓存、日志、.env、config.ini 不输出内容；本地配置只在报告中标记风险。新增 docs/tests 不作为教育业务遗留，以免递归扫描审计文本。

匹配词：教育、课程、学生、老师、AI课程、Java课程、ai_data、java_data、ops_data、bigdata、通用知识、专业咨询、customer_service_phone、edurag、subjects_kg、学科、培训、师资、jpkb、itcast、edu_document_loaders、edu_text_spliter、bert_query_classifier。每个文本命中行均列出；片段仅用于定位，长行不全文复制。二进制 PDF/Office/图像按原路径标记，未对其中图像执行 OCR，也不声称已完成全部二进制正文关键词检索。

## 分类与处理

- A 必须删除：后续部署前移除 app.py:121-138 旧软件激活/过期 API 示例；未接入且协议错误的 React 草稿应从最终发布物排除。当前未删除历史资产。
- B 后续制造业替换：教育 source/类别、Prompt 业务语义、问候客服/电话、UI 品牌、jpkb/subjects_kg 与 collection 配置。
- C 可以保留但重命名：edu_* 通用 Loader/Splitter 名称、EduRAG logger，迁移时修全引用并验证。
- D 暂时不动：数据、教学 demo、训练集、旧入口、RAGAS 结果和旧页面，原位标记归档候选。

## 历史资产全路径（69 个文件）

| File | Category | Action |
| --- | --- | --- |
| `demo/argparse/demo01_argparse.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/bm25/demo01_bm25_search.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/bm25/main.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/agents/demo01_agents_get_all_tool_names.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/agents/demo02_agents.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/chains/demo01_单链.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/chains/demo02_多链.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/data/pku.txt` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/data/衣服属性.txt` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/demo01_UnstructuredLoader.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/demo02_CharacterTextSplitter.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/demo03_RecursiveCharacterTextSplitter.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/demo04_SemanticChunker.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/demo05_markdown.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/demo06_Chroma.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/indexes/demo07_retriever.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/memory/demo01_ChatMessageHistory.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/memory/history.json` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/models/demo01_百炼.py` | D | 本地忽略的教学源码；不随 Git 发布 |
| `demo/langchain/models/demo02_ollama.py` | D | 本地忽略的教学源码；不随 Git 发布 |
| `demo/langchain/models/demo03_ChatModels.py` | D | 本地忽略的教学源码；不随 Git 发布 |
| `demo/langchain/models/demo04_OllamaEmbeddings.py` | D | 本地忽略的教学源码；不随 Git 发布 |
| `demo/langchain/output_parser/demo01_StrOutputParser.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/output_parser/demo02_CommaSeparatedListOutputParser.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/output_parser/demo03_JsonOutputParser.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/output_parser/demo04_PydanticOutputParser.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/output_parser/demo05_自定义解析器.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/prompts/demo01_zero-shot.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/prompts/demo02_few-shot.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/prompts/demo03_ChatPrompts.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/prompts/demo04_ChatPrompts-zero-shot.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/langchain/prompts/demo05_ChatPrompts-few-shot.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/logging/demo01_logging_base.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/logging/demo02_logging_custom_format.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/logging/demo03_logging_filesave.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/logging/demo04_file_console.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/logging/logging_lesson/logger_base/logger.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/logging/logging_lesson/main.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/milvus/demo01_database.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/milvus/demo02_collection_field_index.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/milvus/demo03_entity.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/milvus/demo04_entity_query.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/milvus/demo05_collection_other.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/ollama/demo01.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/redis/redis_lesson/redis_base/logger.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/redis/redis_lesson/redis_client.py` | D | 教育数据/评估/教学参考，原位保留 |
| `demo/test/demo01_zip.py` | D | 教育数据/评估/教学参考，原位保留 |
| `mysql_qa/data/JP学科知识问答.csv` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/classify_data/model_generic_5000.json` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/classify_data/提示词模块.txt` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/ai_data/LLM基础知识.pdf` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/ai_data/人工智能就业课课程大纲.docx` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/ai_data/就业指导课.pptx` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/ai_data/语言模型.png` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/java_data/java从入门到精通.txt` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/ops_data/运维也能高薪.txt` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/samples/ocr_01.pptx` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/samples/ocr_02.docx` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/samples/ocr_03.pdf` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/data/samples/ocr_04.png` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/demo/demo01_embeddings.py` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/demo/demo02_ranker.py` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/rag_assessment/img.png` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/rag_assessment/ollama_ragas.py` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/rag_assessment/rag_evaluate_data.json` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/rag_assessment/ragas_evaluate.py` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/rag_assessment/ragas_evaluation_results.csv` | D | 教育数据/评估/教学参考，原位保留 |
| `rag_qa/rag_assessment/ragas_evaluation_results.csv1` | D | 教育数据/评估/教学参考，原位保留 |

## 全部文本命中（1152 行，31 个文件）

| File:line | Category | Matched terms | Evidence excerpt |
| --- | --- | --- | --- |
| `app.py:44` | B | 学生 | "response": "你好！我是黑马程序员，专注于为学生答疑解惑，很高兴为你服务！" |
| `app.py:48` | B | 教育 | "response": "我是黑马程序员，你的智能学习助手，致力于提供 IT 教育相关的解答！" |
| `app.py:287` | B | 学科 | # 获取有效的学科类别 |
| `base/config.py:24` | C | edu_document_loaders,EDU_DOCUMENT_LOADERS | self.EDU_DOCUMENT_LOADERS_DIR = os.path.join(self.PROJECT_ROOT, 'rag_qa/edu_document_loaders') |
| `base/config.py:42` | B | subjects_kg | self.MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', self.config.get('mysql', 'database', fallback='subjects_kg')) |
| `base/config.py:61` | B | itcast | self.config.get('milvus', 'database_name', fallback='itcast')) |
| `base/config.py:64` | B | edurag | self.config.get('milvus', 'collection_name', fallback='edurag')) |
| `base/config.py:103` | B | bigdata | self.config.get('app', 'valid_sources', fallback='["ai", "java", "test", "ops", "bigdata"]'))) |
| `base/config.py:105` | B | CUSTOMER_SERVICE_PHONE | self.CUSTOMER_SERVICE_PHONE = os.getenv('CUSTOMER_SERVICE_PHONE', |
| `base/config.py:106` | B | customer_service_phone | self.config.get('app', 'customer_service_phone', |
| `base/logger.py:10` | C | EduRAG | def setup_logger(logger_name='EduRAG', logger_file=config.LOG_FILE): |
| `base/logger.py:47` | C | EduRAG | logger = setup_logger('EduRAG') |
| `config.example.ini:7` | B | subjects_kg | database = subjects_kg |
| `config.example.ini:21` | B | itcast | database_name = itcast07 |
| `config.example.ini:22` | B | edurag | collection_name = edurag |
| `config.example.ini:45` | B | bigdata | valid_sources = ["ai", "java", "test", "ops", "bigdata"] |
| `config.example.ini:46` | B | customer_service_phone | customer_service_phone = 13000000000 |
| `demo/langchain/indexes/data/pku.txt:3` | D | 教育 | 在悠久的文明历程中，古代中国曾创立太学、国子学、国子监等国家最高学府，在中国和世界教育史上具有重要影响。北京大学“上承太学正统，下立大学祖庭”，既是中华文脉和教育传统的传承者，也标志着中国现代高等教育的开端。其创办之初也是国家最高教育行政机关，对建立中国现代学制作出重要历史贡献。 |
| `demo/langchain/indexes/data/pku.txt:7` | D | 教育 | 1917年，著名教育家蔡元培就任北京大学校长，他“循思想自由原则，取兼容并包主义”，对北京大学进行了卓有成效的改革，促进了思想解放和学术繁荣。陈独秀、李大钊、毛泽东以及鲁迅、胡适、李四光等一批杰出人士都曾在北京大学任教或任职。 |
| `demo/langchain/prompts/demo05_ChatPrompts-few-shot.py:13` | D | 老师 | ("system", "你是一个语文老师，给出每个单词的反义词"), |
| `docker-compose.yml:2` | B | edurag | edurag-app: |
| `docker-compose.yml:4` | B | edurag | image: edurag:7.0 |
| `docker-compose.yml:5` | B | edurag | container_name: edurag7 |
| `docker-compose.yml:20` | B | subjects_kg | - MYSQL_DATABASE=${MYSQL_DATABASE:-subjects_kg} |
| `docker-compose.yml:31` | B | itcast | - MILVUS_DATABASE_NAME=${MILVUS_DATABASE_NAME:-itcast} |
| `docker-compose.yml:32` | B | edurag | - MILVUS_COLLECTION_NAME=${MILVUS_COLLECTION_NAME:-edurag} |
| `docker-compose.yml:48` | B | bigdata | - VALID_SOURCES=${VALID_SOURCES:-["ai", "java", "test", "ops", "bigdata"]} |
| `docker-compose.yml:49` | B | CUSTOMER_SERVICE_PHONE | - CUSTOMER_SERVICE_PHONE=${CUSTOMER_SERVICE_PHONE:-12345678} |
| `mysql_qa/data/JP学科知识问答.csv:1` | D | 学科 | 学科名称,问题,答案 |
| `mysql_qa/data/JP学科知识问答.csv:2` | D | 学科 | Python学科,用上下文管理器实现函数运行时间的计算?,"import time |
| `mysql_qa/data/JP学科知识问答.csv:25` | D | 学科 | Python学科,"有字典{'a':1,'b':2,'c':3},现在有一个需求 |
| `mysql_qa/data/JP学科知识问答.csv:54` | D | 学科 | Python学科,"两个人开发项目,我push到github上后 |
| `mysql_qa/data/JP学科知识问答.csv:67` | D | 学科 | Python学科,关联子查询的执行顺序是什么,"sql的编写顺序 |
| `mysql_qa/data/JP学科知识问答.csv:89` | D | 学科 | Python学科,定义类字典对象(继承于dict类)，如何修改读写字典元素方法,"class test(dict): |
| `mysql_qa/data/JP学科知识问答.csv:112` | D | 学科 | Python学科,Ubuntu上Navicat for MySQL 显示乱码,"找到 navicat 安装路径，用文本编辑器打开 start_navicat 文件，会看到 export LANG=""en_US.UTF-8"" 将这句话改为 export LANG=""zh_CN.UTF-8""，就可以了。" |
| `mysql_qa/data/JP学科知识问答.csv:113` | D | 学科 | Python学科,为什么isalnum函数会通过中文,"需要在字符串的后面进行编码 |
| `mysql_qa/data/JP学科知识问答.csv:122` | D | 学科 | Python学科,pycharm资源管理区域文件的显示更新,"{""answerText"":""{\""mid\"":\""f3c85641-9c54-4a12-a78d-b1cfe3d879a9\"",\""type\"":\""image/png\"",\""name\"":\""pycharm资源管理区域文件的显示更新.png\"",\""objectMeta\"":{\""width\" …（长行省略；原文件保留全文） |
| `mysql_qa/data/JP学科知识问答.csv:123` | D | 学科 | Python学科,如何在 Ubuntu 中快速创建Pycharm桌面快捷方式？,"官方也有关于pycharm在linux的桌面快捷设置，一条命令就可以搞定： |
| `mysql_qa/data/JP学科知识问答.csv:131` | D | 学科 | Python学科,VMware安装VMware Tools时显示灰色如何解决,"1.关闭虚拟机； |
| `mysql_qa/data/JP学科知识问答.csv:136` | D | 学科 | Python学科,"faild to load module canberra |
| `mysql_qa/data/JP学科知识问答.csv:138` | D | 学科 | Python学科,PyCharm使用中文版本还是英文版本,强烈推荐使用英文版本，中文版本虽然一时半会儿可以让你更快熟悉PyCharm这个软件的部分功能的使用，但是英文IT界内大部分人都是使用的英文版本，所以使用中文版本就会有沟通问题，当你碰到什么问题，或者想要学习更多新功能的时候，此时看到的资料大部分都是英文的。所以推荐刚刚开始学习的时候就使用英文版本，这时候如果有碰到英文单词不知道什么意思，建议 …（长行省略；原文件保留全文） |
| `mysql_qa/data/JP学科知识问答.csv:139` | D | 学科 | Python学科,python3.7 64位版本pygame安装报错,"3.6可以正常通过pip install pygame  进行安装 |
| `mysql_qa/data/JP学科知识问答.csv:148` | D | 学科 | Python学科,"找不到可以连接的有效对等进程 |
| `mysql_qa/data/JP学科知识问答.csv:157` | D | 学科 | Python学科,lxml的tree报错,原因是etree最低支持版本是3.4版本，用户的版本是3.3版本，解决办法是升级python环境 |
| `mysql_qa/data/JP学科知识问答.csv:158` | D | 学科 | Python学科,redis存储类型里面提到的“string类型是二进制安全的,"这个主要是和C语言里面的某些字符串处理函数比较，得到的概念，redis里面的字符串处理函数并不像C语言那样,使用'\0'作为判定一个字符串的结尾，而是使用了独立的 len，这样可以保证即使存储的数据中有'\0'这样的字符,它也是可以支持读取的" |
| `mysql_qa/data/JP学科知识问答.csv:159` | D | 学科,课程 | Python学科,如何创建线程安全的单例对象,"一、首先，复习下课程中的讲解的单例对象的代码。 |
| `mysql_qa/data/JP学科知识问答.csv:178` | D | 学科 | Python学科,selenium使用chrome无头浏览器执行js代码,"准备工作： |
| `mysql_qa/data/JP学科知识问答.csv:188` | D | 学科 | Python学科,怎么获取MongoDB中某个集合中所有文档的键的名字,"db.things.insert( { type : ['dog', 'cat'] } ); |
| `mysql_qa/data/JP学科知识问答.csv:209` | D | 学科 | Python学科,PyCharm只能以单元测试方式运行python代码怎么解决,方法或者类中包含 test |
| `mysql_qa/data/JP学科知识问答.csv:210` | D | 学科 | Python学科,如何给某个特定的Python版本安装pip,"在 pip 的官网有介绍如何给 python 安装 pip |
| `mysql_qa/data/JP学科知识问答.csv:213` | D | 学科 | Python学科,crawler spider中如何处理url返回respon,crawlspider 为我提供了一个方法，所以我们重写parse_start_url(response)方法即可，但是需要注意处理完成后的返回值 |
| `mysql_qa/data/JP学科知识问答.csv:214` | D | 学科 | Python学科,Screenshot: available via scre,"原因： |
| `mysql_qa/data/JP学科知识问答.csv:226` | D | 学科 | Python学科,使用crawlspider爬取aqi历史数据请求多,"原因： |
| `mysql_qa/data/JP学科知识问答.csv:243` | D | 学科 | Python学科,爬虫处理返回的是gzip格式数据,"请求头中需要添加user-agent以外的其他信息例如cookie等 |
| `mysql_qa/data/JP学科知识问答.csv:262` | D | 学科 | Python学科,windows如何安装redis,"    安装3.0.504版本 下载链接，https://github.com/MicrosoftArchive/redis/releases 如果安装其他一些版本建议卸载重现安装此版本，当前gitbub只维护64位版本，如果想使用32位版本请另行查找连接 |
| `mysql_qa/data/JP学科知识问答.csv:265` | D | 学科 | Python学科,Pycharm不能动态获取用户设置的环境变量，需要设置,进行操作添加临时变量后再次使用代码就可以获取到新添加的环境变量 |
| `mysql_qa/data/JP学科知识问答.csv:266` | D | 学科 | Python学科,win10如何安装python虚拟环境以及爬虫环境,"以win10环境为例 |
| `mysql_qa/data/JP学科知识问答.csv:279` | D | 学科 | Python学科,pycharm专业版如何激活,"第一种方式： |
| `mysql_qa/data/JP学科知识问答.csv:300` | D | 学科 | Python学科,os.path.dirname() 方法有什么作用？,"1.os.path.dirname(file) 方法返回 file 文件所在的文件夹的路径 |
| `mysql_qa/data/JP学科知识问答.csv:311` | D | 学科 | Python学科,cssrem设置的时候提示“系统找不到指定路径”如何解决？,"问题分析： |
| `mysql_qa/data/JP学科知识问答.csv:316` | D | 学科 | Python学科,Python中GC的垃圾回收算法是什么？,"在Python中对象的释放有两种方法，引用计数法，垃圾回收法，这里主要讲解GC的垃圾回收方法。 |
| `mysql_qa/data/JP学科知识问答.csv:330` | D | 学科 | Python学科,mongod.service not found 怎么解决,"原因分析 |
| `mysql_qa/data/JP学科知识问答.csv:366` | D | 学科 | Python学科,Missing scheme in request url:,"原因： |
| `mysql_qa/data/JP学科知识问答.csv:377` | D | 学科 | Python学科,Tesseract OCR 中文库如何安装？,"sudo apt-get install tesseract-ocr-all  安装所有可用的语言包 |
| `mysql_qa/data/JP学科知识问答.csv:384` | D | 学科 | Python学科,win7 fiddler4 安装https证书失败如何解决," 请参考播客文章   http://blog.csdn.net/qq_37579266/article/details/78301175 |
| `mysql_qa/data/JP学科知识问答.csv:389` | D | 学科 | Python学科,"scrapy genspider name domain |
| `mysql_qa/data/JP学科知识问答.csv:392` | D | itcast | start_urls 中的url问题  需要自己验证url是否可用例如<http://www.itcast.cn/channel/teacher.shtml>用浏览器可以正常访问,<http://www.itcast.cn/channel/teacher.shtml/>  如果后面加上一个/以后发现不能正常访问，平常我们去访问https://www.baidu.com  https://www.b …（长行省略；原文件保留全文） |
| `mysql_qa/data/JP学科知识问答.csv:395` | D | 学科 | Python学科,spider爬取图片后重命名不能创建新目录,"原因 |
| `mysql_qa/data/JP学科知识问答.csv:405` | D | 学科 | Python学科,Phantom虚拟机默认访问127.0.0.1不能获取到数据,"原因 |
| `mysql_qa/data/JP学科知识问答.csv:415` | D | 学科 | Python学科,scrapy中item使用'.'点号的方式赋值出现错误,item继承与scrapy.Item 是一个类 字典的类型，而且比字典还会多一些错误校验的措施（例如定义的字段名字是title，但是赋值的时候使用item['tittle'] 这时候就会给我报错，如果我们使用的是普通字典则不会报错），使用方式与字典的方式一样使用。 |
| `mysql_qa/data/JP学科知识问答.csv:416` | D | 学科 | Python学科,chrome中xpath能提百度贴吧帖子链接，使用代码提不到,"原因： |
| `mysql_qa/data/JP学科知识问答.csv:423` | D | 学科 | Python学科,urllib2.HTTPError:HTTP Error,"win7下面使用fiddler后使用urllib2出现以下问题urllib2.HTTPError: HTTP Error 504: Fiddler - Receive Failure |
| `mysql_qa/data/JP学科知识问答.csv:435` | D | 学科 | Python学科,爬虫爬取下来的数据写入文件有哪些方式,"爬取下来的数据格式不同，写入文件的方式也不同 |
| `mysql_qa/data/JP学科知识问答.csv:442` | D | 学科 | Python学科,ubuntu 中如何安装Selenium,"ubuntu 中使用sudo apt-get install selenium，则可能会出现安装完成后selenium中的部分功能不能用, |
| `mysql_qa/data/JP学科知识问答.csv:444` | D | 学科 | Python学科,xpath中的 position 方法怎么理解,position 方法是相对于当前节点的父节点说的 |
| `mysql_qa/data/JP学科知识问答.csv:445` | D | 学科 | Python学科,not 运算符什么时候使用，有什么作用,"not 运算符可以用来对原来的 boolean 表达式的值进行取反运算，如果原来表达式的值是 True，经过not运算之后，表达式的值是 False; 如果原来表达式的值是 False，经过 not 运算之后，表达式的值是 True。 |
| `mysql_qa/data/JP学科知识问答.csv:451` | D | 老师 | # 1. 如果老师今天没有生病，那么今天就约美女班主任老师去看电影 |
| `mysql_qa/data/JP学科知识问答.csv:460` | D | 老师 | print(""今天约美女班主任老师去看电影"") |
| `mysql_qa/data/JP学科知识问答.csv:467` | D | 老师 | # 所以如果 print(""今天约美女班主任老师去看电影"") 语句要执行，if 后面的表达式 ""xxx is_sick"" 必须为 True |
| `mysql_qa/data/JP学科知识问答.csv:473` | D | 学科 | Python学科,is 运算符在iPython3中和PyCharm中结果不一致,对于Python而言，存储好的脚本文件（Script file）和在Console中的交互式（interactive）命令，执行方式不同。对于脚本文件，解释器将其当作整个代码块执行，而对于交互性命令行中的每一条命令，解释器将其当作单独的代码块执行。而Python在执行同一个代码块的初始化对象的命令时，会检查是否其值是否 …（长行省略；原文件保留全文） |
| `mysql_qa/data/JP学科知识问答.csv:474` | D | 学科 | Python学科,用mkvirtualenv命令创建虚拟环境提示找不到命令,"方法一： |
| `mysql_qa/data/JP学科知识问答.csv:489` | D | 学科 | Python学科,网络调试助手无法收到 ubuntu发送的包,"可能的原因： |
| `mysql_qa/data/JP学科知识问答.csv:494` | D | 学科 | Python学科,字符串类型和数字类型怎么比较大小,"在Python2中，比较运算遵循以下规则: |
| `mysql_qa/data/JP学科知识问答.csv:525` | D | 学科 | Python学科,mv命令系统如何判断命令是改名字还是移动,"mv source target |
| `mysql_qa/data/JP学科知识问答.csv:538` | D | 学科 | Python学科,为什么可以用2个对象接收一个函数,"此方法是在基础阶段最开始讲解函数部分，返回多个对象章节中讲到的 |
| `mysql_qa/data/JP学科知识问答.csv:545` | D | 学科 | Python学科,为什么不在同一网段的ip不能直接通信,这里 有一篇帖子 ：https://www.cnblogs.com/S-volcano/p/5032065.html 作为参考。 |
| `mysql_qa/data/JP学科知识问答.csv:546` | D | 学科 | Python学科,docker 创建容器的参数,"-p是映射端口 |
| `mysql_qa/data/JP学科知识问答.csv:551` | D | 学科 | Python学科,归一化算法问题,"用(x1-x2)^2 是在计算两个特征的距离 来计算两个特征在空间中的距离 |
| `mysql_qa/data/JP学科知识问答.csv:564` | D | 学科 | Python学科,关于vim 退出,"w：保存 |
| `mysql_qa/data/JP学科知识问答.csv:569` | D | 学科 | Python学科,怎么让一个用python写的服务器.py程序一直运行呢,python-daemon 这个 python包 研究一下 |
| `mysql_qa/data/JP学科知识问答.csv:570` | D | 学科 | Python学科,def 末尾return None,"return None  跟不写, 没有任何区别" |
| `mysql_qa/data/JP学科知识问答.csv:571` | D | 学科 | Python学科,全局变量可以在函数中定义么,"可以, 定义时加个global |
| `mysql_qa/data/JP学科知识问答.csv:576` | D | 学科 | Python学科,绑定端口时为什么不需要写具体的ip地址呢,如果 不写的话 就是 绑定 自己的 本地的ip地址。 |
| `mysql_qa/data/JP学科知识问答.csv:577` | D | 学科 | Python学科,./run.sh 是什么意思,"""./""代表""本目录""的意思，所以""./run.sh"" 代表执行本目录下名为 run.sh 的文件" |
| `mysql_qa/data/JP学科知识问答.csv:578` | D | 学科 | Python学科,pycharm导入模块的快捷键是什么,alt+enter |
| `mysql_qa/data/JP学科知识问答.csv:579` | D | 学科 | Python学科,在方法中的局部变量，是不是无法被其他方法调用,方法 中的 局部变量 不能在 其他 方法里使用。如果想做到这样，可以 根据 情况 定义成 实例属性或者类属性 |
| `mysql_qa/data/JP学科知识问答.csv:580` | D | 学科 | Python学科,"数据库,明明关联会降低查询性能，为什么还会分出这么多表",因为 如果 都存 一张表里 很多 字段 都是重复的。太消耗 磁盘空间了 |
| `mysql_qa/data/JP学科知识问答.csv:581` | D | 学科 | Python学科,mac 安装mysql无配置文件,"mac 系统下。没有配置文件，需要自己手动创建。 |
| `mysql_qa/data/JP学科知识问答.csv:584` | D | 学科 | Python学科,live-server安装失败,降低node版本，使用sudo安装 |
| `mysql_qa/data/JP学科知识问答.csv:585` | D | 学科 | Python学科,"windows环境中验证码不显示 |
| `mysql_qa/data/JP学科知识问答.csv:587` | D | 学科 | Python学科,axis 的问题," axix = 0 在不同的方法看起来好像有不同的方向 但是掌握一个大原则 |
| `mysql_qa/data/JP学科知识问答.csv:592` | D | 学科 | Python学科,vmWare三种网络模式：桥连接、net模式、仅主机模式区别,理解这个 需要 对 网络有 很不错的基础才行哦。https://www.linuxidc.com/Linux/2016-09/135521p3.htm  这里 有一篇文章你看看，能看懂最好，看不懂 也别纠结。知识储备 没到这个 程度。 |
| `mysql_qa/data/JP学科知识问答.csv:593` | D | 学科 | Python学科,"arrary切片, data[:,-1]","data是一个二维数组, data[:, -1]表示: |
| `mysql_qa/data/JP学科知识问答.csv:595` | D | 学科 | Python学科,没有middleware.py文件,需要 切换到 虚拟环境里 创建 爬虫项目 |
| `mysql_qa/data/JP学科知识问答.csv:596` | D | 学科 | Python学科,服务器uwsgi运行不起来,"如果是 502 的話說明虽然支持项目运行的uwsgi进程已经不再了。 |
| `mysql_qa/data/JP学科知识问答.csv:601` | D | 学科 | Python学科,熵的解释,"可以简单粗暴的理解为『当混乱度越高 熵值就越高』 |
| `mysql_qa/data/JP学科知识问答.csv:610` | D | 学科 | Python学科,jQuery中关于$符号的规则,$ 符号是 JQ 对象的一个简写，只要是透过 JQ 获取元素或者初始化的时候都需要添加 |
| `mysql_qa/data/JP学科知识问答.csv:611` | D | 学科 | Python学科,cls.pokes前为什么要加cls?不可以直接pokes.,pokes 如果是类属性，可以通过类对象获取到，一般 cls 表示类对象 |
| `mysql_qa/data/JP学科知识问答.csv:612` | D | 学科 | Python学科,Flask mysqldb Library not load,"因为你是使用的python3 ,MySQLdb是之前python2的，并不支持Python3， 使用时可以通过pymysql.install_as_MySQLdb()这句话，意思就是用pymysql来代替mysqldb" |
| `mysql_qa/data/JP学科知识问答.csv:613` | D | 学科 | Python学科,“浮点型”转换成“整型”的问题,"浮点数 float 类型可以转 int 类型啊，只是转换之后会有精度丢失 |
| `mysql_qa/data/JP学科知识问答.csv:616` | D | 学科 | Python学科,"app = Flask(__name__) name路径 |
| `mysql_qa/data/JP学科知识问答.csv:618` | D | 学科 | Python学科,select模块里只有poll()方法没有epoll()方法,mac电脑 是不支持 epoll的 ，epoll的代码 你需要在 ubuntu里写 |
| `mysql_qa/data/JP学科知识问答.csv:619` | D | 学科 | Python学科,大数字除法不精准问题,使用 decimal 模块 可以解决这种 精度问题 |
| `mysql_qa/data/JP学科知识问答.csv:620` | D | 学科 | Python学科,虚拟机桥接模式后不能上网,切换成 nat模式 |
| `mysql_qa/data/JP学科知识问答.csv:621` | D | 学科 | Python学科,什么是SerializeToString,"SerializeToString()序列化为字符串 |
| `mysql_qa/data/JP学科知识问答.csv:630` | D | 学科 | Python学科,"Flask routing BaseConverter |
| `mysql_qa/data/JP学科知识问答.csv:634` | D | 学科 | Python学科,getattr作用,"返回对象属性值。 |
| `mysql_qa/data/JP学科知识问答.csv:645` | D | 学科 | Python学科,实例变量/实例方法怎么理解,"举个例子什么是实例 |
| `mysql_qa/data/JP学科知识问答.csv:665` | D | 学科 | Python学科,python -m ,"python xxx.py |
| `mysql_qa/data/JP学科知识问答.csv:670` | D | 学科 | Python学科,sys模块中的exit与pygame中的exit方法的区别,"sys.exit 执行会直接退出程序，这也是经常使用的方法，也不需要考虑平台等因素的影响，一般是退出Python程序的首选方法。 |
| `mysql_qa/data/JP学科知识问答.csv:680` | D | 学科 | Python学科,如何实现在一段字符串中显示某个字符串多次出现的位置,"例如""hello world hello python""中o出现的位置，显示结果为（4，5，16，23） |
| `mysql_qa/data/JP学科知识问答.csv:700` | D | 学科 | Python学科,pycharm拖动静态文件到templates文件夹,"pycharm拖动静态文件到templates文件夹时，无法像课件那样自动更改html中导入的js图片路径 |
| `mysql_qa/data/JP学科知识问答.csv:702` | D | 学科 | Python学科,父进程会不会等待子进程结束才结束,"不会等待, 除非设置join方法, 否则父进程退出后，是不会通知子进程的，这个时候子进程会成为孤儿进程，最终被init进程收养" |
| `mysql_qa/data/JP学科知识问答.csv:703` | D | 学科 | Python学科,jinja2模板没有自动补全,电脑没有反应过来清缓存重新加载 |
| `mysql_qa/data/JP学科知识问答.csv:704` | D | 学科 | Python学科,__name__	与__qualname__的区别,"官方解释：https://www.python.org/dev/peps/pep-3155/ |
| `mysql_qa/data/JP学科知识问答.csv:709` | D | 学科 | Python学科,write()方法覆盖问题,write方法 是否覆盖 文件内容，是由 文件打开模式 决定的。如果 不想 覆盖文件原来的内容 就 使用 a 模式打开。a模式打开之后 就不会覆盖 原来的信息了。 |
| `mysql_qa/data/JP学科知识问答.csv:710` | D | 学科 | Python学科,无法CD到var/log下的redis文件夹中,想进入这个文件里，可以先su 切换到root账户，在cd redis |
| `mysql_qa/data/JP学科知识问答.csv:711` | D | 学科 | Python学科,如何判断字符串中含有特殊字符,"调用 isalpha方法, 如果返回True, 那么就没有特殊字符" |
| `mysql_qa/data/JP学科知识问答.csv:712` | D | 学科 | Python学科,实例方法、类方法和静态方法,"实例方法 |
| `mysql_qa/data/JP学科知识问答.csv:729` | D | 学科 | Python学科,把一个元素全为数字的列表中的所有偶数加1,"这个问题我们需要遍历整个，然后把每个元素的 index 出来 |
| `mysql_qa/data/JP学科知识问答.csv:743` | D | 学科 | Python学科,redis端口和连接,"redis的默认端口是6379，通过对redis的配置文件修改，可以修改端口 |
| `mysql_qa/data/JP学科知识问答.csv:750` | D | 学科 | Python学科,SQLAlchemy 多对多中间表 操作命令,"我看到以下这篇文章，是用于多对多的，你可以参考一下，希望能够对你有帮助 |
| `mysql_qa/data/JP学科知识问答.csv:755` | D | 学科 | Python学科,使用循环手工输入5个整数，将其存入列表，打印出最大值和最小值,"import re |
| `mysql_qa/data/JP学科知识问答.csv:763` | D | 学科 | Python学科,解释器与集成开发环境的本质区别,"解释器     相当于空气，人类没有空气就直接死了 |
| `mysql_qa/data/JP学科知识问答.csv:772` | D | 学科 | Python学科,递归调用最大层级1000次是只有python这样吗,"php最大递归调用 256次 |
| `mysql_qa/data/JP学科知识问答.csv:781` | D | 学科 | Python学科,如何查看python里函数的帮助,"在函数上点击ctrl，鼠标在点击那个函数，即可看到函数的源码内容以及注释了 |
| `mysql_qa/data/JP学科知识问答.csv:784` | D | 学科 | Python学科,MAC地址是指的什么,可以认为是 交换机等 数据链路层设备 用来 传输数据的 地址。ip地址 是用来 路由器等 网路设备之间 传输 数据的地址。 |
| `mysql_qa/data/JP学科知识问答.csv:785` | D | 学科 | Python学科,变量可以私有化,"變量的確可以被私有化， |
| `mysql_qa/data/JP学科知识问答.csv:792` | D | 学科 | Python学科,如何利用径向神经网络解决异或问题,"在数字逻辑中，异或是对两个运算元的一种逻辑分析类型，符号为XOR或EOR或⊕。 |
| `mysql_qa/data/JP学科知识问答.csv:801` | D | 学科 | Python学科,使用celery报错 ModuleNotFoundError,"celery -A celery_tasks.main worker -l info 运行 |
| `mysql_qa/data/JP学科知识问答.csv:806` | D | 学科,老师 | Python学科,激活码从哪里获得,http://47.93.248.15/pycharm/  文章，你可以访问以下，按照文章进行破解，如果无法破解成功，请联系老师远程为你操作 |
| `mysql_qa/data/JP学科知识问答.csv:807` | D | 学科 | Python学科,什么是cart算法,"CART 算法可以做分类 也可以做回归，我们今天就讨落在决策树上的使用，也就是在分类上。 |
| `mysql_qa/data/JP学科知识问答.csv:814` | D | 学科 | Python学科,函数和类区别,python中 一切皆 对象。函数 也是一个 对象。类 实际也是一个 对象。 函数和类，他们的 类型不同，语法不同，其他 区别  我们 不关心。面向对象 编程 类和函数 都可能用到，所以 没什么 适用不适用 这一说 |
| `mysql_qa/data/JP学科知识问答.csv:815` | D | 学科 | Python学科,虚拟环境使用,"每个虚拟环境尽量只创建一个项目,因为使用虚拟环境的目的，就是怕多个项目之间存在版本差异" |
| `mysql_qa/data/JP学科知识问答.csv:816` | D | 学科 | Python学科,python 单引号的使用,"单引号字符串：'abc' |
| `mysql_qa/data/JP学科知识问答.csv:818` | D | 学科 | Python学科,Non-ASCII character '\xe5' in ,可以在python文件最上方加上  # -*- coding:UTF-8 -*-  这句话 |
| `mysql_qa/data/JP学科知识问答.csv:819` | D | 学科 | Python学科,特征值、目标值占位符的作用是什么,"特征值的作用是帮我们用来推测目标值 |
| `mysql_qa/data/JP学科知识问答.csv:834` | D | 学科 | Python学科,什么是张量,"你可以当做是一个多维的数组，维度可以是0，也可以是10 |
| `mysql_qa/data/JP学科知识问答.csv:847` | D | 学科 | Python学科,"fit_transform, fit","fit方法是用于从一个训练集中学习模型参数，其中就包括了归一化时用到的均值，标准偏差。 |
| `mysql_qa/data/JP学科知识问答.csv:856` | D | 学科 | Python学科,deepcody,"这是深复制. |
| `mysql_qa/data/JP学科知识问答.csv:860` | D | 学科 | Python学科,print(0 and False)得到的结果怎么是0,"and 二边返回的是结果，2边的结果必须都是1才为1 |
| `mysql_qa/data/JP学科知识问答.csv:877` | D | 学科 | Python学科,Django的前端页面显示不出来,"当执行127.0.0.1：8000/register.html的时候怎么设置urls让它显示? |
| `mysql_qa/data/JP学科知识问答.csv:881` | D | 学科 | Python学科,加载html网页时，如果出现html是汉字命名,"可以通过以下方法进行转换 |
| `mysql_qa/data/JP学科知识问答.csv:886` | D | 学科 | Python学科,pycharm导包时出于灰色状态,灰色 是因为 你在代码里 还没使用 导入的 类或者方法。这个 不是错误。 |
| `mysql_qa/data/JP学科知识问答.csv:887` | D | 学科 | Python学科,process.queue()和manger().queue,multiprocessing.Queue 实现了 一些 额外的方法，这些方法是 manger().queue() 里 没有的。但是 这些 额外方法，在大部分代码里 是 用不到的。所以基本上 可以认为这俩队列是一样的。 |
| `mysql_qa/data/JP学科知识问答.csv:888` | D | 学科 | Python学科,"[None,28*28,1]28*28是一张图片的像素吗","28*28 的意思是 输入的格式为 28*28的方式 |
| `mysql_qa/data/JP学科知识问答.csv:891` | D | 学科 | Python学科,代码上方会表明编码格式 # coding:utf-8,python2 中 不支持中文，所以 代码第一行 会写上 # coding:utf-8 ，用来支持中文的。Python3中 默认情况下是 支持 中文的，所以不用写 |
| `mysql_qa/data/JP学科知识问答.csv:892` | D | 学科 | Python学科,进程通信为什不用全局变量来实现,"进程之间 不 共享 全局变量，所以用 全局变量是不行的。 |
| `mysql_qa/data/JP学科知识问答.csv:894` | D | 学科 | Python学科,if else 能返回上一级继续判断吗,if else  做不到 这样的 逻辑  循环可以 |
| `mysql_qa/data/JP学科知识问答.csv:895` | D | 学科 | Python学科,print和return在打印和接收数据的区别,"1、print是直接输入内容到终端上 |
| `mysql_qa/data/JP学科知识问答.csv:918` | D | 学科 | Python学科,使用 变量 += 元组 时，为什么会自动对元组进行拆包,"1、是固定语法 |
| `mysql_qa/data/JP学科知识问答.csv:925` | D | 学科 | Python学科,使用more命令时，按f可以向下翻，按b不会往回走，没反应,"Ctrl+f 向下滚动一屏 |
| `mysql_qa/data/JP学科知识问答.csv:927` | D | 学科 | Python学科,K-means算法中，求的是谁的平均值,"K-means的思路是这样的​​​​​​​ |
| `mysql_qa/data/JP学科知识问答.csv:934` | D | 学科 | Python学科,python私有属性/方法中单下划线和双下划线区别,"单下划线没有意义(一般是提示程序员这个变量当私有变量来处理, 但是外部还是可以进行调用, 所以只是一个提示作用, 有经验的程序在看到这种变量的时候都会将其作为私有变量来处理)，双下划线是在对象初始化以后，外部无法调用" |
| `mysql_qa/data/JP学科知识问答.csv:935` | D | 学科 | Python学科,列表中那么多的数，我想实现相邻两个数只差怎么办,"比如， |
| `mysql_qa/data/JP学科知识问答.csv:954` | D | 学科 | Python学科,Linux高级编程中ubantu可以换成centos吗,"可以，都一样 |
| `mysql_qa/data/JP学科知识问答.csv:959` | D | 学科 | Python学科,为什么要在vim模式下写python,"1、简单直白点就是练习你打字速度 |
| `mysql_qa/data/JP学科知识问答.csv:964` | D | 学科 | Python学科,已经commit了还能rollback吗,"commit是提交事务，rollback是当事务出现错误的时候才会回滚，也就是数据撤回 |
| `mysql_qa/data/JP学科知识问答.csv:967` | D | 学科 | Python学科,移动设备也有固定的IP地址吗,移动设备 也会有 ip地址 ，默认 ip地址 是动态分配的哦，不是固定的。 |
| `mysql_qa/data/JP学科知识问答.csv:968` | D | 学科 | Python学科,在 vim 状态怎么进入编辑模式,使用 vim 打开文件后，按 i或者a 进入 编辑模式 |
| `mysql_qa/data/JP学科知识问答.csv:969` | D | 学科 | Python学科,gevent中的join(),join 方法 的作用 实际上 是让 主线程 阻塞，等所有的 协程 执行完了 ，主线程再继续执行。如果 不加join，主线程 结束之后，协程也会跟着结束。所以要加 join 。web服务器中 不加join 是 因为 主线程是 死循环，不会结束。所以不加join也可以 |
| `mysql_qa/data/JP学科知识问答.csv:970` | D | 学科 | Python学科,CTRL +c 是中断什么的,"ctrl + c 是中断当前程序的运行 |
| `mysql_qa/data/JP学科知识问答.csv:973` | D | 学科 | Python学科,init的变量设置时，什么时候需要使用None,如果 你定义了一个变量 ，但是暂时不想给 这个变量赋值，那么你可以把 这个变量 设置成None。把 变量的值 设置成None，不影响 以后的赋值 |
| `mysql_qa/data/JP学科知识问答.csv:974` | D | 学科 | Python学科,用什么方法计算selenium通过chrome下载文件的速度,这个部分跟您的网路设置有关，目前并没有计算的方法 |
| `mysql_qa/data/JP学科知识问答.csv:975` | D | 学科 | Python学科,桥接后怎么就没有了ipv4 的地址,学校的网，必须要 使用nat模式才行 |
| `mysql_qa/data/JP学科知识问答.csv:976` | D | 学科 | Python学科,tuple index out of range,"tuple index out of range意为元组指数超过范围 |
| `mysql_qa/data/JP学科知识问答.csv:993` | D | 学科 | Python学科,"xshell中,scp不是内部或外部命令",scp 是 用于 两个 linux系统之间 赋值文件的。不适用于 windows |
| `mysql_qa/data/JP学科知识问答.csv:994` | D | 学科 | Python学科,vim中在行前加入“# ”号的快捷键是什么？即单行注释快捷键,"Step 1：在命令行模式下，将光标固定在第一列，按Ctrl+V快捷键进入VB可视化模式： |
| `mysql_qa/data/JP学科知识问答.csv:1009` | D | 学科,课程 | Python学科,python里的多态是什么意思,"python的多态，在课程中有讲解 |
| `mysql_qa/data/JP学科知识问答.csv:1014` | D | 学科 | Python学科,请问有没有什么函数或内置属性可以用来查看某个类的父类是谁,在定义类的时候，你不写是默认继承自obj类，如果写就是指定的类，实际上最基类都是obj |
| `mysql_qa/data/JP学科知识问答.csv:1015` | D | 学科 | Python学科,tcp服务器和客户端是什么意思,"客户端就是类似你打王者荣耀的手机 |
| `mysql_qa/data/JP学科知识问答.csv:1018` | D | 学科 | Python学科,多种内置属性的含义,"__name__: 类名 |
| `mysql_qa/data/JP学科知识问答.csv:1027` | D | 学科 | Python学科,"飞机大战内存释放 |
| `mysql_qa/data/JP学科知识问答.csv:1029` | D | 学科 | Python学科,mac的PyCharm是不是不能用epoll,"epoll是liunx 2.6内核增加的新功能 |
| `mysql_qa/data/JP学科知识问答.csv:1034` | D | 学科 | Python学科,为什么说python是一种胶水语言,"胶水可以黏接两种不同的材质，而 python 也具备有这样的特质 |
| `mysql_qa/data/JP学科知识问答.csv:1039` | D | 学科 | Python学科,"做tcp,绑定的端口老是会提示呗占用","这个问题是因为你在第一次使用的时候端口就已经被占用了 |
| `mysql_qa/data/JP学科知识问答.csv:1044` | D | 学科 | Python学科,如何用公有方法获取在类里面定义的私有属性,"class Person(object): |
| `mysql_qa/data/JP学科知识问答.csv:1054` | D | 学科 | Python学科,公有属性和公有方法不明白,公有属性，就是 前面不加俩下划线的属性。公有方法 也是一样的。 |
| `mysql_qa/data/JP学科知识问答.csv:1055` | D | 学科 | Python学科,遇到python内置类型使用错误,int('6') 提示不是一个callback 检查 前面的代码是不是把内置int替换赋值成其他数 int = 100 ，导致我们int此时是一个变量而不是一个函数 |
| `mysql_qa/data/JP学科知识问答.csv:1056` | D | 学科 | Python学科,正则匹配密码强度,"要求密码包含特殊字符【数字键盘0~9上面的字符】，数字，字母区分大小写，密码长度至少8位最多16位 |
| `mysql_qa/data/JP学科知识问答.csv:1079` | D | 学科 | Python学科,input 函数解释,"使用方式：data = input(""提示信息"") |
| `mysql_qa/data/JP学科知识问答.csv:1081` | D | 学科 | Python学科,MySQL 全局变量查询,"1. 查看所有全局变量 SHOW GLOBAL VARIABLES; |
| `mysql_qa/data/JP学科知识问答.csv:1086` | D | 学科 | Python学科,空字符串匹配正则问题,"空字符匹配任何正则都可以匹配命中，且返回空字符串 |
| `mysql_qa/data/JP学科知识问答.csv:1088` | D | 学科 | Python学科,re  findall取消分组,"# 取消分组 |
| `mysql_qa/data/JP学科知识问答.csv:1092` | D | 学科 | Python学科,scrapy 同一个进程同时运行多个爬虫示例,"默认情况当你每次执行scrapy crawl命令时会创建一个新的进程。但我们可以使用核心API在同一个进程中同时运行多个spider |
| `mysql_qa/data/JP学科知识问答.csv:1114` | D | 学科 | Python学科,MYSQL 导入数据出现外键引用,"问题： 由于数据库外键引用检查导致的，可以先关闭 |
| `mysql_qa/data/JP学科知识问答.csv:1118` | D | 学科 | Python学科,xpath 中如何使用正则,"doc.xpath(r'//*[re:match(@id, ""postmessage_\d+"")]', namespaces={""re"": ""http://exslt.org/regular-expressions""}) |
| `mysql_qa/data/JP学科知识问答.csv:1120` | D | 学科 | Python学科,Mysql如何查询一个表的所有字段,select COLUMN_NAME from information_schema.COLUMNS where table_name = 'table_name' |
| `mysql_qa/data/JP学科知识问答.csv:1121` | D | 学科 | Python学科,linux下面批量停止同一类进程,"ps -ef \| grep main.py \|awk '{print $2}'\|xargs kill -9 |
| `mysql_qa/data/JP学科知识问答.csv:1127` | D | 学科 | Python学科,xpath – 如何匹配包含某个字符串的属性？,"标签 |
| `mysql_qa/data/JP学科知识问答.csv:1133` | D | 学科 | Python学科,linux下面查看端口占用,"lsof -i :11366 \|grep ""(LISTEN)"" \| awk '{printf($1)}' |
| `mysql_qa/data/JP学科知识问答.csv:1135` | D | 学科 | Python学科,重置vmware虚拟机网络,"{""answerText"":""d310928c-9dba-45ea-91fc-e058f0758c4d"",""answerType"":""NEWS""}" |
| `mysql_qa/data/JP学科知识问答.csv:1136` | D | 学科 | Python学科,typora 中markdown插入视频,"插入video标签即可 |
| `mysql_qa/data/JP学科知识问答.csv:1138` | D | 学科 | Python学科,linux 查看指定进程的资源占用情况,"top -p \`pgrep python \| tr ""\\n"" "","" \| sed 's/,$//\`' |
| `mysql_qa/data/JP学科知识问答.csv:1141` | D | 学科 | Python学科,"no module name ""MySQLdb""",pip install PyMySQL，将数据库连接改为 mysql+pymysql://username:password@server/db，接下来的操作就一切正常了。 |
| `mysql_qa/data/JP学科知识问答.csv:1142` | D | 学科 | Python学科,虚安环境安装flask成功，找不到,直接用pip instal，如果加了sudo默认装到真实环境里，并没有装到虚拟环境，所以在虚拟环境里找不到了 |
| `mysql_qa/data/JP学科知识问答.csv:1143` | D | 学科 | Python学科,OSError:mysql_config not found,"原因是linux需要mysql相关的一些依赖包, |
| `mysql_qa/data/JP学科知识问答.csv:1145` | D | 学科 | Python学科,error keyword argument 'method,注册路由route时 methods属性 写成method，修改为methods即可 |
| `mysql_qa/data/JP学科知识问答.csv:1146` | D | 学科 | Python学科,python中的条件语句,"1. 条件语句常常用于if 或者 while 后面做为判断执行的条件 |
| `mysql_qa/data/JP学科知识问答.csv:1152` | D | 学科 | Python学科,面向对象类名字命名规则,类名字命名与变量命名类似，见名知意，类命名主要以类的功能用户来命名，例如： Person类 ：包含一些人的特征属性以及行为，不要包含其他的行为属性。 |
| `mysql_qa/data/JP学科知识问答.csv:1153` | D | 学科 | Python学科,获取修改密码的token的时候报错,"错误：Could not find config for 'verify_code' in settings.CACHES |
| `mysql_qa/data/JP学科知识问答.csv:1155` | D | 学科 | Python学科,celery 启动任务添加不成功,"检查导包路径： |
| `mysql_qa/data/JP学科知识问答.csv:1157` | D | 学科 | Python学科,点击run 的话 不会运行django服务器，而运行帮助文档,配置 edit configurations 中 parameters  中添加runserver |
| `mysql_qa/data/JP学科知识问答.csv:1158` | D | 学科 | Python学科,pymysql.err.InterfaceError,"错误原因，因为使用了一个已关闭的链接导致的问题导致 |
| `mysql_qa/data/JP学科知识问答.csv:1163` | D | 学科 | Python学科,{'172001': '网络错误'}云通讯失败,"在sms.py中,添加下列代码即可 |
| `mysql_qa/data/JP学科知识问答.csv:1167` | D | 学科 | Python学科,docker pull elastisearch 不成功,"添加版本号之后pull |
| `mysql_qa/data/JP学科知识问答.csv:1169` | D | 学科 | Python学科,manage.py  No such file or ...,"切换到manage文件上,之后在执行 启动命令" |
| `mysql_qa/data/JP学科知识问答.csv:1170` | D | 学科 | Python学科,chrome无法访问本地6000端口服务,"错误312（net：：ERR_UNSAFE_PORT):未知错误 |
| `mysql_qa/data/JP学科知识问答.csv:1175` | D | 学科 | Python学科,python socket 异常一览表,"{""answerText"":""e65204c6-7539-40a0-9154-9e050eed09c2"",""answerType"":""NEWS""}" |
| `mysql_qa/data/JP学科知识问答.csv:1176` | D | 学科 | Python学科,f-string表达式,"f-string python的新式格式化方式，python3.6后出现的 |
| `mysql_qa/data/JP学科知识问答.csv:1190` | D | 学科 | Python学科,datetime与字符串相互转化,"datetime转字符串，使用datetime对象的strftimef方法 |
| `mysql_qa/data/JP学科知识问答.csv:1202` | D | 学科 | Python学科,python 进程 jion方法," join 默认是阻塞回收等待进程结束并回收进程资源 |
| `mysql_qa/data/JP学科知识问答.csv:1206` | D | 学科 | Python学科,xhsell or CRT 进行远程文件传输,"1. 安装lrzsz 命令，centos： sudo yum install lrzsz  ubuntu：sudo apt-get install lrzsz |
| `mysql_qa/data/JP学科知识问答.csv:1210` | D | 学科 | Python学科,PEP 484规则，解释器自动进行类型判断,"# 语法格式如下，参数类型 使用: 标识 |
| `mysql_qa/data/JP学科知识问答.csv:1217` | D | 学科 | Python学科,http中GET与POST请求区别,"get 请求主要用于获取资源使用，请求体无法携带数据，相关的插入参数主要依赖 URL path 以及查询参数，以及cookie协携带的数据 |
| `mysql_qa/data/JP学科知识问答.csv:1219` | D | 学科 | Python学科,mysql5.7 忘记 root密码怎么办？,"1.在配置文件[mysqld]部分添加skip-grant-tables参数，重启服务 |
| `mysql_qa/data/JP学科知识问答.csv:1225` | D | 学科 | Python学科,redis 设置密码访问," |
| `mysql_qa/data/JP学科知识问答.csv:1235` | D | 学科 | Python学科,哪些元素 可以设置 z-index 样式,只有相对定位，绝对定位，固定定位的元素有此属性，其余标准流，浮动，静态定位都无此属性，亦不可指定此属性。 |
| `mysql_qa/data/JP学科知识问答.csv:1236` | D | 学科 | Python学科,redis 如何开启 远程访问？,"找到配置文件后  注释：bind  127.0.0.1 |
| `mysql_qa/data/JP学科知识问答.csv:1239` | D | 学科 | Python学科,通过apt仓库 安装最新版mysql,"1. 添加 mysql apt 仓库 |
| `mysql_qa/data/JP学科知识问答.csv:1259` | D | 学科 | Python学科,pip ：cannot import name 'main',"解决办法1： |
| `mysql_qa/data/JP学科知识问答.csv:1267` | D | 学科 | Python学科,pip 使用 豆瓣源 安装 python包,例如：pip3 install pygame -i http://pypi.douban.com/simple/  --trusted-host=pypi.douban.com |
| `mysql_qa/data/JP学科知识问答.csv:1268` | D | 学科 | Python学科,高版本 jquery 入口函数 报错,"{""answerText"":""6aa39167-a6cb-4bb2-918e-50383d03bf7b"",""answerType"":""NEWS""}" |
| `mysql_qa/data/JP学科知识问答.csv:1269` | D | 学科 | Python学科,win10 可以 ping同 乌班图虚拟机，反过来不行,关闭 杀毒软件，和 win10 系统自带的 防火墙 |
| `mysql_qa/data/JP学科知识问答.csv:1270` | D | 学科 | Python学科,mac电脑 打不开乌班图 虚拟机,"VMware虚拟机打不开/dev/vmmon无此文件或目录 |
| `mysql_qa/data/JP学科知识问答.csv:1281` | D | 学科 | Python学科,vscode编辑器 相对路径 问题,这个编辑器 比较别扭 ./ 指的是 相对于 工作区顶层文件夹，而不是 相对于文件当前目录 |
| `mysql_qa/data/JP学科知识问答.csv:1282` | D | 学科 | Python学科,html 中如何解决 嵌套盒子 垂直外边距合并问题,父盒子 加上 样式：overflow: hidden; |
| `mysql_qa/data/JP学科知识问答.csv:1283` | D | 学科 | Python学科,pip10 工具bug," 如果使用pip 出现这个错误：ImportError: cannot import name 'main' |
| `mysql_qa/data/JP学科知识问答.csv:1294` | D | 学科 | Python学科,python3 自带 的虚拟环境使用,"win10下： |
| `mysql_qa/data/JP学科知识问答.csv:1311` | D | 学科 | Python学科,js中 dom元素的 offsetHeight 属性,如果子元素 不脱离文档流，这个属性的值 就是 盒子最终的高度值，包含 padding和 border |
| `mysql_qa/data/JP学科知识问答.csv:1312` | D | 学科 | Python学科,jinja2.exceptions.undefinederr,"在setting 补充jinja2模版引擎环境 |
| `mysql_qa/data/JP学科知识问答.csv:1314` | D | 学科 | Python学科,pycharm运行app，启动找不到app,"edit_configurations 编辑manager ,在parameters 中添加runserver" |
| `mysql_qa/data/JP学科知识问答.csv:1315` | D | 学科 | Python学科,python manager.py db init 运行程序,将程序app.run()  改成manager.run() |
| `mysql_qa/data/JP学科知识问答.csv:1316` | D | 学科 | Python学科,mac如何显示隐藏文件呀？,按command + shift + . 进行隐藏与非隐藏 |
| `mysql_qa/data/JP学科知识问答.csv:1317` | D | 学科 | Python学科,live-server 运行失败  = async path,"需更新node版本 |
| `mysql_qa/data/JP学科知识问答.csv:1319` | D | 学科 | Python学科,docler pull elasticsearch 失败,docker image pull delron/elasticsearch-ik:2.4.6-1.0 指定版本pull 成功 |
| `mysql_qa/data/JP学科知识问答.csv:1320` | D | 学科 | Python学科,push rejected,"git pull |
| `mysql_qa/data/JP学科知识问答.csv:1324` | D | 学科 | Python学科,js 中因es5爆红,在左上角file --setting里打开，languages$frameworks 中的javascript选中ECMAScript6 |
| `mysql_qa/data/JP学科知识问答.csv:1325` | D | 学科 | Python学科,"远程链接云服务器中mysql,redis,docker等链接",需在云服务器中开放对应端口安全组 |
| `mysql_qa/data/JP学科知识问答.csv:1326` | D | 学科 | Python学科,vue : cannot find element #app,先检查 html里面 div 是否绑定app，如已绑定，检查将导入 regiser.js script语句放在html最后 |
| `mysql_qa/data/JP学科知识问答.csv:1327` | D | 学科 | Python学科,expected an indented block 缩进错,"1. 第一种 python中的代码块控制，主要是靠缩进保证的，遇到这个问题 |
| `mysql_qa/data/JP学科知识问答.csv:1331` | D | 学科 | Python学科,前端引用了jquery 报$ undefined的错误,$主要是jquery中定义的，遇到未定义的错误的时候，正常是疑问juquery没有加载成功，可以检查下jquery的路径是否有问题导致的jquery没有加载成功！ |
| `mysql_qa/data/JP学科知识问答.csv:1332` | D | 学科 | Python学科,linux系统中使用pip安装python模块包提示没有权限,出现这样的问题的时候，一般是在系统环境中安装东西的时候可能会出现，可以使用sudo pip install xxx 这样解决权限不足的问题 |
| `mysql_qa/data/JP学科知识问答.csv:1333` | D | 学科 | Python学科,用weget apt 等安装出现https 40x错误的情况,"1. 这个情况一般都是网路出现问题 |
| `mysql_qa/data/JP学科知识问答.csv:1338` | D | 学科 | Python学科,(admin.E403) A 'django.......,出现此问题，通常是使用了django2 版本之上，建议使用django 完成此项目，此问题解决 django2 版本之前，如果使用jinja2 配置中必须保留 原本django  DjangoTemplate 配置 |
| `mysql_qa/data/JP学科知识问答.csv:1339` | D | 学科 | Python学科,StrictredisCluster 包导入不成功,"出现此问题，为redis 与 redis-py-cluster 版本不兼容问题 |
| `mysql_qa/data/JP学科知识问答.csv:1341` | D | 学科 | Python学科,TypeError: 'ConfiguredStorage',检查utils 文件中 jinja2_env 中是否为 staticfiles_storage.url |
| `mysql_qa/data/JP学科知识问答.csv:1342` | D | 学科 | Python学科,centos下面安装开发相关的工具环境,"# 直接使用yum安装工具集【例如编译相关的工具】 |
| `mysql_qa/data/JP学科知识问答.csv:1345` | D | 学科 | Python学科,远程传输工具安装,"# ubuntu |
| `mysql_qa/data/JP学科知识问答.csv:1353` | D | 学科 | Python学科,Ubuntu配置MySQL8.0 允许远程访问,参考链接: https://www.jianshu.com/p/852915e5a62b |
| `mysql_qa/data/JP学科知识问答.csv:1354` | D | 学科 | Python学科,js 中 箭头函数 需要注意哪些问题,"        （1）函数体内的this对象，就是定义时所在的对象，而不是使用时所在的对象。 |
| `mysql_qa/data/JP学科知识问答.csv:1361` | D | 学科 | Python学科,npm 使用淘宝下载源,"执行这行命令，以后你的 npm 就会从淘宝镜像下载包了，速度会比原来快很多 |
| `mysql_qa/data/JP学科知识问答.csv:1363` | D | 学科 | Python学科,live-server 服务器 配置 允许任意 ip 访问,参考链接:  https://www.jianshu.com/p/7cf79b0883ec |
| `mysql_qa/data/JP学科知识问答.csv:1364` | D | 学科 | Python学科,django配置 允许跨域请求,参考链接: https://www.jianshu.com/p/af80c99dc976 |
| `mysql_qa/data/JP学科知识问答.csv:1365` | D | 学科 | Python学科,python3 内建函数有哪些,参考链接: https://www.jianshu.com/p/8bf11a2ed489 |
| `mysql_qa/data/JP学科知识问答.csv:1366` | D | 学科 | Python学科,mac 系统下 安装了mysql，配置任意目录 访问,参考链接:https://www.jianshu.com/p/1420285866a8 |
| `mysql_qa/data/JP学科知识问答.csv:1367` | D | 学科 | Python学科,远程连接mysql 不成功,"在mysql 所在系统 |
| `mysql_qa/data/JP学科知识问答.csv:1372` | D | 学科 | Python学科,anaconda 在wiindows上面出现各种问题,"anaconda 在windows上面会出现各种各样的问题，建议同学 |
| `mysql_qa/data/JP学科知识问答.csv:1374` | D | 学科 | Python学科,ubuntu pip 安装包 timeout ,"创建文件 |
| `mysql_qa/data/JP学科知识问答.csv:1382` | D | 学科 | Python学科,python虚拟环境的目的,"最根本原因是解决包的版本依赖问题 |
| `mysql_qa/data/JP学科知识问答.csv:1384` | D | 学科 | Python学科,出现包安装，导入失败的问题,我们明明已经把包安装了，但是在pycharm中导入却提示失败没有此模块，出现这中问题，基本都是，我们安装模块的环境与pycharm配置的python环境不一致导致的，例如我们安装的模块在python2 环境中，pycharm使用了python3的环境！ 切换到我们与pycharm一致的环境再次安装模块就ok了 |
| `mysql_qa/data/JP学科知识问答.csv:1385` | D | 学科 | Python学科,创建虚拟环境出现OSError: Command错误,"出现这个错误的原因很大的可能是pip版本过低以及setuptools工具包版本太低导致 |
| `mysql_qa/data/JP学科知识问答.csv:1393` | D | 学科 | Python学科,mysql不支持bool类型,"如果当把一个数据设置成bool类型的时候， |
| `mysql_qa/data/JP学科知识问答.csv:1395` | D | 学科 | Python学科,列表推导式单条件判断与2个条件判断使用,"#1. 单条件判断,注意条件是循环后,仅保留满足条件的 |
| `mysql_qa/data/JP学科知识问答.csv:1405` | D | 学科 | Python学科,django中使用celery出现不能发现任务的问题,有的同学经常在配置django的异步celery任务的时候，经常出现发现不了任务，出现这种情况是因为我们celery任务中没有加载djaong的环境，所以导致任务加载不到！ 请同学配置django项目的环境后，再次启动celery 应该可以正常发现任务了 |
| `mysql_qa/data/JP学科知识问答.csv:1406` | D | 学科 | Python学科,打包python程序为可执行程序,有的同学想把自己写的python程序打包成可以执行文件，同学可以使用pyinstaller模块去打包成，建议查询下想要的教程 |
| `mysql_qa/data/JP学科知识问答.csv:1407` | D | 学科 | Python学科,float方法使用,"float 用于转化浮点数, 有2种使用方式 |
| `mysql_qa/data/JP学科知识问答.csv:1410` | D | 学科 | Python学科,python中类的属性的查找顺序,"python面向对象涉及到继承的时候，属性查找顺序，就不是在单一类中进行查找了，具体查找顺序，按照继承的MRO顺便查找，例如 Sub（A,B） 这样的一个多继承，MRO表【Sub，A，B】，假如我要找一个show方法，首先在sub类中进行查找，如果sub中没有，则向后遍历从A查找，直至查找到这个属性，或者抛出没有属性的异常" |
| `mysql_qa/data/JP学科知识问答.csv:1411` | D | 学科 | Python学科,vscode配置成 sublime text3 风格 主题,参考博客：https://www.jianshu.com/p/1a126aed93c3 |
| `mysql_qa/data/JP学科知识问答.csv:1412` | D | 学科 | Python学科,python3运算符 += 和 = 之间的区别,参考博客：https://www.jianshu.com/p/cf2e96196906 |
| `mysql_qa/data/JP学科知识问答.csv:1413` | D | 学科 | Python学科,回车和换行符 ,参考博客：https://www.jianshu.com/p/95f556ec2667 |
| `mysql_qa/data/JP学科知识问答.csv:1414` | D | 学科 | Python学科,配置 vscode 字体,参考博客：https://www.jianshu.com/p/117a875f4c8e |
| `mysql_qa/data/JP学科知识问答.csv:1415` | D | 学科 | Python学科,Vue-devtools 安装成功但无法使用,参考博客：https://www.jianshu.com/p/7d53a3771907 |
| `mysql_qa/data/JP学科知识问答.csv:1416` | D | 学科 | Python学科,python中if表达式中表达真假,"python中下面的常用的几种数据类型在if表达式中表达真假 |
| `mysql_qa/data/JP学科知识问答.csv:1419` | D | 学科 | Python学科,linux 下面的普通用户与root用户,"普通用户与root用户区别 |
| `mysql_qa/data/JP学科知识问答.csv:1423` | D | 学科 | Python学科,正则中的^符号,"正则中^有两种使用场景，分别表示不同的意思 |
| `mysql_qa/data/JP学科知识问答.csv:1426` | D | 学科 | Python学科,Windows上面修改myslql密码,"windows 最简单的方式使用mysqladmin命令 |
| `mysql_qa/data/JP学科知识问答.csv:1429` | D | 学科 | Python学科,concurrent_log_handler 问题,"concurrent_log_handler 在windwos下面使用报错误import win32file ImportError: DLL load failed: 找不到指定的程序 出现这样的错误 |
| `mysql_qa/data/JP学科知识问答.csv:1433` | D | 学科 | Python学科,hmtl的url地址,"假如我们当前的地址： http://127.0.0.1:8000/movie/ |
| `mysql_qa/data/JP学科知识问答.csv:1439` | D | 学科 | Python学科,面向对象 私有属性,"1. 面向对象的属性分为私有跟公有属性 |
| `mysql_qa/data/JP学科知识问答.csv:1443` | D | 学科 | Python学科,ValueError: last_login,"ValueError: The following fields do not exist in this model or are m2m fields: last_login Django |
| `mysql_qa/data/JP学科知识问答.csv:1445` | D | 学科 | Python学科,lambda表达式,lambda 表达式是个匿名函数，返回值是个函数，所以我们可以使变量取接收，然后当做函数调用， lambda表达仅仅编写一些简单的表达式，是为了简化我们的一些编写，完全可以用函数定义的方式替换，所以同学们把这个当做一个简化的函数定义即可 |
| `mysql_qa/data/JP学科知识问答.csv:1446` | D | 学科 | Python学科,try 异常传递,异常是有传递特性的，这个是异常的机制，在传递过程，任何一个环节都可以捕获，如果不捕获继续向上传递。 举例说明： main-->fn1-->fn2 假如fn2中出现异常，fn2方法中没有捕获，则向上传递至fn2 的调用者fn1 假如fn1也捕获继续向上传递至main，假如main也不捕获就会异常导致程序终止 |
| `mysql_qa/data/JP学科知识问答.csv:1447` | D | 学科 | Python学科,"pycharm打开导航栏 |
| `mysql_qa/data/JP学科知识问答.csv:1452` | D | 学科 | Python学科,"多继承 MRO 父类 属性查找 |
| `mysql_qa/data/JP学科知识问答.csv:1454` | D | 学科 | Python学科,"ubuntu 创建Python虚拟环境 出现错误 |
| `mysql_qa/data/JP学科知识问答.csv:1458` | D | 学科 | Python学科,ubuntu pip 安装包 timeout,"创建文件 |
| `mysql_qa/data/JP学科知识问答.csv:1466` | D | 学科 | JAVA学科,IncompleteElementException,"org.apache.ibatis.builder.IncompleteElementException |
| `mysql_qa/data/JP学科知识问答.csv:1470` | D | 学科 | JAVA学科,套餐列表图片没有办法正常显示,"套餐列表图片没有办法正常显示 |
| `mysql_qa/data/JP学科知识问答.csv:1474` | D | 学科 | JAVA学科,七牛云图片上传成功 图片不回显,"七牛云图片上传成功 图片不回显 |
| `mysql_qa/data/JP学科知识问答.csv:1478` | D | 学科 | JAVA学科,interface not allow null!,"interface not allow null dubboadmin中没有提供者 |
| `mysql_qa/data/JP学科知识问答.csv:1482` | D | 学科 | JAVA学科,表单校验语法报错 () => {},"传智健康-html页面表单校验语法报错 () => {} |
| `mysql_qa/data/JP学科知识问答.csv:1485` | D | 学科 | JAVA学科,xls或者xlsx文件上传失败,"传智健康上传excel的xls或者xlsx文件上传失败 |
| `mysql_qa/data/JP学科知识问答.csv:1489` | D | 学科 | JAVA学科,NoSuchMethodError,"java.lang.NoSuchMethodError: com.google.gson.JsonObject.keySet()Ljava/util/Set; |
| `mysql_qa/data/JP学科知识问答.csv:1493` | D | 学科 | JAVA学科,体检预约成功后不显示预约信息,"体检预约成功后不显示预约信息 |
| `mysql_qa/data/JP学科知识问答.csv:1496` | D | 学科 | JAVA学科,FreeMarker生成html之后，中文乱码,"静态页面生成中文乱码 |
| `mysql_qa/data/JP学科知识问答.csv:1499` | D | 学科 | JAVA学科,在传智健康的PDF报表生成的时候出现找不到华文宋体,"PDF报表生成的时候出现找不到华文宋体 |
| `mysql_qa/data/JP学科知识问答.csv:1502` | D | 学科 | JAVA学科,Timeout 连接zookeeper失败,"1. zookeeper server can not be connected 2. Zookeeper连接失败 |
| `mysql_qa/data/JP学科知识问答.csv:1505` | D | 学科 | JAVA学科,日历展示预约信息，样式出不来,"传智健康项目做日历展示预约信息，样式出不来 |
| `mysql_qa/data/JP学科知识问答.csv:1509` | D | 学科 | JAVA学科,执行生成静态页面之后，页面报错,"执行生成静态页面之后，页面报错 |
| `mysql_qa/data/JP学科知识问答.csv:1513` | D | 学科 | JAVA学科,getOrderSettingByMonth,"getOrderSettingByMonth方法返回的数据只有1-7天导致最后前端页面展示不正确 |
| `mysql_qa/data/JP学科知识问答.csv:1516` | D | 学科 | JAVA学科,套餐详情页面中检查组和检查项的数据都是空的,"checkGroups数组为空数组 |
| `mysql_qa/data/JP学科知识问答.csv:1519` | D | 学科 | JAVA学科,Spring-redis.xml文件配置报错,"Spring-redis.xml文件中beans报红 |
| `mysql_qa/data/JP学科知识问答.csv:1522` | D | 学科 | JAVA学科,Access is denied 拒绝访问 登陆失败,"AccessDeniedException Access is denied 拒绝访问 登陆失败 |
| `mysql_qa/data/JP学科知识问答.csv:1525` | D | 学科 | JAVA学科,做分页查询的时候报空指针异常 检查组分页查询空指针,"com.itheima.service.CheckGroupServise, method: pageQuery, exception: java.lang.NullPointerException: null, dubbo version: 2.6.0, current host: 127.0.0.1 java.lang.Nul …（长行省略；原文件保留全文） |
| `mysql_qa/data/JP学科知识问答.csv:1529` | D | 学科 | JAVA学科,parameterType和resultType区别,"传智健康 mybatis中的parameterType和resultType区别 |
| `mysql_qa/data/JP学科知识问答.csv:1532` | D | 学科 | JAVA学科,传智健康体检预约收不到短信验证码,"传智健康体检预约点击发送验证码后收不到短信验证码 |
| `mysql_qa/data/JP学科知识问答.csv:1535` | D | 学科 | JAVA学科,Spring Boot 请求访问URL页面显示404,"访问URL页面显示404 |
| `mysql_qa/data/JP学科知识问答.csv:1538` | D | 学科 | JAVA学科,找不到文件: Cento 64位.vmdk,"开启此虚拟机需要用到此文件,如果移动了此文件,请提供它的新位置 |
| `mysql_qa/data/JP学科知识问答.csv:1541` | D | 学科 | JAVA学科,SpringBoot无法使用@Runwith注解,"快速构建SpringBoot项目的测试类无法使用@Runwith注解 |
| `mysql_qa/data/JP学科知识问答.csv:1544` | D | 学科 | JAVA学科,Spring Cloud 定义Feign 启动失败,"A bean with that name has already been defined in null and overriding is disabled. |
| `mysql_qa/data/JP学科知识问答.csv:1548` | D | 学科 | JAVA学科,rabbitmq 路由模式,具体参考下:https://www.cnblogs.com/zousc/p/12739504.html |
| `mysql_qa/data/JP学科知识问答.csv:1549` | D | 学科 | Python学科,"input标签中的placeholder  与value的区 |
| `mysql_qa/data/JP学科知识问答.csv:1556` | D | 学科 | Python学科,"python中编码规范网址？ |
| `mysql_qa/data/JP学科知识问答.csv:1558` | D | 老师 | 老师python的规范的网站多少呢","我们最常用的是pep 8 规范，对应的网址是：https://www.python.org/dev/peps/pep-0008/ |
| `mysql_qa/data/JP学科知识问答.csv:1562` | D | 学科 | Python学科,"python 中 in关键词用法 |
| `mysql_qa/data/JP学科知识问答.csv:1567` | D | 学科 | Python学科,flask paginate 怎么使用,"请参考使用文档：https://pythonhosted.org/Flask-paginate/ |
| `mysql_qa/data/JP学科知识问答.csv:1568` | D | 老师 | 如果对使用有疑惑可以再问老师。" |
| `mysql_qa/data/JP学科知识问答.csv:1569` | D | 学科 | JAVA学科,实现购物车加1 减1 会出现数量累加的问题,"当用户手动输入数量失去焦点时，会出现数量累加的问题 |
| `mysql_qa/data/JP学科知识问答.csv:1572` | D | 学科 | JAVA学科,搜索模块批量导入数据到ES,"搜索模块批量导入数据到ES报错-内存溢出 |
| `mysql_qa/data/JP学科知识问答.csv:1575` | D | 学科 | JAVA学科,UnsupportedEncodingException,"java.io.UnsupportedEncodingException: UTF - 8 |
| `mysql_qa/data/JP学科知识问答.csv:1578` | D | 学科 | JAVA学科,consul启动指定错盘符问题,"consul启动时指定盘符不存在错误 |
| `mysql_qa/data/JP学科知识问答.csv:1581` | D | 学科 | JAVA学科,consul服务启动报错,"powerShell启动consul报错 |
| `mysql_qa/data/JP学科知识问答.csv:1584` | D | 学科 | JAVA学科,充吧项目 连接MySQL的10060错误,"充吧项目 连接MySQL的10060错误:Can't connect to MySQL server on '192.168.200.129'(10060) |
| `mysql_qa/data/JP学科知识问答.csv:1587` | D | 学科 | JAVA学科,Mysql驱动问题,"The server time zone value '???ú±ê×??±??' is unrecognized or represents more than one time zone. |
| `mysql_qa/data/JP学科知识问答.csv:1589` | D | 学科 | Python学科,"ssh无法连接远程 |
| `mysql_qa/data/JP学科知识问答.csv:1597` | D | 学科 | JAVA学科,"请问Java基础方面有书籍推荐吗 |
| `mysql_qa/data/JP学科知识问答.csv:1599` | D | 学科 | JAVA学科,"微信支付 |
| `mysql_qa/data/JP学科知识问答.csv:1603` | D | 学科 | JAVA学科,"根据名称或编码查询,在更新数据时如何清空缓存",先根据key删除数据，在重新添加数据到redis |
| `mysql_qa/data/JP学科知识问答.csv:1604` | D | 学科 | JAVA学科,"首页广告轮播图图片不展示 |
| `mysql_qa/data/JP学科知识问答.csv:1608` | D | 学科 | JAVA学科,自己写构造方法和系统默认给出来哪个好,一般使用系统默认的构造方法，如果有需求的话，可以自定义构造方法 |
| `mysql_qa/data/JP学科知识问答.csv:1609` | D | 学科 | JAVA学科,"git推送失败了 |
| `mysql_qa/data/JP学科知识问答.csv:1611` | D | 学科 | JAVA学科,#工具没说在哪里下载啊,工具在资料中有，资料下载地址可以找班主任获取 |
| `mysql_qa/data/JP学科知识问答.csv:1612` | D | 学科 | Python学科,"git仓库创建成功之后,克隆的时候出现没有权限,访问被拒绝等","解决方案:如果使用ssh的地址进行克隆很有可能出现访问被拒绝,这是因为没有配置公钥和私钥 |
| `mysql_qa/data/JP学科知识问答.csv:1614` | D | 学科 | Python学科,"pycharm中解决前端模板语法报红 |
| `mysql_qa/data/JP学科知识问答.csv:1618` | D | 学科 | JAVA学科,"构造方法()里的初始化顺序, 是要按照定义时候的顺序来写吗?",是的.  先写的优先被初始化 |
| `mysql_qa/data/JP学科知识问答.csv:1619` | D | 学科 | JAVA学科,枚举和数组和集合的关系,具体请参考:http://c.biancheng.net/java/110/ |
| `mysql_qa/data/JP学科知识问答.csv:1620` | D | 学科 | JAVA学科,如果方法无返回值，然后里面还用到return;说明什么,说明程序不在执行. 不需要任何返回直接写return;就可以或者.不写这个return;二者都行 |
| `mysql_qa/data/JP学科知识问答.csv:1621` | D | 学科 | JAVA学科,"break,和continue是只能跳出循环吧",是的 用于跳出循环 |
| `mysql_qa/data/JP学科知识问答.csv:1622` | D | 学科 | Python学科,"for 循环 语法格式 |
| `mysql_qa/data/JP学科知识问答.csv:1627` | D | 学生 | item 每次循环返回一个元素值， 这个变量是我们自己定义的，名字你可以随便起名的，推荐见名知意的方式取名字 例如： 我要遍历一个班级的学生 可以这样： for student in students： pass  student 可以明确的让看到代码的人知道 我遍历得到的元素是一个学生对象。更利于代码维护。" |
| `mysql_qa/data/JP学科知识问答.csv:1628` | D | 学科 | Python学科,"虚拟机创建快照 |
| `mysql_qa/data/JP学科知识问答.csv:1631` | D | 学科 | JAVA学科,黑马面面 企业模块添加数据或修改出现乱码,"出现乱码. 说明请求的传递到后台的已经出现乱码. 1.使用request.setCharacterEncoding(""UTF-8"");解决乱码. 2.可以使用过滤器统一解决乱码问题" |
| `mysql_qa/data/JP学科知识问答.csv:1632` | D | 学科 | JAVA学科,SpringBoot中如何把一个自定义类的对象添加到Ioc中,"编写一个自定义类,只需要在类上加上@Component即可声明到Spring的ioc容器中" |
| `mysql_qa/data/JP学科知识问答.csv:1633` | D | 学科 | Python学科,"python中__main__理解 |
| `mysql_qa/data/JP学科知识问答.csv:1636` | D | 学科 | Python学科,"chrome 插件如何下载？ |
| `mysql_qa/data/JP学科知识问答.csv:1639` | D | 老师 | 我需要老师帮忙安装xpath",同学chrome插件需要翻墙才能下载，如果你的可以翻墙 直接下载安装即可，如果不可以同学可以去这个地址搜索下载然后离线安装即可： https://pictureknow.com/extensions |
| `mysql_qa/data/JP学科知识问答.csv:1640` | D | 学科 | JAVA学科,html与jsp文件的区别,"html是静态语言,可以直接在浏览器打开. 而jsp是动态语言需要部署到tomcat上才可以.本身jsp就是一个sevlet" |
| `mysql_qa/data/JP学科知识问答.csv:1641` | D | 学科 | JAVA学科,idea创建maven项目没有src文件夹问题,具体操作可以参考:https://blog.csdn.net/lk142500/article/details/88782116/ |
| `mysql_qa/data/JP学科知识问答.csv:1642` | D | 学科 | JAVA学科,SecureCRT的sftp怎么操作,具体可以参考:https://www.cnblogs.com/wq-9/p/13259622.html |
| `mysql_qa/data/JP学科知识问答.csv:1643` | D | 学科 | JAVA学科,Map集合中如何根据value删除键值对,"首先循环遍历整个Map , 然后比对value值是否和要删除得value值是否一样, 如果一样取出key,将其value删除" |
| `mysql_qa/data/JP学科知识问答.csv:1644` | D | 学科 | JAVA学科,idea中 maven启动控制台中文出现乱码,请查看以下链接: https://www.cnblogs.com/grimm/p/12069026.html |
| `mysql_qa/data/JP学科知识问答.csv:1645` | D | 学科 | JAVA学科,sout回车 为什么不会自动生成输出语句？,在方法里面去写才可以 |
| `mysql_qa/data/JP学科知识问答.csv:1646` | D | 学科 | Python学科,"css 样式修改了，前端不生效？ |
| `mysql_qa/data/JP学科知识问答.csv:1652` | D | 学科 | Python学科,"linux下面怎么使用管理员权限？ |
| `mysql_qa/data/JP学科知识问答.csv:1659` | D | 学科 | Python学科,"导入数据库提示FOREIGNKEY 错误 |
| `mysql_qa/data/JP学科知识问答.csv:1665` | D | 学科 | JAVA学科,为什么要学反射#里反射是做什么用的?,具体可以参考这里：https://blog.csdn.net/weixin_40307206/article/details/101268931 |
| `mysql_qa/data/JP学科知识问答.csv:1666` | D | 学科 | JAVA学科,#控制台会一直打印吗,RuntimeException 是运行时异常，不会一直打印，会一次性把代码运行的错误打印出来 |
| `mysql_qa/data/JP学科知识问答.csv:1667` | D | 学科 | JAVA学科,"搜索服务启动无限报错 |
| `mysql_qa/data/JP学科知识问答.csv:1671` | D | 学科 | JAVA学科,"畅购项目导入starter-canal   pom文件报红 |
| `mysql_qa/data/JP学科知识问答.csv:1677` | D | 学科 | JAVA学科,"畅购添加商品报错 |
| `mysql_qa/data/JP学科知识问答.csv:1681` | D | 学科 | Python学科,"pycharm打了断点，没执行到哪里 |
| `mysql_qa/data/JP学科知识问答.csv:1685` | D | 学科 | Python学科,"pycharm不能用了 |
| `mysql_qa/data/JP学科知识问答.csv:1690` | D | 老师 | 老师我ubuntu里的pycharm到期了，怎么破解呀",请同学可以参考下面的链接：https://www.shuopython.com/archives/2339  或者自行百度查找 |
| `mysql_qa/data/JP学科知识问答.csv:1691` | D | 学科,课程 | Python学科,"解锁后面的课程 |
| `mysql_qa/data/JP学科知识问答.csv:1692` | D | 课程 | 如何解锁后面的课程 |
| `mysql_qa/data/JP学科知识问答.csv:1693` | D | 学科,课程 | 解锁后面的学科","1. 正常情况我们都是通过阶段作业后自动解锁后面课程，主要是检查你当前阶段课程学习的怎么样 |
| `mysql_qa/data/JP学科知识问答.csv:1694` | D | 课程 | 2. 如果同学有特殊情况，例如我工作马上需要，或者我毕业论文要用到等 请同学跟班主任沟通申请解锁课程" |
| `mysql_qa/data/JP学科知识问答.csv:1695` | D | 学科 | Python学科,"python 中pycharm打断点问题 |
| `mysql_qa/data/JP学科知识问答.csv:1700` | D | 学科 | JAVA学科,切割字符中，特殊符号的切割,"字符串切割特殊字符时，需要进行转义比如split(""\#""),加上转义就可以了" |
| `mysql_qa/data/JP学科知识问答.csv:1701` | D | 学科 | JAVA学科,"请问可以帮我,看看简历可以吗?",那你把简历发给我吧 |
| `mysql_qa/data/JP学科知识问答.csv:1702` | D | 学科 | JAVA学科,"split切割传入的字符串 也分中英文状态下吧 |
| `mysql_qa/data/JP学科知识问答.csv:1704` | D | 学科 | JAVA学科,idea中#的作用,可以参考这个：https://www.cnblogs.com/signheart/p/4d2058ae687f9a29680c070de85f7fbe.html |
| `mysql_qa/data/JP学科知识问答.csv:1705` | D | 学科 | JAVA学科,快速生产方法的返回值#这有什么作用,ctrl+alt+v可以为当前的方法或者接收道的变量添加返回值 ，可以参考idea的快捷键使用：https://blog.csdn.net/qq_38963960/article/details/89552704 |
| `mysql_qa/data/JP学科知识问答.csv:1706` | D | 学科 | JAVA学科,"idea登录不了，显示已过期，需要激活使用 |
| `mysql_qa/data/JP学科知识问答.csv:1709` | D | 学科 | JAVA学科,#定义是什么呢，我输入成agrn不会报错，也可以正常打印,args可以理解为是一个变量名称，就是main方法上接收的变量名。 |
| `mysql_qa/data/JP学科知识问答.csv:1710` | D | 学科 | Python学科,"京东图书案例，scrapy爬取不到数据 |
| `mysql_qa/data/JP学科知识问答.csv:1712` | D | 学科 | Python学科,"ssh链接远程密码 |
| `mysql_qa/data/JP学科知识问答.csv:1715` | D | 学科 | Python学科,django安装的django-redis目录不对怎么处理,出现这个问题，就是同学你使用的python环境问题，很大的可能你安装django-redis的环境与你自己pycharm中使用的不是一个环境，如果使用虚拟环境，请先切换到对应的虚拟环境后再安装，如果你使用系统环境，请确认你使用的python版本是否正确。使用正确的环境才可能正确安装 |
| `mysql_qa/data/JP学科知识问答.csv:1716` | D | 学科 | Python学科,"pycharm （社区）官网下载不了 |
| `mysql_qa/data/JP学科知识问答.csv:1721` | D | 学科 | JAVA学科,mybatis查询插入多个参数,"<a  target=""_blank"" href=""https://www.cnblogs.com/xiaoshen666/p/11117967.html"">该链接有答案</a>" |
| `mysql_qa/data/JP学科知识问答.csv:1722` | D | 学科 | Python学科,pycharm run 的时候，显示的是运行过的任务（文件）,"{""answerText"":""43fad2e4-4f24-41b8-8644-e2f01ff47d6f"",""answerType"":""NEWS""}" |
| `mysql_qa/data/JP学科知识问答.csv:1723` | D | 学科 | Python学科,pycharm中如何分屏展示多个python文件,"{""answerText"":""cb123d06-6be9-4073-a457-3e8c5a0084bf"",""answerType"":""NEWS""}" |
| `mysql_qa/data/JP学科知识问答.csv:1724` | D | 学科 | JAVA学科,反射的作用,"JAVA反射机制是在运行状态中，对于任意一个类，都能够知道这个类的所有属性和方法；对于任意一个对象，都能够调用它的任意一个方法；这种动态获取的以及动态调用对象的方法的功能称为java语言的反射机制。主要用途： |
| `mysql_qa/data/JP学科知识问答.csv:1726` | D | 学科 | JAVA学科,v-model是什么,"v-model就是vue的双向绑定的指令,能将页面上控件输入的值同步更新到相关绑定的data属性,也会在更新data绑定属性时候,更新页面上输入控件的值" |
| `mysql_qa/data/JP学科知识问答.csv:1727` | D | 学科 | JAVA学科,el表达式,是一种在JSP页面获取数据的简单方式 |
| `mysql_qa/data/JP学科知识问答.csv:1728` | D | 学科 | JAVA学科,indexOf和substring,该链接有答案 |
| `mysql_qa/data/JP学科知识问答.csv:1729` | D | 学科 | Python学科,"python 中 % 取余符号 |
| `mysql_qa/data/JP学科知识问答.csv:1731` | D | 学科 | Python学科,"思维导图安装 |
| `mysql_qa/data/JP学科知识问答.csv:1735` | D | 学科 | Python学科,"调整学习计划 |
| `mysql_qa/data/JP学科知识问答.csv:1737` | D | 学科,老师 | JAVA学科,"老师，CRT安装后没有安装成功，只是弹出了一些文本框 |
| `mysql_qa/data/JP学科知识问答.csv:1740` | D | 学科 | JAVA学科,"畅购支付回调无法完成内网映射 |
| `mysql_qa/data/JP学科知识问答.csv:1741` | D | 课程 | #内网映射工具 现在不能使用了吗",目前课程中提供的内网穿透失效了，现在可以使用这个https://my.oschina.net/u/3514138/blog/2222980 |
| `mysql_qa/data/JP学科知识问答.csv:1742` | D | 学科 | JAVA学科,"VNW 虚拟机安装,没有密钥",密钥参考：https://www.cnblogs.com/vhhi/p/10202204.html |
| `mysql_qa/data/JP学科知识问答.csv:1743` | D | 学科 | JAVA学科,"数字类#集合，排序使用什么方法？ |
| `mysql_qa/data/JP学科知识问答.csv:1745` | D | 学科 | Python学科,python -m,"python xxx.py |
| `mysql_qa/data/JP学科知识问答.csv:1750` | D | 学科 | Python学科,Non-ASCII character '\xe5' in,可以在python文件最上方加上  # -*- coding:UTF-8 -*-  这句话 |
| `mysql_qa/data/JP学科知识问答.csv:1751` | D | 学科 | Python学科,回车和换行符,参考博客：https://www.jianshu.com/p/95f556ec2667 |
| `mysql_qa/data/JP学科知识问答.csv:1752` | D | 学科 | JAVA学科,400错误,"很多同学出现的问题都是在以后接口测试的过程中经常出现400错误 |
| `mysql_qa/data/JP学科知识问答.csv:1755` | D | 学科 | JAVA学科,微信支付jar包安装步骤,"在加入微信支付的依赖之后，总是下载不下来微信支付的依赖，所以需要手动安装 |
| `mysql_qa/data/JP学科知识问答.csv:1758` | D | 学科 | JAVA学科,IllegalStateException,"Caused by: java.lang.IllegalStateException: availableProcessors is already set to [4], rejecting [4] |
| `mysql_qa/data/JP学科知识问答.csv:1761` | D | 学科 | JAVA学科,InstantiationException,"Error invoking SqlProvider method (tk.mybatis.mapper.provider.base.BaseSelectProvider.dynamicSQL) |
| `mysql_qa/data/JP学科知识问答.csv:1764` | D | 学科 | JAVA学科,server authentication,"登录认证失败cannot retry due to server authentication, in streaming mode |
| `mysql_qa/data/JP学科知识问答.csv:1767` | D | 学科 | JAVA学科,畅购结算页面点击购买数量+加号时，数量会增加2,"在结算页面点击+时，数量会加2，后台会调用两次请求 |
| `mysql_qa/data/JP学科知识问答.csv:1770` | D | 学科 | JAVA学科,"去登陆页面,重定向次数过多","去登陆页面,一直重定向重定向次数过多登录页面无法访问 |
| `mysql_qa/data/JP学科知识问答.csv:1773` | D | 学科 | JAVA学科,库存没有回滚,"测试的时候发现如果出现异常，库存并没有回滚 |
| `mysql_qa/data/JP学科知识问答.csv:1776` | D | 学科 | JAVA学科,FeignException,"Caused by: feign.FeignException: status 404 reading SkuFeignClient#findSkusBySpuId() |
| `mysql_qa/data/JP学科知识问答.csv:1779` | D | 学科 | JAVA学科,跳转支付页面报错,"报ClassCastException异常 |
| `mysql_qa/data/JP学科知识问答.csv:1783` | D | 学科 | JAVA学科,"加入购物车时, 抛出空指针异常","在通过postman来测试添加购物车接口时, 发现后端报错NullPointerException ; |
| `mysql_qa/data/JP学科知识问答.csv:1786` | D | 学科 | JAVA学科,头部携带的令牌重复的问题,"网关路径跳转到具体微服务需要携带令牌，但有时会出现头部携带的令牌重复的问题 |
| `mysql_qa/data/JP学科知识问答.csv:1789` | D | 学科 | JAVA学科,HttpRetryException,"Caused by: java.net.HttpRetryException: cannot retry due to server authentication, in streaming mode |
| `mysql_qa/data/JP学科知识问答.csv:1792` | D | 学科 | JAVA学科,为什么第三天和第九天生成jwt的方式不一样,"为什么第三天和第九天生成jwt的方式不一样 |
| `mysql_qa/data/JP学科知识问答.csv:1795` | D | 学科 | JAVA学科,携带令牌访问资源服务出错报错 401,"携带令牌访问资源服务出错 |
| `mysql_qa/data/JP学科知识问答.csv:1798` | D | 学科 | JAVA学科,UnsatisfiedDependencyException,"Error creating bean with name 'albumServiceImpl': Unsatisfied dependency expressed through field 'brandMapper' |
| `mysql_qa/data/JP学科知识问答.csv:1801` | D | 学生,学科 | JAVA学科,nginx出现404,"商品详情页生成后需要部署 到nginx中，学生访问经常出现404 |
| `mysql_qa/data/JP学科知识问答.csv:1804` | D | 学科 | JAVA学科,静态资源在前端控制台加载时报404,"在访问购物车 , 订单模块时, 访问不到静态资源 , 页面报错404 ; |
| `mysql_qa/data/JP学科知识问答.csv:1807` | D | 学科 | JAVA学科,IllegalArgumentException,"Caused by: java.lang.IllegalArgumentException: mapper [categoryName] of different type, current_type [text], merged_type [keyword] |
| `mysql_qa/data/JP学科知识问答.csv:1810` | D | 学科 | JAVA学科,rabbitmq连接不上,"启动服务报rabbitmq服务连接不上 |
| `mysql_qa/data/JP学科知识问答.csv:1815` | D | 学科 | JAVA学科,jwtAccessTokenConverter'创建失败,"jwtAccessTokenConverter'创建失败，空指针异常 |
| `mysql_qa/data/JP学科知识问答.csv:1818` | D | 学科 | JAVA学科,访问某个路径会包401未授权,"自定义路径过滤器实现后，访问某个路径会包401未授权 |
| `mysql_qa/data/JP学科知识问答.csv:1821` | D | 学科 | JAVA学科,秒杀时间段不显示,"秒杀页面时间段不显示moment.min.js识别不到 |
| `mysql_qa/data/JP学科知识问答.csv:1824` | D | 学科 | JAVA学科,fescar-server 启动闪退,"fescar-server 在启动时 , 点击 fescar-server.bat时 , 出现闪退 ; |
| `mysql_qa/data/JP学科知识问答.csv:1827` | D | 学科 | JAVA学科,lombok集成之后，添加@Slf4j报红,"添加@Slf4j报红 |
| `mysql_qa/data/JP学科知识问答.csv:1828` | D | 学生 | 很多学生在进行lombok集成之后，添加@Slf4j报红 |
| `mysql_qa/data/JP学科知识问答.csv:1831` | D | 学科 | JAVA学科,没有队列boot_queue,"No queue ‘boot_queue’没有队列boot_queue |
| `mysql_qa/data/JP学科知识问答.csv:1835` | D | 学科 | JAVA学科,"Springboot启动失败,加载失败Environment","Causedby: org.springframework.beans.factory.NoSuchBeanDefinitionException: No qualifying bean of type 'org.springframework.core.env.Environment' available |
| `mysql_qa/data/JP学科知识问答.csv:1839` | D | 学科 | JAVA学科,unknown POSIX error,"rabbitmq 【ERROR: epmd error for host ""192"":badarg (unknown POSIX error)】 |
| `mysql_qa/data/JP学科知识问答.csv:1843` | D | 学科 | JAVA学科,"通过网关访问,路径正确,访问结果404","通过Gateway访问微服务页面显示Whitelabel Error Page |
| `mysql_qa/data/JP学科知识问答.csv:1846` | D | 学科 | JAVA学科,TransportException,"Cannot execute request on any known server |
| `mysql_qa/data/JP学科知识问答.csv:1849` | D | 学科 | JAVA学科,rabbitMQ连接不上,"SocketTimeoutException |
| `mysql_qa/data/JP学科知识问答.csv:1852` | D | 学科 | JAVA学科,lombok无法安装,"IDEA上搜索不到Lombok，无法进行安装 |
| `mysql_qa/data/JP学科知识问答.csv:1855` | D | 学科 | JAVA学科,EurekaServer高可用环境搭建的时候报错,"java.lang.IllegalArgumentException: Schema specific part is opaque |
| `mysql_qa/data/JP学科知识问答.csv:1858` | D | 学科 | JAVA学科,SpringCloud通过Ribbon远程调用服务报错,"IllegalStateException:No instances available for user-service |
| `mysql_qa/data/JP学科知识问答.csv:1861` | D | 学科 | JAVA学科,springboot中遇到不能返回页面，只返回字符串。,"不能返回页面，只返回字符串。 |
| `mysql_qa/data/JP学科知识问答.csv:1864` | D | 学科 | JAVA学科,授权码模式获取jwt令牌报错,"解决办法如下: |
| `mysql_qa/data/JP学科知识问答.csv:1866` | D | 学科 | JAVA学科,"LocalDateTime不能直接实例化不能直接实例化 |
| `mysql_qa/data/JP学科知识问答.csv:1868` | D | 学科 | JAVA学科,idea一直报错 java: 程序包context不存在,将工程复制到一个新的目录下从新导入下工程.再试试 |
| `mysql_qa/data/JP学科知识问答.csv:1869` | D | 学科,老师 | JAVA学科,老师的案例打开报错,具体报的是什么错误信息. 截图看下 |
| `mysql_qa/data/JP学科知识问答.csv:1870` | D | 学科 | JAVA学科,char类型的数组怎么转成String类型的数组,具体请参考这个帖子: https://www.cnblogs.com/cdsj/articles/5895031.html |
| `mysql_qa/data/JP学科知识问答.csv:1871` | D | 学科 | JAVA学科,CRT注册失败,资料里面有注册机. 使用下就行了 |
| `mysql_qa/data/JP学科知识问答.csv:1872` | D | 学科 | JAVA学科,changgou_web模块 是干什么得,changgou_web模块是前端用户展示的页面服务 |
| `mysql_qa/data/JP学科知识问答.csv:1873` | D | 学科 | JAVA学科,jdk配置失败怎么回事,按照视频在一步一步配置一遍. |
| `mysql_qa/data/JP学科知识问答.csv:1874` | D | 学科 | Python学科,"Mysql grand 授权详解 |
| `mysql_qa/data/JP学科知识问答.csv:1920` | D | 学科 | Python学科,"windows 提示不是内部或外部命令 |
| `mysql_qa/data/JP学科知识问答.csv:1927` | D | 学科 | JAVA学科,handleCurrentChange,"Property or method ""handleCurrentChange"" is not defined |
| `mysql_qa/data/JP学科知识问答.csv:1930` | D | 学科 | JAVA学科,TemplateCode is mandatory,"com.aliyuns.exception.ClientException:MissingTeplateCode:TemplateCode is mandatory for this action. |
| `mysql_qa/data/JP学科知识问答.csv:1934` | D | 学科 | JAVA学科,BeanCreationException,"org.springframework.beans.factory.BeanCreationException |
| `mysql_qa/data/JP学科知识问答.csv:1938` | D | 学科 | JAVA学科,valid hostname,"java.lang.IllegalStateException: Request URI does not contain a valid hostname 注意服务名不能写下滑线 |
| `mysql_qa/data/JP学科知识问答.csv:1941` | D | 学科 | JAVA学科,fescar-server,"com.alibaba.fescar.common.exception.FrameworkException: can not connect to fescar-server. |
| `mysql_qa/data/JP学科知识问答.csv:1944` | D | 学科 | JAVA学科,RetryableException,"feign.RetryableException: cannot retry due to redirection, in streaming mode executing POST |
| `mysql_qa/data/JP学科知识问答.csv:1947` | D | 学科 | JAVA学科,获取jwt只能用localhost不能用127.0.0.1,"访问127.0.0.1:8001/api/oauth/login获取jti，cookie的时候。可以返回正确的Result,在redis中也有jwt生成，但是没有cookie,但是使用localhost就正常获取cookie |
| `mysql_qa/data/JP学科知识问答.csv:1950` | D | 学科 | JAVA学科,畅购连接数据库提示1251,"畅购 远程连接docker容器中，MySQL数据库，连接不上 |
| `mysql_qa/data/JP学科知识问答.csv:1953` | D | 学科 | JAVA学科,添加购物测时报错,"添加购物测时报Unable to connect to localhost:6379 |
| `mysql_qa/data/JP学科知识问答.csv:1956` | D | 学科 | JAVA学科,申请令牌测试的时候报错401,"在测试时候postman 返回错误信息为{ |
| `mysql_qa/data/JP学科知识问答.csv:1962` | D | 学科 | JAVA学科,数据库拒绝连接,"解决办法如下: |
| `mysql_qa/data/JP学科知识问答.csv:1964` | D | 学科 | JAVA学科,CartFeign#add404或者500,"添加购物车经常出现CartFeign#add（String，Integer）404或者500 |
| `mysql_qa/data/JP学科知识问答.csv:1967` | D | 学科 | JAVA学科,创建数组会分配内存，如果程序中创建数组然后删除，内存会清理吗,线程结束后，jvm会自动进行垃圾回收。回收内存 |
| `mysql_qa/data/JP学科知识问答.csv:1968` | D | 学科 | JAVA学科,带参数的方法定义的格式中小括号里能只写变量名吗,不可以。定义方法的时候，必须是 （类型  参数名称） |
| `mysql_qa/data/JP学科知识问答.csv:1969` | D | 学科 | JAVA学科,JDK在哪里可以下载呢,在资料当中已经提供好了JDK，在day01天的资料中，如果没有资料信息，请联系班主任 |
| `mysql_qa/data/JP学科知识问答.csv:1970` | D | 学科 | Python学科,"vmware ubuntu 调整磁盘大小 |
| `mysql_qa/data/JP学科知识问答.csv:1973` | D | 学科 | Python学科,"键盘是否属于计算机一部分 |
| `mysql_qa/data/JP学科知识问答.csv:1976` | D | 学科 | JAVA学科,collection的remove方法得介绍,Collection的remove适合于非遍历情况下的删除，直接调用底层自己实现的remove方法，但是因为对底层实现的不了解，所以当其在遍历情况下，将导致异常或者BUG，比如在ArrayList中，直接删除元素后，所有之后的元素会向前移一位，如果不考虑清楚，则可能会遗漏若干个对象的判断，而Iterator的remove方法是由底层各个实 …（长行省略；原文件保留全文） |
| `mysql_qa/data/JP学科知识问答.csv:1977` | D | 学科 | JAVA学科,网页端不能缓存视频吗,不可以得， 只有app端可以缓存 |
| `mysql_qa/data/JP学科知识问答.csv:1978` | D | 学科 | Python学科,"python中子类不能获取父类__init__中的属性 |
| `mysql_qa/data/JP学科知识问答.csv:1980` | D | 学科,老师 | Python学科,老师，有可以恢复移动硬盘数据的方法吗？,有一款软件工具 diskgenius，不能保证可以完全恢复，如果不是很重要的数据，丢一些无所谓，可以考虑使用，如果是重要的数据，建议同学自己找专门的数据恢复的店进行恢复 |
| `mysql_qa/data/JP学科知识问答.csv:1981` | D | 学科 | Python学科,"pycharm 哪里下载？ |
| `mysql_qa/data/JP学科知识问答.csv:1983` | D | 学科 | Python学科,如何打开虚拟机,"打开别人提供的好的虚拟机环境，请同学先下载安装VMware 软件 然后再请参考下面的连接中的2个文档：链接：https://pan.baidu.com/s/1gPnl5GX2YmnKrTCCWI6xZw |
| `mysql_qa/data/JP学科知识问答.csv:1985` | D | 学科 | JAVA学科,Java中变量与常量的区别是什么?,常量是不可改变的.变量是可以在程序运行过程中发生改变的. |
| `mysql_qa/data/JP学科知识问答.csv:1986` | D | 学科 | JAVA学科,IDEA中设置浏览器打开选项,请参考如下:https://jingyan.baidu.com/article/59703552bee84f8fc1074051.html |
| `mysql_qa/data/JP学科知识问答.csv:1987` | D | 学科 | JAVA学科,javac不是内部或外部命令，也不是可运行的程序或批处理文件,这个是代表Java得环境变量配置有误，仔细检查下环境变量 |
| `mysql_qa/data/JP学科知识问答.csv:1988` | D | 学科 | JAVA学科,"eureka中的ip的不是localhost而是电脑名称 |
| `mysql_qa/data/JP学科知识问答.csv:1990` | D | 学科 | JAVA学科,mybatis获取XML配置文件地址的时候获取不到,检查xml所在得包是什么结构得。xml所在得包应该是a/b/c这种，而不是a.b.c |
| `mysql_qa/data/JP学科知识问答.csv:1991` | D | 学科 | JAVA学科,mac笔记本配置jdk环境,具体参考：https://jingyan.baidu.com/article/7f766daffd99354101e1d095.html |
| `mysql_qa/data/JP学科知识问答.csv:1992` | D | 学科 | Python学科,"32位电脑是否可以安装pycharm |
| `mysql_qa/data/JP学科知识问答.csv:1996` | D | 学科 | Python学科,"jupyter 要安装到windows还是ubuntu |
| `mysql_qa/data/JP学科知识问答.csv:1998` | D | 学科 | Python学科,ch系数模型评估,https://www.cnblogs.com/xingnie/p/10334572.html 同学可以参考下这个博客 里面相对不错 |
| `mysql_qa/data/JP学科知识问答.csv:1999` | D | 学科 | Python学科,"pycharm中如何设置console相关属性 |
| `mysql_qa/data/JP学科知识问答.csv:2001` | D | 学科 | JAVA学科,使用分页插件查数据时，跳转页面只展示数据没有前端页面效果,"第一: 检查下是否配置试图解析器,  第二. 看下Controller上面的注解是@Controller 还是 @RestController. 如果是 @RestController的话返回值会当做json展示" |
| `mysql_qa/data/JP学科知识问答.csv:2002` | D | 学科 | JAVA学科,java中String和char的区别是什么?,具体区别详情请参考:https://blog.csdn.net/qauchangqingwei/article/details/80831797 |
| `mysql_qa/data/JP学科知识问答.csv:2003` | D | 学科 | JAVA学科,"装饰者模式 |
| `mysql_qa/data/JP学科知识问答.csv:2005` | D | 学科,老师 | JAVA学科,在学习springmvc框架的入门案例中，找不到出错的问题,如果程序在运行过程中出现问题，首先将错误信息复制，使用百度进行查找，可以多参考几个帖子，根据网上给出的思路，尝试解决问题，这样可以锻炼自己解决问题的能力，如果还是未解决，可以在线答疑，找老师帮忙解决 |
| `mysql_qa/data/JP学科知识问答.csv:2006` | D | 学科 | JAVA学科,"证书协议问题 |
| `mysql_qa/data/JP学科知识问答.csv:2010` | D | 学科,老师 | JAVA学科,老师，为什么我的psvm回车生成不了主方法,可能是idea没有加载完成，可以等待会在重新输入psvm，或者是不小心设置了什么东西，可以尝试重置设置，在输入psvm进行测试 |
| `mysql_qa/data/JP学科知识问答.csv:2011` | D | 学科 | JAVA学科,#程序包#不存在,https://www.pianshen.com/article/28591577403/  参考该方法进行解决 |
| `mysql_qa/data/JP学科知识问答.csv:2012` | D | 学科 | JAVA学科,不同模块下的类无法导入,不同模块下的类是无法导入的，只能在同模块才能导入类 |
| `mysql_qa/data/JP学科知识问答.csv:2013` | D | 学科 | JAVA学科,Lambda表达式在JDK8之后才能使用吗,是的，jdk1.8的新特性 |
| `mysql_qa/data/JP学科知识问答.csv:2014` | D | 学科 | JAVA学科,classpath 具体指哪里呢,"classpath是指 WEB-INF文件夹下的classes目录 |
| `mysql_qa/data/JP学科知识问答.csv:2018` | D | 学科 | JAVA学科,Tomcat在docker里下载什么版本呢？,Tomcat在docker里下载什么版本需要根据当前项目需求决定，目前一般使用tomcat8 |
| `mysql_qa/data/JP学科知识问答.csv:2019` | D | 学科 | JAVA学科,maven deploy,该命令是将maven的web项目部署到远程服务器 |
| `mysql_qa/data/JP学科知识问答.csv:2020` | D | 学科,老师 | JAVA学科,"老师你好，问一下# |
| `mysql_qa/data/JP学科知识问答.csv:2021` | D | 老师 | 老师我想我问下#怎么调",getIndex这个是你在其他类中调用的还是在你导入的jar包中调用的，首先要确保该方法是在哪里调用 |
| `mysql_qa/data/JP学科知识问答.csv:2022` | D | 学科 | JAVA学科,"还是jsp调用摄像头拍照的事情 |
| `mysql_qa/data/JP学科知识问答.csv:2025` | D | 学科,老师 | JAVA学科,"老师，帮看看crt装上用不了 |
| `mysql_qa/data/JP学科知识问答.csv:2026` | D | 老师 | 老师帮看看crt连不上",crt连接不上：1，先查看本地和远程是否能ping通。2，关闭本地的防护墙。3，关闭远程服务的防火墙。4，保证本地和远程能ping在进行连接。 |
| `mysql_qa/data/JP学科知识问答.csv:2027` | D | 学科 | JAVA学科,#配置web,具体可以参考这个：https://www.cnblogs.com/sam-uncle/p/8676529.html |
| `mysql_qa/data/JP学科知识问答.csv:2028` | D | 学科 | JAVA学科,这个初始的16怎么理解呀,"StringBuilder里面维护了一个char数组，默认数组长度为16，append(""123456"")，那就还可以再拼接10个长度的字符，满了之后会重新生成数组，如果你能大概知道你要拼接字符串是多长，最好指定长度，避免内部频繁扩容" |
| `mysql_qa/data/JP学科知识问答.csv:2029` | D | 学科 | JAVA学科,java代码运行显示数据库拒绝访问和jdk有关系吗？,显示数据库拒绝访问，这个是和jdk没有关系，你可以尝试：1，看下数据库是否启动，2，如果数据在远程，查看本地和远程是否通信。 |
| `mysql_qa/data/JP学科知识问答.csv:2030` | D | 学科 | JAVA学科,在磁盘中无法新建文本文档,1，首先查看是不是磁盘权限问题，2，确认登录的用户有没有创建文本的权限 |
| `mysql_qa/data/JP学科知识问答.csv:2031` | D | 学科 | Python学科,"区块链第七阶段货币网址打不开 |
| `mysql_qa/data/JP学科知识问答.csv:2035` | D | 学科 | Python学科,"代码下面显示灰色的波浪线是什么原因？ |
| `mysql_qa/data/JP学科知识问答.csv:2041` | D | 学科 | JAVA学科,static静态方法使用非静态变量,"在外部调用静态方法时，可以使用""类名.方法名""的方式，也可以使用""对象名.方法名""的方式。而实例方法只有后面这种方式。也就是说，调用静态方法可以无需创建对象。 |
| `mysql_qa/data/JP学科知识问答.csv:2044` | D | 学科 | Python学科,"f-string格式输出保留数字 |
| `mysql_qa/db/mysql_client.py:37` | B | jpkb | CREATE TABLE IF NOT EXISTS jpkb ( |
| `mysql_qa/db/mysql_client.py:58` | B | jpkb | sql = 'INSERT INTO jpkb (subject_name, question, answer) VALUES (%s, %s, %s)' |
| `mysql_qa/db/mysql_client.py:59` | B | 学科 | res = self.cursor.execute(sql, (row['学科名称'], row['问题'], row['答案'])) |
| `mysql_qa/db/mysql_client.py:72` | B | jpkb | self.cursor.execute('SELECT question FROM jpkb') |
| `mysql_qa/db/mysql_client.py:92` | B | jpkb | self.cursor.execute("SELECT answer FROM jpkb WHERE question=%s", (question,)) |
| `mysql_qa/db/mysql_client.py:118` | B | edurag,学科 | # data_dir = r'E:\HZAI05\01_edurag\edu_rag\mysql_qa\data\JP学科知识问答.csv' |
| `new_main.py:219` | B | 学科 | print(f"支持的学科类别：{config.VALID_SOURCES}") |
| `new_main.py:229` | B | 学科 | source_filter = input(f"请输入学科类别 ({'/'.join(config.VALID_SOURCES)}) (直接回车默认不过滤): ").strip() |
| `new_main.py:231` | B | 学科 | logger.warning(f"main 无效的学科类别 '{source_filter}'，将不过滤") |
| `rag_qa/classify_data/model_generic_5000.json:1` | D | 通用知识 | {"query": "1024乘以768等于多少？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:2` | D | 通用知识 | {"query": "Python如何读取CSV文件？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:3` | D | 通用知识 | {"query": "解释一下什么是RESTful API。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:4` | D | 专业咨询,学科,课程 | {"query": "AI学科的最新课程安排是什么时候？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:5` | D | 专业咨询 | {"query": "Java零基础入门班学费是多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:6` | D | 通用知识 | {"query": "数据库三大范式是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:7` | D | 学生,通用知识 | {"query": "写一个SQL查询，找出'students'表中所有姓'张'的学生。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:8` | D | 专业咨询,课程 | {"query": "测试开发课程包含自动化测试工具的使用吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:9` | D | 专业咨询,老师,课程 | {"query": "大数据课程的老师背景如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:10` | D | 通用知识 | {"query": "5的阶乘是多少？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:11` | D | 通用知识 | {"query": "什么是Docker？它和虚拟机的区别？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:12` | D | 专业咨询,课程 | {"query": "运维课程有没有关于Kubernetes的内容？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:13` | D | 专业咨询,课程 | {"query": "报名Python全栈课程有什么优惠活动？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:14` | D | 通用知识 | {"query": "用Java写一个冒泡排序算法。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:15` | D | 专业咨询 | {"query": "请问贵校的教学点在哪里？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:16` | D | 通用知识 | {"query": "什么是HTTPS？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:17` | D | AI课程,专业咨询 | {"query": "AI课程的项目是独立完成还是小组合作？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:18` | D | 专业咨询,课程 | {"query": "前端课程学习周期大概多久？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:19` | D | 通用知识 | {"query": "计算 1/3 + 1/6", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:20` | D | 通用知识 | {"query": "解释下Python的GIL（全局解释器锁）。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:21` | D | Java课程,专业咨询,老师 | {"query": "Java课程的授课老师是谁？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:22` | D | 专业咨询 | {"query": "大数据分析需要学习哪些编程语言？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:23` | D | 通用知识 | {"query": "生成一个长度为10的随机密码，包含大小写字母和数字。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:24` | D | 通用知识 | {"query": "什么是敏捷开发？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:25` | D | 专业咨询,课程 | {"query": "测试课程结束后会颁发证书吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:26` | D | 专业咨询,课程 | {"query": "运维课程的学费支持分期支付吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:27` | D | 通用知识 | {"query": "1到100所有整数的和是多少？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:28` | D | 通用知识 | {"query": "解释TCP的三次握手过程。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:29` | D | 专业咨询 | {"query": "AI专业的就业前景怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:30` | D | 专业咨询 | {"query": "学习Java需要准备什么样的电脑配置？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:31` | D | 通用知识 | {"query": "Python的装饰器是什么原理？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:32` | D | 通用知识 | {"query": "写一个函数判断一个数是否是素数。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:33` | D | 专业咨询,课程 | {"query": "大数据课程会涉及到Hadoop和Spark吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:34` | D | 专业咨询,课程 | {"query": "你们提供线上的运维课程吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:35` | D | 通用知识 | {"query": "什么是面向对象编程的三大特性？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:36` | D | 专业咨询,课程 | {"query": "测试课程的报名截止日期是什么时候？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:37` | D | 通用知识 | {"query": "平方根的计算方法有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:38` | D | 通用知识 | {"query": "Java和Python哪个更适合初学者？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:39` | D | AI课程,专业咨询,教育 | {"query": "AI课程的学费可以申请教育贷款吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:40` | D | 专业咨询,课程 | {"query": "请介绍一下Python Web开发课程的项目案例。", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:41` | D | 通用知识 | {"query": "什么是二分查找算法？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:42` | D | 通用知识 | {"query": "写一段JavaScript代码实现页面元素的隐藏和显示。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:43` | D | 专业咨询 | {"query": "大数据专业毕业后可以从事哪些岗位？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:44` | D | 专业咨询,课程 | {"query": "测试课程有没有晚班？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:45` | D | 通用知识 | {"query": "解释Linux常用命令ls, cd, mkdir的作用。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:46` | D | 专业咨询,课程 | {"query": "运维课程对学历有要求吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:47` | D | AI课程,专业咨询 | {"query": "AI课程使用的主要编程语言是什么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:48` | D | 通用知识 | {"query": "斐波那契数列的第10项是多少？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:49` | D | 通用知识 | {"query": "什么是DNS解析？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:50` | D | 专业咨询,课程 | {"query": "Java后端开发课程会教Spring Boot吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:51` | D | 专业咨询,课程 | {"query": "大数据课程需要自带电脑上课吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:52` | D | 通用知识 | {"query": "请给我推荐几本学习Python的经典书籍。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:53` | D | 专业咨询,课程 | {"query": "测试开发课程的课时是如何安排的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:54` | D | 通用知识 | {"query": "运维工程师的主要职责是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:55` | D | 专业咨询,老师 | {"query": "AI专业的老师有工业界经验吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:56` | D | 专业咨询,培训 | {"query": "Java培训一般需要多长时间？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:57` | D | 通用知识 | {"query": "什么是哈希表？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:58` | D | 通用知识 | {"query": "写一个正则表达式匹配有效的邮箱地址。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:59` | D | 专业咨询,课程 | {"query": "大数据分析课程会用到哪些工具？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:60` | D | 专业咨询,课程 | {"query": "运维课程有没有重听的机会？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:61` | D | 通用知识 | {"query": "解释一下并发和并行的区别。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:62` | D | 专业咨询,课程 | {"query": "测试课程的教材是自己购买还是学校提供？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:63` | D | AI课程,专业咨询 | {"query": "AI课程毕业需要完成什么样的作品？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:64` | D | 通用知识 | {"query": "解方程：x^2 - 5x + 6 = 0", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:65` | D | 通用知识 | {"query": "Python中的列表和元组有什么不同？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:66` | D | Java课程,专业咨询 | {"query": "Java课程包含数据库操作的内容吗？比如MySQL？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:67` | D | 专业咨询,课程 | {"query": "大数据课程对数学基础要求高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:68` | D | 通用知识 | {"query": "生成5个不同的1到10之间的随机整数。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:69` | D | 专业咨询 | {"query": "测试开发学习路线是怎样的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:70` | D | 通用知识 | {"query": "什么是云计算？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:71` | D | 专业咨询,课程 | {"query": "运维课程有没有针对网络安全的讲解？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:72` | D | AI课程,专业咨询 | {"query": "AI课程是不是很难学？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:73` | D | 通用知识 | {"query": "Python代码缩进错误会怎么样？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:74` | D | 通用知识 | {"query": "解释HTTP和HTTPS的主要区别。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:75` | D | Java课程,专业咨询 | {"query": "Java课程会讲解JVM调优吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:76` | D | 专业咨询,师资 | {"query": "大数据专业的师资力量如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:77` | D | 通用知识 | {"query": "计算定积分 ∫(0,1) x dx", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:78` | D | 专业咨询,课程 | {"query": "测试课程的学费包含哪些内容？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:79` | D | 通用知识 | {"query": "运维需要学习Linux操作系统吗？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:80` | D | AI课程,专业咨询 | {"query": "AI课程报名需要参加入学考试吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:81` | D | 通用知识 | {"query": "Python可以用来做什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:82` | D | 专业咨询 | {"query": "Java全栈开发包含前端技术吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:83` | D | 专业咨询,课程 | {"query": "大数据课程毕业生的平均薪资水平大概多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:84` | D | 通用知识 | {"query": "如何用Python连接MySQL数据库？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:85` | D | 专业咨询,课程 | {"query": "测试课程注重理论还是实践？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:86` | D | 通用知识 | {"query": "运维工程师需要考什么认证？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:87` | D | 专业咨询,培训 | {"query": "AI培训结束后能达到什么水平？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:88` | D | 通用知识 | {"query": "Java虚拟机（JVM）是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:89` | D | 专业咨询,课程 | {"query": "大数据课程有没有实训环节？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:90` | D | 通用知识 | {"query": "Python的lambda函数怎么用？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:91` | D | 专业咨询,课程 | {"query": "测试开发课程对英语水平有要求吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:92` | D | 专业咨询,课程 | {"query": "运维课程的教室在哪里？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:93` | D | 通用知识 | {"query": "什么是进程和线程？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:94` | D | AI课程,专业咨询,老师 | {"query": "AI课程的老师是全职还是兼职的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:95` | D | 专业咨询 | {"query": "Java学完后能做哪些类型的项目？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:96` | D | 通用知识 | {"query": "1+2+...+10 = ?", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:97` | D | 专业咨询,课程 | {"query": "大数据课程的授课方式是怎样的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:98` | D | 通用知识 | {"query": "Python如何处理JSON数据？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:99` | D | 通用知识 | {"query": "测试部门常用哪些缺陷管理工具？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:100` | D | 专业咨询,课程 | {"query": "运维课程的学费可以打折吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:101` | D | AI课程,专业咨询 | {"query": "AI课程包含深度学习框架（如TensorFlow, PyTorch）吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:102` | D | 通用知识 | {"query": "什么是版本控制系统？Git是做什么的？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:103` | D | Java课程,专业咨询 | {"query": "Java课程的实战项目难度大吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:104` | D | 通用知识 | {"query": "大数据分析主要用到哪些算法？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:105` | D | 专业咨询,课程 | {"query": "测试课程的讲师有实际项目经验吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:106` | D | 专业咨询,课程 | {"query": "运维课程的上课时间是固定的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:107` | D | 通用知识 | {"query": "解释一下什么是API。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:108` | D | AI课程,专业咨询 | {"query": "AI课程的招生对象是哪些人？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:109` | D | 专业咨询,培训 | {"query": "Java培训有就业保障吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:110` | D | 通用知识 | {"query": "求解线性方程组: x+y=5, x-y=1", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:111` | D | 专业咨询,课程 | {"query": "大数据课程结束后推荐工作吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:112` | D | 通用知识 | {"query": "Python的\`__init__\`方法是做什么的？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:113` | D | 通用知识 | {"query": "软件测试的基本流程是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:114` | D | 专业咨询 | {"query": "运维自动化主要学什么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:115` | D | 专业咨询 | {"query": "AI专业需要很强的数学背景吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:116` | D | 通用知识 | {"query": "什么是堆和栈？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:117` | D | 通用知识 | {"query": "Java Web开发常用的框架有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:118` | D | 专业咨询,课程 | {"query": "大数据课程提供住宿吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:119` | D | 专业咨询,课程 | {"query": "测试课程的学员反馈怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:120` | D | 通用知识 | {"query": "写一个Python类表示一个简单的银行账户。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:121` | D | 通用知识 | {"query": "运维工程师需要具备哪些技能？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:122` | D | AI课程,专业咨询 | {"query": "AI课程除了技术还会教其他软技能吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:123` | D | 专业咨询,培训 | {"query": "Java培训对年龄有限制吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:124` | D | 通用知识 | {"query": "计算圆周率近似值的方法有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:125` | D | 专业咨询,课程 | {"query": "大数据专业的课程体系是怎样的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:126` | D | 通用知识 | {"query": "Python如何进行文件操作？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:127` | D | 通用知识 | {"query": "测试人员需要懂代码吗？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:128` | D | 专业咨询,课程 | {"query": "运维课程的教学环境好不好？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:129` | D | 专业咨询 | {"query": "人工智能专业学完后可以做什么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:130` | D | 通用知识 | {"query": "什么是递归？举个例子。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:131` | D | 专业咨询,培训 | {"query": "Java培训的费用是多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:132` | D | 通用知识 | {"query": "大数据分析常用的可视化库有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:133` | D | 专业咨询,课程 | {"query": "测试课程会教性能测试吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:134` | D | 专业咨询,课程 | {"query": "运维课程的实操练习多不多？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:135` | D | 通用知识 | {"query": "解释一下操作系统的主要功能。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:136` | D | AI课程,专业咨询 | {"query": "AI课程有没有试听课？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:137` | D | 专业咨询 | {"query": "Java学习路线图推荐一下。", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:138` | D | 通用知识 | {"query": "100的二进制表示是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:139` | D | 专业咨询,课程 | {"query": "大数据课程的讲义是电子版还是纸质版？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:140` | D | 通用知识 | {"query": "Python中的生成器是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:141` | D | 通用知识 | {"query": "什么是黑盒测试和白盒测试？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:142` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师负责答疑吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:143` | D | 专业咨询,课程 | {"query": "人工智能专业的课程难易程度如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:144` | D | 通用知识 | {"query": "什么是算法复杂度？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:145` | D | 专业咨询,培训 | {"query": "Java培训期间会有考试吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:146` | D | 通用知识 | {"query": "大数据处理常用的数据库有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:147` | D | 专业咨询,课程 | {"query": "测试课程毕业生的就业率高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:148` | D | 专业咨询,课程 | {"query": "运维课程报名需要什么条件？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:149` | D | 通用知识 | {"query": "写一个Python脚本，统计一个文本文件中单词出现的频率。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:150` | D | AI课程,专业咨询 | {"query": "AI课程的学习资料在哪里获取？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:151` | D | 通用知识 | {"query": "Java语言有哪些特点？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:152` | D | 专业咨询,课程 | {"query": "大数据课程的实战项目是基于真实数据吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:153` | D | 通用知识 | {"query": "Python的虚拟环境有什么用？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:154` | D | 通用知识 | {"query": "软件测试工程师的发展前景如何？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:155` | D | 专业咨询,老师,课程 | {"query": "运维课程的授课老师是固定的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:156` | D | 通用知识 | {"query": "人工智能现在有哪些主要的应用领域？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:157` | D | 专业咨询,培训 | {"query": "Java培训机构哪家比较好？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:158` | D | 通用知识 | {"query": "大数据分析师需要具备哪些素质？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:159` | D | 专业咨询,课程 | {"query": "测试课程的学费可以退吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:160` | D | 专业咨询,课程 | {"query": "运维课程的学习氛围怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:161` | D | 通用知识 | {"query": "什么是链表？它和数组有什么区别？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:162` | D | AI课程,专业咨询 | {"query": "AI课程有没有在线答疑平台？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:163` | D | 专业咨询 | {"query": "Java学习遇到瓶颈怎么办？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:164` | D | 通用知识 | {"query": "计算 sin(30度)", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:165` | D | 专业咨询,课程 | {"query": "大数据课程的作业多吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:166` | D | 通用知识 | {"query": "Python的异步编程怎么实现？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:167` | D | 通用知识 | {"query": "自动化测试和手动测试哪个更重要？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:168` | D | 专业咨询,课程 | {"query": "运维课程的学员来自哪些背景？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:169` | D | 专业咨询 | {"query": "人工智能专业毕业后的薪资待遇如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:170` | D | 通用知识 | {"query": "什么是二叉搜索树？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:171` | D | 专业咨询,培训 | {"query": "Java培训班的地址在哪里？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:172` | D | 通用知识 | {"query": "大数据分析需要学习统计学知识吗？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:173` | D | 专业咨询,课程 | {"query": "测试课程有周末班吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:174` | D | 通用知识 | {"query": "运维工程师需要值夜班吗？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:175` | D | AI课程,专业咨询 | {"query": "AI课程的讲师有哪些认证？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:176` | D | 通用知识 | {"query": "Java Web开发和Java后端开发有什么区别？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:177` | D | 专业咨询,课程 | {"query": "大数据课程的报名流程是怎样的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:178` | D | 通用知识 | {"query": "Python的常用数据科学库有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:179` | D | 通用知识 | {"query": "测试开发工程师需要掌握哪些编程语言？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:180` | D | 专业咨询,课程 | {"query": "运维课程提供实习机会吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:181` | D | 专业咨询 | {"query": "人工智能专业的学习门槛高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:182` | D | 通用知识 | {"query": "什么是死锁？产生的条件是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:183` | D | 专业咨询,培训 | {"query": "Java培训期间的项目可以写在简历上吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:184` | D | 通用知识 | {"query": "大数据分析平台有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:185` | D | 专业咨询,老师,课程 | {"query": "测试课程的老师会批改作业吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:186` | D | 专业咨询,课程 | {"query": "运维课程结束后如何找工作？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:187` | D | 通用知识 | {"query": "写一个SQL语句，统计每个部门的员工人数。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:188` | D | AI课程,专业咨询 | {"query": "AI课程的学习周期是多长？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:189` | D | 通用知识 | {"query": "解释一下什么是MVC设计模式。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:190` | D | 专业咨询,课程 | {"query": "大数据课程会教数据清洗吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:191` | D | 通用知识 | {"query": "Python的多线程和多进程有什么区别？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:192` | D | 通用知识 | {"query": "接口测试怎么做？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:193` | D | 专业咨询,培训,课程 | {"query": "运维课程有没有针对云计算平台的培训，比如AWS或阿里云？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:194` | D | 专业咨询 | {"query": "人工智能专业对英语的要求高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:195` | D | 专业咨询,培训 | {"query": "Java培训有入学测试吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:196` | D | 通用知识 | {"query": "大数据分析师日常工作内容是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:197` | D | 专业咨询,课程 | {"query": "测试课程的学费包含考试费吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:198` | D | 专业咨询,课程 | {"query": "运维课程的教室有空调吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:199` | D | 通用知识 | {"query": "什么是图灵测试？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:200` | D | AI课程,专业咨询 | {"query": "AI课程的授课地点在哪里？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:201` | D | 通用知识 | {"query": "Java如何实现多线程？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:202` | D | 专业咨询,课程 | {"query": "大数据课程的学习强度大不大？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:203` | D | 通用知识 | {"query": "Python怎么操作Excel文件？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:204` | D | 通用知识 | {"query": "功能测试和非功能测试的区别是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:205` | D | 专业咨询,课程 | {"query": "运维课程结束后能达到什么水平？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:206` | D | 通用知识 | {"query": "机器学习和深度学习是什么关系？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:207` | D | 专业咨询,培训 | {"query": "Java培训报名需要准备什么材料？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:208` | D | 通用知识 | {"query": "大数据分析在金融行业的应用有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:209` | D | 专业咨询,课程 | {"query": "测试课程有没有线上录播可以回看？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:210` | D | 专业咨询,课程 | {"query": "运维课程对计算机基础要求高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:211` | D | 通用知识 | {"query": "什么是B树和B+树？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:212` | D | AI课程,专业咨询,老师 | {"query": "AI课程的老师教学经验丰富吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:213` | D | 专业咨询 | {"query": "Java Web开发主要学习哪些技术栈？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:214` | D | 通用知识 | {"query": "2的10次方是多少？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:215` | D | 专业咨询,课程 | {"query": "大数据课程的学费可以优惠吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:216` | D | 通用知识 | {"query": "Python如何发送HTTP请求？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:217` | D | 通用知识 | {"query": "单元测试、集成测试、系统测试的区别？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:218` | D | 专业咨询,课程 | {"query": "运维课程的学习资料是中文还是英文？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:219` | D | 专业咨询 | {"query": "人工智能专业毕业后好找工作吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:220` | D | 通用知识 | {"query": "什么是红黑树？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:221` | D | 专业咨询,培训 | {"query": "Java培训的通过率怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:222` | D | 通用知识 | {"query": "大数据常用的ETL工具有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:223` | D | 专业咨询,课程 | {"query": "测试课程会不会太理论化？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:224` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师是哪里请来的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:225` | D | 通用知识 | {"query": "写一个简单的HTML页面，包含一个标题和一个段落。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:226` | D | AI课程,专业咨询 | {"query": "AI课程的学费包含了哪些项目？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:227` | D | 通用知识 | {"query": "Java的垃圾回收机制（GC）是如何工作的？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:228` | D | 专业咨询,课程 | {"query": "大数据课程的实战项目会用到哪些技术？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:229` | D | 通用知识 | {"query": "Python的\`*args\`和\`**kwargs\`是什么意思？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:230` | D | 通用知识 | {"query": "什么是回归测试？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:231` | D | 专业咨询,课程 | {"query": "运维课程有没有包含数据库管理的内容？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:232` | D | 专业咨询,课程 | {"query": "人工智能专业需要学习哪些数学课程？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:233` | D | 专业咨询,培训 | {"query": "Java培训学完可以达到什么水平？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:234` | D | 通用知识 | {"query": "大数据分析师需要考取哪些证书？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:235` | D | 专业咨询,课程 | {"query": "测试课程的课后作业多么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:236` | D | 专业咨询,课程 | {"query": "运维课程有针对女生的优惠政策吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:237` | D | 通用知识 | {"query": "什么是时间复杂度和空间复杂度？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:238` | D | AI课程,专业咨询 | {"query": "AI课程的教学模式是怎样的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:239` | D | 通用知识 | {"query": "Java IO流有哪些种类？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:240` | D | 专业咨询,课程 | {"query": "大数据课程对编程基础要求高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:241` | D | 通用知识 | {"query": "Python的常用Web框架有哪些？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:242` | D | 通用知识 | {"query": "性能测试主要关注哪些指标？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:243` | D | 专业咨询,课程 | {"query": "运维课程毕业学员的就业情况如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:244` | D | 通用知识 | {"query": "自然语言处理（NLP）是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:245` | D | 专业咨询,培训 | {"query": "Java培训有试听课吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:246` | D | 通用知识 | {"query": "大数据分析师的职业发展路径是怎样的？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:247` | D | 专业咨询,课程 | {"query": "测试课程有没有就业指导服务？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:248` | D | 专业咨询,课程 | {"query": "运维课程的学费贵不贵？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:249` | D | 通用知识 | {"query": "什么是快速排序？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:250` | D | AI课程,专业咨询,师资 | {"query": "AI课程的师资队伍构成？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:251` | D | 通用知识 | {"query": "Java SE 和 Java EE 有什么区别？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:252` | D | 专业咨询,课程 | {"query": "大数据课程会教数据仓库吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:253` | D | 通用知识 | {"query": "Python如何解析XML文件？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:254` | D | 通用知识 | {"query": "安全测试主要包含哪些方面？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:255` | D | 专业咨询,课程 | {"query": "运维课程有没有考试？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:256` | D | 专业咨询,课程 | {"query": "人工智能专业需要学习哪些核心课程？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:257` | D | 专业咨询,培训 | {"query": "Java培训报名有没有学历要求？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:258` | D | 通用知识 | {"query": "大数据行业的发展趋势如何？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:259` | D | 专业咨询,课程 | {"query": "测试课程的教学质量怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:260` | D | 专业咨询,课程 | {"query": "运维课程的教学设备新吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:261` | D | 通用知识 | {"query": "写一个函数计算两个数的最大公约数。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:262` | D | AI课程,专业咨询 | {"query": "AI课程的毕业项目是什么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:263` | D | 通用知识 | {"query": "解释一下Spring框架的核心概念（IOC, AOP）。", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:264` | D | 专业咨询,课程 | {"query": "大数据课程适合转行的人学习吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:265` | D | 通用知识 | {"query": "Python的标准库有哪些常用的模块？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:266` | D | 通用知识 | {"query": "什么是探索性测试？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:267` | D | 专业咨询,课程 | {"query": "运维课程有没有针对特定行业的解决方案讲解？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:268` | D | 专业咨询 | {"query": "人工智能专业毕业生的竞争力如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:269` | D | 专业咨询,培训,课程 | {"query": "Java培训的课程大纲可以看一下吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:270` | D | 通用知识 | {"query": "大数据分析的流程一般是怎样的？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:271` | D | 专业咨询,老师,课程 | {"query": "测试课程的老师会提供简历指导吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:272` | D | 专业咨询,课程 | {"query": "运维课程的上课地点交通方便吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:273` | D | 通用知识 | {"query": "什么是操作系统内核？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:274` | D | AI课程,专业咨询 | {"query": "AI课程的学习压力大不大？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:275` | D | 通用知识 | {"query": "Java中==和equals()的区别是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:276` | D | 专业咨询,课程 | {"query": "大数据课程的学费包含了教材费吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:277` | D | 通用知识 | {"query": "Python如何进行多进程编程？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:278` | D | 通用知识 | {"query": "可用性测试是什么？", "label": "通用知识"} |
| `rag_qa/classify_data/model_generic_5000.json:279` | D | 专业咨询,课程 | {"query": "运维课程有没有实践项目？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:280` | D | 专业咨询 | {"query": "人工智能专业需要具备哪些能力？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:281` | D | 专业咨询,培训 | {"query": "Java培训结束后能找到工作吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:282` | D | 专业咨询 | {"query": "大数据常用的可视化工具（如Tableau, PowerBI）会教吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:283` | D | 专业咨询,课程 | {"query": "测试课程的讲师水平怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:284` | D | 专业咨询,培训,课程 | {"query": "运维课程的培训周期是多长？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:285` | D | AI课程,专业咨询 | {"query": "AI课程对数学的要求有多高？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:286` | D | 专业咨询,培训 | {"query": "Java培训的讲师是哪里的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:287` | D | 专业咨询,老师,课程 | {"query": "大数据课程的授课老师有项目经验吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:288` | D | 专业咨询,课程 | {"query": "测试课程的费用是多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:289` | D | 专业咨询 | {"query": "运维专业的就业方向有哪些？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:290` | D | 专业咨询,培训 | {"query": "AI培训的地点在哪里？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:291` | D | Java课程,专业咨询 | {"query": "Java课程有没有周末班？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:292` | D | 专业咨询 | {"query": "大数据技术栈主要包括哪些？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:293` | D | 专业咨询,课程 | {"query": "测试开发课程学完能做什么工作？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:294` | D | 专业咨询,课程 | {"query": "运维课程的上课形式是线上还是线下？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:295` | D | AI课程,专业咨询 | {"query": "请问AI课程的学习资料是中文的还是英文的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:296` | D | 专业咨询,培训 | {"query": "Java培训班有年龄限制吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:297` | D | 专业咨询,课程 | {"query": "大数据分析课程对学历有要求吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:298` | D | 专业咨询,课程 | {"query": "测试课程的学费能不能优惠？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:299` | D | 专业咨询,师资,课程 | {"query": "运维课程的师资力量怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:300` | D | AI课程,专业咨询 | {"query": "AI课程毕业后可以拿到什么证书？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:301` | D | 专业咨询,课程 | {"query": "Java Web开发课程包含哪些前端框架？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:302` | D | 专业咨询,课程 | {"query": "大数据课程的实训项目是独立完成吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:303` | D | 专业咨询,课程 | {"query": "测试课程的报名方式是什么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:304` | D | 专业咨询,课程 | {"query": "运维课程提供住宿安排吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:305` | D | 专业咨询,课程 | {"query": "人工智能课程的学习难度如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:306` | D | 专业咨询,培训 | {"query": "Java培训的教学质量如何评估？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:307` | D | 专业咨询,课程 | {"query": "大数据课程的作业量大吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:308` | D | 专业咨询,课程 | {"query": "测试开发课程的学时有多长？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:309` | D | 专业咨询,课程 | {"query": "运维课程有没有针对网络工程师的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:310` | D | AI课程,专业咨询,老师 | {"query": "AI课程的老师会进行一对一辅导吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:311` | D | 专业咨询,培训 | {"query": "Java培训的就业率大概是多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:312` | D | 专业咨询,课程 | {"query": "大数据专业的课程内容包括哪些？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:313` | D | 专业咨询,课程 | {"query": "测试课程的教材费用需要另外支付吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:314` | D | 专业咨询,课程 | {"query": "运维课程的学员评价怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:315` | D | 专业咨询 | {"query": "人工智能专业需要掌握哪些核心技术？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:316` | D | 专业咨询,培训 | {"query": "Java培训的费用支持哪些支付方式？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:317` | D | 专业咨询,课程 | {"query": "大数据课程的实战项目和企业接轨吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:318` | D | 专业咨询,课程 | {"query": "测试开发课程适合女生学习吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:319` | D | 专业咨询,课程 | {"query": "运维课程结束后有推荐就业的服务吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:320` | D | AI课程,专业咨询 | {"query": "AI课程有没有预科班？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:321` | D | 专业咨询,培训 | {"query": "Java培训班的班级人数多吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:322` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师都是全职的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:323` | D | 专业咨询,课程 | {"query": "测试课程的理论课和实践课比例是多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:324` | D | 专业咨询,课程 | {"query": "运维课程的上课时间灵活吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:325` | D | 专业咨询 | {"query": "人工智能专业的招生简章在哪里看？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:326` | D | 专业咨询,培训,课程 | {"query": "Java培训的课程更新速度快吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:327` | D | 专业咨询,课程 | {"query": "大数据课程的学习资料收费吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:328` | D | 专业咨询,课程 | {"query": "测试开发课程的毕业要求是什么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:329` | D | 专业咨询,课程 | {"query": "运维课程有没有包含虚拟化技术，比如VMware？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:330` | D | AI课程,专业咨询 | {"query": "AI课程需要自带电脑吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:331` | D | 专业咨询,培训 | {"query": "Java培训的口碑怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:332` | D | 专业咨询,课程 | {"query": "大数据课程对编程零基础友好吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:333` | D | 专业咨询,课程 | {"query": "测试课程的讲师是来自大厂吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:334` | D | 专业咨询,课程 | {"query": "运维课程的教学场地设施如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:335` | D | 专业咨询 | {"query": "人工智能专业的项目实践机会多吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:336` | D | 专业咨询,培训 | {"query": "Java培训期间食宿怎么解决？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:337` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师答疑及时吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:338` | D | 专业咨询,课程 | {"query": "测试开发课程结束后能独立做项目吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:339` | D | 专业咨询,课程 | {"query": "运维课程会讲解监控工具（如Zabbix, Prometheus）吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:340` | D | AI课程,专业咨询 | {"query": "AI课程的学习氛围好不好？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:341` | D | 专业咨询,培训 | {"query": "Java培训的老学员评价如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:342` | D | 专业咨询,课程 | {"query": "大数据课程有没有入学水平测试？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:343` | D | 专业咨询,课程 | {"query": "测试课程的实战项目和实际工作内容差别大吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:344` | D | 专业咨询,课程 | {"query": "运维课程的学费是一次性交清还是可以分期？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:345` | D | 专业咨询,课程 | {"query": "人工智能专业的课程结束后，技术能达到什么程度？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:346` | D | 专业咨询,培训,老师 | {"query": "Java培训的老师会布置课后作业吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:347` | D | 专业咨询,课程 | {"query": "大数据课程的教学大纲可以提供吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:348` | D | 专业咨询,课程 | {"query": "测试开发课程有没有针对面试的辅导？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:349` | D | 专业咨询,课程 | {"query": "运维课程的学费包含了哪些服务？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:350` | D | AI课程,专业咨询 | {"query": "AI课程需要学习高等数学吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:351` | D | 专业咨询,培训 | {"query": "Java培训结束后，推荐的工作薪资大概多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:352` | D | 专业咨询,课程 | {"query": "大数据分析课程会讲授机器学习算法吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:353` | D | 专业咨询,课程 | {"query": "测试课程有没有线上直播课？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:354` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师是否都有认证？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:355` | D | 专业咨询,课程 | {"query": "人工智能专业的课程是否包含计算机视觉内容？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:356` | D | 专业咨询,培训,课程 | {"query": "Java培训的课程难度如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:357` | D | 专业咨询,课程 | {"query": "大数据课程的学习周期是几个月？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:358` | D | 专业咨询,课程 | {"query": "测试开发课程的讲师从业经验多久？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:359` | D | 专业咨询,课程 | {"query": "运维课程会不会很难跟上？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:360` | D | AI课程,专业咨询 | {"query": "AI课程的上课地址具体在哪个区？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:361` | D | 专业咨询,培训 | {"query": "Java培训班的上课时间安排？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:362` | D | 专业咨询,课程 | {"query": "大数据分析课程的先修课程有哪些？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:363` | D | 专业咨询,老师,课程 | {"query": "测试课程的毕业项目选题是自己定还是老师分配？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:364` | D | 专业咨询,课程 | {"query": "运维课程的学费有没有早鸟价？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:365` | D | 专业咨询,课程 | {"query": "人工智能专业的课程体系包含哪些模块？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:366` | D | 专业咨询,培训,学生 | {"query": "Java培训是否适合非计算机专业学生？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:367` | D | 专业咨询,课程 | {"query": "大数据课程结束后能胜任数据分析师岗位吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:368` | D | 专业咨询,课程 | {"query": "测试开发课程的讲师是固定的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:369` | D | 专业咨询,课程 | {"query": "运维课程的实践环境是真实的服务器吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:370` | D | AI课程,专业咨询 | {"query": "AI课程的学费包含电脑使用费吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:371` | D | 专业咨询,培训 | {"query": "Java培训的毕业学员都去哪些公司了？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:372` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师会分享行业经验吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:373` | D | 专业咨询,课程 | {"query": "测试课程的考核方式是什么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:374` | D | 专业咨询,课程 | {"query": "运维课程的教学内容会根据技术发展更新吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:375` | D | 专业咨询 | {"query": "人工智能专业的学习资源丰富吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:376` | D | 专业咨询,培训 | {"query": "Java培训报名截止到什么时候？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:377` | D | 专业咨询,课程 | {"query": "大数据课程对英语的要求高不高？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:378` | D | 专业咨询,课程 | {"query": "测试开发课程的班级规模大概多少人？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:379` | D | 专业咨询,培训,课程 | {"query": "运维课程有没有针对系统管理员的培训？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:380` | D | AI课程,专业咨询 | {"query": "AI课程的实战项目有哪些？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:381` | D | 专业咨询,培训 | {"query": "Java培训的老学员推荐率高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:382` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师是否有耐心解答问题？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:383` | D | 专业咨询,课程 | {"query": "测试课程有没有补考机会？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:384` | D | 专业咨询,课程 | {"query": "运维课程的教学管理严格吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:385` | D | 专业咨询 | {"query": "人工智能专业学出来好就业吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:386` | D | 专业咨询,培训,老师 | {"query": "Java培训的老师负责吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:387` | D | 专业咨询,课程 | {"query": "大数据课程的教材是什么版本的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:388` | D | 专业咨询,课程 | {"query": "测试开发课程的教学方法是怎样的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:389` | D | 专业咨询,课程 | {"query": "运维课程的上课纪律怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:390` | D | AI课程,专业咨询 | {"query": "AI课程的学习需要什么基础？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:391` | D | 专业咨询,培训 | {"query": "Java培训有包就业的承诺吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:392` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师讲课风格如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:393` | D | 专业咨询,课程 | {"query": "测试课程的毕业设计要求高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:394` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师是教授还是工程师？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:395` | D | 专业咨询 | {"query": "人工智能专业会学习Python吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:396` | D | 专业咨询,培训 | {"query": "Java培训地点交通便利吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:397` | D | 专业咨询,课程 | {"query": "大数据课程的案例是真实的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:398` | D | 专业咨询,课程 | {"query": "测试开发课程的学费可以按月支付吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:399` | D | 专业咨询,课程 | {"query": "运维课程的实训设备够用吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:400` | D | AI课程,专业咨询,老师 | {"query": "AI课程的老师会推荐就业吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:401` | D | 专业咨询,培训 | {"query": "Java培训的报名条件是什么？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:402` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师是博士吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:403` | D | 专业咨询,课程 | {"query": "测试课程的练习题多吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:404` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师会带项目吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:405` | D | 专业咨询,课程 | {"query": "人工智能专业的核心课程是哪些？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:406` | D | 专业咨询,培训,课程 | {"query": "Java培训的课程表能发我一份吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:407` | D | 专业咨询,课程 | {"query": "大数据课程的学习需要购买额外的软件吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:408` | D | 专业咨询,老师,课程 | {"query": "测试开发课程的老师有自己的博客或GitHub吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:409` | D | 专业咨询,课程 | {"query": "运维课程的实战平台是云服务器吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:410` | D | AI课程,专业咨询 | {"query": "AI课程的结业证书是国家承认的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:411` | D | 专业咨询,培训 | {"query": "Java培训的退费政策是怎样的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:412` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师会定期考核吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:413` | D | 专业咨询,课程 | {"query": "测试课程的学员可以互相交流学习吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:414` | D | 专业咨询,课程 | {"query": "运维课程的教学方法有哪些？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:415` | D | 专业咨询 | {"query": "人工智能专业有奖学金吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:416` | D | 专业咨询,培训 | {"query": "Java培训的教室环境怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:417` | D | 专业咨询,老师,课程 | {"query": "大数据课程的老师会留作业吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:418` | D | 专业咨询,老师,课程 | {"query": "测试开发课程的老师讲课细致吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:419` | D | 专业咨询,课程 | {"query": "运维课程的学员就业去向主要是哪些公司？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:420` | D | AI课程,专业咨询 | {"query": "AI课程的报名电话是多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:421` | D | 专业咨询,培训 | {"query": "Java培训的学费大概范围是多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:422` | D | 专业咨询,课程 | {"query": "大数据分析课程的难度适合新手吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:423` | D | 专业咨询,课程 | {"query": "测试课程的实战项目是分组进行吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:424` | D | 专业咨询,课程 | {"query": "运维课程的教学计划是怎样的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:425` | D | 专业咨询 | {"query": "人工智能专业报名需要什么资格？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:426` | D | 专业咨询,培训 | {"query": "Java培训提供住宿吗？费用怎么算？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:427` | D | 专业咨询,老师,课程 | {"query": "大数据课程的老师会提供学习建议吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:428` | D | 专业咨询,课程 | {"query": "测试开发课程结束后能掌握哪些核心技能？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:429` | D | 专业咨询,课程 | {"query": "运维课程的教室有没有网络？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:430` | D | AI课程,专业咨询,老师 | {"query": "AI课程的老师讲课水平如何？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:431` | D | 专业咨询,培训 | {"query": "Java培训的报名官网是哪个？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:432` | D | 专业咨询,课程 | {"query": "大数据分析课程的教材用的是哪一本？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:433` | D | 专业咨询,老师,课程 | {"query": "测试课程的老师会分享面试经验吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:434` | D | 专业咨询,课程 | {"query": "运维课程有没有晚自习安排？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:435` | D | 专业咨询 | {"query": "人工智能专业的学费可以申请助学贷款吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:436` | D | 专业咨询,培训,课程 | {"query": "Java培训的课程顾问联系方式？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:437` | D | 专业咨询,课程 | {"query": "大数据课程有没有线下面授班？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:438` | D | 专业咨询,课程 | {"query": "测试开发课程的讲师是专职的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:439` | D | 专业咨询,课程 | {"query": "运维课程的实训项目是模拟真实环境吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:440` | D | AI课程,专业咨询 | {"query": "AI课程的报名入口在哪里？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:441` | D | 专业咨询,培训,课程 | {"query": "Java培训的课程内容多久更新一次？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:442` | D | 专业咨询,课程 | {"query": "大数据分析课程对计算机操作熟练度有要求吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:443` | D | 专业咨询,老师,课程 | {"query": "测试课程的老师会帮忙修改简历吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:444` | D | 专业咨询,课程 | {"query": "运维课程的班主任负责吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:445` | D | 专业咨询 | {"query": "人工智能专业的学费是统一的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:446` | D | 专业咨询,培训 | {"query": "Java培训机构的地址是？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:447` | D | 专业咨询,课程 | {"query": "大数据课程需要学习Linux吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:448` | D | 专业咨询,课程 | {"query": "测试开发课程的就业服务怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:449` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师会推荐实习吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:450` | D | AI课程,专业咨询,课程 | {"query": "AI课程的课程顾问是谁？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:451` | D | 专业咨询,培训 | {"query": "Java培训的学时总共多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:452` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师有相关的行业认证吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:453` | D | 专业咨询,课程 | {"query": "测试课程的实战项目是自己找题目吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:454` | D | 专业咨询,课程 | {"query": "运维课程会教脚本编程（如Shell, Python）吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:455` | D | 专业咨询,课程 | {"query": "人工智能专业的课程有实验课吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:456` | D | 专业咨询,培训 | {"query": "Java培训的教室有投影仪吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:457` | D | 专业咨询,老师,课程 | {"query": "大数据课程的老师会布置预习任务吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:458` | D | 专业咨询,老师,课程 | {"query": "测试开发课程的老师会课后答疑吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:459` | D | 专业咨询,课程 | {"query": "运维课程的毕业生起薪大概多少？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:460` | D | AI课程,专业咨询 | {"query": "AI课程的报名有没有优惠码？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:461` | D | 专业咨询,培训,师资 | {"query": "Java培训的师资介绍页面在哪里？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:462` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师教学经验几年了？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:463` | D | 专业咨询,课程 | {"query": "测试课程的实践平台是免费使用的吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:464` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师讲课生动吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:465` | D | 专业咨询,课程 | {"query": "人工智能专业的课程表可以看下吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:466` | D | 专业咨询,培训,课程 | {"query": "Java培训的课程会包含微服务架构吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:467` | D | 专业咨询,课程 | {"query": "大数据课程的考试难度怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:468` | D | 专业咨询,老师,课程 | {"query": "测试开发课程的老师有没有出过书？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:469` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师是哪里毕业的？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:470` | D | AI课程,专业咨询 | {"query": "AI课程的学费是一次性付清还是可以分期？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:471` | D | 专业咨询,培训 | {"query": "Java培训的就业指导包括哪些内容？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:472` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师讲课条理清晰吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:473` | D | 专业咨询,课程 | {"query": "测试课程的学员可以旁听其他课程吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:474` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师会分享实际工作中的坑吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:475` | D | 专业咨询 | {"query": "人工智能专业对编程能力要求高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:476` | D | 专业咨询,培训 | {"query": "Java培训有线上的答疑群吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:477` | D | 专业咨询,老师,课程 | {"query": "大数据课程的老师会根据学员基础调整进度吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:478` | D | 专业咨询,课程 | {"query": "测试开发课程的实战项目是否真实的企业级项目？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:479` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师会推荐学习资料吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:480` | D | AI课程,专业咨询 | {"query": "AI课程的学费包含了哪些杂费？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:481` | D | 专业咨询,培训 | {"query": "Java培训的住宿条件怎么样？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:482` | D | 专业咨询,老师,课程 | {"query": "大数据分析课程的老师会做项目演示吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:483` | D | 专业咨询,课程 | {"query": "测试课程的学员转行成功率高吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:484` | D | 专业咨询,老师,课程 | {"query": "运维课程的老师会组织技术分享会吗？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:485` | D | 专业咨询 | {"query": "人工智能专业的就业方向有哪些选择？", "label": "专业咨询"} |
| `rag_qa/classify_data/model_generic_5000.json:486` | D | 专业咨询 | {"query": "大数据应用在哪些领域？", "label": "专业咨询"} |
| `rag_qa/classify_data/提示词模块.txt:1` | D | 专业咨询,通用知识 | 你是一个高效的文本分类系统，任务是判断用户的查询属于“通用知识”还是“专业咨询”。 |
| `rag_qa/classify_data/提示词模块.txt:4` | D | 通用知识 | - “通用知识”类主要包含数学计算、代码生成/纠错、概念与原理问题以及其他常识性问题。 |
| `rag_qa/classify_data/提示词模块.txt:5` | D | 专业咨询,培训,师资,教育,课程 | - “专业咨询”类专指与IT教育培训相关的查询，如课程详情、师资介绍、项目内容、培训周期、地点、时间和费用等。 |
| `rag_qa/classify_data/提示词模块.txt:10` | D | 专业咨询,培训,师资,课程 | - 如果内容涉及IT培训（例如JAVA、AI、测试等课程介绍、培训服务、师资力量、学习周期等），请标注为“专业咨询”； |
| `rag_qa/classify_data/提示词模块.txt:11` | D | 通用知识 | - 如果内容主要涉及计算、代码处理或基础概念问题，请标注为“通用知识”。 |
| `rag_qa/classify_data/提示词模块.txt:20` | D | 通用知识 | "label": "通用知识" |
| `rag_qa/classify_data/提示词模块.txt:24` | D | 课程 | “JAVA的课程大纲是什么？” |
| `rag_qa/classify_data/提示词模块.txt:27` | D | 课程 | "query": "JAVA的课程大纲是什么？", |
| `rag_qa/classify_data/提示词模块.txt:28` | D | 专业咨询 | "label": "专业咨询" |
| `rag_qa/classify_data/提示词模块.txt:33` | D | 专业咨询,培训,教育 | - 如果存在歧义，请优先判断是否涉及具体的IT教育培训服务，如果是，则分类为“专业咨询”； |
| `rag_qa/classify_data/提示词模块.txt:34` | D | 专业咨询,通用知识 | - 输出时请保持标签仅为“通用知识”或“专业咨询”。 |
| `rag_qa/core/document_processor.py:8` | B | edu_document_loaders | from rag_qa.edu_document_loaders.edu_docloader import OCRDOCLoader |
| `rag_qa/core/document_processor.py:9` | B | edu_document_loaders | from rag_qa.edu_document_loaders.edu_imgloader import OCRIMGLoader |
| `rag_qa/core/document_processor.py:10` | B | edu_document_loaders | from rag_qa.edu_document_loaders.edu_pdfloader import OCRPDFLoader |
| `rag_qa/core/document_processor.py:11` | B | edu_document_loaders | from rag_qa.edu_document_loaders.edu_pptloader import OCRPPTLoader |
| `rag_qa/core/document_processor.py:13` | B | edu_text_spliter | from rag_qa.edu_text_spliter.edu_chinese_recursive_text_splitter import ChineseRecursiveTextSplitter |
| `rag_qa/core/document_processor.py:123` | B | ai_data | chunks = load_documents_from_directory(f"{config.DATA_DIR}/ai_data") |
| `rag_qa/core/document_processor.py:125` | B | ai_data | # chunks = process_documents(f"{config.DATA_DIR}/ai_data") |
| `rag_qa/core/new_rag_system.py:21` | B | bert_query_classifier | model_path=f'{config.MODELS_DIR}/bert_query_classifier') |
| `rag_qa/core/new_rag_system.py:109` | B | 学科 | logger.info(f"retrieve_and_merge 开始处理查询: '{query}', 学科过滤: {source_filter}") |
| `rag_qa/core/new_rag_system.py:147` | B | 学科 | logger.info(f"generate_answer 开始处理查询: '{query}', 学科过滤: {source_filter}") |
| `rag_qa/core/new_rag_system.py:169` | B | 通用知识 | # 判断查询类型，通用知识还是专业知识 |
| `rag_qa/core/new_rag_system.py:175` | B | 通用知识 | if query_category == "通用知识": |
| `rag_qa/core/new_rag_system.py:176` | B | 通用知识 | logger.info("查询为通用知识，直接调用 LLM") |
| `rag_qa/core/new_rag_system.py:181` | B | CUSTOMER_SERVICE_PHONE | phone=config.CUSTOMER_SERVICE_PHONE |
| `rag_qa/core/new_rag_system.py:184` | B | 专业咨询 | logger.info("查询为专业咨询，执行 RAG 流程") |
| `rag_qa/core/new_rag_system.py:198` | B | CUSTOMER_SERVICE_PHONE | phone=config.CUSTOMER_SERVICE_PHONE |
| `rag_qa/core/new_rag_system.py:224` | B | CUSTOMER_SERVICE_PHONE | yield f"抱歉，处理您的问题时出错。请联系人工客服：{config.CUSTOMER_SERVICE_PHONE}" |
| `rag_qa/core/new_rag_system.py:228` | B | CUSTOMER_SERVICE_PHONE | yield f"抱歉，处理您的问题时出错。请联系人工客服：{config.CUSTOMER_SERVICE_PHONE}" |
| `rag_qa/core/prompts.py:48` | B | 课程 | # 原始问题："人工智能课程和运维课程有什么区别？" |
| `rag_qa/core/query_classifier.py:23` | B | 专业咨询,通用知识 | 1. 数据加载：读取 5000 条 JSON 数据集，包含查询和标签（“通用知识”或“专业咨询”） |
| `rag_qa/core/query_classifier.py:26` | B | EduRAG | 4. 预测接口：支持实时分类，集成到 EduRAG 系统。 |
| `rag_qa/core/query_classifier.py:39` | B | bert_query_classifier | def __init__(self, model_path='models/bert_query_classifier'): |
| `rag_qa/core/query_classifier.py:53` | B | 专业咨询,通用知识 | self.label_map = {"通用知识": 0, "专业咨询": 1} |
| `rag_qa/core/query_classifier.py:84` | B | 通用知识 | # labels：[标签1,标签2,...标签n] -> ["通用知识"] |
| `rag_qa/core/query_classifier.py:94` | B | 专业咨询,通用知识 | # labels = ["通用知识", "专业咨询", .....] |
| `rag_qa/core/query_classifier.py:95` | B | 专业咨询,通用知识 | # 标签转为 0 和 1    # {"通用知识": 0, "专业咨询": 1} |
| `rag_qa/core/query_classifier.py:136` | B | 通用知识 | # value: {"query": "1024乘以768等于多少？", "label": "通用知识"} |
| `rag_qa/core/query_classifier.py:141` | B | 专业咨询,通用知识 | # 标签 = ["通用知识", "专业咨询", ....] |
| `rag_qa/core/query_classifier.py:245` | B | 专业咨询,通用知识 | target_names=["通用知识", "专业咨询"] |
| `rag_qa/core/query_classifier.py:255` | B | 通用知识 | # 默认返回通用知识 |
| `rag_qa/core/query_classifier.py:256` | B | 通用知识 | return "通用知识" |
| `rag_qa/core/query_classifier.py:268` | B | 专业咨询,通用知识 | return "专业咨询" if prediction == 1 else "通用知识" |
| `rag_qa/core/query_classifier.py:274` | B | bert_query_classifier | classifier = QueryClassifier(model_path=config.MODELS_DIR + "/bert_query_classifier1") |
| `rag_qa/core/query_classifier.py:281` | B | 学科,课程 | "AI学科的课程大纲是什么", |
| `rag_qa/core/query_classifier.py:282` | B | JAVA课程 | "JAVA课程费用多少？", |
| `rag_qa/core/query_classifier.py:284` | B | 培训,老师 | "AI培训有哪些老师？", |
| `rag_qa/core/query_classifier.py:287` | B | 学科 | "AI学科需要学历要求？", |
| `rag_qa/core/rag_system.py:25` | D | bert_query_classifier | model_path=f'{config.MODELS_DIR}/bert_query_classifier') |
| `rag_qa/core/rag_system.py:121` | D | 学科 | logger.info(f"retrieve_and_merge 开始处理查询: '{query}', 学科过滤: {source_filter}, 检索策略: {strategy}") |
| `rag_qa/core/rag_system.py:154` | D | 学科 | logger.info(f"generate_answer 开始处理查询: '{query}', 学科过滤: {source_filter}") |
| `rag_qa/core/rag_system.py:160` | D | 通用知识 | #   如果查询属于“通用知识”类别，则直接使用 LLM 回答 |
| `rag_qa/core/rag_system.py:161` | D | 通用知识 | if query_category == "通用知识": |
| `rag_qa/core/rag_system.py:162` | D | 通用知识 | logger.info("查询为通用知识，直接调用 LLM 生成答案") |
| `rag_qa/core/rag_system.py:164` | D | CUSTOMER_SERVICE_PHONE | context="", question=query, phone=config.CUSTOMER_SERVICE_PHONE, history="", |
| `rag_qa/core/rag_system.py:171` | D | CUSTOMER_SERVICE_PHONE,通用知识 | answer = f"抱歉，处理您的通用知识问题时出错。请联系人工客服：{config.CUSTOMER_SERVICE_PHONE}" |
| `rag_qa/core/rag_system.py:173` | D | 通用知识 | logger.info(f"通用知识查询处理完成 (耗时: {processing_time:.2f}s, 查询: '{query}')") |
| `rag_qa/core/rag_system.py:177` | D | 专业咨询 | logger.info("generate_answer 查询为专业咨询，执行 RAG 流程") |
| `rag_qa/core/rag_system.py:198` | D | CUSTOMER_SERVICE_PHONE | context=context, question=query, phone=config.CUSTOMER_SERVICE_PHONE, history="", |
| `rag_qa/core/rag_system.py:206` | D | CUSTOMER_SERVICE_PHONE,专业咨询 | answer = f"抱歉，处理您的专业咨询问题时出错。请联系人工客服：{config.CUSTOMER_SERVICE_PHONE}" |
| `rag_qa/core/strategy_selector.py:36` | B | 学科 | * 查询：AI学科学费是多少？ |
| `rag_qa/core/strategy_selector.py:38` | B | 课程 | * 查询：JAVA的课程大纲是什么？ |
| `rag_qa/core/strategy_selector.py:44` | B | 教育 | * 查询：人工智能在教育领域的应用有哪些？ |
| `rag_qa/core/strategy_selector.py:98` | B | 学科 | ss.select_strategy('AI大模型学科学费多少？') |
| `rag_qa/core/vector_store.py:76` | B | 学科 | # 添加学科类别字段，VARCHAR 类型，最大长度 50 |
| `rag_qa/core/vector_store.py:248` | B | ai_data | # docs = process_documents(config.DATA_DIR + "/ai_data") |
| `rag_qa/edu_document_loaders/edu_docloader.py:2` | C | edu_document_loaders | from rag_qa.edu_document_loaders.edu_ocr import get_ocr |
| `rag_qa/edu_document_loaders/edu_imgloader.py:2` | C | edu_document_loaders | from rag_qa.edu_document_loaders.edu_ocr import get_ocr |
| `rag_qa/edu_document_loaders/edu_pdfloader.py:7` | C | edu_document_loaders | from rag_qa.edu_document_loaders.edu_ocr import get_ocr |
| `rag_qa/edu_document_loaders/edu_pptloader.py:2` | C | edu_document_loaders | from rag_qa.edu_document_loaders.edu_ocr import get_ocr |
| `rag_qa/rag_assessment/rag_evaluate_data.json:3` | D | 课程 | "question": "人工智能就业课的课程版本是什么？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:4` | D | 学科,课程 | "context": ["人工智能学科全新升级——人工智能开发V6.0课程。"], |
| `rag_qa/rag_assessment/rag_evaluate_data.json:5` | D | 课程 | "answer": "人工智能就业课的课程版本是V6.0。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:9` | D | 课程 | "question": "课程的一句话概括是什么？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:11` | D | 课程 | "answer": "课程的一句话概括是：解锁「大模型」新技能成就「高薪AI」人才。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:15` | D | 课程 | "question": "课程优势有哪些？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:16` | D | 课程 | "context": ["课程优势\n\n优势一：热门岗位覆盖...\n优势二：与大厂深入合作...\n优势三：定制垂直行业大模型专项领域赋能...\n优势四：覆盖NLP、大模型解决方案和经典技术栈"], |
| `rag_qa/rag_assessment/rag_evaluate_data.json:17` | D | 课程 | "answer": "课程优势包括热门岗位覆盖、与大厂深入合作、定制垂直行业大模型、覆盖NLP和大模型解决方案。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:33` | D | 课程 | "question": "课程与大厂合作有什么优势？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:34` | D | 课程 | "context": ["优势二：与大厂深入合作（共建大模型课程，助你掌握前沿技术，增强就业竞争力)"], |
| `rag_qa/rag_assessment/rag_evaluate_data.json:35` | D | 课程 | "answer": "与大厂深入合作可以共建大模型课程，帮助掌握前沿技术，增强就业竞争力。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:36` | D | 课程 | "ground_truth": "共建大模型课程，掌握前沿技术，增强就业竞争力。" |
| `rag_qa/rag_assessment/rag_evaluate_data.json:39` | D | 课程 | "question": "课程新增了哪些技术？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:40` | D | 课程 | "context": ["d 课程新增技术\n\n新增：大模型开发基础与项目\n\n升级：机器学习\n\n升级：自然语言处理项目1\n\n升级：自然语言处理项目"], |
| `rag_qa/rag_assessment/rag_evaluate_data.json:41` | D | 课程 | "answer": "课程新增了大模型开发基础与项目，并升级了机器学习、自然语言处理项目1和自然语言处理项目。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:123` | D | 课程 | "question": "NLP自然语言处理基础阶段在课程中的第几部分？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:125` | D | 课程 | "answer": "NLP自然语言处理基础阶段是课程的第六部分。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:129` | D | 课程 | "question": "自然语言处理项目1在课程中的位置是？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:131` | D | 课程 | "answer": "自然语言处理项目1是课程的第七部分。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:135` | D | 课程 | "question": "大模型开发基础与项目在课程中的位置是？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:137` | D | 课程 | "answer": "大模型开发基础与项目是课程的第九部分。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:141` | D | 课程 | "question": "课程的整体内容目录包含哪些部分？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:143` | D | 课程 | "answer": "课程内容目录包括大模型语言基础、进阶、数据处理与统计分析、机器学习、深度学习基础、NLP基础、NLP项目1、NLP项目2、大模型开发基础与项目。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:159` | D | 课程 | "question": "课程为什么适合AI行业入门者？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:160` | D | 学生,学科,课程 | "context": ["随着大模型时代的到来，人工智能技术和应用发展越来越快，但是以往的人工智能开发门槛高、入门难，为了帮助梦想进入人工智能行业的学生找到更适宜的入门途径，人工智能学科全新升级——人工智能开发V6.0课程。"], |
| `rag_qa/rag_assessment/rag_evaluate_data.json:161` | D | 课程 | "answer": "课程适合AI行业入门者，因为它针对人工智能开发门槛高、入门难的问题进行了全新升级，推出了V6.0课程，提供更适宜的入门途径。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:162` | D | 课程 | "ground_truth": "针对人工智能开发门槛高、入门难的问题，推出全新升级的V6.0课程，提供更适宜的入门途径。" |
| `rag_qa/rag_assessment/rag_evaluate_data.json:165` | D | 课程 | "question": "课程如何帮助学员成为大模型应用开发人才？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:167` | D | 课程 | "answer": "课程通过机器学习技术栈完成数据挖掘任务，深度学习技术栈完成NLP和大模型开发任务，帮助学员成为懂AI、能实战的大模型应用开发人才。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:171` | D | 课程 | "question": "机器学习在课程中的位置是？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:173` | D | 课程 | "answer": "机器学习是课程的第四部分。", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:177` | D | 课程 | "question": "深度学习基础在课程中的位置是？", |
| `rag_qa/rag_assessment/rag_evaluate_data.json:179` | D | 课程 | "answer": "深度学习基础是课程的第五部分。", |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json:3` | D | 课程 | "question": "人工智能就业课的课程版本是什么？", |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json:4` | D | 学科,课程 | "context": ["人工智能学科全新升级——人工智能开发V6.0课程。"], |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json:5` | D | 课程 | "answer": "人工智能就业课的课程版本是V6.0。", |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json:9` | D | 课程 | "question": "课程的一句话概括是什么？", |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json:11` | D | 课程 | "answer": "课程的一句话概括是：解锁「大模型」新技能成就「高薪AI」人才。", |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json:15` | D | 课程 | "question": "课程优势有哪些？", |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json:16` | D | 课程 | "context": ["课程优势\n\n优势一：热门岗位覆盖...\n优势二：与大厂深入合作...\n优势三：定制垂直行业大模型专项领域赋能...\n优势四：覆盖NLP、大模型解决方案和经典技术栈"], |
| `rag_qa/rag_assessment/rag_evaluate_data_small.json:17` | D | 课程 | "answer": "课程优势包括热门岗位覆盖、与大厂深入合作、定制垂直行业大模型、覆盖NLP和大模型解决方案。", |
| `rag_qa/rag_assessment/ragas_evaluation_results.csv:2` | D | 学科,课程 | "[{'faithfulness': 0.0, 'answer_relevancy': np.float64(0.9987430827275402), 'context_precision': 0.9999999999, 'context_recall': 1.0}, {'faithfulness': nan, 'answer_relevancy': nan, 'context_precision …（长行省略；原文件保留全文） |
| `rag_qa/rag_assessment/ragas_evaluation_results.csv1:2` | D | 学科,课程 | "[{'faithfulness': 0.0, 'answer_relevancy': np.float64(0.9533325560167252), 'context_precision': 0.9999999999, 'context_recall': 1.0}, {'faithfulness': 0.0, 'answer_relevancy': np.float64(0.9180493670 …（长行省略；原文件保留全文） |
| `rag_qa/rag_main.py:71` | B | 学科 | # --- 数据处理模式 --- 将 data 目录下所有学科的文档数据库写入到Milvus中 |
| `rag_qa/rag_main.py:111` | B | bigdata | # ["ai", "java", "test", "ops", "bigdata"] |
| `rag_qa/rag_main.py:113` | B | EduRAG | print("\n欢迎使用 EduRAG 交互式查询系统！") |
| `rag_qa/rag_main.py:114` | B | 学科 | print(f"支持的学科类别：{valid_sources}") |
| `rag_qa/rag_main.py:124` | B | 学科 | # source_filter_input 用户输入的学科过滤条件 |
| `rag_qa/rag_main.py:125` | B | 学科 | source_filter_input = input(f"请输入学科类别 ({'/'.join(valid_sources)}) (直接回车默认不过滤)：").strip() |
| `rag_qa/rag_main.py:126` | B | 学科 | # 学科过滤条件 |
| `rag_qa/rag_main.py:131` | B | 学科 | logger.info(f"用户选择了学科过滤: {source_filter}") |
| `rag_qa/rag_main.py:134` | B | 学科 | f"无效的学科类别 '{source_filter_input}'，将不过滤" |
| `rag_qa/rag_main.py:136` | B | 学科 | print(f"提示：输入的学科 '{source_filter_input}' 无效，将不过滤。") |
| `rag_qa/rag_main.py:159` | B | EduRAG | parser = argparse.ArgumentParser(description="EduRAG System Main Entry Point") |
| `rag_qa/rag_main.py:163` | B | ai_data | # 字符串类型，默认值：./data/ai_data |
| `rag_qa/rag_main.py:164` | B | ai_data | parser.add_argument('--data-dir', type=str, default='./data/ai_data', |
| `static/index.html:6` | B | EduRAG,教育 | <title>传智教育EduRAG智慧问答系统</title> |
| `static/index.html:340` | B | EduRAG,教育 | <h1>传智教育EduRAG智慧问答系统</h1> |
| `static/index.html:374` | B | 学科 | <label for="sourceFilter">学科类别：</label> |
| `static/index.html:377` | B | 学科 | <!-- 学科类别选项将动态添加 --> |
| `static/index.html:406` | B | 学科 | const sourceFilter = document.getElementById('sourceFilter'); // 学科过滤器 |
| `static/index.html:421` | B | 学科 | // 加载学科类别 |
| `static/index.html:466` | B | 学科 | // 加载学科类别 |
| `static/index.html:472` | B | 学科 | throw new Error('获取学科类别失败'); |
| `static/index.html:480` | B | 学科 | // 添加学科类别选项 |
| `static/index.html:489` | B | 学科 | console.error('加载学科类别错误:', error); |
| `static/old_index.html:357` | D | 学科 | <label for="sourceFilter">学科类别：</label> |
| `static/old_index.html:360` | D | 学科 | <!-- 学科类别选项将动态添加 --> |
| `static/old_index.html:404` | D | 学科 | // 加载学科类别 |
| `static/old_index.html:449` | D | 学科 | // 加载学科类别 |
| `static/old_index.html:455` | D | 学科 | throw new Error('获取学科类别失败'); |
| `static/old_index.html:463` | D | 学科 | // 添加学科类别选项 |
| `static/old_index.html:472` | D | 学科 | console.error('加载学科类别错误:', error); |
| `static/src/App.jsx:12` | D | 学科 | // 学科类别（从后端获取或硬编码） |
| `static/src/App.jsx:125` | D | 学科 | <label className="block text-sm font-medium text-gray-700">学科类别（可选）</label> |
