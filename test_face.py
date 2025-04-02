import ftplib
import os

# FTP 서버에 연결
ftp = ftplib.FTP()
ftp.connect('172.30.1.119', 3000)  # 서버 주소와 포트
ftp.login('sgbaek', 'sgbaek123')  # 로그인 정보

# 업로드할 파일 경로
file_path = r"C:\AI\source\9531457-uhd_2160_4096_25fps\Edit_Data_1.zip"
print("bsg 11111111111111\n")
# 파일을 바이너리 모드로 열기
with open(file_path, 'rb') as file:
    print("bsg 22222222222222222\n")
    # 파일 이름만 추출
    filename = os.path.basename(file_path)
    print("bsg 3333333333333\n")
    # 파일을 FTP 서버에 업로드

    ftp.set_pasv(False)
    ftp.storbinary(f"STOR {filename}", file)
    print("bsg 4444444444444444\n")

# FTP 연결 종료
ftp.quit()
