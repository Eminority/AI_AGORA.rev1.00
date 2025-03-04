import httpx
from dotenv import load_dotenv
import os
from utils.mongodb_connection import MongoDBConnection
from utils.image_manager import ImageManager
from fastapi.responses import FileResponse
import base64
import re
from datetime import datetime

class GetData():
    def __init__(self):
        load_dotenv()
        self.PROGRESS_SERVER = os.getenv("PROGRESS_SERVER")
        if not self.PROGRESS_SERVER:
            self.PROGRESS_SERVER = "127.0.0.1:8000"

        self.mongodb_connection = None
        self.image_manager = None
        mongoUri = os.getenv("MONGO_URI")
        mongoDBName = os.getenv("DB_NAME")

        self.IMAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static/image"))
        self.PROFILE_IMG_PATH = os.path.join(self.IMAGE_PATH, "profile")
        
        if mongoUri and mongoDBName:
            self.mongodb_connection = MongoDBConnection(mongoUri, mongoDBName)
            self.image_manager = ImageManager(self.mongodb_connection,
                                        self.PROFILE_IMG_PATH)
        else:
            print(".env에 MONGO_URI, DB_NAME 설정 필요")


    def get_profile_list(self) -> dict:
        # mongodb_connection 없는 경우
        if not self.mongodb_connection:
            url = f"{self.PROGRESS_SERVER}/profile/list"
            with httpx.Client() as client:
                response = client.get(url = url)
            return response.json()
        else:
            #image를 id에서 파일로 고쳐서 반환해야함
            obj_all = self.mongodb_connection.select_data_from_query("object")
            result = {str(obj["_id"]) : {key : value for key, value in obj.items()}
                for obj in obj_all}
            for id, obj in result.items():
                img_id = obj.get("img")
                result[id]["stats"] = self.get_stats_by_id(self.mongodb_connection.get_collection("object"), id)
                if img_id:
                    img_filename = self.img_id_to_filename(str(img_id))
                    result[id]["img"] = img_filename
            return result
    
    def get_profile_detail(self, id:str):
        if not self.mongodb_connection:
            url = f"{self.PROGRESS_SERVER}/profile/detail?id={id}"
            with httpx.Client() as client:
                response = client.get(url=url)
            return response.json()
        else:
            profile = self.mongodb_connection.select_data_from_id("object",id)
            profile["_id"] = id
            img_id = profile.get("img")
            if img_id:
                img_filename = self.img_id_to_filename(str(img_id))
                profile["img"] = img_filename
            return profile

    def img_id_to_filename(self, id:str) -> str:
        image_from_db = self.mongodb_connection.select_data_from_id("image", id) 
        image_from_local = os.path.join(self.PROFILE_IMG_PATH, image_from_db.get("filename"))
        if not os.path.exists(image_from_local):
            image_byte = base64.b64decode(image_from_db["data"])
            with open(image_from_local, "wb") as f:
                f.write(image_byte)
        return image_from_db["filename"]

    def img_filename_to_file(self, image_filename:str):
        image = os.path.join(self.PROFILE_IMG_PATH, image_filename)
        if os.path.exists(image):
            return FileResponse(image, media_type="image/png")
        image_from_db = self.mongodb_connection.select_data_from_query("image",{"filename":image_filename})[0]
        if image_from_db:
            with open(image, "wb") as f:
                f.write(bytes(image_from_db["data"]))
            return FileResponse(image, media_type="image/png")
        return FileResponse(os.path.join(self.IMAGE_PATH,"default.png"), media_type="image/png")

    def get_ai_list(self) -> dict:
        url = f"{self.PROGRESS_SERVER}/ai"
        with httpx.Client() as client:
            responce = client.get(url=url)
        return responce.json()

    def get_progress_list(self) -> dict:
        if not self.mongodb_connection:
            url = f"{self.PROGRESS_SERVER}/progress/list"
            with httpx.Client() as client:
                response = client.get(url=url)
            return response.json()
        else:
            progress_all = self.mongodb_connection.select_data_from_query("progress")
            result = {str(progress["_id"]) : {key : value for key, value in progress.items()}
                for progress in progress_all}
            return result
    

    def get_progress_detail(self, id:str) -> dict:
        if not self.mongodb_connection:
            url = f"{self.PROGRESS_SERVER}/progress/detail?id={id}"
            with httpx.Client() as client:
                response = client.get(url=url)
            progress = response.json()
        else:
            progress = self.mongodb_connection.select_data_from_id("progress",id)
        if progress:
            progress["_id"] = str(progress["_id"])
            ## ** **를 굵은 글씨로 바꿔서 반환
            for log in progress.get("debate_log"):
                speaker = progress["participants"].get(log["speaker"])
                if speaker:
                    log["speaker"] = log["speaker"] + f" ({speaker['name']})"
                log["message"] = format_to_bold(log["message"])
                log["timestamp"] = format_datetime(str(log["timestamp"]))
        return progress
    
    
    # 특정 이름의 ID를 조회하는 헬퍼 함수
    def get_name_by_id(self, collection, target_id):
        """
        주어진 이름에 해당하는 ID를 찾는 함수
        - participants.pos.name 또는 participants.neg.name에서 이름 검색
        - 중복 이름이 없다고 가정하고 첫 번째 매칭 결과 반환
        """
        # pos에서 이름 검색
        pos_result = collection.find_one({"participants.pos.id": target_id})
        if pos_result:
            return pos_result["participants"]["pos"]["name"]

        # neg에서 이름 검색
        neg_result = collection.find_one({"participants.neg.id": target_id})
        if neg_result:
            return neg_result["participants"]["neg"]["name"]

        return None  # 이름에 해당하는 ID를 찾지 못한 경우

    def get_stats_by_id(self, collection, target_id):
        """
        특정 이름의 토론 통계(토론 횟수, 승/패, 각 점수의 평균)를 조회하는 함수
        """
        target_name = self.get_name_by_id(collection, target_id)
        if not target_id:
            return {
                "target_name": target_name,
                "target_id": None,
                "total_debates": 0,
                "wins": 0,
                "losses": 0,
                "avg_logicality": 0.0,
                "avg_rebuttal": 0.0,
                "avg_persuasion": 0.0,
                "avg_match": 0.0,
                "message": f"No participant found with name: {target_name}"
            }

        # 해당 사용자가 pos 또는 neg로 참여한 모든 문서를 찾음
        cursor = collection.find({
            "$or": [
                {"participants.pos.id": target_id},
                {"participants.neg.id": target_id}
            ]
        })

        total_debates = 0
        wins = 0
        losses = 0

        sum_logicality = 0.0
        sum_rebuttal = 0.0
        sum_persuasion = 0.0
        sum_match = 0.0

        # 실제 점수를 합산한 문서 수 (점수가 전혀 없는 문서는 제외)
        score_count = 0

        for doc in cursor:
            total_debates += 1

            # 사용자가 pos인지 neg인지 확인
            if doc["participants"]["pos"]["id"] == target_id:
                user_position = "pos"
            else:
                user_position = "neg"

            # 승리·패배 로직
            if user_position == "pos" and doc.get("result") == "positive":
                wins += 1
            elif user_position == "neg" and doc.get("result") == "negative":
                wins += 1
            else:
                losses += 1

            # 점수 합산
            score_data = doc.get("score", {})
            if user_position == "pos":
                # pos 점수 합산
                if "logicality_pos" in score_data:
                    sum_logicality += score_data["logicality_pos"]
                if "rebuttal_pos" in score_data:
                    sum_rebuttal += score_data["rebuttal_pos"]
                if "persuasion_pos" in score_data:
                    sum_persuasion += score_data["persuasion_pos"]
                if "match_pos" in score_data:
                    sum_match += score_data["match_pos"]
                # score가 하나라도 있으면 이 문서는 점수 카운팅
                if any(k in score_data for k in ["logicality_pos", "rebuttal_pos", "persuasion_pos", "match_pos"]):
                    score_count += 1
            else:
                # neg 점수 합산
                if "logicality_neg" in score_data:
                    sum_logicality += score_data["logicality_neg"]
                if "rebuttal_neg" in score_data:
                    sum_rebuttal += score_data["rebuttal_neg"]
                if "persuasion_neg" in score_data:
                    sum_persuasion += score_data["persuasion_neg"]
                if "match_neg" in score_data:
                    sum_match += score_data["match_neg"]
                # score가 하나라도 있으면 이 문서는 점수 카운팅
                if any(k in score_data for k in ["logicality_neg", "rebuttal_neg", "persuasion_neg", "match_neg"]):
                    score_count += 1

        # 평균 계산 (score_count가 0이면 0으로)
        avg_logicality = sum_logicality / score_count if score_count else 0.0
        avg_rebuttal   = sum_rebuttal   / score_count if score_count else 0.0
        avg_persuasion = sum_persuasion / score_count if score_count else 0.0
        avg_match      = sum_match      / score_count if score_count else 0.0
        winning_rate = wins/losses*100
        return {
            "target_name": target_name,
            "target_id": target_id,
            "total_debates": total_debates,
            "winning_rate": winning_rate,
            "wins": wins,
            "losses": losses,
            "avg_match": int(avg_match),
            "avg_logicality": int(avg_logicality),
            "avg_rebuttal": int(avg_rebuttal),
            "avg_persuasion": int(avg_persuasion)
        }

def format_to_bold(text:str) -> str:
    """
    **굵은 글씨**를 <strong>굵은글씨</strong>으로 바꿔주는 함수
    짝이 맞지 않는 경우 마지막에 ** 추가.
    """
    count = text.count("**")
    if count % 2 != 0:
        text += "**"  # 강제로 닫는 태그 추가
    return re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

def format_datetime(timestamp: str) -> str:
    """ 년-월-일 시:분:초.밀리초 또는 년-월-일T시:분:초.밀리초Z 형식을 변환 """
    try:
        # ISO 형식인지 확인 (T 포함 여부)
        if "T" in timestamp:
            if "." in timestamp:
                dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        else:
            if "." in timestamp:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            else:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        return dt.strftime("%Y-%m-%d %H:%M:%S")  # 밀리초 제거 후 변환
    except ValueError:
        print(f"Invalid timestamp format: {timestamp}")
        return timestamp  # 에러 발생 시 원본 반환
    
    
    
getData = GetData()
