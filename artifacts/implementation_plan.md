# 워크숍용 인스타 라이트 (Insta-Lite) 구현 계획

이 문서는 사용자의 PRD와 [Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines), Responsive Design 원칙을 반영하여 "Insta-Lite"를 구현하기 위한 계획입니다.

## User Review Required

> [!IMPORTANT]
> **디자인 시스템**: 외부 CSS 프레임워크(Bootstrap, Tailwind 등) 없이 **Vanilla CSS**만을 사용하여 Responsive Design과 Web Guidelines를 준수하는 자체 디자인 시스템(Variables, Utility classes)을 구축합니다.
>
> **데이터베이스**: SQLite를 사용하며, 별도의 ORM(SQLAlchemy 등) 없이 Python 표준 `sqlite3` 라이브러리를 사용하여 쿼리를 직접 작성, 학습 복잡도를 낮춥니다. (필요 시 가벼운 래퍼 함수 작성)

## Proposed Changes

### 1. Project Setup & Dependencies
`uv` 패키지 매니저를 사용하여 Python 환경을 구성하고 필수 패키지를 설치합니다.

#### [NEW] [pyproject.toml](file:///Users/yoonani/Works/workshop/web-dev-apply-skills/pyproject.toml)
- `fastapi`, `uvicorn`, `python-multipart` (파일 업로드), `bcrypt` (비밀번호 해시), `pyjwt` (인증 토큰), `jinja2` (템플릿 렌더링) 의존성 정의.

#### [NEW] [Project Structure]
```
/
├── app.py              # FastAPI 메인 애플리케이션 및 라우트
├── database.py         # SQLite DB 연결 및 테이블 초기화
├── models.py           # (선택적) Pydantic 모델 정의
├── static/
│   ├── css/
│   │   ├── reset.css   # 브라우저 기본 스타일 초기화
│   │   ├── variables.css # 색상, 폰트, Spacing 변수 (Fluid Typography)
│   │   └── style.css   # 컴포넌트 및 유틸리티 스타일
│   └── js/
│       ├── api.js      # Fetch API 래퍼 (에러 핸들링 포함)
│       └── main.js     # UI 로직 및 DOM 조작
├── templates/
│   ├── base.html       # 공통 레이아웃 (메타 태그, CSS/JS 포함)
│   ├── index.html      # 메인 피드
│   ├── login.html      # 로그인 페이지
│   └── register.html   # 회원가입 페이지
└── uploads/            # 업로드된 이미지 저장소
```

---

### 2. Frontend Development (Web Guidelines & Responsive Design)

#### [NEW] [variables.css](file:///Users/yoonani/Works/workshop/web-dev-apply-skills/static/css/variables.css)
- **Fluid Typography**: `clamp()` 함수를 사용하여 뷰포트에 따라 자연스럽게 조절되는 폰트 사이즈 정의 (`--text-sm`, `--text-base`, `--text-xl` 등).
- **Colors**: 다크 모드 지원을 고려한 CSS 변수 (`--bg-primary`, `--text-primary`, `--accent-color`).
- **Spacing**: Fluid spacing 적용.

#### [NEW] [style.css](file:///Users/yoonani/Works/workshop/web-dev-apply-skills/static/css/style.css)
- **Mobile-First**: 모바일 스타일을 기본으로 작성하고 `@media (min-width: ...)`로 데스크탑 스타일 확장.
- **Micro-interactions**: 버튼 Hover, Active, Focus-visible 상태 명시적 정의.
- **Forms**: `input` 태그의 터치 타겟(44px+) 확보, 명확한 `focus` 링, 에러 메시지 스타일링.
- **Layout**: CSS Grid를 활용한 카드 레이아웃 (모바일 1열 -> 태블릿/데스크탑 다열).

#### [NEW] [HTML Templates]
- `meta name="viewport"` 설정 및 시맨틱 태그(`header`, `main`, `article`, `nav`) 사용.
- **접근성(a11y)**: 폼 라벨 연결(`htmlFor`), 이미지 `alt` 속성, 적절한 `type` 및 `inputmode` 속성 사용.

---

### 3. Backend Development (FastAPI + SQLite)

#### [NEW] [database.py](file:///Users/yoonani/Works/workshop/web-dev-apply-skills/database.py)
- `schema.sql`: PRD에 정의된 Users, Posts, Comments, Likes, Tags, PostTags 테이블 생성 쿼리.
- DB 연결 및 커서 관리 헬퍼 함수.

#### [NEW] [app.py](file:///Users/yoonani/Works/workshop/web-dev-apply-skills/app.py)
- **Authentication**: `POST /auth/register`, `POST /auth/login` (HTTPOnly Cookie 또는 LocalStorage 토큰 방식).
- **Static Files**: `/static`, `/uploads` 디렉토리 마운트.
- **API Endpoints**:
    - `POST /api/posts`: 이미지 업로드 및 게시글 저장.
    - `GET /api/posts`: 페이지네이션을 고려한 게시글 조회.
    - `PUT/DELETE /api/posts/{id}`: 작성자 로직 검증 후 처리.

---

### 4. Verification Plan

#### Automated Tests
- 현재 환경 특성상 `pytest`를 이용한 단위 테스트보다는 **API 엔드포인트 테스트(HTTP Client 활용)**와 **브라우저 수동 테스트**에 집중합니다.
- `test_db.py`: 데이터베이스 테이블 생성 및 기본 CRUD 동작 확인 스크립트 실행.

#### Manual Verification
1. **Responsive Check**: 개발자 도구의 Device Mode를 사용하여 모바일(375px), 태블릿(768px), 데스크탑(1440px) 뷰포트에서 레이아웃 깨짐 확인.
2. **Web Guidelines Check**:
    - 키보드 탭 탐색 시 포커스 링 표시 여부.
    - 로그인/회원가입 폼에서 유효성 검사 에러가 명확히 표시되는지.
    - 네트워크 스로틀링 상태에서 로딩 상태(Spinner 등) 표시 여부.
3. **Core Use Cases**: 회원가입 -> 로그인 -> 글 작성(이미지 포함) -> 피드 확인 -> 본인 글 수정/삭제.
