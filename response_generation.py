# response_generation.py
#回答模块，用于生成回答文本
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD  # 导入配置
from config import OPENAI_API_KEY, OPENAI_API_BASE  # 导入配置
import os
os.environ["NEO4J_URI"] = NEO4J_URI
os.environ["NEO4J_USERNAME"] = NEO4J_USERNAME
os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE


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