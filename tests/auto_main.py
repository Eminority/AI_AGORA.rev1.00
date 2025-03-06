
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import traceback

import os
import yaml
import json
from dotenv import load_dotenv
from Back.src.ai.model.gemini import GeminiAPI
from Back.src.utils.mongodb_connection import MongoDBConnection
from Back.src.utils.vectorstorehandler import VectorStoreHandler  # 벡터스토어 관련 모듈
from Back.src.ai.ai_factory import AI_Factory
from Back.src.utils.participant_factory import ParticipantFactory 
from Back.src.progress.debate import Debate
from Back.src.utils.progress_manager import ProgressManager
from Back.src.utils.web_scrapper import WebScrapper
from Back.src.utils.detect_persona import DetectPersona
from test_random_sampling import RandomSelect

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
    
    random_selector = RandomSelect(MONGO_URI, DB_NAME)

    loopcount = int(input("자동으로 돌아갈 횟수 입력 :"))


    for _ in range(loopcount):
        random_docs = random_selector.GetRandomName(count = 2)


        if len(random_docs) < 2 :
            print("문서가 충분하지 않습니다")
            sys.exit(0)

        pos_doc, neg_doc = random_docs

        pos = {
            "_id": str(pos_doc["_id"]),  # _id를 문자열로 변환
            "name": pos_doc.get("name", ""),
            "ai": "GEMINI",
            "object_attribute": pos_doc.get("object_attribute", ""),
            "create_time": str(pos_doc.get("create_time", "")),
            "img": pos_doc.get("img", None)
            }


        neg = {
            "_id": str(neg_doc["_id"]),
            "name": neg_doc.get("name", ""),
            "ai": "GEMINI",
            "object_attribute": neg_doc.get("object_attribute", ""),
            "create_time": str(neg_doc.get("create_time", "")),
            "img": neg_doc.get("img", None)
            }
        
        
        judge = {"ai": "GEMINI", "name":"판사"}
        next_speaker_agent = {"ai": "GEMINI", "name":"next_speaker_agent"}
        progress_agent = {"ai": "GEMINI", "name":"progress_agent"}
        judge_1 = {"ai": "GEMINI", "name":"judge_1"}
        judge_2 = {"ai": "GEMINI", "name":"judge_2"}
        judge_3 = {"ai": "GEMINI", "name":"judge_3"}

        participants = {"pos" : pos, "neg" : neg, "judge" : judge, "next_speaker_agent" : next_speaker_agent, "progress_agent" : progress_agent, "judge_1" : judge_1, "judge_2" : judge_2, "judge_3" : judge_3}
        
        topic = progress_manager.auto_topic_create()
        try:
            progress_manager.create_progress("debate_2", participant=participants, topic=topic)
        except Exception as e:
            print(e)
            traceback.print_exc()
            break

    ###############################임시로 입력받는 테스트 코드
    
    debates = progress_manager.progress_pool.values()
    
    ###############################임시로 실행하는 테스트 코드
    for debate in debates:
        while debate.data["status"]["type"] != "end":
            result = debate.progress()
            print()
            print(f"{result['speaker']} : {result['message']}")
        progress_manager.save(str(debate.data["_id"]))
    ###############################임시로 실행하는 테스트 코드