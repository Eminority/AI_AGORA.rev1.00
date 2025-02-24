## ai 프로필을 만들어서 저장하고 불러올 수 있게끔 하는 모듈
from .mongodb_connection import MongoDBConnection

    
class Profile:
    def __init__(self, _id:str=None,
                        name:str=None,
                        img:str=None,
                        ai:str=None,
                        create_time:str=None,
                        object_attribute:str=None,
                        debate_history:list=[]):
        self.data = {}
        self.data["name"]           = name
        self.data["img"]            = img
        self.data["ai"]             = ai
        self.data["create_time"]    = create_time
        self.data["object_attribute"] = object_attribute
        self.data["debate_history"] = debate_history
        if _id: # id가 None으로라도 들어가있으면 에러 내니까 None이면 아예 안만들기
            self.data["_id"]        = _id

    def save(self, db:MongoDBConnection):
        if self.data.get("_id"): #_id가 이미 있는 경우 update
            db.update_data("object", self.data)
        else : #_id가 없는 경우 insert하고 self id저장
            self.data["_id"] = db.insert_data("object", self.data)