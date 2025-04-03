from PyQt5.QtWidgets import QDialog, QPlainTextEdit, QVBoxLayout, QApplication
import sys

class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("로그 창")
        self.setGeometry(300, 300, 600, 300)
        
        self.log_view = QPlainTextEdit(self)
        self.log_view.setReadOnly(True)  # 편집 불가능한 로그 창
        
        layout = QVBoxLayout()
        layout.addWidget(self.log_view)
        self.setLayout(layout)

    def append_log(self, message):
        """ 로그를 추가하고 창을 갱신 """
        self.log_view.appendPlainText(message)  # 기존 메시지 유지하면서 추가
        self.show()  # 창이 보이도록 설정
        QApplication.processEvents()  # UI가 멈추지 않도록 갱신
