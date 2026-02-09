# Insta-Lite

Insta-Lite는 워크숍용으로 개발된 경량 인스타그램 클론입니다. FastAPI, SQLite, Vanilla JS를 사용하여 핵심 기능을 구현했습니다.

## 🚀 실행 방법

### 1. 환경 설정

```bash
# 가상환경이 없다면 생성
uv init --python 3.12 && uv sync

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
uv sync
```

### 2. 서버 실행

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

서버가 시작되면 브라우저에서 [http://localhost:8000](http://localhost:8000)으로 접속합니다.

## ✨ 주요 기능

- **회원가입 및 로그인**: JWT 기반 인증 시스템
- **게시글 작성**: 이미지 업로드 및 텍스트 작성
- **피드 조회**: 최신 게시물 순으로 피드 확인
- **상호작용**: 좋아요 및 댓글 기능
- **반응형 디자인**: 모바일 우선(Mobile-first) 설계, 다크 모드 지원

## 📂 프로젝트 구조

- `app.py`: FastAPI 메인 애플리케이션 진입점
- `database.py`: SQLite 데이터베이스 연결 및 세션 관리
- `auth.py`: JWT 토큰 생성/검증 및 비밀번호 해싱 (Auth/Bcrypt)
- `test_app.py`: Pytest 기반 단위 및 통합 테스트
- `templates/`: Jinja2 서버사이드 렌더링용 HTML 템플릿
- `static/`:
    - `css/`: 전역 스타일 및 컴포넌트 스타일
    - `js/`: 바닐라 자바스크립트 프론트엔드 로직
- `db/`: 데이터베이스 스키마 및 마이그레이션 스크립트
- `uploads/`: 사용자 업로드 콘텐츠 (Git 제외)
- `instruction/`: PRD 및 요구사항 문서
- `pyproject.toml` / `uv.lock`: Python 프로젝트 의존성 및 메타데이터 정의

---

이 코드는 **Q의 지침**에 따라 **Google Antigravity**가 생성했습니다.
생성일: 2026-02-09
