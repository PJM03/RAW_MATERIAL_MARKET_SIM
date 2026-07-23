from fastapi import FastAPI
from services.db_service import DBService
from schemas.api_schema import ApiResponse
from schemas.item_schema import Item
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from services.scheduler.news_scheduler import get_llm_news

scheduler = BackgroundScheduler()

async_db_service = DBService()
def scheduled_job():
    print("LLM News request...")
    response = get_llm_news([i.name for i in get_item_list().data])
    async_db_service.new_news(response)
    print("LLM Response complete!")
    print(response)
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(scheduled_job, "interval", seconds=20)
    scheduler.start()
    print("LLM Scheduler Started.")
    
    yield
    
    scheduler.shutdown()
    print("LLM Scheduler Stoped.")

app = FastAPI(lifespan=lifespan)

db_service = DBService()

@app.get(
    path = "/item/list",
    response_model=ApiResponse[list[Item]])
def get_item_list() -> ApiResponse[list[Item]]:
    result = db_service.get_items()
    
    return ApiResponse(
        success=True,
        message="",
        data=result
    )
    
@app.get(
    path="/item/price/{item_id}",
    response_model=ApiResponse[list]
)
def get_price_list(item_id: int) -> ApiResponse[list]:
    result = db_service.get_price_history(item_id=item_id)
    
    return ApiResponse(
        success=True,
        message="",
        data=result
    )
    
@app.get(
    path="/news"
)
def get_news(id: int):
    result = db_service.get_news(id)
    return ApiResponse(
        success=True,
        message="",
        data=result
    )
    
@app.get(
    path="/news/latest"
)
def get_latest_news():
    result = db_service.get_latest_news()
    return ApiResponse(
        success=True,
        message="",
        data=result
    )
    
@app.get(
    path="/item/data"
)
def get_item_data(id: int):
    result = {}
    result['item'] = db_service.get_item(id)
    phs = db_service.get_price_history(id)
    result['prices'] = [ph.price for ph in phs]
    latest_news_id = max(phs, key=lambda x: x.news_id).news_id
    result['news'] = db_service.get_news(latest_news_id)
    return result

@app.get(
    path="/item/data/all"
)
def get_all_item_data():
    result = {
        "items": [],
        "latest_news": get_latest_news()
    }
    for item in db_service.get_items():
        result["items"].append(get_item_data(item.id))
    
    return result