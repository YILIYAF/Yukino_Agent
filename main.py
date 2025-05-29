# main.py
#未来的程序入口，无论是问句还是陈述句都从这里输入，然后调用各个模块的接口进行处理
import asyncio
import pyttsx3  # 导入语音合成库
from information_extraction import EntityRelationExtractor
from knowledge_graph_manager import EnhancedNeo4jConnector
from memory_retrieval import MemoryRetriever

# 初始化语音引擎
engine = pyttsx3.init()

# 定义语音输出函数
def speak(text):
    """将文本转换为语音并播放"""
    engine.say(text)
    engine.runAndWait()

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
    print("欢迎回来~~我叫Yukino，请问想和我聊什么呀~😊\n如果想退出，请输入'退出'或'exit'~~")
    speak("欢迎回来，我叫 Yukino，请问想和我聊什么呀？如果想退出，请输入退出或 exit。")
    while True:
        user_input = input("\n想聊点什么呢~：")
        if user_input == "退出" or user_input == "exit":
            print("再见啦~期待和你的下次聊天呀~😊")
            speak("再见啦，期待和你的下次聊天呀！")
            break
        # 处理用户输入
        kg = await extractor.extract(user_input, userid)
        connector.store_graph_data(kg.entities, kg.relations)
        # print(f"已存储：{user_input}")
        
        # 查询知识图谱
        response = await retriever.process_question(user_input, userid)
        print(f"[助理回答]：{response}")
        speak(response)  # 将回答转换为语音输出

if __name__ == "__main__":
    asyncio.run(main_flow())