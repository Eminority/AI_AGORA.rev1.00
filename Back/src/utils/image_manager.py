import base64
from fastapi import UploadFile, File
from db_module import MongoDBConnection
from datetime import datetime
import shutil
import os
from PIL import Image
class ImageManager:
    def __init__(self, db:MongoDBConnection, img_path:str):
        self.db = db
        self.img_path = img_path
    

    def save_image_in_mongoDB_from_local(self, image_name:str) -> dict:
        """
        image_name과 self.img_path를 조합해서 저장된 이미지를 mongoDB에 올리기기
        {"result": "success" or "error", "file_id":mongoDB에 업로드된 ID}
        """
        full_path = os.path.join(self.img_path, image_name)
        if not os.path.exists(full_path):
            return {"result":"error"}
        with open(full_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        image_data = {"filename" : f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{image_name}", "data": encoded_string}
        result = self.db.insert_data('image', image_data)
        return {"result":"success", "file_id": str(result)}

    def save_image_in_local_from_mongoDB(self, file_id:str) -> dict:
        try:
            image_data = self.db.select_data_from_id('image', file_id)

            if not image_data:
                return {"error": "File not found"}
            
            image = base64.b64decode(image_data["data"])
            with open(f"{self.img_path}\\{image_data['filename']}", "wb") as file:
                file.write(image)
            return {"result":True, "data": f"{self.img_path}\\{image_data['filename']}"}
        
        except Exception as e:
            return {"result":False, "data":e}
        
    def save_image_in_local_from_form(self, file:UploadFile=File(...)) -> dict:
        save_path = f"{self.img_path}\\{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{file.filename}.png"
        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            return {"result":True, "data":save_path}
        except Exception as e:
            print(e)
            return {"result":False, "data":e}
        
    def crop_image(self, image_path:str, objectlist:list) -> dict:
        """
        로컬의 이미지를 잘라서 저장하고 자른 목록을 반환
        """
        image_name = image_path.split("\\")[-1]
        target_image = Image.open(image_path)
        result = {}
        for detected_object in objectlist:
            bbox = detected_object["bounding_box"]
            x1 = int(bbox["x1"])
            x2 = int(bbox["x2"])
            y1 = int(bbox["y1"])
            y2 = int(bbox["y2"])
            cropped_image = target_image.crop((x1, y1, x2, y2))
            cropped_image_name = f"cropped_{detected_object['object_name']}_{image_name}"
            cropped_image_path = os.path.join(self.img_path, cropped_image_name)
            cropped_image.save(cropped_image_path)
            result[cropped_image_name] = {"name":detected_object["object_name"],"filename":cropped_image_name}
        return result