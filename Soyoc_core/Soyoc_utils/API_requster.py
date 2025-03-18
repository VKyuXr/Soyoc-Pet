import requests
import openai

class APIRequster:
    API_platform_list = [
        {
            "platform_name": "siliconflow",
            "platform_url": "https://api.siliconflow.cn/v1/chat/completions",
            "compatible_openai": False
        },
        {
            "platform_name": "deepseek",
            "platform_url": "https://api.deepseek.com",
            "compatible_openai": True
        }
    ]

    def __init__(self, config_editor):
        self.config_editor = config_editor

        for API_platform in self.API_platform_list:
            if self.config_editor.target_platform == API_platform["platform_name"]:
                self.target_url = API_platform["platform_url"]
                self.compatible_openai = API_platform["compatible_openai"]

    def request_API(self, messages: list):
        if self.compatible_openai:
            client = openai.OpenAI(api_key=self.config_editor.api_key, base_url=self.target_url)

            response = client.chat.completions.create(
                model=self.config_editor.target_model,
                messages=messages,
                stream=False
            )

            message = response.choices[0].message.content
            tokens_info = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        elif self.target_url == "https://api.siliconflow.cn/v1/chat/completions":
            url = self.target_url

            payload = {
                "model": self.config_editor.target_model,
                "messages": messages,
                "stream": False,
                "max_tokens": 512,
                "stop": None,
                "temperature": 0.7,
                "top_p": 0.7,
                "top_k": 50,
                "frequency_penalty": 0.5,
                "n": 1,
                "response_format": {"type": "text"},
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "description": "<string>",
                            "name": "<string>",
                            "parameters": {},
                            "strict": False
                        }
                    }
                ]
            }
            headers = {
                "Authorization": f"Bearer {self.config_editor.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.request("POST", url, json=payload, headers=headers)
            message = response.json()["choices"][0]["message"]["content"].strip()
            tokens_info = response.json()["usage"]
            tokens_info_str = str(tokens_info).replace("{", "").replace("}", "").replace("'", "")
        return message, tokens_info_str
