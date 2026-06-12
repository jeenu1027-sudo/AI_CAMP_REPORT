# 🔧 하네스 설정 가이드

철강산업 대시보드 프로젝트의 자동화 하네스(개발자 도구) 설정 가이드입니다.

---

## 📋 포함된 하네스

### 0. **루브릭 자동 검증** 📋
- **목적**: 매일 프로젝트 루브릭 자동 검증
- **실행 시간**: 매일 오전 8:00 AM JST (동경표준시)
- **항목**: 40개+ 검증 항목 (기능, 안정성, 사용성, 성능, 보안 등)
- **파일**: `rubric_validator.py`

### 1. **Pre-commit Hook** 🎣
- **목적**: Git 커밋 전 자동으로 코드 검사
- **포함**: 린트, 포맷팅, 타입 체크
- **파일**: `.pre-commit-config.yaml`

### 2. **Pytest 테스트 프레임워크** 🧪
- **목적**: 자동화된 단위 및 통합 테스트
- **커버리지**: 70% 이상 유지
- **파일**: `pytest.ini`, `tests/` 디렉토리

### 3. **린트 설정** 🔍
- **Flake8**: 코드 스타일 검사
- **Black**: 코드 자동 포맷팅
- **isort**: import 정리
- **mypy**: 타입 체크
- **파일**: `.flake8`, `setup.cfg`

### 4. **GitHub Actions CI/CD** 🚀
- **목적**: 자동 테스트, 린트, 보안 검사
- **트리거**: push, pull request
- **파일**: `.github/workflows/ci.yml`

---

## 🚀 빠른 시작

### Windows 사용자
```bash
# PowerShell에서 실행
.\setup_harness.bat
```

### Linux/Mac 사용자
```bash
# Terminal에서 실행
chmod +x setup_harness.sh
./setup_harness.sh
```

---

## 🔍 루브릭 검증 실행

### 자동 실행 (스케줄)
```bash
# Flask 앱 시작하면 자동으로 매일 8:00 AM JST에 실행됨
python app.py
```

### 수동 실행
```bash
# 루브릭 검증 스크립트 직접 실행
python rubric_validator.py

# 또는 Python 코드에서
from rubric_validator import validate_rubric
results = validate_rubric()
print(f"통과율: {results['summary']['pass_rate']:.1f}%")
```

### 검증 항목 (40개+)
- **기능성**: 6개 데이터 카테고리, 스케줄링, 웹 대시보드
- **안정성**: 에러 처리, 재시도, 부분 성공, 동시성 제어
- **사용성**: 5개 문서, 6개 API, 친화적 메시지
- **성능**: 배치 저장, 누적 카운터, 타임아웃 관리
- **보안**: 환경변수 관리, 입력 검증
- **코드 품질**: 타입 힌팅, 명확한 함수명
- **테스트**: 45개+ 테스트 케이스, pytest
- **개발 도구**: Pre-commit, CI/CD, 설정 자동화

### 검증 결과 저장
```
C:\AI리더양성과제\rubric_validation.json
```

결과 파일 예시:
```json
{
  "timestamp": "2026-06-12T08:00:00+09:00",
  "summary": {
    "total_checks": 45,
    "passed_checks": 45,
    "failed_checks": 0,
    "pass_rate": 100.0
  },
  "checks": {
    "✓ Flask 메인 앱": {"passed": true, "details": "파일: app.py"},
    "✓ 크롤러 모듈": {"passed": true, "details": "파일: crawler.py"}
  }
}
```

---

## 📦 설치 상세 가이드

### Step 1: 의존성 설치
```bash
pip install -r requirements.txt
```

**설치되는 개발 도구:**
```
pre-commit==3.5.0
pytest==7.4.3
pytest-cov==4.1.0
black==23.12.0
flake8==7.0.0
isort==5.13.2
mypy==1.7.1
```

### Step 2: Pre-commit 설치 및 활성화
```bash
# Git hook 설치
pre-commit install

# 모든 파일 검사 (처음 한 번)
pre-commit run --all-files
```

**자동 검사 항목:**
- 공백 정리 (trailing whitespace)
- 파일 끝에 newline 추가
- YAML/JSON 형식 검사
- 큰 파일(>1MB) 감지
- Merge conflict 표시 감지
- Black 자동 포맷팅
- isort import 정리
- Flake8 스타일 검사
- mypy 타입 검사

---

