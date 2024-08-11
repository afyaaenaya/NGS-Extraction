import os

def get_api_keys():

    llama_cloud_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not llama_cloud_api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY is not set. Please set it in the environment.")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set. Please set it in the environment.")
    
    return llama_cloud_api_key, openai_api_key