
import pyttsx3  # 导入语音合成库
# 列出所有可用的语音类型
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for index, voice in enumerate(voices):
    print(f"语音索引：{index}")
    print(f"语音名称：{voice.name}")
    print(f"语音ID：{voice.id}")
    print(f"语音语言：{voice.languages}\n")