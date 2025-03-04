from .participant_factory import ParticipantFactory
from ..progress.debate import Debate
from ..progress.progress import Progress
from ..progress.debate_2 import Debate_2
from ..progress.debate_3 import Debate_3
from ..ai.ai_instance import AI_Instance
from .mongodb_connection import MongoDBConnection
from .web_scrapper import WebScrapper
from .vectorstorehandler import VectorStoreHandler
from .profile_manager import ProfileManager
import asyncio
from typing import Dict
class ProgressManager:
    def __init__(self, participant_factory:ParticipantFactory,
                        web_scrapper:WebScrapper,
                        mongoDBConnection:MongoDBConnection,
                        topic_checker:AI_Instance,
                        vectorstore_handler: VectorStoreHandler,
                        generate_text_config: dict):
        
        self.participant_factory = participant_factory
        self.web_scrapper = web_scrapper
        self.mongoDBConnection = mongoDBConnection
        self.topic_checker = topic_checker
        self.vectorstore_handler = vectorstore_handler
        self.progress_pool:Dict[str, Progress] = {}
        self.generate_text_config = generate_text_config
        self.auto_progress_create_task = None
        self.load_data_from_db()


    def create_progress(self, progress_type:str, participant:dict, topic:str) -> dict:
        """
        progress의 type과 참여자, 주제를 받아 progress를 생성, 작성하고 self.progress_pool에 등록하는 메서드
        반환값은 {"result":성공여부(bool), "id":생성된 progress id(str)}
        """
        result = {"result":False, "id":None}
        progress = None
        # 기본 토론 타입
        if progress_type == "debate":
            if self.check_topic_for_debate(topic):
                # progress type==debate인 경우
                # participant = {pos = {}, neg = {}}
                # debate에서 judge 없으면 끼워넣기
                if not participant.get("judge"):
                    participant["judge"] = {"ai":"GEMINI", "name":"judge"}
                generated_participant = self.set_participant(participants=participant)
                progress = Debate(participant=generated_participant, generate_text_config=self.generate_text_config["debate"])
                #progress.vectorstore = self.ready_to_progress(topic=topic)
        # 판사 3명인 토론 타입
        elif progress_type == "debate_2":
            # self.chect_topic_for_debate(topic) 생략
            if not participant.get("judge_1"):
                participant["judge_1"] = {"ai":"GEMINI", "name":"judge_1"}
            if not participant.get("judge_2"):
                participant["judge_2"] = {"ai":"GEMINI", "name":"judge_2"}
            if not participant.get("judge_3"):
                participant["judge_3"] = {"ai":"GEMINI", "name":"judge_3"}
            generated_participant = self.set_participant(participant)
            progress = Debate_2(participant=generated_participant, generate_text_config=self.generate_text_config["debate"])
        # 발언자 결정 에이전트 집어넣은 타입
        elif progress_type == "debate_3":
            if not participant.get("judge"):
                participant["judge"] = {"name"  : "judge",
                                        "ai"    : "GEMINI",
                                        "img" : None,
                                        "object_attribute": ""}
            if not participant.get("judge_1"):
                participant["judge"] = {"name"  : "judge",
                                        "ai"    : "GEMINI",
                                        "img" : None,
                                        "object_attribute": ""}
            if not participant.get("judge_2"):
                participant["judge"] = {"name"  : "judge",
                                        "ai"    : "GEMINI",
                                        "img" : None,
                                        "object_attribute": ""}
            if not participant.get("judge_3"):
                participant["judge"] = {"name"  : "judge",
                                        "ai"    : "GEMINI",
                                        "img" : None,
                                        "object_attribute": ""}                                 
            if not participant.get("next_speaker_agent"):
                participant["next_speaker_agent"] = {"name"  : "next_speaker_agent",
                                        "ai"    : "GEMINI",
                                        "img" : None,
                                        "object_attribute": ""}
            if not participant.get("progress_agent"):
                participant["progress_agent"] = {"name"  : "progress_agent",
                                        "ai"    : "GEMINI",
                                        "img" : None,
                                        "object_attribute": ""}
            generated_participant = self.set_participant(participant)
            progress = Debate_3(participant=generated_participant,
                              generate_text_config=self.generate_text_config["debate"])

        if progress:
            progress.data["topic"] = topic
            id = str(self.mongoDBConnection.insert_data("progress", progress.data))
            progress.vectorstore = self.ready_to_progress_with_personality(topic, generated_participant)
            progress.data["_id"] = id
            self.progress_pool[id] = progress
            result["result"] = True
            result["id"] = id
        print(f"progress 생성됨! {type(progress)}, {progress.data['topic']}")
        return result

    def ready_to_progress(self, topic):
        """
        progress를 위해서 topic을 crawling해서 vectorstoring해서 vectorstore 반환
        """
        articles = self.web_scrapper.get_articles(topic=topic)
        return self.vectorstore_handler.vectorstoring(articles=articles)

    def ready_to_progress_with_personality(self, topic, participants):
        articles = []
        articles.extend(self.web_scrapper.get_articles(topic=topic))
        for participant in participants.values():
            print(participant.name)
            articles.extend(self.web_scrapper.get_articles(participant.name))
        print(articles)
        return self.vectorstore_handler.vectorstoring(articles)
    
    def check_topic_for_debate(self, topic:str) -> bool:
        """
        LLM을 사용하여 주제가 토론 가능 여부를 판별합니다.
        :param topic: 사용자가 입력한 토론 주제
        :return: True (토론 가능) / False (토론 불가능)
        """
        prompt = f"""
        Determine if the following topic is debatable. 
        A debatable topic must have valid opposing arguments for both sides. 
        If the topic is too subjective or lacks logical opposition, return False. 
        Respond only with 'True' or 'False'.
        
        Topic: "{topic}"
        """

        try:
            response = self.topic_checker.generate_text(prompt, max_tokens=5, temperature=0.5)  # 최대 5토큰 (True/False 응답만 받도록)
            result = response.strip().lower()
            return result == "true"
        except Exception as e:
            print(f"Error in is_debatable_topic: {e}")
            return False  # 오류 시 기본값 False 반환

    def set_participant(self, participants:dict) -> dict:
        """
        participant dict 형태의 데이터를 받아서 ai 객체를 생성해 반환하는 함수
        debate의 participants의 경우 {"pos": { ... }, "neg": { ... }, "judge": { ... } }
        """
        result = {}
        for role in participants.keys():
            # 이름과 ai가 할당되어있지 않다면
            if not participants[role].get("ai") and not participants[role].get("name"):
                # id값으로 받아와서 채우기
                participants[role] = self.mongoDBConnection.select_data_from_id("object", participants[role].get("id"))
            result[role] = self.participant_factory.make_participant(participants[role])
        return result
    
    def save(self, progress_id:str):
        """
        progress id를 받아 해당 아이디의 progress를 저장하는 함수
        """
        return self.mongoDBConnection.update_data("progress", self.progress_pool[progress_id].data)


    def load_data_from_db(self):
        progress_list = self.mongoDBConnection.select_data_from_query("progress")
        # progress 목록 불러오기
        for data in progress_list:
            self.progress_pool[str(data["_id"])] = self.load_progress(data)
            print(str(data["_id"]))
        print (f"{len(progress_list)} 개의 Progress 로드됨!")

    def load_progress(self, data:dict) -> Progress:
        """
        progress를 data만 받아서 pool에 등록하는 메서드
        end일 경우 데이터만 남기기.
        end가 아닐 경우 participants의 데이터를 읽어와서 ai 등록
        """
        progress = None
        id = data.get("_id")
        if not id:
            print("아이디 없는 데이터!")
            return progress
        if data.get("status") and data["status"].get("type") == "end":
            progress = Progress(participant={},
                                        generate_text_config={},
                                        data=data)
            return progress
        elif data.get("status"):
            # end가 아니고 status가 있는 경우 - ai 등록하기.
            # debate인 경우 debate로 생성
            participants = self.set_participant(data.get("participants"))
            if data.get("type") == "debate":
                progress = Debate(participant = participants,
                                  generate_text_config = self.generate_text_config["debate"],
                                  data = data)
            elif data.get("type") == "debate_2":
                progress = Debate_2(participant = participants,
                                  generate_text_config = self.generate_text_config["debate"],
                                  data = data)
            elif data.get("type") == "debate_3":
                progress = Debate_3(participant = participants,
                                  generate_text_config = self.generate_text_config["debate"],
                                  data = data)
            else:
                progress = Progress(participant = participants,
                                    generate_text_config={},
                                    data = data)
            return progress
        else:
            print("뭔가 잘못된 데이터!")
            return progress
        

    async def auto_progress_create(self, profile_manager:ProfileManager, topic:str=None):
        if not topic:
            topic = self.auto_topic_create()
        profiles = list(profile_manager.objectlist.keys())
        front = 0
        try:
            while front < len(profiles) -1:
                pos = {"id":profiles[front]}
                back = front + 1
                while back < len(profiles):
                    neg = {"id":profiles[back]}
                    print(f"{front}, {back}")
                    try:
                        participants = {"pos":pos, "neg":neg}
                        await asyncio.to_thread(self.create_progress, "debate_2", participants, topic)
                        participants2 = {"pos":neg, "neg":pos}
                        await asyncio.to_thread(self.create_progress, "debate_2", participants2, topic)
                    except Exception as e:
                        print(f"auto_progress_create 중 오류 {e} 발생")
                    back += 1
                front += 1
                await asyncio.sleep(1)
        except Exception as e:
            print(f"auto_progress_create 중 오류 발생 : {e}")
            
        
        

    def auto_topic_create(self) -> str:
        user_prompt = "Return a single debate topic in one sentence. Keep it concise and argumentative. No extra details."
        topic = self.topic_checker.generate_text(user_prompt,temperature=0.5,max_tokens=100)
        print(topic)
        return topic