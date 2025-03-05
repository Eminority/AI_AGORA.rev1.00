import os
import random
from dotenv import load_dotenv
from Back.src.utils.mongodb_connection import MongoDBConnection


class RandomSelect :
    def __init__(self, MONGO_URI : str, DB_NAME : str) -> None:
        # MongoDB 연결 객체 생성
        self.db_conn = MongoDBConnection(MONGO_URI, DB_NAME)

    def GetRandomName(self, count : int = 2) :
        # 전체 문서를 가져옵니다. (필요한 경우 쿼리 조건을 추가할 수 있습니다.)
        docs = self.db_conn.select_data_from_query("object", {})
        docs = list(docs)
        # 각 문서에서 'name' 필드를 추출합니다.
        # names = [doc.get("name") for doc in docs if "name" in doc]
        # 문서가 충분한지 확인한 후, 무작위로 두 개 선택합니다.
        if len(docs) < count:
            print("문서가 충분하지 않습니다.")
            return []
        return random.sample(docs, count)
        
            
    def close_connection(self):
        # MongoDB 연결 종료
        self.db_conn.close_connection()
