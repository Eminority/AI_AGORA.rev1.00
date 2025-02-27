import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


from fastapi import FastAPI, Form, Query, File, UploadFile
from fastapi.responses import FileResponse
import os
import yaml
import json
from contextlib import asynccontextmanager
import asyncio
from dotenv import load_dotenv
from src.ai.ai_factory import AI_Factory
from src.utils.progress_manager import ProgressManager
from src.utils.participant_factory import ParticipantFactory
from src.utils.mongodb_connection import MongoDBConnection
from src.utils.vectorstorehandler import VectorStoreHandler
from src.utils.profile_manager import ProfileManager
from src.yolo.yolo_detect import YOLODetect
from src.utils.image_manager import ImageManager
from src.utils.detect_persona import DetectPersona
from src.utils.web_scrapper import WebScrapper
from src.schema.schema import ProfileCreateRequestData, ProgressCreateRequestData
import base64

# 환경 변수 로드
load_dotenv()

# MongoDB 연결
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise ValueError("MONGO_URI 또는 DB_NAME이 .env 파일에서 설정되지 않았습니다.")

mongodb_connection = MongoDBConnection(MONGO_URI, DB_NAME)

# AI API 키 불러오기
AI_API_KEY = json.loads(os.getenv("AI_API_KEY"))
ai_factory = AI_Factory(AI_API_KEY)

# 벡터스토어 핸들러 생성
vectorstore_handler = VectorStoreHandler(chunk_size=500, chunk_overlap=50)


# participant factory 인스턴스 초기화
participant_factory = ParticipantFactory(vectorstore_handler, ai_factory)


# YOLO 탐지 객체 생성
yoloDetector = YOLODetect()


