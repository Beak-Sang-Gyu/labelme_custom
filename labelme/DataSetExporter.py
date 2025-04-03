import os
import ftplib
import json
from loguru import logger
from PyQt5.QtWidgets import QApplication

class DatasetExporter:
    def __init__(self, ftp, remote_base_path, main_window=None):
        self.ftp = ftp
        self.remote_base_path = remote_base_path.rstrip('/')
        self.main_window = main_window

    def log(self, message, warning=False, error=False):
        if warning:
            logger.warning(message)
        elif error:
            logger.error(message)
        else:
            logger.info(message)

        if self.main_window:
            self.main_window.status_bar.showMessage(message, 5000)
            QApplication.processEvents()

    def create_remote_directory(self, path):
        path_parts = path.strip('/').split('/')
        current_path = self.remote_base_path
        for part in path_parts:
            current_path = os.path.join(current_path, part).replace("\\", "/")
            try:
                self.ftp.cwd(current_path)
            except ftplib.error_perm:
                try:
                    self.ftp.mkd(current_path)
                    self.log(f"디렉토리 생성: {current_path}")
                except Exception as e:
                    self.log(f"디렉토리 생성 실패: {current_path}, 오류: {e}", error=True)
                    return

    def upload_to_ftp(self, local_path, base_filename):
        allowed_folders = {"data", "image"}
        for root, dirs, files in os.walk(local_path):
            rel_path = os.path.relpath(root, local_path).replace("\\", "/")
            if rel_path == ".":
                continue

            parts = rel_path.split('/') if rel_path else []
            if not parts or parts[0].lower() not in allowed_folders:
                self.log(f"예상되지 않은 폴더 경로: {self.remote_base_path}/{rel_path}, 무시됨.", warning=True)
                continue

            first_dir = parts[0].lower()
            if first_dir == "data":
                remote_folder = "annotations"
            elif first_dir == "image":
                # image 폴더 최상위의 파일은 원본 이미지로 간주 → origins/images에 업로드
                if len(parts) == 1:
                    remote_folder = "origins/images"
                else:
                    label = parts[1]
                    remote_folder = f"images/{label}"  # 하위 폴더: crop 이미지로 업로드
            else:
                self.log(f"예상되지 않은 폴더: {first_dir}, 무시됨.", warning=True)
                continue

            self.create_remote_directory(remote_folder)
            full_remote_folder = f"{self.remote_base_path}/{remote_folder}"
            try:
                self.ftp.cwd(full_remote_folder)
            except ftplib.error_perm:
                self.log(f"디렉토리 변경 실패: {full_remote_folder}", error=True)
                continue

            for file in files:
                local_file_path = os.path.join(root, file)
                new_filename = f"{base_filename}_{file}"
                if first_dir == "data":
                    if file.endswith(".json"):
                        if "coco_annotation" in file:
                            remote_path = f"{self.remote_base_path}/annotations/{new_filename}"
                        else:
                            remote_path = f"{self.remote_base_path}/annotations/labelme_jsons/{new_filename}"
                            self.create_remote_directory("annotations/labelme_jsons")
                    elif file.lower().endswith(('.zip', '.tar', '.tar.gz', '.tgz')):
                        remote_path = f"{self.remote_base_path}/annotations/archives/{new_filename}"
                        self.create_remote_directory("annotations/archives")
                    else:
                        continue
                elif first_dir == "image":
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        if len(parts) == 1:
                            remote_path = f"{self.remote_base_path}/origins/images/{new_filename}"
                        else:
                            remote_path = f"{self.remote_base_path}/{remote_folder}/{new_filename}"
                    else:
                        continue
                else:
                    continue

                try:
                    with open(local_file_path, "rb") as f:
                        self.ftp.storbinary(f"STOR {remote_path}", f)
                        self.log(f"파일 업로드 완료: {remote_path}")
                except Exception as e:
                    self.log(f"파일 업로드 실패: {remote_path}, 오류: {e}", error=True)

        # 아카이브 파일 업로드
        self.upload_archive(local_path, base_filename)

        # COCO 변환 및 업로드
        data_folder = os.path.join(local_path, "data")
        if os.path.exists(data_folder):
            json_files = [os.path.join(data_folder, f) for f in os.listdir(data_folder) if f.endswith(".json")]
            local_coco_json = os.path.join(local_path, f"{base_filename}_coco.json")
            self.convert_to_coco(json_files, local_coco_json)
            remote_coco_json = f"{self.remote_base_path}/annotations/coco/{base_filename}_coco.json"
            self.create_remote_directory("annotations/coco")
            try:
                with open(local_coco_json, "rb") as f:
                    self.ftp.storbinary(f"STOR {remote_coco_json}", f)
                    self.log(f"COCO 파일 업로드 완료: {remote_coco_json}")
            except Exception as e:
                self.log(f"COCO 파일 업로드 실패: {remote_coco_json}, 오류: {e}", error=True)

    def upload_archive(self, local_path, base_filename):
        parent_dir = os.path.dirname(local_path)
        archive_path = os.path.join(parent_dir, f"{base_filename}.zip")
        if os.path.exists(archive_path):
            self.create_remote_directory("archives")
            remote_archive_path = f"{self.remote_base_path}/archives/{base_filename}.zip"
            try:
                with open(archive_path, "rb") as f:
                    self.ftp.storbinary(f"STOR {remote_archive_path}", f)
                    self.log(f"아카이브 파일 업로드 완료: {remote_archive_path}")
            except Exception as e:
                self.log(f"아카이브 파일 업로드 실패: {remote_archive_path}, 오류: {e}", error=True)


    def convert_to_coco(self, json_files, output_path):
        coco_data = {"images": [], "annotations": [], "categories": []}
        annotation_id = 1
        category_map = {}
        category_id = 1

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                image_id = len(coco_data["images"]) + 1
                coco_data["images"].append({
                    "id": image_id,
                    "file_name": data["imagePath"],
                    "width": data["imageWidth"],
                    "height": data["imageHeight"]
                })

                for shape in data["shapes"]:
                    label = shape["label"]
                    if label not in category_map:
                        category_map[label] = category_id
                        coco_data["categories"].append({"id": category_id, "name": label})
                        category_id += 1

                    coco_data["annotations"].append({
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": category_map[label],
                        "bbox": [0, 0, 0, 0],  # 임시값, 실제 변환 필요
                        "area": 0,
                        "segmentation": [],
                        "iscrowd": 0
                    })
                    annotation_id += 1

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(coco_data, f, indent=4)
        self.log(f"COCO 변환 완료: {output_path}")
