from .participant_factory import ParticipantFactory
from ..progress.debate import Debate
from ..ai.ai_instance import AI_Instance
from .mongodb_connection import MongoDBConnection
from .web_scrapper import WebScrapper
from .vectorstorehandler import VectorStoreHandler
class ProgressManager:
    def __init__(self, participant_factory:ParticipantFactory,
                        web_scrapper:WebScrapper,
                        mongoDBConnection:MongoDBConnection,
                        topic_checker:AI_Instance,
                        vectorstore_handler: VectorStoreHandler):
        
        self.participant_factory = participant_factory
        self.web_scrapper = web_scrapper
        self.mongoDBConnection = mongoDBConnection
        self.topic_checker = topic_checker
        self.vectorstore_handler = vectorstore_handler
        self.progress_pool = {}


    def create_progress(self, progress_type:str, participant:dict, topic:str) -> dict:
        """
        progress의 type과 참여자, 주제를 받아 progress를 생성, 작성하고 self.progress_pool에 등록하는 메서드
        반환값은 {"result":성공여부(bool), "id":생성된 progress id(str)}
        """
        result = {"result":False, "id":None}

        if progress_type == "debate":
            if self.check_topic_for_debate(topic):
                # progress type==debate인 경우
                # participant = {judge = {}, pos = {}, neg = {}}
                generated_participant = self.set_participant(participants=participant)
                debate = Debate(participant=generated_participant)
                debate.vectorstore = self.ready_to_progress(topic=topic)
                debate.data["topic"] = topic
                debate.data["_id"] = id
                id = self.mongoDBConnection.insert_data("debate", debate.data)
                self.progress_pool[id] = debate
                result["result"] = True
                result["id"] = id
                return result
        else:
            return result
        

    def ready_to_progress(self, topic):
        """
        progress를 위해서 topic을 crawling해서 vectorstoring해서 vectorstore 반환
        """
        articles = self.web_scrapper.get_articles(topic=topic)
        return self.vectorstore_handler.vectorstoring(articles=articles)

    
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
            response = self.topic_checker.generate_text(prompt, max_tokens=5)  # 최대 5토큰 (True/False 응답만 받도록)
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
            result[role] = self.participant_factory.make_participant(participants[role])
        return result
    
    def save(self, progress_id:str):
        """
        progress id를 받아 해당 아이디의 progress를 저장하는 함수
        """
        pass

    def load(self):
        """
        load해서 self.progress_pool에 등록하는 함수
        """
        pass
