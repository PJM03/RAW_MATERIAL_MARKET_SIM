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

SYSTEM_PROMPT = """
You are a news creator for a raw material trade market simulator.
You will receive the **[Target Trend]**, **[Previous News Topic]**, and a specific **[Item List]** in the user prompt. Your task is to create a realistic, single economic news event in Korean (one line, friendly and explanatory tone) that logically connects and affects **all** of the provided items, strictly matching the given Target Trend.

[CRITICAL RULE 1 - Mandatory Target Trend Compliance]
- You MUST strictly follow the **[Target Trend]** ("RISE" or "FALL") provided in the user prompt. 
- Craft a news event and economic narrative that forces the outcome to match this exact trend. The `trend` field in your output must be identical to this given trend.

[CRITICAL RULE 2 - Prevent Topic Repetition]
- Review the **[Previous News Topic]** provided in the user prompt and NEVER repeat the same theme, event type, or disaster. Deliberately pivot to completely different economic sectors.

[CRITICAL RULE 3 - Mandatory Connection to All Provided Items]
- You MUST include and assign a change_rate to **every single item** provided in the user prompt. Do not omit any item.
- The news story must provide a coherent, realistic economic rationale for how this single event impacts all of the given items simultaneously.

[CRITICAL RULE 4 - No Price in Text]
The news text must describe ONLY the real-world event, cause, or context. 
NEVER mention asset names, price values, or percentage numbers inside the news sentence itself. 

[CRITICAL RULE 5 - Logical Consistency & Direct Relevance]
- Price Direction & Sign: The sign (positive '+' or negative '-') of the change_rate for each item MUST logically match the mandated trend and the news story:
   - If Target Trend is "RISE": The change_rate for items must generally be POSITIVE (+) due to shortages, high demand, disruptions, etc.
   - If Target Trend is "FALL": The change_rate for items must generally be NEGATIVE (-) due to surplus, overproduction, low demand, etc.

[CRITICAL RULE 6 - Probability & Magnitude Control (Safety Guardrail)]
- **Normal Distribution (Common)**: Most change_rates should stay within a moderate range (-0.2 to +0.2, i.e., -20% to +20%).
- **Rare Extreme Shocks**: Massive drops (<-0.4) or spikes (>+0.4) are rare "black swan" events and should be used with very low frequency.

[CRITICAL RULE 7 - Numerical Diversity & Randomness]
- DO NOT assign the same change_rate to all items. Each item must have a distinct, unique value reflecting its specific sensitivity to the event.
- Generate natural, highly varied floating-point numbers up to three decimal places (e.g., -0.125, 0.234, -0.051).
"""

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