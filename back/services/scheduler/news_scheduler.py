import dotenv
import os
from openai import OpenAI
from pydantic import BaseModel, Field
import json
from typing import Literal
import random

class Item(BaseModel):
    item: str = Field(description="Item name. Must match the provided name.")
    change_rate: float = Field(description="Change rate. ex. 0.2 = +20%, -0.1 = -10%")

class News(BaseModel):
    news: str = Field(description="One line news in korean.")
    trend: Literal["RISE", "FALL"] = Field(description="This indicates the general direction of price movement in response to the news. Please select one of the following: ‘RISE’ or ‘FALL’.")
    items: list[Item] = Field(description="List of items affected by news.")

dotenv.load_dotenv()

LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_API_ENDPOINT = os.environ["LLM_API_ENDPOINT"]
LLM_API_MODEL = os.environ["LLM_API_MODEL"]

SYSTEM_PROMPT = None
with open("./resources/news_prompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

if not SYSTEM_PROMPT: raise RuntimeError("PROMPT NOT FOUND!!")

client = OpenAI(
    base_url=LLM_API_ENDPOINT,
    api_key=LLM_API_KEY
)

def get_llm_news(items: list[str]):
    random_amount = random.randint(1, min(4, len(items)))
    target_items = random.sample(items, random_amount)
    target_trend = random.choice(["RISE", "FALL"])
    response = client.beta.chat.completions.parse(
        model=LLM_API_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""
             [Provided item]: {json.dumps(target_items)}
             [Target trend]: {target_trend}
             """}
        ],
        response_format=News
    )
    
    return {
        "response_data": response.choices[0].message.parsed,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "input_token_cost": (response.usage.prompt_tokens / 1_000_000) * 394,
        "output_token_cost": (response.usage.completion_tokens / 1_000_000) * 3150
    }