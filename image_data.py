import os
import zipfile

# 1. 임의의 테스트 디렉토리 만들기
test_dir = "test_directory"
os.makedirs(test_dir, exist_ok=True)  # 디렉토리가 없으면 생성

# 2. 디렉토리 안에 파일 생성하기
file_path = os.path.join(test_dir, "test_file.txt")
with open(file_path, 'w') as file:
    file.write("This is a test file inside the test directory.")

print(f"파일이 {file_path}에 생성되었습니다.")

# 3. 디렉토리 압축하기
zip_filename = "test_directory.zip"

# zip 파일 생성
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # 디렉토리 내 모든 파일을 압축
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            # 파일 경로 생성
            file_path = os.path.join(root, file)
            # 파일을 zip에 추가
            zipf.write(file_path, os.path.relpath(file_path, test_dir))

print(f"디렉토리가 {zip_filename}로 압축되었습니다.")
os.system('dir')
