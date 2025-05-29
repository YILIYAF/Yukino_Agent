# Description: 知识图谱管理器，负责将信息存入图数据库
from typing import Union
from neo4j import GraphDatabase, Transaction
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD  # 导入配置
from information_extraction import EntityRelationExtractor, KnowledgeGraph  
from information_extraction import EntityNode, RelationEdge
import logging
import os
import asyncio

#ne04j数据库连接信息，请在防火墙中开启端口7474的输入输出权限，否则无法连接
#名字和密码改成自己的
os.environ["NEO4J_URI"] = NEO4J_URI
os.environ["NEO4J_USERNAME"] = NEO4J_USERNAME
os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD

class EnhancedNeo4jConnector:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.extractor = EntityRelationExtractor()  # 直接实例化信息抽取模块
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    async def process_text(self, text: str, userid: str) -> Union[KnowledgeGraph, None]:
        """端到端处理流程：文本分析+数据存储"""
        try:
            # 调用信息抽取模块（注意异步调用）
            kg = await self.extractor.extract(text, userid)
            
            entities = kg.entities  # 直接获取EntityNode实例列表
            relations = kg.relations  # 直接获取RelationEdge实例列表
            
            # 存储到图数据库
            success = self.store_graph_data(entities, relations)
            return kg if success else None
        except Exception as e:
            self.logger.error(f"端到端处理失败: {str(e)}")
            return None


    def _execute_transaction(self, tx: Transaction, entities: list, relations: list) -> None:
        """使用APOC实现智能关系合并"""
        try:
            # 批量合并节点（自动去重）
            merge_nodes_query = """
            UNWIND $entities AS entity
            CALL apoc.merge.node(
                [entity.type],
                {name: entity.name},
                {create_time: datetime()},  
                {}
            ) YIELD node
            RETURN count(node)
            """
            tx.run(merge_nodes_query, entities=[e.dict() for e in entities])

            # 批量合并关系（自动跳过已存在关系）
            merge_rels_query = """
            UNWIND $rels AS rel
            MATCH (s {name: rel.subj}), (o {name: rel.obj})
            CALL apoc.merge.relationship(
                s, 
                rel.type,
                {}, 
                {create_time: datetime()},
                o,
                {}
            ) YIELD rel AS createdRel
            RETURN count(createdRel)
            """
            # 转换关系格式
            rel_params = [{
                "subj": r.subject,
                "obj": r.object,
                "type": r.relationship.upper()
            } for r in relations]
            
            tx.run(merge_rels_query, rels=rel_params)
        except Exception as e:
            self.logger.error(f"事务执行失败: {str(e)}")
            raise  # 触发自动回滚

    def store_graph_data(self, entities: list, relations: list) -> bool:
        """带事务管理的存储入口"""
        with self.driver.session() as session:
            try:
                # 使用APOC的事务管理
                result = session.execute_write(
                    lambda tx: self._execute_transaction(tx, entities, relations)
                )
                return True
            except Exception as e:
                self.logger.error(f"数据存储失败: {str(e)}")
                # 自动触发事务回滚
                return False
            finally:
                self.driver.close()

    def validate_connection(self) -> bool:
        """验证数据库连接"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN apoc.version()")  # 验证APOC安装
                return True if result else False
        except Exception as e:
            self.logger.error(f"数据库连接异常: {str(e)}")
            return False

# 使用示例
async def test_integrated_flow():
    """端到端流程测试（文本输入到数据库存储）"""
    connector = EnhancedNeo4jConnector()
    
    # 测试正常流程
    #我叫小明，在上海腾讯公司工作，担任后端开发工程师，擅长GO和Python
    #我的女朋友是赵薇
    #我的妈妈在上海买了小米SU7Pro
    #我这次月考语文得了2分
    sample_text = "我的妈妈上周在上海买了小米SU7Pro"
    userid = "user123"
    
    result = await connector.process_text(sample_text, userid)
    assert result is not None, "流程执行失败"
    
    # # 验证数据库记录
    # with connector.driver.session() as session:
    #     query = """
    #     MATCH (u:core_user {name: $userid})-[:母亲]->(m:亲属)-[:购买过]->(p)
    #     RETURN m.name AS mother_name, p.name AS product
    #     """
    #     records = session.run(query, userid=userid).data()
    #     assert len(records) > 0, "预期关系未创建"

if __name__ == "__main__":
    # 异步执行测试
    asyncio.run(test_integrated_flow())