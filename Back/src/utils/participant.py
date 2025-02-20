from ..ai.ai_instance import AI_Instance

class Participant:
    #db에서의 _id, name, 사용할 ai, 프로필 사진을 받아오기.
    def __init__(self, id:str, name:str = None, ai_instance:AI_Instance = None, img = None):
        self.id = id
        self.name = name
        self.img = img
        self.ai_instance = ai_instance

    

