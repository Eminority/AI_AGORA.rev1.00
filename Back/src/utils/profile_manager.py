from .mongodb_connection import MongoDBConnection
from .detect_persona import DetectPersona
from .profile import Profile
from datetime import datetime
class ProfileManager:
    def __init__(self, db: MongoDBConnection, detect_persona:DetectPersona):
        self.db = db
        data = db.select_data_from_query(collection_name="object", query={})
        self.objectlist = {}
        self.detect_persona = detect_persona
        for raw_object in data:
            profile = Profile(_id           = str(raw_object.get("_id")),
                          name              = raw_object.get("name"),
                          img               = raw_object.get("img"),
                          ai                = raw_object.get("ai"),
                          create_time       = raw_object.get("create_time"),
                          object_attribute  = raw_object.get("object_attribute"),
                          debate_history    = raw_object.get("debate_history", [])
                          )
            if str(raw_object.get("_id")):
                self.objectlist[profile.data["_id"]] = profile

    async def create_profile(self,
                        name:str=None,
                        img:str=None,
                        ai:str=None):
        if not self.duplicate_object_check(name, ai):
            return {"result":False}
        object_attribute = self.detect_persona.get_traits(name)
        new_obj = Profile(name=name,
                            img=img,
                            ai=ai,
                            object_attribute=object_attribute,
                            create_time=datetime.now()
                            )
        new_obj.save(self.db)
        new_obj.data["_id"] = str(new_obj.data["_id"])
        self.objectlist[new_obj.data["_id"]] = new_obj
        return {"resulr":True, "id":str(new_obj.data["_id"])}
    
    def duplicate_object_check(self, name:str, ai:str):
        """
        참이면 중복없음
        거짓이면 중복있음
        """
        search_result = self.db.select_data_from_query("object",{"name":name, "ai":ai})
        print(search_result)
        if not search_result:
            return True
        else:
            return False
