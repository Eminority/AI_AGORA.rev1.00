from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/history")
async def history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request, "title":"TITLE TEST"})
