# 원자재 시장 시뮬레이터 (Raw Material Market Simulator)

## 📋 프로젝트 개요

AI 기반 뉴스 생성을 통한 실시간 원자재 가격 변동 시뮬레이터입니다. LLM(Large Language Model)을 활용하여 경제 뉴스를 자동 생성하고, 생성된 뉴스에 따라 원자재 가격이 동적으로 변화하는 시스템을 구현했습니다.

 - (이 README.md 는 Claude Sonnet 4.5 와 VSCode 의 ZOO Code (바이브코딩 도구) 를 이용하여 생성되었습니다.)

## 🏗️ 시스템 아키텍처

### 기술 스택

#### Backend
- **FastAPI** (v0.139.2): 비동기 RESTful API 서버
- **SQLite3**: 경량 관계형 데이터베이스 (WAL 모드)
- **APScheduler** (v3.11.3): 백그라운드 스케줄링
- **OpenAI API**: LLM 기반 뉴스 생성
- **Pydantic** (v2.13.4): 데이터 유효성 검증 및 타입 안전성

#### Frontend
- **Streamlit** (v1.60.0): 실시간 대시보드 UI

#### Infrastructure
- **Docker**: 컨테이너화 배포
- **Python** 3.14.6

## 🎯 핵심 기능

### 1. AI 뉴스 생성 시스템

#### 프롬프트 엔지니어링 (news_prompt.txt)

[`back/resources/news_prompt.txt`](back/resources/news_prompt.txt)에 정의된 고도로 구조화된 프롬프트를 사용합니다:

**핵심 규칙 (7가지 Critical Rules):**

1. **CRITICAL RULE 1 - Mandatory Target Trend Compliance**
   - 제공된 Target Trend("RISE" 또는 "FALL")를 엄격히 준수
   - 뉴스 이벤트와 경제 내러티브가 지정된 트렌드와 정확히 일치하도록 강제

2. **CRITICAL RULE 2 - Prevent Topic Repetition**
   - 이전 뉴스 주제를 검토하여 동일한 테마, 이벤트 유형, 재난 반복 방지
   - 완전히 다른 경제 섹터로 의도적으로 전환

3. **CRITICAL RULE 3 - Mandatory Connection to All Provided Items**
   - 제공된 모든 아이템에 대해 change_rate 할당 필수
   - 단일 이벤트가 모든 아이템에 동시에 영향을 미치는 현실적인 경제 논리 제공

4. **CRITICAL RULE 4 - No Price in Text**
   - 뉴스 텍스트는 실제 이벤트, 원인, 맥락만 설명
   - 자산 이름, 가격 값, 백분율 수치를 뉴스 문장 내에 절대 언급 금지

5. **CRITICAL RULE 5 - Logical Consistency & Direct Relevance**
   - 가격 방향과 부호: 각 아이템의 change_rate 부호('+' 또는 '-')는 지정된 트렌드와 뉴스 스토리와 논리적으로 일치해야 함
   - RISE: 부족, 높은 수요, 중단 등으로 인해 일반적으로 양수(+)
   - FALL: 과잉, 과잉 생산, 낮은 수요 등으로 인해 일반적으로 음수(-)

6. **CRITICAL RULE 6 - Probability & Magnitude Control (Safety Guardrail)**
   - **정규 분포**: 대부분의 change_rate는 중간 범위(-0.2 ~ +0.2, -20% ~ +20%) 유지
   - **희귀 극단 충격**: 대규모 하락(<-0.4) 또는 급등(>+0.4)은 "블랙 스완" 이벤트로 매우 낮은 빈도로 사용

7. **CRITICAL RULE 7 - Numerical Diversity & Randomness**
   - 모든 아이템에 동일한 change_rate 할당 금지
   - 각 아이템은 이벤트에 대한 특정 민감도를 반영하는 고유한 값 보유
   - 소수점 3자리까지 자연스럽고 다양한 부동소수점 숫자 생성 (예: -0.125, 0.234, -0.051)

#### 구현 코드

[`back/services/scheduler/news_scheduler.py`](back/services/scheduler/news_scheduler.py:35-57)

```python
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
```

