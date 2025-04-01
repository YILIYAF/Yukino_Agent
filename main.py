# main.py
#未来的程序入口，无论是问句还是陈述句都从这里输入，然后调用各个模块的接口进行处理
import asyncio
from information_extraction import EntityRelationExtractor
from knowledge_graph_manager import EnhancedNeo4jConnector
from memory_retrieval import MemoryRetriever

async def main_flow():
    userid = "user123"
    
    # 初始化各模块
    extractor = EntityRelationExtractor()
    connector = EnhancedNeo4jConnector()
    retriever = MemoryRetriever()

    # # 测试数据录入
    # statements = [
    #     "我妈妈上周在上海买了小米SU7Pro",
    #     "我爸爸是数学老师",
    #     "我女朋友赵薇喜欢看科幻电影"
    # ]
    
    # for text in statements:
    #     kg = await extractor.extract(text, userid)
    #     connector.store_graph_data(kg.entities, kg.relations)
    #     print(f"已存储：{text}")

    #测试问题查询
    # questions = [
    #     "我妈妈最近买了什么？",
    #     "我爸的工作是什么？",
    #     "我女朋友有什么兴趣爱好？"
    # ]
    
    # for q in questions:
    #     print(f"\n用户提问：{q}")
    #     response = await retriever.process_question(q, userid)
    #     print(f"助手回答：{response}")
    response = await retriever.process_question("我的女朋友喜欢什么？", userid)
    print(f"助手回答：{response}")

if __name__ == "__main__":
    asyncio.run(main_flow())