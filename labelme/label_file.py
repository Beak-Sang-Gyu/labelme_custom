import base64
import contextlib
import io
import json
import csv
import os
import os.path as osp
import cv2
import numpy as np

import PIL.Image
from loguru import logger

from labelme import __version__
from labelme import utils
import zipfile

PIL.Image.MAX_IMAGE_PIXELS = None


@contextlib.contextmanager
def open(name, mode):
    assert mode in ["r", "w"]
    encoding = "utf-8"
    yield io.open(name, mode, encoding=encoding)
    return

#2025 03 20 bsg crop image polygon and background black jpg
import os
import cv2
import numpy as np

def display_cropped_image(image_path, points, index, shape, shape_type="polygon"):
    directory = os.path.dirname(image_path)
    file_name = os.path.basename(image_path)
    directory_path = os.path.join(directory, f"crop_{file_name[:-4]}")
    directory_label_path = os.path.join(directory_path, shape)
    save_path = os.path.join(directory_label_path, f"crop_{index}_{file_name}")

    # 디렉토리 생성
    os.makedirs(directory_label_path, exist_ok=True)

    # 이미지 로드
    image = cv2.imread(image_path)
    if image is None:
        print("no image file", image_path)
        return

    # 다각형 좌표를 numpy 배열로 변환
    points = np.array(points, dtype=np.int32)

    # 바운딩 박스 좌표 계산
    x_min, y_min = np.min(points, axis=0)
    x_max, y_max = np.max(points, axis=0)

    if shape_type == "rectangle":
        # 기존 바운딩 박스 방식
        cropped_image = image[y_min:y_max, x_min:x_max]
    elif shape_type == "polygon":
        # 다각형 마스킹 방식
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [points], 255)
        masked_image = cv2.bitwise_and(image, image, mask=mask)
        cropped_image = masked_image[y_min:y_max, x_min:x_max]
    else:
        print("Invalid shape_type! Use 'bbox' or 'polygon'.")
        return

    # 결과 저장
    cv2.imwrite(save_path, cropped_image)
    print(f"crop image saved in {save_path}")

#2025 03 20 bsg crop image polygon and background black jpg end

#2025 03 20 bsg crop image polygon and background X png

# def display_cropped_image(image_path, points, index, shape, shape_type="polygon"):
#     directory = os.path.dirname(image_path)
#     file_name = os.path.basename(image_path)
#     directory_path = os.path.join(directory, f"crop_{file_name[:-4]}")
#     directory_label_path = os.path.join(directory_path, shape)
#     save_path = os.path.join(directory_label_path, f"crop_{index}_{file_name[:-4]}.png")  # PNG 저장

#     os.makedirs(directory_label_path, exist_ok=True)

#     image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
#     if image is None:
#         print("no image file", image_path)
#         return

#     points = np.array(points, dtype=np.int32)

#     # 다각형이 포함된 최소한의 사각형 계산
#     x_min, y_min = np.min(points, axis=0)
#     x_max, y_max = np.max(points, axis=0)

#     if shape_type == "rectangle":
#         cropped_image = image[y_min:y_max, x_min:x_max]
#     elif shape_type == "polygon":
#         # RGBA 변환 (투명도 추가)
#         if image.shape[2] == 3:
#             image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

#         mask = np.zeros(image.shape[:2], dtype=np.uint8)
#         cv2.fillPoly(mask, [points], 255)

#         # 알파 채널에 마스크 적용 (투명 배경 만들기)
#         image[:, :, 3] = mask
#         cropped_image = image[y_min:y_max, x_min:x_max]
#     else:
#         print("Invalid shape_type! Use 'rectangle' or 'polygon'.")
#         return

#     cv2.imwrite(save_path, cropped_image)
#     print(f"Transparent crop saved in {save_path}")

#2025 03 20 bsg crop image polygon and background X png end

class LabelFileError(Exception):
    pass


