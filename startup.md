# 프로젝트 초기 실행 스크립트

# 1. 프로젝트 루트로 이동
cd KDT_BE13_Toy_Project4

# 2. DB만 Docker로 실행
docker-compose -f /docker/docker-compose.dev.yml up -d

# 3. 헬스체크 확인
docker-compose -f /docker/docker-compose.dev.yml ps

# 4. Python 서버 실행 (터미널)
cd python-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 5. Spring 서버 실행 (IntelliJ)
# - IntelliJ에서 프로젝트 열기
# - Run → Run 'Application' (Shift+F10)
# - application.yml에서 active: local 확인