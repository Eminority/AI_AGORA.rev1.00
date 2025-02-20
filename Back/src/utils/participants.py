from .agora_ai import Agora_AI
from .ai_module.ai_factory import AI_Factory
from vectorstore_module import VectorStoreHandler  
class ParticipantFactory:
    def __init__(self, vector_handler: VectorStoreHandler, ai_factory:AI_Factory):
        self.vector_handler = vector_handler
        self.ai_factory = ai_factory

    def make_participant(self, data: dict = None):
        ai_type = data.get("ai", None)
        # ai type을 기반으로 instance 만들어주기
        ai_instance = self.ai_factory.create_ai_instance(ai_type)
        # 만들어진 ai instance를 참가자 형태로 만들기
        agora_ai = Agora_AI(ai_type=ai_type, ai_instance=ai_instance, personality=data.get("object_attribute", ""), vector_handler=self.vector_handler)
        return Participant(id=str(data["_id"]), name=data["name"], agora_ai=agora_ai, img=data.get("img"))



class Participant:
    #db에서의 _id, name, 사용할 ai, 프로필 사진을 받아오기.
    def __init__(self, id:str, name:str = None, agora_ai:Agora_AI = None, img = None):
        self.id = id
        self.name = name
        self.agora_ai = agora_ai
        self.img = img

    def answer(self, prompt:str = None):
        #ai인 경우
        if self.agora_ai:
            return self.agora_ai.generate_text(prompt)
        # ai가 아닌 경우 = 사람인 경우
        else:
            ###########################임시 작성된 코드
            #실제로는 외부의 입력창 등에서 답변 받아와서 리턴해야.
            #현재는 console창에 입력을 받도록 되어있음.
            return input(prompt)
            ###########################임시 작성된 코드

    

