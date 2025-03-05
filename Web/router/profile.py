from fastapi import APIRouter, Request, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
import httpx
from schema.schema import ProfileCreateRequestData
import os
from utils.get_data import getData

router = APIRouter()
templates = Jinja2Templates(directory="templates")

""" 
profile
    get /profile
        profile_page() : 프로필 목록 페이지. get_profile_list()를 호출
    get /profile/detail?id=
        get_profile_detail(id) : 프로필 상세보기기 페이지.
    get /profile/create
        profile_create_page() : 프로필 생성 페이지
    post /profile/create
        profile_create_request(name, img, ai): 프로필 만들기 요청
    post /profile/objectdetect
        object_detect_request(img): 객체 탐지 요청
"""

#profile 페이지
@router.get("/profile")
async def profile_page(request:Request):
    profiles = getData.get_profile_list()
    return templates.TemplateResponse("profile/list.html", {"request":request, "profiles":profiles})

#profile 상세보기
@router.get("/profile/detail")
async def get_profile_detail(request:Request, id:str = Query(...)):
    profile = getData.get_profile_detail(id)
    return templates.TemplateResponse("profile/detail.html", {"request":request, "profile":profile})

# profile 만들기 페이지
@router.get("/profile/create")
async def profile_create_page(request:Request):
    ai_list = getData.get_ai_list()
    return templates.TemplateResponse("profile/create.html",{"request":request, "ai_list":ai_list})

#profile 만들기 요청
@router.post("/profile/create")
async def profile_create_request(request_data:ProfileCreateRequestData):
    url = f"{getData.PROGRESS_SERVER}/profile/create"
    headers = {"Content-Type": "application/json"}
    with httpx.Client() as client:
        response = client.post(
            timeout=60.0,
            url=url,
            headers=headers,
            json=request_data.model_dump()
        )
    return response.json()

#profile의 객체 탐지
@router.post("/profile/objectdetect")
async def object_detect_request(image:UploadFile = File(...)):
    url = f"{getData.PROGRESS_SERVER}/profile/objectdetect"
    with httpx.Client() as client:
        response = client.post(
            url, files = {"file":(image.filename, image.file, image.content_type)}
        )
    return response.json()



@router.get("/profile/image/{filename}")
def get_image(filename:str):
    return getData.img_filename_to_file(filename)

    # profile_img_path = "static/image/profile"
    # realpath = os.path.abspath(profile_img_path)
    # file_path = os.path.join(profile_img_path, filename)
    # if not os.path.exists(realpath):
    #     os.makedirs(realpath, exist_ok=True)
    # if not os.path.exists(os.path.join(realpath, filename)):
    #     url = f"{getData.PROGRESS_SERVER}/profile/image/{filename}"
    #     with httpx.Client() as client:
    #         response = client.get(url=url)
    #     with open(file_path, "wb") as f:
    #         f.write(response.content)
    # return FileResponse(file_path)