class LabelFile(object):
    suffix = ".json"

    def __init__(self, filename=None):
        self.shapes = []
        self.imagePath = None
        self.imageData = None
        if filename.endswith(".csv"):
            LabelFile.suffix=".csv"
        if filename is not None:
            self.load(filename)
        self.filename = filename

    @staticmethod
    def load_image_file(filename):
        try:
            image_pil = PIL.Image.open(filename)
        except IOError:
            logger.error("Failed opening image file: {}".format(filename))
            return

        # apply orientation to image according to exif
        image_pil = utils.apply_exif_orientation(image_pil)

        with io.BytesIO() as f:
            ext = osp.splitext(filename)[1].lower()
            if ext in [".jpg", ".jpeg"]:
                format = "JPEG"
            else:
                format = "PNG"
            image_pil.save(f, format=format)
            f.seek(0)
            return f.read()

    def load(self, filename):
        keys = [
            "version",
            "imageData",
            "imagePath",
            "shapes",  # polygonal annotations
            "flags",  # image level flags
            "imageHeight",
            "imageWidth",
        ]
        shape_keys = [
            "label",
            "points",
            "group_id",
            "shape_type",
            "flags",
            "description",
            "mask",
        ]

        if not os.path.exists(filename):
            return
        #2025 03 14 load seperate .json and .csv
        if LabelFile.suffix==".json":
            try:
                with open(filename, "r") as f:
                    data = json.load(f)

                if data["imageData"] is not None:
                    imageData = base64.b64decode(data["imageData"])
                else:
                    # relative path from label file to relative path from cwd
                    imagePath = osp.join(osp.dirname(filename), data["imagePath"])
                    imageData = self.load_image_file(imagePath)
                flags = data.get("flags") or {}
                imagePath = data["imagePath"]
                self._check_image_height_and_width(
                    base64.b64encode(imageData).decode("utf-8"),
                    data.get("imageHeight"),
                    data.get("imageWidth"),
                )
                shapes = [
                    dict(
                        label=s["label"],
                        points=s["points"],
                        shape_type=s.get("shape_type", "polygon"),
                        flags=s.get("flags", {}),
                        description=s.get("description"),
                        group_id=s.get("group_id"),
                        mask=utils.img_b64_to_arr(s["mask"]).astype(bool)
                        if s.get("mask")
                        else None,
                        other_data={k: v for k, v in s.items() if k not in shape_keys},
                    )
                    for s in data["shapes"]
                ]
            except Exception as e:
                raise LabelFileError(e)

            otherData = {}
            for key, value in data.items():
                if key not in keys:
                    otherData[key] = value

            # Only replace data after everything is loaded.
            self.flags = flags
            self.shapes = shapes
            self.imagePath = imagePath
            self.imageData = imageData
            self.filename = filename
            self.otherData = otherData
            # logger.warning(f"bsg json ###################################################\n")
            # logger.warning(f"bsg ------------------- self.flags | {self.flags}")
            # logger.warning(f"bsg ------------------- self.shapes | {self.shapes}")
            # logger.warning(f"bsg ------------------- self.imagePath | {self.imagePath}")
            # logger.warning(f"bsg ------------------- self.imageData | {self.imageData}")
            # logger.warning(f"bsg ------------------- self.filename | {self.filename}")
            # logger.warning(f"bsg ------------------- self.otherData | {self.otherData}")
            # logger.warning(f"bsg ###################################################\n")
        elif LabelFile.suffix==".csv":
            try:
                with open(filename, "r") as f:
                    reader = csv.DictReader(f)
                    
                    shapes = []
                    flags = {}
                    description = ""
                    imagePath = None
                    imageHeight = None
                    imageWidth = None
                    imageData = None

                    for row in reader:
                        points = json.loads(row["points"]) if row["points"] else []

                        flags = json.loads(row["flags"]) if row["flags"] else {}

                        description = json.loads(row["description"]) if row["description"] else ""

                        mask = json.loads(row["mask"]) if row["mask"] else None
                        
                        shape = {
                            "label": row["label"],
                            "points": points,
                            "shape_type": row["shape_type"],
                            "description": description,
                            "flags": flags,
                            "group_id": int(row["group_id"]) if row["group_id"] else None,
                            "mask": mask,
                        }
                        shapes.append(shape)

                        if not imagePath:
                            imagePath = row["imagePath"]
                        # if not imageHeight:
                        #     imageHeight = int(row["imageHeight"]) if row["imageHeight"] else None
                        # if not imageWidth:
                        #     imageWidth = int(row["imageWidth"]) if row["imageWidth"] else None
                        # if not imageData and row["imageData"]:
                        #     imageData = base64.b64decode(row["imageData"])
                        # else : 
                        imagePath = osp.join(osp.dirname(filename), imagePath)
                        imageData = self.load_image_file(imagePath)

            except Exception as e:
                raise LabelFileError(e)

            self.flags = flags
            self.shapes = shapes
            self.imagePath = imagePath
            self.imageData = imageData
            # self.imageHeight = imageHeight
            # self.imageWidth = imageWidth
            self.imageHeight = None
            self.imageWidth = None
            self.filename = filename
            self.otherData = {}
            # logger.warning(f"bsg csv ###################################################\n")
            # logger.warning(f"bsg ------------------- self.flags | {self.flags}")
            # logger.warning(f"bsg ------------------- self.shapes | {self.shapes}")
            # logger.warning(f"bsg ------------------- self.imagePath | {self.imagePath}")
            # logger.warning(f"bsg ------------------- self.imageData | {self.imageData}")
            # logger.warning(f"bsg ------------------- self.imageHeight | {self.imageHeight}")
            # logger.warning(f"bsg ------------------- self.imageWidth | {self.imageWidth}")
            # logger.warning(f"bsg ------------------- self.filename | {self.filename}")
            # logger.warning(f"bsg ------------------- self.otherData | {self.otherData}")
            # logger.warning(f"bsg ###################################################\n")        
        #2025 03 14 load seperate .json and .csv end 

    @staticmethod
    def _check_image_height_and_width(imageData, imageHeight, imageWidth):
        img_arr = utils.img_b64_to_arr(imageData)
        if imageHeight is not None and img_arr.shape[0] != imageHeight:
            logger.error(
                "imageHeight does not match with imageData or imagePath, "
                "so getting imageHeight from actual image."
            )
            imageHeight = img_arr.shape[0]
        if imageWidth is not None and img_arr.shape[1] != imageWidth:
            logger.error(
                "imageWidth does not match with imageData or imagePath, "
                "so getting imageWidth from actual image."
            )
            imageWidth = img_arr.shape[1]
        return imageHeight, imageWidth

    def save(
        self,
        filename,
        shapes,
        imagePath,
        imageHeight,
        imageWidth,
        imageData=None,
        otherData=None,
        flags=None,
    ):

        logger.warning(f"bsg  save save save save save save save save\n") 
        if imageData is not None:
            imageData = base64.b64encode(imageData).decode("utf-8")
            imageHeight, imageWidth = self._check_image_height_and_width(
                imageData, imageHeight, imageWidth
            )
        if otherData is None:
            otherData = {}
        if flags is None:
            flags = {}
        data = dict(
            version=__version__,
            flags=flags,
            shapes=shapes,
            imagePath=imagePath,
            imageData=imageData,
            imageHeight=imageHeight,
            imageWidth=imageWidth,
        )
        #2025 03 13 seperate .json and .csv
        if filename.endswith(".json"):
            for key, value in otherData.items():
                assert key not in data
                data[key] = value
            try:
                with open(filename, "w") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.filename = filename
            except Exception as e:
                raise LabelFileError(e)

        elif filename.endswith(".csv"):
            self.save_csv(filename,data)
        #2025 03 13 seperate .json and .csv end

    @staticmethod
    # def is_label_file(filename):
    #     return osp.splitext(filename)[1].lower() == LabelFile.suffix

    #2025 03 13 csv type recognize
    def is_label_file(filename):
        ext = osp.splitext(filename)[1].lower() 
        if ext == ".json" or ext == ".csv":  
            LabelFile.suffix=ext
            return True
        else:
            return False
    #2025 03 13 csv type recognize end

    #2025 03 13 save csv file
    def save_csv(self, filename, json_data):
        data = {
            "version": json_data.get('version', 'unknown'),
            "flags": json_data.get('flags', {}),
            "shapes": json_data.get('shapes', []),
            "imagePath": json_data.get('imagePath', ''),
        }
            # "imageHeight": json_data.get('imageHeight', 0),
            # "imageWidth": json_data.get('imageWidth', 0),
            # "imageData" : json_data.get('imageData',''),

        try:
            with open(filename, mode="w") as file:
                writer = csv.writer(file)

                writer.writerow(["label", "points", "group_id","description", "shape_type", "flags", "mask","imagePath"])#, "imageHeight", "imageWidth","imageData"])

                for index, shape in enumerate(data["shapes"]):
                    points = shape.get("points", [])
                    flags = shape.get("flags", {})
                    
                    writer.writerow([
                        shape["label"],
                        json.dumps(points),
                        shape["group_id"],
                        shape["description"],
                        shape["shape_type"],
                        json.dumps(flags),
                        shape["mask"],
                        data["imagePath"],
                    ])
                        # data["imageHeight"],
                        # data["imageWidth"],
                        # data["imageData"],
                    #2025 03 18 bsg rectangle crop
                    # if shape["shape_type"] == "rectangle":
                    file_name = filename[:-4]+".jpg"
                    display_cropped_image(file_name,points,index,shape["label"],shape["shape_type"])
                    #2025 03 18 bsg rectangle crop end
            directory = os.path.dirname(file_name)
            file__name = os.path.basename(file_name)
            directory_path = directory+"/crop_"+file__name[:-4]+"/"
            if os.path.exists(directory_path):
                zip_dir(directory_path[:-1],directory_path)
                
            logger.warning(f"CSV file save : {filename}")
        except Exception as e:
            logger.error(f"CSV file save error : {e}")
    #2025 03 13 bsg save csv file end

def zip_dir(zip_name, dir_path):
    zip_path = os.path.join(os.path.abspath(os.path.join(dir_path, os.pardir)), zip_name + '.zip')
    new_zips = zipfile.ZipFile(zip_path, 'w')
    dir_path = dir_path + '/'

    for root, directory, files in os.walk(dir_path):
        for file in files:
            path = os.path.join(root, file)
            new_zips.write(path, arcname=os.path.relpath(os.path.join(root, file), dir_path), compress_type=zipfile.ZIP_DEFLATED)

    new_zips.close()
    