## 🧪 테스트 실행

### 모든 테스트 실행
```bash
pytest tests/ -v
```

### 특정 테스트만 실행
```bash
# 크롤러 테스트만
pytest tests/test_crawler.py -v

# 네트워크 테스트 제외
pytest tests/ -v -m "not network"

# 특정 테스트 함수만
pytest tests/test_app.py::TestFlaskApp::test_health_endpoint_exists -v
```

### 커버리지 리포트
```bash
# 터미널에 출력
pytest tests/ --cov=. --cov-report=term-missing

# HTML 리포트 생성
pytest tests/ --cov=. --cov-report=html
# htmlcov/index.html 열기
```

---

## 🔍 코드 품질 검사

### Black (자동 포맷팅)
```bash
# 포맷팅 확인 (수정 안함)
black --check .

# 포맷팅 수정
black .

# 특정 파일만
black crawler.py app.py
```

### Flake8 (스타일 검사)
```bash
# 모든 파일 검사
flake8 .

# 특정 파일만
flake8 crawler.py

# 상세 출력
flake8 . --show-source --statistics
```

### isort (Import 정리)
```bash
# 확인만
isort . --check-only

# 자동 정리
isort .
```

### mypy (타입 체크)
```bash
# 타입 검사
mypy .

# 특정 파일만
mypy crawler.py --ignore-missing-imports
```

---

## 📊 GitHub Actions CI/CD

### 자동 실행 조건
- Push to `main` or `develop` 브랜치
- Pull Request 생성/업데이트

### 실행 내용
1. **Test Job** (`test`)
   - Python 3.8, 3.9, 3.10, 3.11에서 테스트
   - pytest 실행
   - 커버리지 리포트 생성
   - Codecov에 업로드

2. **Lint Job** (`lint`)
   - Flake8 검사
   - Black 포맷 검사
   - mypy 타입 검사

3. **Security Job** (`security`)
   - Bandit 보안 검사
   - Safety 의존성 취약점 검사

4. **Code Quality Job** (`code-quality`)
   - Pylint 분석

---

## 🛠️ 커스터마이징

### Pre-commit Hook 수정
`.pre-commit-config.yaml` 파일을 편집하면 됩니다:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        args: [--line-length=100]  # 수정 가능
```

### Pytest 설정 수정
`pytest.ini` 파일을 편집:

```ini
[pytest]
testpaths = tests          # 테스트 경로
addopts = -v --cov=.     # 기본 옵션
```

### 린트 규칙 수정
`.flake8` 파일을 편집:

```ini
[flake8]
max-line-length = 100      # 수정 가능
ignore = E203, W503       # 무시할 규칙
```

---

## 📋 체크리스트

### 첫 설정 시
- [ ] `pip install -r requirements.txt` 실행
- [ ] `pre-commit install` 실행
- [ ] `pytest tests/` 실행해서 모든 테스트 통과 확인
- [ ] `black . && flake8 .` 실행해서 코드 품질 확인

### 커밋 전
- [ ] Pre-commit hook이 자동 실행되고 통과하는지 확인
- [ ] 새로운 기능에 대한 테스트 작성
- [ ] 테스트 커버리지 70% 이상 유지

### Pull Request 전
- [ ] 로컬에서 모든 테스트 통과 확인
- [ ] GitHub Actions CI/CD 통과 대기
- [ ] 코드 리뷰 요청

---

## 🆘 문제 해결

### Pre-commit Hook이 실행되지 않음
```bash
# Hook 재설치
pre-commit uninstall
pre-commit install

# 수동 실행
pre-commit run --all-files
```

### Pytest가 모듈을 찾을 수 없음
```bash
# 프로젝트 루트에서 실행
cd C:\AI리더양성과제
pytest tests/
```

### Git Hook 스킵하기 (응급 상황만)
```bash
git commit --no-verify  # ⚠️ 권장하지 않음
```

### 모든 파일 자동 포맷팅
```bash
black .
isort .
```

---

## 📚 참고 자료

- [Pre-commit 공식 문서](https://pre-commit.com/)
- [Pytest 공식 문서](https://docs.pytest.org/)
- [Black 공식 문서](https://black.readthedocs.io/)
- [Flake8 공식 문서](https://flake8.pycqa.org/)
- [mypy 공식 문서](https://mypy.readthedocs.io/)

---

**마지막 업데이트**: 2026-06-12  
**버전**: 1.0
