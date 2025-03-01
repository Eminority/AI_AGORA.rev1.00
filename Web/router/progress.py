from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
import httpx
from common_data import PROGRESS_SERVER, get_progress_list, get_profile_list
from schema.schema import ProgressCreateRequestData
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
    return templates.TemplateResponse("progress/detail.html", {"request":request,"progress":progress})

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