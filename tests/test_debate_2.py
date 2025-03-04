
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from Back.src.utils.profile_manager import ProfileManager

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
    
    
    judge_1 = {"ai": "GEMINI", "name":"judge"}
    judge_2 = {"ai": "GEMINI", "name":"judge"}
    judge_3 = {"ai": "GEMINI", "name":"judge"}


    participants = {"pos" : user, "neg" : opponent, "judge_1" : judge_1, "judge_2" : judge_2, "judge_3" : judge_3}
    
    # topic = input("주제 입력 : ")
    topic = "Is it beneficial to walk your pet?"

    progress_manager.create_progress("debate_2", participant=participants, topic=topic)

    debates = progress_manager.progress_pool.values()
    ###############################임시로 입력받는 테스트 코드
    
    
    ###############################임시로 실행하는 테스트 코드
    for debate in debates:
        while debate.data["status"]["type"] != "end":
            result = debate.progress()
            print()
            print(f"{result['speaker']} : {result['message']}")
            progress_manager.save(str(debate.data["_id"]))
    ###############################임시로 실행하는 테스트 코드

    collection = mongodb_connection.get_collection("progress")  # "progress" 컬렉션 예시
    # ProfileManager 객체 생성
    profile_manager = ProfileManager(db=mongodb_connection, detect_persona=detect_persona)

    # target_id 설정
    target_id = "67b5486164b7152a1538359b"

    # get_stats_by_id 메서드 호출 (ProfileManager 객체를 통해 호출)
    stats_result = profile_manager.get_stats_by_id(collection, target_id)

    # 결과 출력
    if stats_result:
        print("====== Extended Stats and Scores ======")
        print(f"Name: {stats_result['target_name']}")
        print(f"ID: {stats_result['target_id']}")
        print(f"토론 참여 횟수 (total_debates): {stats_result['total_debates']}")
        print(f"승률 (winning_rate): {stats_result['winning_rate']}%")
        print(f"승리 횟수 (wins): {stats_result['wins']}")
        print(f"패배 횟수 (losses): {stats_result['losses']}")
        print(f"평균 Match: {stats_result['avg_match']}")
        print(f"평균 Logicality: {stats_result['avg_logicality']}")
        print(f"평균 Rebuttal: {stats_result['avg_rebuttal']}")
        print(f"평균 Persuasion: {stats_result['avg_persuasion']}")
    else:
        print("통계 정보를 가져오는 데 실패했습니다.")

    # 연결 종료
    mongodb_connection.close_connection()