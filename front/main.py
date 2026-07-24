import streamlit as st
import pandas as pd
import requests, json

st.set_page_config(layout="wide")


st.title("원자재 실시간 가격")

def get_all_data() -> pd.DataFrame:
    response = requests.get(f"http://127.0.0.1:8000/item/data/all")
    response.raise_for_status()
    
    return response.json()

def text_slice(text: str, max_len: int):
    if len(text) <= max_len: return text
    return f"{text[:max_len]}..."

@st.fragment(run_every=16)
def render():
    res_data = get_all_data()
    item_data = res_data["items"]
    latest_news = res_data["latest_news"]['data']
    
    with st.chat_message(
        name="news",
        avatar="📰"
    ):
        news_status = latest_news['trend'] == "RISE"
        related_items = json.loads(latest_news['related_items'])
        st.write(latest_news['news'])
        mapped = [f":{"red" if news_status else "blue"}-badge[{x['item']} {"▲" if news_status else "▼"} {abs(x['change_rate']) * 100:.2f}%]" for x in related_items]
        st.markdown(' '.join(mapped))
        
    for data in item_data:
        price_status = data['news']['trend'] == "RISE"
        with st.container(border=True):
            st.badge(
                text_slice(data['news']['news'], 100), 
                color="red" if price_status else "blue")
            delta = (data["prices"][-1] - data["prices"][-2]) / data['prices'][-2] * 100
            c1, c2, c3 = st.columns([1.5, 6.5, 2])
            with c1:
                st.write(data["item"]["description"])
                st.caption(data["item"]["name"])
            with c2:
                st.line_chart(data=data['prices'], height="stretch", color="red" if price_status else "blue")
            with c3:
                st.metric(
                    label="현재가 (KRW)",
                    value=f"{data['item']['price']:.2f}",
                    delta=f"{delta:.2f}%"
                )
render()