## config.yaml 불러와서 변수에 저장해두기
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config/config.yaml"))
with open(config_path, "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)


# 이미지 관리자 - MongoDB에 업로드, MongoDB에서 다운로드 시켜주는 관리자
IMAGE_SAVE_PATH = config.get("image_path") if config.get("image_path") else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets/image"))
real_image_save_path = os.path.join(os.getcwd(), IMAGE_SAVE_PATH)
os.makedirs(real_image_save_path, exist_ok=True)
image_manager = ImageManager(db=mongodb_connection, img_path=real_image_save_path)

#persona 생성기
detect_persona = DetectPersona(GEMINI_API_KEY=AI_API_KEY["GEMINI"])

#프로필 관리 객체 생성
profile_manager = ProfileManager(db=mongodb_connection, detect_persona=detect_persona)

#크롤링하는 객체 생성
web_scrapper = WebScrapper()

#토론 주제 확인 객체 - AI 인스턴스
topic_checker = ai_factory.create_ai_instance("GEMINI")

#토론 관리 인스턴스 생성
progress_manager = ProgressManager(participant_factory=participant_factory,
                                    web_scrapper=web_scrapper,
                                    mongoDBConnection=mongodb_connection,
                                    topic_checker=topic_checker,
                                    vectorstore_handler=vectorstore_handler,
                                    generate_text_config=config["generate_text_config"])

################################## 이 아래로 작성 필요




# 백그라운드에서 자동으로 토론 계속 진행시키기
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(auto_progressing())
    yield
    task.cancel()

# progress 자동진행 메서드
async def auto_progressing():
    while (True):
        try:
            for id, progress in progress_manager.progress_pool.items():
                #progress가 종료되지 않았다면
                if progress.data.get("status") and progress.data.get("status").get("type") != "end":
                    #계속 progress 진행하기
                    print(progress.progress())
                    #진행 후 저장
                    progress_manager.save(id)
                await asyncio.sleep(1) 
        except Exception as e:
            print(f"오류 발생 : {e}")




# FastAPI 앱 생성
app = FastAPI(lifespan=lifespan)


# progress 생성 API - 일단 토론만
# @app.post("/create/debate")
# def create_debate(pos_id: str = Form(...),
#                   neg_id: str = Form(...),
#                   topic: str = Form(...)) -> dict:
#     pos = mongodb_connection.select_data_from_id("object", pos_id)
#     pos["img"] = mongodb_connection.select_data_from_id("image", pos.get("img")).get("filename")
#     neg = mongodb_connection.select_data_from_id("object", neg_id)
#     neg["img"] = mongodb_connection.select_data_from_id("image", neg.get("img")).get("filename")

#     participant = {"pos":pos, "neg":neg}

#     result = progress_manager.create_progress("debate", participant, topic)
    
#     return result


# 토론 상태 확인 API
# 토론 정보를 받아오면 자동으로 status가 반환되므로 사용하지 않음
# @app.get("/debate/status")
# def get_debate_status(id:str):
#     return progress_manager.progress_pool[id].data["status"]

# 토론 진행 API
# 토론은 자동진행되므로 더 이상 사용되지 않음
# 자동으로 토론 info 받는걸로 진행
# @app.post("/debate/progress")
# def progress_debate(id:str= Form(...),
#                     message:str=Form(...)):
#     if progress_manager.progress_pool[id].debate["status"]["type"] == "end":
#         return {"message": "토론이 이미 종료되었습니다."}
    
#     return {"progress": progress_manager.progress_pool[id].progress()}


#사용 가능한 ai 목록 반환
@app.get("/ai")
async def get_ai_list():
    return config["ai"]


#실행중인 토론 목록 받아오기
# { id : {topic:topic, status:status}} 형태의 dict 반환
@app.get("/progress/list")
async def get_progress_list():
    progresslist = {}
    for id in progress_manager.progress_pool.keys():
        progress = progress_manager.progress_pool[id]
        progresslist[id] = {
            "topic": progress.data["topic"],
            "stauts": progress.data["status"]["type"],
            "participants": [{"position":position,
                              "name": obj.name,
                              "id":obj.id,
                              "img":obj.img,
                              "ai":obj.ai_instance.model_name}
                            for position, obj in progress.participant.items()]
        }
    return progresslist


# progress session 받아오기
@app.get("/progress/detail")
async def get_progress_detail(id:str = Query(..., description="토론 id")):
    progress = progress_manager.progress_pool.get(id)
    if progress:
        progress_data = progress.data
        progress_data["_id"] = str(progress_data["_id"])
        return progress_data
    else:
        return {}


# progress 생성, {result:성공여부, id:id} 반환
@app.post("/progress/create")
async def create_progress(progressData:ProgressCreateRequestData):
    progressType = progressData.type
    participants = progressData.participants
    topic = progressData.topic
    return progress_manager.create_progress(progressType, participants, topic)




##이미 생성되어있는 사물 프로필 목록 반환
@app.get("/profile/list")
async def get_ai_list():
    # id - data 형태로 묶어서 데이터 전송
    result = {obj.data["_id"] : {key : value for key, value in obj.data.items()}
              for obj in profile_manager.objectlist.values()}
    for id, obj in result.items():
        img_id = obj["img"]
        image_from_db = mongodb_connection.select_data_from_id("image", str(img_id))
        image_from_local = os.path.join(IMAGE_SAVE_PATH, image_from_db.get("filename"))
        if not os.path.exists(image_from_local):
            image_byte = base64.b64decode(image_from_db["data"])
            with open(image_from_local, "wb") as f:
                f.write(image_byte)
        result[id]["img"] = image_from_db.get("filename")
    return result

@app.get("/profile/detail")
async def get_profile(id:str):
    data = profile_manager.objectlist.get(id).data
    result = dict(data)
    img_id = str(data.get("img"))
    image_from_db = mongodb_connection.select_data_from_id("image", str(img_id))
    image_from_local = os.path.join(IMAGE_SAVE_PATH, image_from_db.get("filename"))
    if not os.path.exists(image_from_local):
        image_byte = base64.b64decode(image_from_db["data"])
        with open(image_from_local, "wb") as f:
            f.write(image_byte)
    result["img"] = image_from_db.get("filename")
    return result


#최종적으로 이미지 포함 프로필 만들기
@app.post("/profile/create")
async def create_ai_profile(request_data:ProfileCreateRequestData):
    save_result = image_manager.save_image_in_mongoDB_from_local(request_data.img)
    if save_result.get("result") == "success":
        await profile_manager.create_profile(name=request_data.selected_object,
                                    img=save_result["file_id"],
                                    ai=request_data.ai)
        return {"result":"success"}
    return {"result":"error"}


##yolo로 이미지 판단해서 {result:(bool),data:(list)} 반환하기
@app.post("/profile/objectdetect")
async def object_detect(file: UploadFile = File(...)) -> dict:
    """
    form으로 전달받은 이미지를 저장하고 yolo로 분석해서 뭐가 들어있는지 결과 반환.
    """
    local_image_data = image_manager.save_image_in_local_from_form(file)
    result_data = {"result":local_image_data.get("result")}
    if result_data["result"]:
        detect_data = yoloDetector.detect_objects(local_image_data["data"])
        if detect_data:
            result_data["data"] = []
            for detected in detect_data:
                cropped_image = image_manager.crop_image(local_image_data["data"], detected)
                result_data["data"].append({"name":detected["object_name"], "filename":cropped_image})
            result_data["detected"] = True
        else:
            result_data["detected"] = False
            result_data["data"] = [{"filename": local_image_data.get("data")}]
    return result_data



#webserver에서 profile 이미지 요청하면 건네주는 코드
@app.get("/profile/image/{image_name}")
async def send_image(image_name:str):
    image = os.path.join(IMAGE_SAVE_PATH, image_name)
    if os.path.exists(image):
        return FileResponse(image, media_type="image/png")
    image_from_db = mongodb_connection.select_data_from_query("image", {"filename":image_name})[0]
    if image_from_db:
        with open(image, "wb") as f: 
            f.write(bytes(image_from_db["data"]))
        return FileResponse(image, media_type="image/png")
    return None


##실행코드
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# uvicorn main:app --port 8000 --reload --no-access-log
