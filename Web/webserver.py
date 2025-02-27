import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

print(project_root)


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from router import index, profile, progress

"""
페이지 흐름
home
-> profile : 프로필 목록 페이지
    ->profile/create : 프로필 생성 페이지
    ->profile/{id} : 프로필 상세정보
-> progress : 생성된 대화 세션 목록
    ->progress/create : 대화 세션 생성 페이지
    ->progress/{id} : 대화 세션 상세정보
"""



app = FastAPI()

# staticFiles 관리하기
app.mount("/static", StaticFiles(directory="static"), name="static") 


## 라우터 등록
"""
index
    get /
        home() : 첫 화면


profile
    get /profile
        profile_page() : 프로필 목록 페이지. get_profile_list()를 호출
    get /profile/detail?id=
        profile_detail(id) : 프로필 상세보기 페이지.
    get /profile/create
        profile_create_page() : 프로필 생성 페이지
    post /profile/create
        profile_create_request(name, img, ai): 프로필 만들기 요청
    post /profile/objectdetect
        object_detect_request(img): 객체 탐지 요청

progress
    get /progress
        progress_page() : 세션 목록 페이지. get_progress_list()를 호출
    get /progress/detail?is=
        progress_detail(id) : 세션 상세보기.
    get /progress/create
        progress_create_page() : 세션 생성 페이지
    post /progress/create
        progress_create_request(type, topic, participants) : 세션 생성 요청 페이지
    

"""
#index
app.include_router(index.router)
#profile
app.include_router(profile.router)
#progress
app.include_router(progress.router)

# 실행 코드
# python -m uvicorn webserver:app --host 0.0.0.0 --port 8001 --reload
# .env 안에 DEBATE_SERVER="http://127.0.0.1:8000" 넣기기