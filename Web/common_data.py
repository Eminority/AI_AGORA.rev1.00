import httpx
from dotenv import load_dotenv
import os
from utils.mongodb_connection import MongoDBConnection
from utils.image_manager import ImageManager
import base64
load_dotenv()



PROGRESS_SERVER = os.getenv("PROGRESS_SERVER")
if not PROGRESS_SERVER:
    PROGRESS_SERVER = "127.0.0.1:8000"

mongodb_connection = None
image_manager = None
mongoUri = os.getenv("MONGO_URI")
mongoDBName = os.getenv("DB_NAME")

PROFILE_IMG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "static/image/profile"))

if mongoUri and mongoDBName:
    mongodb_connection = MongoDBConnection(mongoUri, mongoDBName)
    image_manager = ImageManager(mongodb_connection,
                                 PROFILE_IMG_PATH)
else:
    print(".env에 MONGO_URI, DB_NAME 설정 필요")



def get_profile_list() -> dict:
    # mongodb_connection 없는 경우
    if not mongodb_connection:
        url = f"{PROGRESS_SERVER}/profile/list"
        with httpx.Client() as client:
            response = client.get(url = url)
        return response.json()
    else:
        #image를 id에서 파일로 고쳐서 반환해야함
        obj_all = mongodb_connection.select_data_from_query("object")
        result = {str(obj["_id"]) : {key : value for key, value in obj.items()}
              for obj in obj_all}
        for id, obj in result.items():
            img_id = obj.get("img")
            if img_id:
                img_filename = img_id_to_filename(str(img_id))
                result[id]["img"] = img_filename
        return result
   
def get_profile_detail(id:str):
    if not mongodb_connection:
        url = f"{PROGRESS_SERVER}/profile/detail?id={id}"
        with httpx.Client() as client:
            response = client.get(url=url)
        return response.json()
    else:
        profile = mongodb_connection.select_data_from_id("object",id)
        profile["_id"] = id
        img_id = profile.get("img")
        if img_id:
            img_filename = img_id_to_filename(str(img_id))
            profile["img"] = img_filename
        return profile

def img_id_to_filename(id:str) -> str:
    image_from_db = mongodb_connection.select_data_from_id("image", id) 
    image_from_local = os.path.join(PROFILE_IMG_PATH, image_from_db.get("filename"))
    if not os.path.exists(image_from_local):
        image_byte = base64.b64decode(image_from_db["data"])
        with open(image_from_local, "wb") as f:
            f.write(image_byte)
    return image_from_db["filename"]


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