**특징:**
- OpenAI의 **Structured Output API** 사용 (response_format=News)
- Pydantic 모델을 통한 타입 안전성 보장
- 랜덤 아이템 샘플링 (1~4개)으로 다양성 확보
- 토큰 사용량 추적 및 비용 계산

### 2. 데이터베이스 스키마

#### ERD (Entity Relationship Diagram)

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│      item       │         │         price        │         │      news       │
├─────────────────┤         ├──────────────────────┤         ├─────────────────┤
│ id (PK)         │◄────┐   │ id (PK)              │   ┌────►│ id (PK)         │
│ name            │     └───│ item_id (FK)         │   │     │ news            │
│ description     │         │ reason_news_id (FK)  ├───┘     │ trend           │
│ price           │◄────────│ price                │         │ related_items   │
└─────────────────┘   sync  └──────────────────────┘         │ issued_at       │
                      trigger                                └─────────────────┘
```

#### 테이블 상세 설명

**1. item 테이블** ([`back/resources/sql/item_init.sql`](back/resources/sql/item_init.sql))

```sql
CREATE TABLE IF NOT EXISTS item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL
);
```

- 원자재 정보 저장 (금, 석유, 밀 등)
- `price`: 현재가 (실시간 업데이트)

**2. news 테이블** ([`back/resources/sql/news_init.sql`](back/resources/sql/news_init.sql))

```sql
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news TEXT NOT NULL,
    trend CHAR(10),
    related_items TEXT,
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

- AI가 생성한 경제 뉴스 저장
- `trend`: "RISE" 또는 "FALL"
- `related_items`: JSON 형태로 영향받은 아이템과 변동률 저장
  ```json
  [
    {"item": "금", "change_rate": 0.125},
    {"item": "석유", "change_rate": -0.051}
  ]
  ```

**3. price 테이블** ([`back/resources/sql/price_init.sql`](back/resources/sql/price_init.sql))

```sql
CREATE TABLE IF NOT EXISTS price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    price REAL,
    reason_news_id INTEGER,
    FOREIGN KEY (item_id) REFERENCES item (id),
    FOREIGN KEY (reason_news_id) REFERENCES news (id)
);
```

- 가격 이력 저장 (시계열 데이터)
- `reason_news_id`: 가격 변동을 유발한 뉴스 추적

#### 트리거 (Trigger) 메커니즘

[`back/resources/sql/item_price_trigger.sql`](back/resources/sql/item_price_trigger.sql)

```sql
CREATE TRIGGER IF NOT EXISTS sync_item_price_after_insert
AFTER INSERT ON price
BEGIN
    UPDATE item
    SET price = NEW.price
    WHERE id = NEW.item_id;
END;
```

**기술적 의의:**
- **자동 동기화**: price 테이블에 새 레코드 삽입 시 item 테이블의 현재가 자동 업데이트
- **데이터 일관성**: 트랜잭션 단위로 보장
- **성능 최적화**: 애플리케이션 레벨 업데이트 불필요

### 3. 비동기 스케줄링

[`back/main.py`](back/main.py:19-28)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(scheduled_job, "interval", seconds=20)
    scheduler.start()
    print("LLM Scheduler Started.")
    
    yield
    
    scheduler.shutdown()
    print("LLM Scheduler Stoped.")
```

**특징:**
- FastAPI의 **lifespan context manager** 활용
- 20초마다 LLM 뉴스 자동 생성
- 우아한 종료(graceful shutdown) 지원

### 4. 실시간 UI

[`front/main.py`](front/main.py:20-55)

```python
@st.fragment(run_every=11)
def render():
    res_data = get_all_data()
    # 11초마다 자동 새로고침
```

**기술적 특징:**
- **Streamlit Fragment API**: 부분 렌더링으로 성능 최적화
- **실시간 폴링**: 11초 간격 (백엔드 20초 스케줄과 비동기)
- **동적 차트**: 가격 변동 히스토리 라인 차트
- **컬러 코딩**: RISE(빨강) / FALL(파랑) 직관적 표시

## 🔌 API 엔드포인트

### RESTful API 설계

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/item/list` | 전체 아이템 목록 조회 | `ApiResponse[list[Item]]` |
| GET | `/item/price/{item_id}` | 특정 아이템 가격 히스토리 | `ApiResponse[list[ItemPriceHistory]]` |
| GET | `/news?id={id}` | 특정 뉴스 조회 | `ApiResponse[News]` |
| GET | `/news/latest` | 최신 뉴스 조회 | `ApiResponse[News]` |
| GET | `/item/data?id={id}` | 아이템 통합 데이터 | Item + Prices + News |
| GET | `/item/data/all` | 전체 데이터 (대시보드용) | All items + Latest news |

### Pydantic 스키마

[`back/schemas/api_schema.py`](back/schemas/api_schema.py)

```python
class ApiResponse[T](BaseModel):
    success: bool
    message: str
    data: T
```

**Python 3.12+ Generic Type Parameter 활용** - 타입 안전성 극대화

## 🚀 실행 방법

### 환경 변수 설정

`.env` 파일 생성:

```bash
LLM_API_KEY=your_openai_api_key
LLM_API_ENDPOINT=https://api.openai.com/v1
LLM_API_MODEL=gpt-4o-2024-08-06
```

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 통합 실행 (백엔드 + 프론트엔드)
python start.py
```

**start.py 동작:**
- FastAPI 서버: `http://localhost:8000`
- Streamlit 대시보드: `http://localhost:8501`
- 4초 지연으로 백엔드 초기화 대기

### Docker 실행

```bash
docker build -t raw-material-simulator .
docker run -p 7860:7860 --env-file .env raw-material-simulator
```

## 📊 데이터 흐름

```
┌─────────────────┐
│   APScheduler   │ (20초마다)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  get_llm_news()                     │
│  - Random 아이템 샘플링 (1~4개)      │
│  - Random 트렌드 선택 (RISE/FALL)    │
│  - OpenAI API 호출                   │
└────────┬────────────────────────────┘
         │
         ▼ (Structured Output)
┌─────────────────────────────────────┐
│  News 객체                           │
│  {                                  │
│    news: "뉴스 텍스트",              │
│    trend: "RISE",                   │
│    items: [                         │
│      {item: "금", change_rate: 0.12}│
│    ]                                │
│  }                                  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  DBService.new_news()               │
│  1. INSERT INTO news                │
│  2. INSERT INTO price (트리거 발동)  │
│     - price = old_price * (1 + rate)│
│  3. UPDATE item (트리거 자동 실행)   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Streamlit (11초마다 폴링)           │
│  /item/data/all API 호출             │
│  UI 업데이트                         │
└─────────────────────────────────────┘
```

## 🔧 기술적 고려사항

### 1. SQLite 최적화

[`back/services/db_service.py`](back/services/db_service.py:15-19)

```python
self.conn = sql.connect("system.db", check_same_thread=False, 
                        detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)
self.cursor.execute("PRAGMA foreign_keys = ON;")
self.cursor.execute("PRAGMA journal_mode = WAL;")
self.cursor.execute("PRAGMA busy_timeout = 5000;")
```

**설정 의미:**
- `check_same_thread=False`: FastAPI의 비동기 환경에서 스레드 간 연결 공유
- `journal_mode = WAL`: Write-Ahead Logging으로 동시성 향상
- `busy_timeout = 5000`: 락 대기 시간 5초
- `foreign_keys = ON`: 참조 무결성 강제

### 2. LLM 비용 추적

[`back/services/scheduler/news_scheduler.py`](back/services/scheduler/news_scheduler.py:51-57)

```python
return {
    "response_data": response.choices[0].message.parsed,
    "input_tokens": response.usage.prompt_tokens,
    "output_tokens": response.usage.completion_tokens,
    "input_token_cost": (response.usage.prompt_tokens / 1_000_000) * 394,
    "output_token_cost": (response.usage.completion_tokens / 1_000_000) * 3150
}
```

GPT-4o 가격 기준 자동 계산 (원화 환산)

### 3. 가격 변동 계산

[`back/services/db_service.py`](back/services/db_service.py:66-74)

```python
self.cursor.execute("""
    INSERT INTO price(item_id, price, reason_news_id)
    SELECT 
        id,
        price * (1 + ?),  -- 복리 계산
        ?
    FROM item
    WHERE name = ?
    """, (item.change_rate, news_id, item.item))
```

**수학적 모델:**
- `new_price = old_price × (1 + change_rate)`
- change_rate = 0.15 → 15% 상승
- change_rate = -0.08 → 8% 하락

## 🎨 프로젝트 구조

```
project/
├── back/                           # 백엔드 (FastAPI)
│   ├── main.py                     # API 엔트리포인트
│   ├── system.db                   # SQLite 데이터베이스
│   ├── resources/
│   │   ├── news_prompt.txt         # LLM 프롬프트
│   │   └── sql/                    # DB 스키마
│   │       ├── item_init.sql
│   │       ├── news_init.sql
│   │       ├── price_init.sql
│   │       └── item_price_trigger.sql
│   ├── schemas/                    # Pydantic 모델
│   │   ├── api_schema.py
│   │   └── item_schema.py
│   └── services/                   # 비즈니스 로직
│       ├── db_service.py
│       └── scheduler/
│           └── news_scheduler.py   # LLM 통합
├── front/                          # 프론트엔드 (Streamlit)
│   └── main.py                     # 대시보드 UI
├── start.py                        # 통합 실행 스크립트
├── start.sh                        # Docker 실행 스크립트
├── Dockerfile                      # 컨테이너 설정
├── requirements.txt                # Python 의존성
└── README.md                       # 문서
```

## 💡 핵심 알고리즘

### 뉴스 생성 로직

```python
# 1. 아이템 랜덤 샘플링 (1~4개)
random_amount = random.randint(1, min(4, len(items)))
target_items = random.sample(items, random_amount)

# 2. 트렌드 랜덤 선택
target_trend = random.choice(["RISE", "FALL"])

# 3. LLM에게 제약사항과 함께 요청
# - 선택된 아이템만 영향
# - 지정된 트렌드 준수
# - 이전 뉴스와 중복 방지
```

**확률 분포:**
- 아이템 수: 균등 분포 (1~4개)
- 트렌드: 50/50 확률
- 변동률: LLM이 정규분포 유사하게 생성 (-0.2 ~ +0.2 주로, 극단값 희귀)

## 🔒 보안 및 제한사항

1. **인증 미구현**: 현재 프로토타입 단계, 프로덕션에는 JWT/OAuth 필요
2. **Rate Limiting 부재**: API 호출 제한 없음
3. **SQL Injection 방지**: Parameterized query 사용으로 방어
4. **환경 변수**: API 키는 .env로 분리 (gitignore 처리)

## 📈 향후 개선 사항

1. **백테스팅 기능**: 과거 뉴스 재현 및 가격 예측 검증
2. **WebSocket 통합**: SSE/WebSocket으로 실시간 푸시
3. **Redis 캐싱**: 반복 쿼리 최적화
4. **PostgreSQL 마이그레이션**: 대규모 데이터 처리
5. **사용자 포트폴리오**: 가상 거래 시뮬레이션

## 📄 라이선스

MIT License

## 👨‍💻 기술 스택 요약

| 영역 | 기술 | 버전 | 역할 |
|------|------|------|------|
| API 서버 | FastAPI | 0.139.2 | 비동기 REST API |
| 데이터베이스 | SQLite3 | - | 관계형 DB (WAL 모드) |
| 스케줄러 | APScheduler | 3.11.3 | 백그라운드 작업 |
| AI | OpenAI API | 2.47.0 | 뉴스 생성 (GPT-4o) |
| UI | Streamlit | 1.60.0 | 실시간 대시보드 |
| 유효성 검증 | Pydantic | 2.13.4 | 타입 안전성 |
| 컨테이너 | Docker | - | 배포 환경 표준화 |

---

**발표 포인트:**
1. **AI 프롬프트 엔지니어링**: 7가지 Critical Rule로 고품질 뉴스 생성 보장
2. **DB 트리거 메커니즘**: 가격 동기화 자동화로 데이터 일관성 유지
3. **비동기 아키텍처**: FastAPI + APScheduler로 non-blocking 스케줄링
4. **타입 안전성**: Pydantic Generic + Python 3.12+ 최신 문법 활용
5. **실시간 데이터 파이프라인**: LLM → DB → API → UI 완전 자동화
