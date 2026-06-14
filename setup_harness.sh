#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 철강산업 대시보드 하네스 설정${NC}"
echo "========================================"

# 1. Python 버전 확인
echo -e "${YELLOW}1️⃣  Python 버전 확인 중...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 버전: $python_version"

if [[ $python_version < "3.8" ]]; then
    echo -e "${YELLOW}⚠️  Python 3.8 이상이 필요합니다${NC}"
    exit 1
fi

# 2. 가상환경 생성 (선택사항)
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}2️⃣  가상환경 생성 중...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ 가상환경 생성 완료${NC}"
else
    echo -e "${GREEN}✓ 가상환경이 이미 존재합니다${NC}"
fi

# 3. 가상환경 활성화 (선택사항)
echo -e "${YELLOW}3️⃣  가상환경 활성화 중...${NC}"
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null || true

# 4. 의존성 설치
echo -e "${YELLOW}4️⃣  의존성 설치 중...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ 의존성 설치 완료${NC}"

# 5. Pre-commit 초기화
echo -e "${YELLOW}5️⃣  Pre-commit 초기화 중...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    pre-commit run --all-files 2>/dev/null || true
    echo -e "${GREEN}✓ Pre-commit 설치 완료${NC}"
else
    echo -e "${YELLOW}⚠️  pre-commit이 설치되지 않았습니다. requirements.txt를 확인하세요.${NC}"
fi

# 6. 테스트 디렉토리 생성
echo -e "${YELLOW}6️⃣  테스트 디렉토리 확인 중...${NC}"
mkdir -p tests
mkdir -p .github/workflows
echo -e "${GREEN}✓ 디렉토리 설정 완료${NC}"

# 7. Pytest 실행
echo -e "${YELLOW}7️⃣  테스트 실행 중...${NC}"
if command -v pytest &> /dev/null; then
    pytest tests/ -v --tb=short || echo -e "${YELLOW}⚠️  일부 테스트 실패 (자세한 내용은 위를 참조)${NC}"
    echo -e "${GREEN}✓ 테스트 실행 완료${NC}"
else
    echo -e "${YELLOW}⚠️  pytest가 설치되지 않았습니다.${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✓ 하네스 설정 완료!${NC}"
echo ""
echo "다음 명령어를 실행하세요:"
echo "  python app.py          # Flask 앱 실행"
echo "  pytest tests/          # 테스트 실행"
echo "  flake8 .               # 린트 검사"
echo "  black .                # 코드 포맷팅"
echo ""
echo "Git 커밋 전 자동 검사 활성화:"
echo "  pre-commit install     # Pre-commit hook 설치"
echo "========================================"
