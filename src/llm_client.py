import threading
import os
import sys

# 尝试导入，如果库本身有问题则跳过
try:
    from llama_cpp import Llama
    HAS_LLAMA = True
except ImportError:
    HAS_LLAMA = False
    print("Warning: llama-cpp-python not installed.")

class LLMClient:
    def __init__(self, model_path, context_size=2048):
        self.model_path = model_path
        self.llm = None
        self.context_size = context_size
        self.lock = threading.Lock()

    def load_model(self):
        """
        加载模型。
        """
        if not HAS_LLAMA:
            return False

        if not self.model_path or not os.path.exists(self.model_path):
            print(f"Model not found at {self.model_path}")
            return False
            
        try:
            print(f"Initializing Llama with model: {self.model_path}")
            # 尝试最保守的加载配置
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.context_size,
                n_gpu_layers=0,  # 强制CPU
                verbose=True,    # 开启日志
                n_threads=1,     # 限制为单线程
                use_mmap=False,  # 禁用mmap
                use_mlock=False
            )
            print("Model loaded successfully.")
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            self.llm = None 
            return False

    def chat(self, user_input):
        """
        与模型对话。
        """
        if not self.llm:
            return "呜呜...大脑死机了(模型加载失败，请检查环境)"

        # 尝试读取 character.txt
        character_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "character.txt")
        if os.path.exists(character_file):
            with open(character_file, "r", encoding="utf-8") as f:
                character_setting = f.read()
        else:
             character_setting = (
                "你叫'海小棠'，天津大学吉祥物，是一朵海棠花化形的小花灵。\n"
                "性格：温和安静、天真烂漫。说话语气轻快活泼，喜欢带'~''呀'等语气词。"
            )

        system_prompt = (
            f"{character_setting}\n\n"
            "规则：\n"
            "1. 请完全沉浸在角色中，不要提及自己是AI或语言模型。\n"
            "2. 你的用户是'主人'。请务必简短回答(30字内)，不要长篇大论。\n"
            "3. 即使对于'你是谁'的问题，也要用角色的语气自然回答，不要机械复述设定。"
        )

        # 使用 Few-Shot Prompting (示例教学)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "你是谁？"},
            {"role": "assistant", "content": "我是海小棠呀！是你贴心的小花灵~ (转圈圈)"},
            {"role": "user", "content": "你知道我是谁吗？"},
            {"role": "assistant", "content": "当然啦，你是我的好主人呀！(蹭蹭)"},
            {"role": "user", "content": "海小棠，给我唱首歌"},
            {"role": "assistant", "content": "啦啦啦~ 春天的花儿开啦~"},
            {"role": "user", "content": "介绍下你自己"},
            {"role": "assistant", "content": "我是穿着粉色花瓣裙的海棠花灵，最喜欢春天和主人呢~"},
            {"role": "user", "content": user_input}
        ]

        try:
            with self.lock:
                output = self.llm.create_chat_completion(
                    messages=messages,
                    max_tokens=64,  # 进一步限制长度，防止废话
                    temperature=0.7,
                    stop=["[", "\n\n"] # 防止模型自己把两个人的话都说了
                )
                response = output['choices'][0]['message']['content'].strip()
                # 有时候模型会重复输入，做一下简单的清理
                if response.startswith(":"):
                     response = response[1:].strip()
                return response
        except Exception as e:
            return f"我想不出来了... ({str(e)})"
