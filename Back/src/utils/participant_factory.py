from .participant import Participant
from ..ai.ai_factory import AI_Factory
from .vectorstorehandler import VectorStoreHandler
 
class ParticipantFactory:
    def __init__(self, vector_handler: VectorStoreHandler, ai_factory:AI_Factory):
        self.vector_handler = vector_handler
        self.ai_factory = ai_factory

    def make_participant(self, data: dict = None) -> Participant:
        """
        data:dict 구조는 {"name":물체이름, "ai":모델 이름, "img":image id}
        """
        # ai type을 기반으로 instance 만들어주기
        ai_type = data.get("ai", None)
        ai_instance = self.ai_factory.create_ai_instance(ai_type)
        ai_instance.set_personality(data.get("object_attribute"))
        # 만들어진 ai instance를 참가자 형태로 만들기
        return Participant(id=str(data.get("_id", "")),
                           name=data.get("name", ""),
                           ai_instance=ai_instance,
                           img=data.get("img"),
                           object_attribute=data.get("object_attribute"))