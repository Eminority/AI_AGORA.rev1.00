from ultralytics import YOLO
import cv2
import json

class YOLODetect:
    def __init__(self, model_path="yolo11n.pt", confidence_threshold=0.5):
        """
        YOLO 객체 탐지 클래스
        :param model_path: 사용할 YOLO 모델 경로
        :param confidence_threshold: 객체 탐지 임계값
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold

    def detect_objects(self, image_path):
        """
        이미지에서 객체를 탐지하고 JSON 형식으로 반환
        :param image_path: 처리할 이미지 파일 경로
        :return: 탐지된 객체 목록 (JSON 형식)
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"오류: '{image_path}' 이미지를 찾을 수 없습니다.")
            return json.dumps({"error": "Image not found"}, indent=4)

        # 객체 탐지 수행
        results = self.model(image)

        detected_objects = []

        for result in results:
            for box in result.boxes:
                if box.conf >= self.confidence_threshold:
                    class_id = int(box.cls)
                    class_name = self.model.names[class_id]
                    bbox = [round(x.item(), 2) for x in box.xyxy[0]]  # 바운딩 박스 좌표

                    object_data = {
                        "object_name": class_name,
                        "confidence": round(box.conf.item(), 2),
                        "bounding_box": {
                            "x1": bbox[0],
                            "y1": bbox[1],
                            "x2": bbox[2],
                            "y2": bbox[3]
                        }
                    }
                    detected_objects.append(object_data)

        #list로 전송
        return detected_objects

#예시
# from yolo_detect import YOLODetect

# # YOLO 객체 탐지기 생성
# detector = YOLODetect()

# # 원하는 이미지 경로 입력
# image_path = "sample.jpg"  # 여기를 변경하면 다른 이미지를 사용할 수 있음

# # 객체 탐지 실행
# json_result = detector.detect_objects(image_path)

# # 결과 출력
# print(json_result)
