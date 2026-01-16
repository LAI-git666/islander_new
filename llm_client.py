# llm_client.py
import os
import json
import re
import time
import logging
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        # --- 配置区域 (在此处填入您的真实信息) ---
        # 如果初始化时没传参数，就使用这里的默认值
        self.default_api_key = "sk-b0102b6ee8ad4403b4b1a237d2508881"  # <--- 请替换为您的真实 Key
        self.default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.default_model = "qwen-max" # 或 qwen-max
        # ---------------------------------------

        self.client = OpenAI(
            api_key=api_key or self.default_api_key,
            base_url=base_url or self.default_base_url
        )
        self.model = model or self.default_model

    def get_response(self, system_prompt: str, user_prompt: str, max_retries=3) -> dict:
        """调用 LLM 并强制返回 JSON 字典。"""
        retries = 0
        while retries < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    # 千问兼容模式可能对 json_object 格式支持不同
                    # 为保稳定，暂时不加 response_format 参数，依靠 Prompt 约束和正则提取
                )
                
                raw_content = response.choices[0].message.content
                # print(f"DEBUG Raw Response: {raw_content}") # 调试时可打开

                # 正则提取 JSON (应对 ```json ... ``` 包裹的情况)
                json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
                
                if json_match:
                    clean_json_str = json_match.group(0)
                    return json.loads(clean_json_str)
                else:
                    logger.warning(f"No JSON found in response: {raw_content}")
                    
            except Exception as e:
                logger.error(f"API Error: {e}. Retrying {retries+1}/{max_retries}...")
            
            retries += 1
            time.sleep(2 ** retries)

        # 失败保底
        logger.error("Max retries reached. Returning default IDLE action.")
        return {"thought": "API Failed", "action": "idle"}

