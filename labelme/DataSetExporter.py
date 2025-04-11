import os
import json
import shutil
import time
import zipfile
from PIL import Image, ImageDraw
from loguru import logger
from PyQt5.QtWidgets import QApplication
from datetime import datetime

class DatasetExporter:
    def __init__(self, main_window):
        self.main_window = main_window
        # labelPath 끝의 슬래시 제거
        self.labelPath = main_window.labelPath.rstrip(os.sep)

    def log(self, message, warning=False, error=False):
        if warning:
            logger.warning(message)
        elif error:
            logger.error(message)
        else:
            logger.info(message)
        if self.main_window:
            # 상태바에 메시지 표시
            self.main_window.status_bar.showMessage(message, 5000)
            QApplication.processEvents()

    def ensure_dirs(self):
        """
        필요한 디렉터리들이 없으면 생성합니다.
        """
        dirs = [
            os.path.join(self.labelPath, 'annotations', 'coco'),
            os.path.join(self.labelPath, 'annotations', 'labelme_jsons'),
            os.path.join(self.labelPath, 'images'),
            os.path.join(self.labelPath, 'origins','images'),    # 원본 이미지 디렉터리
            os.path.join(self.labelPath, 'archive'),    # ZIP 파일을 저장할 디렉터리
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            self.log(f"디렉토리 확인/생성: {d}")

    def export(self):
        """
        LabelMe JSON → COCO JSON 변환 및 이미지 크롭,
        그리고 최종 ZIP 아카이브 생성까지 수행합니다.
        """
        self.ensure_dirs()

        json_dir = os.path.join(self.labelPath, 'annotations', 'labelme_jsons')
        if not os.path.isdir(json_dir):
            self.log(f"JSON 디렉터리 없음: {json_dir}", error=True)
            return False

        json_files = [f for f in os.listdir(json_dir) if f.lower().endswith('.json')]
        if not json_files:
            self.log("LabelMe JSON 파일을 찾을 수 없습니다.", warning=True)
            return False

        # COCO 구조 초기화
        coco_out = os.path.join(self.labelPath, 'annotations', 'coco', 'dataset_coco.json')
        coco = {"images": [], "annotations": [], "categories": []}
        cat_map = {}
        cat_id = 1
        ann_id = 1  # 전체 COCO용 annotation ID

        for jf in json_files:
            label_count_map = {}
            jf_path = os.path.join(json_dir, jf)
            with open(jf_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 원본 이미지 경로 (origins 폴더로 복사해 두는 경우)
            abs_img = os.path.normpath(self.labelPath + data["imagePath"])
            
            pil_img = Image.open(abs_img).convert("RGBA")
            width, height = pil_img.size

            # COCO images 항목 추가
            img_id = len(coco["images"]) + 1
            coco["images"].append({
                "id": img_id,
                "file_name": data["imagePath"],
                "width": width,
                "height": height,
            })

            for shape in data.get("shapes", []):
                lbl = shape["label"]
                pts = shape["points"]

                # COCO category 처리
                if lbl not in cat_map:
                    cat_map[lbl] = cat_id
                    coco["categories"].append({"id": cat_id, "name": lbl})
                    cat_id += 1

                # bounding box 계산
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                xmin, xmax = int(min(xs)), int(max(xs))
                ymin, ymax = int(min(ys)), int(max(ys))

                # COCO annotation 추가
                coco["annotations"].append({
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": cat_map[lbl],
                    "bbox": [xmin, ymin, xmax - xmin, ymax - ymin],
                    "area": (xmax - xmin) * (ymax - ymin),
                    "segmentation": [sum(pts, [])],
                    "iscrowd": 0,
                })
                ann_id += 1

                # 마스크 생성 및 크롭
                mask = Image.new("L", (width, height), 0)
                draw = ImageDraw.Draw(mask)
                draw.polygon([(int(p[0]), int(p[1])) for p in pts], fill=255)

                region = pil_img.crop((xmin, ymin, xmax, ymax))
                mask_region = mask.crop((xmin, ymin, xmax, ymax))
                region.putalpha(mask_region)

                # 크롭 이미지 저장
                label_count_map[lbl] = label_count_map.get(lbl, 0) + 1
                idx = label_count_map[lbl]
                dst_dir = os.path.join(self.labelPath, 'images', lbl)
                os.makedirs(dst_dir, exist_ok=True)
                base = os.path.splitext(os.path.basename(abs_img))[0]
                crop_fname = f"{base}_{lbl}_{idx}.png"
                save_path = os.path.join(dst_dir, crop_fname)
                region.save(save_path)

            self.log(f"처리 완료: {jf_path}")

        # COCO JSON 저장
        with open(coco_out, 'w', encoding='utf-8') as f:
            json.dump(coco, f, indent=2)
        self.log(f"COCO 파일 생성 완료: {coco_out}")

        # ZIP 아카이브 생성
        self.create_archive()

        return True

    def create_archive(self):
        """
        images/, annotations/, origins/images 폴더를 묶어
        archive/ 안에 ZIP 파일로 저장하며,
        self.log() 로 진행 상황을 출력합니다.
        """
        archive_dir = os.path.join(self.labelPath, 'archive')
        os.makedirs(archive_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"dataset_{timestamp}.zip"
        zip_path = os.path.join(archive_dir, zip_name)

        # 압축할 파일 목록 수집
        folders = {
            'origins/images': os.path.join(self.labelPath, 'origins', 'images'),
            'images': os.path.join(self.labelPath, 'images'),
            'annotations': os.path.join(self.labelPath, 'annotations'),
        }
        entries = []
        for arc_root, real_root in folders.items():
            if not os.path.isdir(real_root):
                self.log(f"폴더가 없습니다, 스킵: {real_root}", warning=True)
                continue
            for root, _, files in os.walk(real_root):
                for fname in files:
                    entries.append((arc_root, real_root, root, fname))

        total = len(entries)
        if total == 0:
            self.log("압축할 파일이 없습니다.", warning=True)
            return

        self.log(f"아카이브 시작: 총 {total}개 파일을 압축합니다.")

        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for idx, (arc_root, real_root, root, fname) in enumerate(entries, start=1):
                abs_path = os.path.join(root, fname)
                rel_path = os.path.join(
                    arc_root,
                    os.path.relpath(abs_path, real_root)
                )
                zf.write(abs_path, rel_path)

                # 진행 상황 로그 (예: [ 10 / 123 ] 압축 중)
                self.log(f"[{idx:>4} / {total}] 압축 중")

        self.log(f"아카이브 생성 완료: {zip_path}")
