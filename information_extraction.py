#Description:从用户对话中提取实体和关系，并转换为实体和关系类，也打算分析是否是问句
from typing import List
from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, OPENAI_API_BASE  # 导入配置
import os
import time
import json
import asyncio

#deepseekAPI
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE


# 数据模型定义，使用pydantic库进行数据转换
class EntityNode(BaseModel):
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")

class RelationEdge(BaseModel):
    subject: str = Field(..., description="关系发起方")
    relationship: str = Field(..., description="关系类型")
    object: str = Field(..., description="关系接收方")
    properties: dict = {}  # 默认空字典

class KnowledgeGraph(BaseModel):
    entities: List[EntityNode]
    relations: List[RelationEdge]

# 异步处理核心类
class EntityRelationExtractor:
    def __init__(self):
        self.parser = JsonOutputParser(pydantic_object=KnowledgeGraph)
        self._init_prompt_template()
        self._init_llm_model()
        self._build_async_chain()

    def _init_prompt_template(self):
        """强化格式控制的提示词模板"""
        system_prompt = """您是需要严格遵循以下规则的信息抽取专家，名为Yukino：
1.判断句子类型，如下类型返回实体关系表
    - 疑问句，如“我妈妈在哪？”、“我爸爸的工作是什么？”等
    - 没有明确的实体和关系，如"我很伤心"，“我很想你”等
    - 祈使句，如“帮我买个手机”、“告诉我你喜欢什么”等
2.识别句子中提及的所有实体和关系
   - 实体类型：人物、地点、职业、兴趣、亲属、消费行为、学科、体育运动、消费物品等
   - 关系类型：工作于、居住在、购买过、亲属关系、时间、学习、得分等

3. 实体识别规则：
   - 核心实体：必选userid实体（固定值），type修改为core_user
   - 对于用户的疑问句，则不提取实体和关系，返回空的实体关系表。如"我妈妈居住在上海吗？"则不提取任何关系和实体。
   - 特殊实体处理：
     * "我/本人/咱" → 强制映射为userid
     * 亲属称谓（如父母/子女/朋友等）→ 创建新实体(type=亲属)
     * 用户姓名 → 创建新实体(type=姓名)并建立映射
            [后续动作的发起方]=妈妈
4.实体类型扩展：
   - 数字(包含单位)，type有具体对话场景自行选择，数字必须与其关联的实体绑定。
   - 时间(对话中出现昨天、去年等现在及过去时间时，需要计算出准确的时间，如2025.3.25日、2025.3、2025等)，示例“我昨天吃了草莓”，应该根据现在的时间计算“昨天”是多久，且和实体“草莓”联系，根据情况具体到年月日。
        *注意，如果没办法计算出具体时间，如“以前”、“这次”、“小时候”等模糊时间，则以“过去”来表示时间
        *注意，当出现“今天”、“正在”、“现在”等表示目前的时间时，应该创建目前时间的实体，如“我正在画画”，应该创建“2025.3.35”的实体（假设是今天的日期）
        *如果不包含前两个注意事项，则不需要添加时间
   - 运动，如跑步、打篮球、溜冰等


5. 关系映射规则：
   a. 发起方处理：
      - 遇到代词“我”时替换为userid
      - 明确用户姓名时必须替换为userid （如，“我是小明，喜欢吃草莓“ ->“userid -> 喜欢 -> 草莓”）
      - 亲属实体可独立作为关系发起方（如"妈妈买手机"→妈妈作为发起方）
   b. 亲属双向映射：
      - 建立从属关系：userid→[亲属关系]→亲属实体（如userid→母亲→妈妈）
      - 允许亲属实体独立绑定其他关系

6. 严格输出格式示例：
输入："我妈妈今天在上海买了新手机"
输出：
{{
  "entities":[
    {{"name":"userid","type":"core_user"}},
    {{"name":"妈妈","type":"亲属"}},
    {{"name":"上海","type":"地点"}},
    {{"name":"手机","type":"消费物品"}}，
    {{"name":"2025.3.26","type":"时间"}}
  ],
  "relations":[
    {{"subject":"userid","relationship":"母亲","object":"妈妈"}},
    {{"subject":"妈妈","relationship":"购买过","object":"手机"}},
    {{"subject":"手机","relationship":"发生时间","object":"2025.3.26"}},
  ]
}}
"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "待分析文本：{input}")
        ])

    def _init_llm_model(self):
        self.model = ChatOpenAI(
            model_name="deepseek-chat",
            max_tokens=1024,
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE")
        )

    def _build_async_chain(self):
        """重构处理链路"""
        self.chain = (
            RunnablePassthrough()
            |  {
                "input": RunnablePassthrough()  # 保持输入变量名与提示词模板一致
            }
            | self.prompt
            | self.model
            | RunnableLambda(self._clean_response)
            | self.parser
        )

    async def _clean_response(self, message):
        """强化格式清洗"""
        try:
            content = message.content
            # 处理代码块包裹的情况
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0]
            else:
                json_str = content
                
            # 处理首尾空格和换行符
            return json_str.strip().replace('\n', '')
        except Exception as e:
            print(f"响应清洗失败: {str(e)}")
            return '{"entities":[],"relations":[]}'

    async def extract(self, text: str, userid: str) -> KnowledgeGraph:
        """修复后的异步接口"""
        try:
            start_time = time.time()
            txt = f"此用户的userid是{userid}"
            txt2 = txt+text
            result = await self.chain.ainvoke({"input": txt2})
            # print(f"总处理时间: {time.time()-start_time:.2f}s")
            # print(result)
            return KnowledgeGraph(**result)
        except ValidationError as e:
            print(f"格式校验失败: {str(e)}")
            return KnowledgeGraph(entities=[], relations=[])

# 异步主函数
async def main():
    extractor = EntityRelationExtractor()
    sample_text = "今天吃什么？"
    userid = "user123"
    print(f"正在分析文本：{sample_text}")
    result = await extractor.extract(sample_text,userid)
    #print(result)
    print("\n实体列表:")
    for entity in result.entities:
        print(f" - {entity.name} ({entity.type})")
    
    print("\n关系列表:")
    for rel in result.relations:
        print(f" {rel.subject} -> {rel.relationship} -> {rel.object}")

if __name__ == "__main__":
    asyncio.run(main())
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
