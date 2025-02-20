from fastapi import FastAPI, Form, Query, File, UploadFile
from fastapi.responses import FileResponse
import os
import json
from dotenv import load_dotenv
from .ai.ai_factory import AI_Factory
from .utils.progress_manager import ProgressManager
from .utils.participant_factory import ParticipantFactory
from .utils.mongodb_connection import MongoDBConnection
from .utils.vectorstorehandler import VectorStoreHandler
from .utils.profile_manager import ProfileManager
from .yolo.yolo_detect import YOLODetect
from .utils.image_manager import ImageManager
from .utils.detect_persona import DetectPersona
from .utils.web_scrapper import WebScrapper
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


# Debate 인스턴스 초기화
participant_factory = ParticipantFactory(vectorstore_handler, ai_factory)

# FastAPI 앱 생성
app = FastAPI()

# YOLO 탐지 객체 생성
yoloDetector = YOLODetect()

# 이미지 관리자 - MongoDB에 업로드, MongoDB에서 다운로드 시켜주는 관리자
IMAGE_SAVE_PATH = os.getenv("IMAGE_SAVE_PATH") if os.getenv("IMAGE_SAVE_PATH") else "image"
real_image_save_path = os.path.join(os.getcwd(), IMAGE_SAVE_PATH)
os.makedirs(real_image_save_path, exist_ok=True)
image_manager = ImageManager(db=mongodb_connection, img_path=real_image_save_path)

#persona 생성기
detect_persona = DetectPersona(AI_API_KEY=AI_API_KEY["GEMINI"])

#프로필 관리 객체 생성
profile_manager = ProfileManager(db=mongodb_connection, persona_module=detect_persona)

#크롤링하는 객체 생성
web_scrapper = WebScrapper(api_keys=AI_API_KEY)

#토론 주제 확인 객체 - AI 인스턴스
topic_checker = ai_factory.create_ai_instance("GEMINI")

#토론 관리 인스턴스 생성
progress_manager = ProgressManager(participant_factory=participant_factory,
                                    mongoDBConnection=mongodb_connection,
                                    topic_checker=topic_checker,
                                    vectorstore_handler=vectorstore_handler,)

################################## 이 아래로 작성 필요

# 토론 생성 API
@app.post("/debate")
def create_debate(pos_id: str = Form(...),
                  neg_id: str = Form(...),
                  topic: str = Form(...)):
    
    if topic_checker.checktopic(topic):
        pos = db_connection.select_data_from_id("object", pos_id)
        pos["img"] = db_connection.select_data_from_id("image", pos.get("img")).get("filename")
        neg = db_connection.select_data_from_id("object", neg_id)
        neg["img"] = db_connection.select_data_from_id("image", neg.get("img")).get("filename")

        print(pos["img"], " ", neg["img"])

        id = debateManager.create_debate(pos, neg, topic)

        return {"result":True, "message": "토론이 생성되었습니다.", "topic": topic, "id":id}
    else:
        return {"result":False, "message": "토론 주제가 적절하지 않습니다."}

# 토론 상태 확인 API
@app.get("/debate/status")
def get_debate_status(id:str):
    return debateManager.debatepool[id].debate["status"]

# 토론 진행 API
@app.post("/debate/progress")
def progress_debate(id:str= Form(...),
                    message:str=Form(...)):
    if debateManager.debatepool[id].debate["status"]["type"] == "end":
        return {"message": "토론이 이미 종료되었습니다."}
    
    return {"progress": debateManager.debatepool[id].progress()}

# 토론 전체 받아오기
@app.get("/debate/info")
def get_debate_history(id:str = Query(..., description="토론 id")):
    if debateManager.debatepool.get(id):
        debatedata = debateManager.debatepool[id].debate
        debatedata["_id"] = str(debatedata["_id"])
        print(debatedata)
        return debatedata
    else:
        return []


#실행중인 토론 목록 받아오기
@app.get("/debate/list")
def get_debate_list():
    debatelist = {}
    for id in debateManager.debatepool.keys():
        debatelist[id] = debateManager.debatepool[id]["debate"]["topic"]
    return debatelist

##이미 생성되어있는 사물 프로필 목록 반환
@app.get("/profile/list")
def get_ai_list():
    # id - data 형태로 묶어서 데이터 전송
    result = {id : profile_manager.objectlist[id] for id in profile_manager.objectlist.keys()}
    print(result)
    return result


##yolo로 이미지 판단해서 list 반환하기
@app.post("/profile/objectdetect")
def object_detect(file: UploadFile = File(...)):
    """
    form으로 전달받은 이미지를 저장하고 yolo로 분석해서 뭐가 들어있는지 결과 반환.
    """
    local_image_data = image_manager.save_image_in_local_from_form(file)
    result_data = {"result":local_image_data.get("result")}
    if result_data["result"]:
        detect_data = yoloDetector.detect_objects(local_image_data["data"])
        if detect_data:
            result_data["detected"] = True
            result_data["data"] = image_manager.crop_image(local_image_data["data"], detect_data)
        else:
            result_data["detected"] = False
            result_data["data"] = {"filename": local_image_data.get("data")}
    return result_data



#최종적으로 이미지 포함 프로필 만들기
@app.post("/profile/create")
def create_ai_profile(name:str = Form(...),
                      img:str = Form(...),
                      ai:str = Form(...)):
    save_result = image_manager.save_image_in_mongoDB_from_local(img)
    if save_result.get("result") == "success":
        new_id = profile_manager.create_profile(name=name,
                                    img=save_result["file_id"],
                                    ai=ai).get("id")
        if new_id:
            print(new_id)
            return {"result":"success", "id":new_id}
    return {"result":"error"}


#webserver에서 이미지 요청하면 건네주는 코드
@app.get("/image/{image_name}")
async def send_image(image_name:str):
    image = os.path.join(IMAGE_SAVE_PATH, image_name)
    if os.path.exists(image):
        return FileResponse(image, media_type="image/png")
    image_from_db = db_connection.select_data_from_query("image", {"filename":image_name})[0]
    print(">>>>>>>>>>>>>>>>>>")
    print(image_from_db)
    if image_from_db:
        with open(image, "wb") as f: 
            f.write(bytes(image_from_db["data"]))
        return FileResponse(image, media_type="image/png")

    print("nope!")


##실행코드
# uvicorn backserver:app --host 0.0.0.0 --port 8000 --reload