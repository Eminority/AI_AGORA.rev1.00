from .participant import Participant
from ..ai.ai_factory import AI_Factory
from .vectorstorehandler import VectorStoreHandler
 
class ParticipantFactory:
    def __init__(self, vector_handler: VectorStoreHandler, ai_factory:AI_Factory):
        self.vector_handler = vector_handler
        self.ai_factory = ai_factory

    def make_participant(self, data: dict = None):
        ai_type = data.get("ai", None)
        # ai type을 기반으로 instance 만들어주기
        ai_instance = self.ai_factory.create_ai_instance(ai_type)
        # 만들어진 ai instance를 참가자 형태로 만들기

        #### 여기서부터 작성
        agora_ai = Agora_AI(ai_type=ai_type, ai_instance=ai_instance, personality=data.get("object_attribute", ""), vector_handler=self.vector_handler)
        return Participant(id=str(data["_id"]), name=data["name"], agora_ai=agora_ai, img=data.get("img"))


