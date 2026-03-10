"""
最小复现：与 tts/ai_anchor.py 完全相同的 OpenAI 调用方式，用于排查环境问题。
"""
import os
import sys

# 加载项目根目录的 .env
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("请设置 OPENAI_API_KEY")
    sys.exit(1)

print("调用 OpenAI...")
client = OpenAI(api_key=api_key)
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "说一个字：好"},
    ],
)
print("回复:", resp.choices[0].message.content)
print("OK")
