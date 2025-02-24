from fastapi import APIRouter, Path, Request, Form
from fastapi.templating import Jinja2Templates
import httpx
import config

router = APIRouter()
templates = Jinja2Templates(directory="templates")

#pydantic 모델 정의


##토론장 입장
# 이 때 기록 받아와서 현재까지 진행된 토론 보이기
@router.get("/debate")
async def get_debate(request:Request):
    return templates.TemplateResponse("debate.html", {"request":request})

#토론 정보 가져오기
@router.get("/debate/info")
async def get_debate_info(id:str):
    url = f"{config.debate_server_uri}/debate/info?id={id}"
    with httpx.Client() as client:
        response = client.get(url)
    return response.json()

##토론 만들기
@router.post("/debate/create")
async def create_debate(pos_id:str=Form(...),
                        neg_id:str=Form(...),
                        topic:str=Form(...)):
    print(pos_id, neg_id, topic)
    url = f"{config.debate_server_uri}/debate"
    with httpx.Client() as client:
        response = client.post(
            url,
            data={ "pos_id" : pos_id,
                    "neg_id" : neg_id,
                    "topic" : topic
                },
            timeout=100)
    return response.json()

#토론 진행하기
@router.post("/debate/progress")
async def progress_debate(request:Request):
    url = f"{config.debate_server_uri}/debate/progress"
    body = await request.body()
    content_type = request.headers.get("Content-Type", "application/x-www-form-urlencoded")
    headers = {"Content-Type" : content_type}
    with httpx.Client() as client:
        response = client.post(url, headers=headers, content=body, timeout=10)
    return response.json()


#토론 목록 받아오기
@router.get("/debate/list")
async def get_debate_list():
    url = f"{config.debate_server_uri}/debate/list"
    with httpx.Client() as client:
        response = client.get(url)
    debate_list = response.json()
    return debate_list
