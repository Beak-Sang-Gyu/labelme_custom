import ftplib
import os
from loguru import logger
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QComboBox
)

class ExportDialog(QDialog):  # 클래스 이름 변경
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("FTP 파일 전송")
        self.setGeometry(100, 100, 400, 300)
        self.main_window = main_window
        layout = QVBoxLayout()

        # 서버 주소 입력
        self.server_input = QLineEdit(self)
        self.server_input.setText("172.30.1.119")
        layout.addWidget(QLabel("FTP 서버 주소:"))
        layout.addWidget(self.server_input)

        # 포트 번호 입력
        self.port_input = QLineEdit(self)
        self.port_input.setText("3000")
        layout.addWidget(QLabel("포트 번호:"))
        layout.addWidget(self.port_input)

        # 사용자 이름 입력
        self.username_input = QLineEdit(self)
        self.username_input.setText("sgbaek")
        layout.addWidget(QLabel("사용자 이름:"))
        layout.addWidget(self.username_input)

        # 비밀번호 입력
        self.password_input = QLineEdit(self)
        self.password_input.setText("sgbaek123")
        self.password_input.setEchoMode(QLineEdit.Password)  # 비밀번호 숨김 처리
        layout.addWidget(QLabel("비밀번호:"))
        layout.addWidget(self.password_input)
        
        self.filename_input = QLineEdit(self)
        self.filename_input.setText("test_Data")
        layout.addWidget(QLabel("파일 이름:"))
        layout.addWidget(self.filename_input)

        self.combo_box = QComboBox(self)
        self.combo_box.addItems([".zip", "coco", "옵션 3"])  # 리스트 추가
        layout.addWidget(self.combo_box)

        # 확인 버튼 (FTP 전송 실행)
        self.ok_button = QPushButton("업로드")
        self.ok_button.clicked.connect(self.upload_file)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def upload_file(self):
        selected_value = self.combo_box.currentText()
        Edit_filename = self.filename_input.text().strip()
        if self.main_window and selected_value==".zip":
            self.file_path=self.main_window.exportFile(Edit_filename)
            # self.file_path=self.main_window.exportFile()
            self.file_path=self.file_path+'.zip'
        if not selected_value==".zip":
            QMessageBox.warning(self, "오류", "아직 지원하지 않습니다.")
            return
        if not self.file_path:
            QMessageBox.warning(self, "오류", "파일을 선택하세요.")
            return

        server = self.server_input.text().strip()
        port = self.port_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not (server and port and username and password):
            QMessageBox.warning(self, "오류", "모든 필드를 입력하세요.")
            return

        try:
            port = int(port)
            with ftplib.FTP() as ftp:
                ftp.connect(server, port)
                ftp.login(username, password)
                with open(self.file_path, "rb") as file:
                    filename = os.path.basename(self.file_path)
                    ftp.set_pasv(False)
                    ftp.storbinary(f"STOR {filename}", file)

                QMessageBox.information(self, "성공", f"파일 '{filename}' 업로드 완료!")
        except Exception as e:
            QMessageBox.critical(self, "FTP 오류", f"오류 발생: {e}")
