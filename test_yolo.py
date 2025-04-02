
from ultralytics import YOLO
import cv2
import os

# YOLOv8n 모델 로드 (사전 학습된 모델)
model = YOLO("yolov8n.pt")  # 'yolov8n.pt' 모델 경로

# 비디오 파일 열기 (0은 웹캠)
video_path = "C:\AI\source\857263-hd_1920_1080_24fps.mp4"  # 동영상 파일 경로, 웹캠 사용 시 0 입력
cap = cv2.VideoCapture(video_path)

# 저장할 폴더 생성
output_folder = "detected_frames"
os.makedirs(output_folder, exist_ok=True)

frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break  # 영상 끝나면 종료

    # YOLO 객체 탐지 실행
    results = model(frame)

    # 객체 감지된 경우 이미지 저장
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # 바운딩 박스 좌표
            class_id = int(box.cls[0])  # 감지된 클래스 ID
            confidence = box.conf[0].item()  # 신뢰도 점수

            # 차량(class_id=2) 감지 & 신뢰도 50% 이상인 경우 저장
            if class_id == 2 and confidence > 0.5:  # 차량은 class_id 2로 설정 (coco dataset 기준)
                cropped_car = frame[y1:y2, x1:x2]  # 차량 부분만 자르기
                car_image_path = f"{output_folder}/car_{frame_count}_{x1}_{y1}.jpg"  # 파일 이름에 좌표 추가
                cv2.imwrite(car_image_path, cropped_car)  # 자른 이미지 저장
                print(f"🚗 차량 감지! {car_image_path} 저장됨")

            # 바운딩 박스 그리기
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Car {confidence:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 전체 프레임 저장
    frame_filename = f"{output_folder}/frame_{frame_count:03d}.jpg"
    cv2.imwrite(frame_filename, frame)
    print(f"🖼️ 프레임 {frame_count} 저장됨: {frame_filename}")

    frame_count += 1

cap.release()