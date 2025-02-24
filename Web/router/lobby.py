from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
import httpx
import config

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/lobby")
async def lobby(request: Request):
    url = f"{config.debate_server_uri}/profile/list"
    with httpx.Client() as client:
        response = client.get(url)
    profiles = response.json()
    print(profiles)
    return templates.TemplateResponse("lobby.html", {"request": request, "profiles":profiles})

@router.get("/lobby/create")
async def lobby_create_debate(request:Request):
    url = f"{config.debate_server_uri}/profile/list"
    with httpx.Client() as client:
        response = client.get(url)
    profiles = response.json()
    return templates.TemplateResponse("lobby_create_debate.html", {"request":request, "profiles":profiles})


@router.post("/lobby/objectdetect")
async def list_from_object_detect(original_image: UploadFile = File(...)):
    """
    사진을 전송해서 object를 감지해서 list를 반환받는 메서드
    """
    url = f"{config.debate_server_uri}/profile/objectdetect"
    with httpx.Client() as client:
        response = client.post(
            url, files = {"file":(original_image.filename, original_image.file, original_image.content_type)}
        )
    return response.json()

@router.post("/lobby/createprofile")
async def create_profile(selected_object: str = Form(...),
                         file_path:str = Form(...),
                         ai:str = Form(...)):
    url = f"{config.debate_server_uri}/profile/create"
    with httpx.Client() as client:
        response = client.post(
            url, data = {"name":selected_object,
                         "img":file_path,
                         "ai":ai}
        )
    return response.json()
