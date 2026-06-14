@echo off
REM Windows 하네스 설정 스크립트

echo.
echo ========================================
echo 철강산업 대시보드 하네스 설정
echo ========================================
echo.

REM 1. Python 버전 확인
echo [1/7] Python 버전 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python이 설치되지 않았습니다.
    exit /b 1
)
python --version

REM 2. 가상환경 생성
if not exist "venv" (
    echo [2/7] 가상환경 생성 중...
    python -m venv venv
    echo. ✓ 가상환경 생성 완료
) else (
    echo [2/7] 가상환경이 이미 존재합니다
)

REM 3. 가상환경 활성화
echo [3/7] 가상환경 활성화 중...
call venv\Scripts\activate.bat

REM 4. 의존성 설치
echo [4/7] 의존성 설치 중...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
echo. ✓ 의존성 설치 완료

REM 5. Pre-commit 초기화
echo [5/7] Pre-commit 초기화 중...
where pre-commit >nul 2>&1
if %errorlevel% equ 0 (
    pre-commit install >nul 2>&1
    echo. ✓ Pre-commit 설치 완료
) else (
    echo. ⚠  pre-commit이 설치되지 않았습니다
)

REM 6. 테스트 디렉토리 생성
echo [6/7] 테스트 디렉토리 확인 중...
if not exist "tests" mkdir tests
if not exist ".github\workflows" mkdir .github\workflows
echo. ✓ 디렉토리 설정 완료

REM 7. Pytest 실행
echo [7/7] 테스트 실행 중...
where pytest >nul 2>&1
if %errorlevel% equ 0 (
    pytest tests/ -v --tb=short
    echo. ✓ 테스트 실행 완료
) else (
    echo. ⚠  pytest가 설치되지 않았습니다
)

echo.
echo ========================================
echo ✓ 하네스 설정 완료!
echo ========================================
echo.
echo 다음 명령어를 실행하세요:
echo   python app.py          # Flask 앱 실행
echo   pytest tests/          # 테스트 실행
echo   flake8 .               # 린트 검사
echo   black .                # 코드 포맷팅
echo.
echo Git 커밋 전 자동 검사 활성화:
echo   pre-commit install     # Pre-commit hook 설치
echo ========================================
echo.
