from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QApplication
import sys

class LogDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("실시간 로그")
        self.setGeometry(100, 100, 600, 400)
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)  # 로그 출력용으로만 사용
        
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
    
    def append_log(self, message):
        self.text_edit.setText(message)  # 로그 추가 (스크롤 유지)
