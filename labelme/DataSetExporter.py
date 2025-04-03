import os
import ftplib
from loguru import logger
import json
import random

class DatasetExporter:
    def __init__(self, ftp, remote_base_path):
        self.ftp = ftp
        self.remote_base_path = remote_base_path.rstrip('/')

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
                    logger.info(f"디렉토리 생성: {current_path}")
                except Exception as e:
                    logger.error(f"디렉토리 생성 실패: {current_path}, 오류: {e}")
                    return

    def upload_to_ftp(self, local_path, base_filename):
        allowed_folders = {"data", "image"}
        for root, dirs, files in os.walk(local_path):
            rel_path = os.path.relpath(root, local_path).replace("\\", "/")
            if rel_path == ".":
                continue

            parts = rel_path.split('/') if rel_path else []
            if not parts or parts[0].lower() not in allowed_folders:
                logger.warning(f"예상되지 않은 폴더 경로: {self.remote_base_path}/{rel_path}, 무시됨.")
                continue

            first_dir = parts[0].lower()

            if first_dir == "data":
                remote_folder = "annotations"
            elif first_dir == "image":
                if len(parts) == 1:
                    remote_folder = "origin/images"
                else:
                    label = parts[1]
                    remote_folder = f"images/{label}"
            else:
                logger.warning(f"예상되지 않은 폴더: {first_dir}, 무시됨.")
                continue
            self.create_remote_directory(remote_folder)
            full_remote_folder = f"{self.remote_base_path}/{remote_folder}"
            try:
                self.ftp.cwd(full_remote_folder)
            except ftplib.error_perm:
                logger.error(f"디렉토리 변경 실패: {full_remote_folder}")
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
                            self.create_remote_directory("/annotations/labelme_jsons")

                    elif file.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz")):
                        remote_path = f"{self.remote_base_path}/annotations/archives/{new_filename}"
                    else:
                        continue
                elif first_dir == "image":
                    if file.lower().endswith((".png", ".jpg", ".jpeg")):
                        if len(parts) == 1:
                            remote_path = f"{self.remote_base_path}/origin/images/{new_filename}"
                        else:
                            remote_path = f"{self.remote_base_path}/{remote_folder}/{new_filename}"
                    else:
                        continue
                else:
                    continue

                try:
                    with open(local_file_path, "rb") as f:
                        self.ftp.storbinary(f"STOR {remote_path}", f)
                        logger.info(f"파일 업로드 완료: {remote_path}")
                except Exception as e:
                    logger.error(f"파일 업로드 실패: {remote_path}, 오류: {e}")

        parent_dir = os.path.dirname(local_path)
        archive_path = os.path.join(parent_dir, f"{base_filename}.zip")

        if os.path.exists(archive_path):
            self.create_remote_directory("archives")
            remote_archive_path = f"{self.remote_base_path}/archives/{base_filename}.zip"
            try:
                with open(archive_path, "rb") as f:
                    self.ftp.storbinary(f"STOR {remote_archive_path}", f)
                    logger.info(f"아카이브 파일 업로드 완료: {remote_archive_path}")
            except Exception as e:
                logger.error(f"아카이브 파일 업로드 실패: {remote_archive_path}, 오류: {e}")
