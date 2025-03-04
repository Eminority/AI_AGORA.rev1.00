from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId

# MongoDB 연결 및 데이터 저장 클래스
class MongoDBConnection:
    def __init__(self, uri: str, db_name: str):
        """
        MongoDB 연결을 위한 초기화.
        :param uri: MongoDB 연결 URI
        :param db_name: 사용할 데이터베이스 이름
        """
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
            # 연결 테스트
            self.client.admin.command('ping')
        except Exception as e:
            print("❌ Connection failed:", e)

    def get_collection(self, collection_name: str):
        """
        지정된 컬렉션 객체를 반환합니다.
        :param collection_name: 컬렉션 이름
        :return: pymongo.collection.Collection 객체
        """
        return self.db[collection_name]

    def insert_data(self, collection_name: str, data: dict):
        return self.db[collection_name].insert_one(data).inserted_id
    
    def select_data_from_id(self, collection_name: str, id: str):
        return self.db[collection_name].find_one({"_id": ObjectId(id)})

    def select_data_from_query(self, collection_name: str, query: dict = {}) -> list:
        cursor = self.db[collection_name].find(query)
        result = []
        for data in cursor:
            result.append(data)
        return result

    def update_data(self, collection_name: str, data: dict):
        original_id = data["_id"]
        if type(original_id) != ObjectId:
            data["_id"] = ObjectId(data["_id"])
        result = self.db[collection_name].update_one({"_id": data["_id"]}, {"$set": data})
        data["_id"] = original_id
        return result

    def close_connection(self):
        """
        MongoDB 연결 종료
        """
        self.client.close()