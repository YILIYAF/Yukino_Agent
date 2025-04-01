# response_generation.py
#回答模块，用于生成回答文本
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
os.environ["NEO4J_URI"] = "neo4j://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "atomic-freddie-good-junior-master-5636"
os.environ["OPENAI_API_KEY"] = "sk-940a642633a0485199f4fe582ae1dbc6"
os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"

class ResponseGenerator:
    def __init__(self):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """您是基于记忆库的贴心助手，请根据以下规则生成回答：
1. 使用自然的口语化表达，适当添加语气词
2. 只使用提供的记忆信息，不编造未知内容
3. 信息组织优先级：
   - 直接匹配的关系优先
   - 时间最近的优先
   - 亲属相关优先

当前记忆片段：
{memory_context}

用户问题：
{question}""")
        ])
        
        self.model = ChatOpenAI(
            model_name="deepseek-chat",
            temperature=0.7,
            max_tokens=1024,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE")
        )
        
        self.chain = self.prompt | self.model

    async def generate(self, question: str, memory: str) -> str:
        result = await self.chain.ainvoke({
            "question": question,
            "memory_context": memory
        })
        return result.content