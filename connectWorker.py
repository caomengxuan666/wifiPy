import time
from PyQt5.QtCore import QThread, pyqtSignal

class ConnectWorker(QThread):
    progress_updated = pyqtSignal(int)
    connect_done = pyqtSignal(bool, str)

    def __init__(self, model, ssid, password):
        super().__init__()
        self.model = model
        self.ssid = ssid
        self.password = password

    def run(self):
        max_attempts = 100
        connection_established = False

        for attempt in range(1, max_attempts + 1):
            # 假设每次尝试连接增加 1% 进度
            self.progress_updated.emit(attempt)
            time.sleep(0.02)  # 模拟连接过程的延时

            # 尝试连接
            if self.model.connect_to_wifi(self.ssid, self.password):
                connection_established = True
                self.progress_updated.emit(100)  # 直接设置为完成
                break
            else:
                # 如果连接失败，立即发出失败信号
                self.connect_done.emit(False, self.ssid)
                return

        # 如果未连接成功，发出失败信号；否则发出成功信号
        self.connect_done.emit(connection_established, self.ssid)
