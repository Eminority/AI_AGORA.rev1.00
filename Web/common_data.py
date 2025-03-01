import httpx
from dotenv import load_dotenv
import os

load_dotenv()

PROGRESS_SERVER = os.getenv("PROGRESS_SERVER")
if not PROGRESS_SERVER:
    PROGRESS_SERVER = "127.0.0.1:8000"


def get_profile_list() -> dict:
    url = f"{PROGRESS_SERVER}/profile/list"
    with httpx.Client() as client:
        response = client.get(url = url)
    return response.json()

def get_ai_list() -> dict:
    url = f"{PROGRESS_SERVER}/ai"
    with httpx.Client() as client:
        responce = client.get(url=url)
    return responce.json()

def get_progress_list() -> dict:
    url = f"{PROGRESS_SERVER}/progress/list"
    with httpx.Client() as client:
        response = client.get(url=url)
    return response.json()

