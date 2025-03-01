from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
import httpx
from common_data import PROGRESS_SERVER, get_progress_list, get_profile_list
from schema.schema import ProgressCreateRequestData
import re

router = APIRouter()
templates = Jinja2Templates(directory="templates")


"""
get /progress
    progress_page() : 세션 목록 페이지. get_progress_list()를 호출
get /progress/detail?is=
    progress_detail(id) : 세션 상세보기.
get /progress/create
    progress_create_page() : 세션 생성 페이지
post /progress/create
    progress_create_request(type, topic, participants) : 세션 생성 요청 페이지
"""

@router.get("/progress")
async def progress_page(request:Request):
    progress_list = get_progress_list()
    return templates.TemplateResponse("/progress/list.html", {"request":request, "progress":progress_list})

@router.get("/progress/detail")
async def progress_detail(request:Request, id:str):
    url = f"{PROGRESS_SERVER}/progress/detail?id={id}"
    with httpx.Client() as client:
        response = client.get(url=url)
    progress = response.json()
    ## ** **를 굵은 글씨로 바꿔서 반환
    for log in progress.get("debate_log"):
        log["message"] = format_to_bold(log["message"])
        log["timestamp"] = format_datetime(log["timestamp"])
    return templates.TemplateResponse("progress/detail.html", {"request":request,"progress":progress})



def format_to_bold(text:str) -> str:
    """
    **굵은 글씨**를 <strong>굵은글씨</strong>으로 바꿔주는 함수
    """
    return re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

def format_datetime(timestamp:str)-> str:
    """ 년-월-일T시:분:초.밀리초 -> 년-월-일 시:분:초 로 변환"""
    if "T" in timestamp:
        date_part, time_part = timestamp.split("T")
        time_part = time_part.split(".")[0]
        return f"{date_part} {time_part}"
    return timestamp



@router.get("/progress/autogenerate")
async def progress_auto_generate(request:Request, topic:str=None):
    url = f"{PROGRESS_SERVER}/progress/autogenerate"
    if topic:
        url += f"?topic={topic}"
    with httpx.Client() as client:
        response = client.get(url=url)
    return response.json()

@router.get("/progress/create")
async def progress_create_page(request:Request):
    profiles = get_profile_list()
    return templates.TemplateResponse("progress/create.html", {"request":request, "profiles":profiles})

@router.post("/progress/create")
async def progress_create_request(progressData:ProgressCreateRequestData):
    url = f"{PROGRESS_SERVER}/progress/create"
    print(progressData.model_dump())
    with httpx.Client() as client:
        response = client.post(
            url=url,
            headers = {"Content-Type": "application/json"},
            json=progressData.model_dump()
        )
        print(response)
    return response.json()