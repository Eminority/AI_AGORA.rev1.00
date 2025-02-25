
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))



import os
import yaml
import json
from dotenv import load_dotenv
from Back.src.ai.model.gemini import GeminiAPI
from Back.src.utils.mongodb_connection import MongoDBConnection
from Back.src.utils.vectorstorehandler import VectorStoreHandler  # 벡터스토어 관련 모듈
from Back.src.ai.ai_factory import AI_Factory
from Back.src.utils.participant_factory import ParticipantFactory 
from Back.src.progress.debate_2 import Debate_2
from Back.src.utils.progress_manager import ProgressManager
from Back.src.utils.web_scrapper import WebScrapper
from Back.src.utils.detect_persona import DetectPersona

if __name__ == "__main__":

    #MONGO_URI, DB_NAME 확인
    load_dotenv(dotenv_path="..\\Back\\src\\.env", override=True)  # .env 파일 로드

    # MongoDB 연결
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME")

    if not MONGO_URI or not DB_NAME:
        raise ValueError("MONGO_URI 또는 DB_NAME이 .env 파일에서 설정되지 않았습니다.")

    mongodb_connection = MongoDBConnection(MONGO_URI, DB_NAME)

    # AI API 키 불러오기
    AI_API_KEY = json.loads(os.getenv("AI_API_KEY"))
    ai_factory = AI_Factory(AI_API_KEY)

    
    ## config.yaml 불러와서 변수에 저장해두기
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\\config\\config.yaml"))
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # 벡터스토어 핸들러 생성
    vectorstore_handler = VectorStoreHandler(chunk_size=config["VectorStoreHandler"]["chunk_size"],
                                             chunk_overlap=config["VectorStoreHandler"]["chunk_overlap"])


    # Debate 인스턴스 초기화
    participant_factory = ParticipantFactory(vectorstore_handler, ai_factory)





    #persona 생성기
    detect_persona = DetectPersona(GEMINI_API_KEY=AI_API_KEY["GEMINI"])

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
    user = {
        "_id": "67ac1d198f64bb663ade93b3",
        "name": "dog",
        "ai" : "GEMINI",
        "object_attribute": "Loyal, friendly, intelligent, protective, trainable, playful, energetic, adaptable, affectionate, independent",
        "create_time":  "2025-02-12T04:01:29.651Z",
        "img":None
        }
    ####임시 사용자


    # opponent_name = input("상대 이름 설정 : ")
    opponent_name = "cat"
    opponent_id = "temp_id_123456789"
    # opponent_ai = input("ai 설정 - 현재 가능한 AI : GEMINI // 입력  :")
    opponent_ai = "GEMINI"
    opponent = {"name"  : opponent_name,
                "_id"   : opponent_id,
                "ai"    : opponent_ai,
                "img" : None,
                "object_attribute": detect_persona.get_traits(opponent_name)
                }
    
    
    judge_1 = {"ai": "GEMINI"}
    judge_2 = {"ai": "GEMINI"}
    judge_3 = {"ai": "GEMINI"}


    participants = {"pos" : user, "neg" : opponent, "judge_1" : judge_1, "judge_2" : judge_2, "judge_3" : judge_3}
    
    # topic = input("주제 입력 : ")
    topic = "Is it beneficial to walk your pet?"

    progress_manager.create_progress("debate", participant=participants, topic=topic)

    debates = progress_manager.progress_pool.values()
    ###############################임시로 입력받는 테스트 코드
    
    
    ###############################임시로 실행하는 테스트 코드
    for debate in debates:
        while debate.data["status"]["type"] != "end":
            result = debate.progress()
            print()
            print(f"{result['speaker']} : {result['message']}")
    ###############################임시로 실행하는 테스트 코드