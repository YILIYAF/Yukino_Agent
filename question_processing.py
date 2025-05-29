# question_processing.py
# 问题分析模块，用于分析用户提问中的核心实体和关系类型
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from pydantic import ValidationError
from config import OPENAI_API_KEY, OPENAI_API_BASE  # 导入配置
import os

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

class QuestionEntities(BaseModel):
    target_entities: list[str] = Field(..., description="问题中涉及的核心实体列表")
    possible_relations: list[str] = Field(..., description="问题中可能涉及的关系类型")

class QuestionAnalyzer:
    def __init__(self):
        self.parser = JsonOutputParser(pydantic_object=QuestionEntities)
        
        system_prompt = """您需要精确识别问题中的关键要素：
1. 核心实体提取规则：
   - 必须包含userid(把代词“我”替换为userid)
   - 识别亲属称谓（自动映射类型）：
     * 爸爸/父亲 → 亲属类型
     * 女朋友/女友 → 亲属类型
     
2. 关系类型推断规则：
   - "工作" → ["职业"]
   - "兴趣爱好" → ["喜欢","关注"]
   - "买了什么" → ["购买过"]
   
示例：
问题：我爸的工作是什么？
输出：{{"target_entities": ["user123", "爸爸"], "possible_relations": ["职业"]}}"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "待分析问题：{question}")
        ])
        
        self.model = ChatOpenAI(
            model_name="deepseek-chat",
            temperature=0.2,
            max_tokens=512,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE")
        )
        
        self.chain = (
            {"question": RunnablePassthrough()}
            | self.prompt
            | self.model
            | self.parser
        )

    async def analyze(self, question: str, userid: str) -> QuestionEntities:
        processed_question = "用户userid:"+userid+"用户提问："+question
        raw_result = await self.chain.ainvoke(processed_question)
        # 将原始字典转换为Pydantic模型
        try:
            result = QuestionEntities(**raw_result)
        except ValidationError as e:
            # 处理解析失败的情况
            print(f"解析错误: {str(e)}")
            result = QuestionEntities(target_entities=[userid], possible_relations=[])

        # 确保userid始终存在
        if userid not in result.target_entities:
            result.target_entities.insert(0, userid)
        
        return result