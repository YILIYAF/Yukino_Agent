import os

# Neo4j 配置
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "atomic-freddie-good-junior-master-5636"

# OpenAI 配置
OPENAI_API_KEY = "sk-1208d9a0f40147138cf2b5477bf1a14b"
OPENAI_API_BASE = "https://api.deepseek.com"

# 设置环境变量（可选）
os.environ["NEO4J_URI"] = NEO4J_URI
os.environ["NEO4J_USERNAME"] = NEO4J_USERNAME
os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE