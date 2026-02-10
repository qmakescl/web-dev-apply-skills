# SQLite에서 Vercel PostgreSQL로 마이그레이션 가이드

사용자 질문: *"SQLite3를 PostgreSQL로 변경하기만 하면 Vercel의 PostgreSQL을 사용할 수 있는 것인가?"*

**답변: "아니요, 단순히 설정만 바꾼다고 되지 않습니다. 코드 수정이 필요합니다."**

`app.py`와 `database.py`가 현재 Python의 **내장 `sqlite3` 모듈**을 사용해 **Raw SQL**을 직접 작성하는 방식으로 구현되어 있기 때문입니다. PostgreSQL은 다른 드라이버(`psycopg2` 등)를 사용하며, SQL 문법(Placeholder)도 다릅니다.

본 문서는 이를 변경하기 위해 필요한 구체적인 작업 내역을 안내합니다.

## 1. 라이브러리 변경 (Dependencies)

내장 `sqlite3` 대신 PostgreSQL 연결을 위한 드라이버를 설치해야 합니다.

```bash
uv add psycopg2-binary
```

## 2. 데이터베이스 연결 설정 (`database.py` 수정)

`sqlite3.connect` 대신 `psycopg2.connect`를 사용해야 하며, 파일 경로가 아닌 **Connection String (DSN)**을 사용합니다.

**변경 전 (SQLite)**:
```python
import sqlite3

def get_db():
    conn = sqlite3.connect("insta_lite.db")
    # ...
```

**변경 후 (PostgreSQL)**:
```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Vercel 환경 변수에서 DB URL을 가져옴
DATABASE_URL = os.environ.get("POSTGRES_URL") 

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()
```

## 3. SQL 쿼리 문법 수정 (`app.py` 전반)

가장 큰 작업입니다. SQLite와 PostgreSQL은 SQL 파라미터를 바인딩하는 기호(Placeholder)가 다릅니다.

*   **SQLite**: `?`
*   **PostgreSQL (`psycopg2`)**: `%s`

**수정 예시 (`app.py`)**:

```python
# [SQLite]
cursor = db.execute("SELECT * FROM users WHERE email = ?", (email,))

# [PostgreSQL]
# psycopg2는 cursor.execute()를 명시적으로 호출해야 함
with db.cursor() as cursor:
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
```

모든 `db.execute(..., (?, ?))` 형태의 코드를 찾아서 `%s`로 바꾸고 커서 사용법을 변경해야 합니다.

## 4. 테이블 생성 (Schema Migration)

SQLite 파일이 없으므로, PostgreSQL 데이터베이스에 접속해서 테이블(`users`, `posts`, `comments`, `likes`)을 새로 생성해 주어야 합니다.
Vercel 대시보드의 "Storage" 탭에서 "Query" 기능을 이용해 `init_db`에 있던 SQL 문을 실행하거나, 별도의 마이그레이션 스크립트를 돌려야 합니다.

**Create Table 쿼리 예시 (Postgres 호환)**:
```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY, -- INTEGER PRIMARY KEY AUTOINCREMENT 대신 SERIAL 사용
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
-- 나머지 테이블들도 PostgreSQL 문법(SERIAL, TIMESTAMP 등)에 맞춰 수정 필요
```

## 5. 추천하는 해결책: ORM 도입 (SQLAlchemy)

직접 `psycopg2`를 쓰면 위처럼 모든 SQL을 일일이 고쳐야 합니다. 만약 프로젝트 초기에 **SQLAlchemy** 같은 ORM을 사용했다면, DB URL만 바꾸면 코드 수정 없이 마이그레이션이 가능했을 것입니다.

**장기적으로는**:
Raw SQL을 유지하면서 `psycopg2`로 전환하는 것보다, 이번 기회에 **SQLAlchemy**를 도입하여 DB 의존성을 낮추는 리팩토링을 고려해보시는 것도 좋습니다.

## 6. 결론

Vercel PostgreSQL을 쓰려면 다음 3단계가 필수입니다.
1.  `psycopg2-binary` 설치.
2.  `database.py`에서 연결 로직 교체.
3.  `app.py`의 모든 SQL 쿼리에서 `?`를 `%s`로 변경하고, `AUTOINCREMENT` 등을 Postgres 문법(`SERIAL`)으로 변경.

---
**작성일**: 2026-02-10
**작성자**: Google Antigravity
