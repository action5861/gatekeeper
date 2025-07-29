# DigiSafe Python Microservices Setup Guide

이 가이드는 DigiSafe 프로젝트의 Python 마이크로서비스들의 가상 환경 설정과 의존성 관리를 위한 것입니다.

## 📋 개요

이 프로젝트는 다음과 같은 Python 마이크로서비스들로 구성되어 있습니다:

- **analysis-service**: 데이터 분석 및 품질 평가 서비스
- **auction-service**: 경매 관리 서비스
- **payment-service**: 결제 처리 서비스
- **quality-service**: 품질 관리 서비스
- **user-service**: 사용자 관리 서비스 (httpx 의존성 포함)
- **verification-service**: 검증 서비스

## 🚀 빠른 시작

### Windows 사용자

1. **스크립트 실행**:
   ```cmd
   setup_services.bat
   ```

2. **수동 설정** (스크립트가 실패하는 경우):
   ```cmd
   cd services\analysis-service
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   deactivate
   ```

### Linux/macOS 사용자

1. **스크립트 실행**:
   ```bash
   ./setup_services.sh
   ```

2. **수동 설정** (스크립트가 실패하는 경우):
   ```bash
   cd services/analysis-service
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

## 🔧 VS Code 설정

### 자동 설정 (권장)

프로젝트 루트의 `.vscode/settings.json` 파일이 이미 모든 서비스의 Python 인터프리터를 올바르게 인식하도록 설정되어 있습니다.

### 수동 설정

각 서비스 폴더를 VS Code에서 열 때:

1. `Ctrl+Shift+P` (Windows) 또는 `Cmd+Shift+P` (macOS)를 눌러 명령 팔레트를 엽니다.
2. "Python: Select Interpreter"를 검색하고 선택합니다.
3. 해당 서비스의 가상 환경을 선택합니다:
   - Windows: `./venv/Scripts/python.exe`
   - Linux/macOS: `./venv/bin/python`

## 📦 의존성 관리

### 공통 의존성

모든 서비스는 다음 기본 의존성을 공유합니다:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
```

### 특별 의존성

- **user-service**: `httpx==0.25.2` 추가

## 🐛 문제 해결

### reportMissingImports 에러 해결

1. **VS Code 재시작**: 설정 변경 후 VS Code를 완전히 재시작합니다.

2. **인터프리터 재선택**:
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - 올바른 가상 환경 선택

3. **Pylance 재시작**:
   - `Ctrl+Shift+P` → "Python: Restart Language Server"

4. **가상 환경 재생성**:
   ```cmd
   # Windows
   rmdir /s /q services\analysis-service\venv
   cd services\analysis-service
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 일반적인 문제들

#### Python이 설치되지 않은 경우
```bash
# Windows: https://www.python.org/downloads/
# macOS
brew install python3

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

#### 가상 환경 활성화 실패
```bash
# Windows PowerShell에서 실행 정책 문제
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Linux/macOS에서 권한 문제
chmod +x venv/bin/activate
```

#### 의존성 설치 실패
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 캐시 클리어
pip cache purge

# 개별 패키지 설치
pip install fastapi uvicorn pydantic
```

## 📁 프로젝트 구조

```
services/
├── analysis-service/
│   ├── .vscode/settings.json
│   ├── pyrightconfig.json
│   ├── requirements.txt
│   ├── main.py
│   └── venv/
├── auction-service/
│   ├── .vscode/settings.json
│   ├── pyrightconfig.json
│   ├── requirements.txt
│   ├── main.py
│   └── venv/
└── ... (기타 서비스들)
```

## 🔍 설정 파일 설명

### .vscode/settings.json
- Python 인터프리터 경로 설정
- Pylance 분석 설정
- 코드 포맷팅 설정

### pyrightconfig.json
- Pylance 언어 서버 설정
- 가상 환경 경로 지정
- 타입 체킹 모드 설정

## 🚀 서비스 실행

각 서비스를 개별적으로 실행하려면:

```bash
# analysis-service 실행 예시
cd services/analysis-service
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
uvicorn main:app --reload --port 8000
```

## 📝 추가 정보

- **Python 버전**: 3.8+ 권장
- **FastAPI**: 최신 버전 사용
- **가상 환경**: 각 서비스별 독립적 환경
- **IDE**: VS Code + Python 확장 권장

## 🤝 지원

문제가 발생하면 다음을 확인하세요:

1. Python 버전이 3.8 이상인지 확인
2. 가상 환경이 올바르게 생성되었는지 확인
3. VS Code Python 확장이 설치되었는지 확인
4. 프로젝트 루트에서 스크립트를 실행했는지 확인

---

**참고**: 이 설정은 모든 `reportMissingImports` 에러를 해결하고, 각 마이크로서비스가 독립적으로 실행 가능한 상태가 되도록 설계되었습니다. 