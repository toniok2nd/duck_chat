from enum import Enum


class ModelType(Enum):
    GPT4o = "gpt-4o-mini"
    Claude = "claude-3-haiku-20240307"
    Llama = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    Mistral = "mistralai/Mistral-Small-24B-Instruct-2501"
    o3mini = "o3-mini"
