import cv2
import random
from ultralytics import YOLO

# YOLO 모델 로드
model = YOLO("best.pt")  # YOLOv8 Nano 모델 사용

# 이미지 로드
image_path = "Volodymyr_Zelenskyy.jpg"  # 탐지할 이미지 파일
image = cv2.imread(image_path)

# 객체 탐지 수행
results = model(image)
font = cv2.FONT_HERSHEY_SIMPLEX
# 클래스별 색상 생성 (클래스 ID에 따라 고유한 색을 할당)
num_classes = len(model.names)


# 탐지 결과 시각화
for result in results:
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])  # 바운딩 박스 좌표
        conf = float(box.conf[0])  # 신뢰도 점수
        cls = int(box.cls[0])  # 클래스 인덱스
        label = f"{model.names[cls]}: {conf:.2f}"  # 라벨 (클래스 이름 + 신뢰도)

        # 클래스에 따른 색상 선택
        color = (0, 0, 255)  

        # 바운딩 박스 그리기
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, label, (x1 - 55, y1 - 5), font, 0.5, color, 2)

# 결과 이미지 저장
cv2.imwrite("Volodymyr_Zelenskyy_output.jpg", image)
print("객체 탐지 완료! 결과가 output.jpg에 저장되었습니다.")
