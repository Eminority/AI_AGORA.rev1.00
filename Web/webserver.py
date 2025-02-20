from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from router import index, debate, lobby, history
from dotenv import load_dotenv
import config
import os

load_dotenv()  # .env 파일 로드
config.debate_server_uri = os.getenv("DEBATE_SERVER")

# print(config.debate_server_uri)


app = FastAPI()

# staticFiles 관리하기
app.mount("/static", StaticFiles(directory="static"), name="static") 


## 라우터 등록
#메인화면
app.include_router(index.router)
#로비
app.include_router(lobby.router)
#토론장
app.include_router(debate.router)
#기록화면
app.include_router(history.router)

# 실행 코드
# uvicorn webserver:app --host 0.0.0.0 --port 8001 --reload
# .env 안에 DEBATE_SERVER="http://127.0.0.1:8000" 넣기
