import os
import ftplib
from loguru import logger
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from labelme.DataSetExporter import DatasetExporter  # FTP 모듈 import

class ExportDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("FTP 파일 전송")
        self.setGeometry(100, 100, 400, 250)
        self.main_window = main_window
        layout = QVBoxLayout()

        self.server_input = QLineEdit(self)
        self.server_input.setText("172.30.1.119")
        layout.addWidget(QLabel("FTP 서버 주소:"))
        layout.addWidget(self.server_input)

        self.port_input = QLineEdit(self)
        self.port_input.setText("3000")
        layout.addWidget(QLabel("포트 번호:"))
        layout.addWidget(self.port_input)

        self.username_input = QLineEdit(self)
        self.username_input.setText("dataset")
        layout.addWidget(QLabel("사용자 이름:"))
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setText("Gnapse1001!")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("비밀번호:"))
        layout.addWidget(self.password_input)

        self.filename_input = QLineEdit(self)
        self.filename_input.setText("test_Data")
        layout.addWidget(QLabel("파일 이름:"))
        layout.addWidget(self.filename_input)

        self.ok_button = QPushButton("업로드")
        self.ok_button.clicked.connect(self.upload_file)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def upload_file(self):
        logger.info("파일 업로드 시작")

        edit_filename = self.filename_input.text().strip()

        ftp_config = {
            "server": self.server_input.text().strip(),
            "port": self.port_input.text().strip(),
            "username": self.username_input.text().strip(),
            "password": self.password_input.text().strip()
        }

        if not all(ftp_config.values()):
            QMessageBox.warning(self, "오류", "모든 필드를 입력하세요.")
            return

        try:
            with ftplib.FTP() as ftp:
                ftp.connect(ftp_config["server"], int(ftp_config["port"]))
                ftp.login(ftp_config["username"], ftp_config["password"])
                ftp.set_pasv(False)
                logger.info("FTP 연결 성공")

                remote_base_path = "/home2/dataset/data"
                dataset_exporter = DatasetExporter(ftp, remote_base_path)

                for folder in ["images", "annotations", "archive", "origin"]:
                    dataset_exporter.create_remote_directory(folder)

                local_dataset_path = self.main_window.exportFile(edit_filename)

                dataset_exporter.upload_to_ftp(local_dataset_path, edit_filename)

                QMessageBox.information(self, "성공", f"파일 '{edit_filename}' 업로드 완료!")

        except Exception as e:
            logger.error(f"FTP 연결 실패: {e}")
            QMessageBox.critical(self, "FTP 오류", f"FTP 연결 실패: {e}")
