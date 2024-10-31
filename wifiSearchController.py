from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox,QLabel
import time
from wifiSearchModel import WifiSearchModel
from wifiSearchView import WifiScannerView
from connectWorker import ConnectWorker

class WifiScannerController:
    def __init__(self):
        self.model = WifiSearchModel()
        self.view = WifiScannerView(self)

        # 创建WiFi扫描线程
        self.worker = WifiScannerWorker(self.model)
        self.worker.wifi_scanned.connect(self.view.display_wifi_list)  # 连接信号与视图显示方法

        # 创建定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.start_wifi_scan)
        self.timer.start(3000)  # 每3秒刷新一次

        self.connect_worker = None  # 当前的连接线程

        # 创建IP地址标签
        self.ip_label = QLabel("未连接到任何WiFi")
        self.view.layout().addWidget(self.ip_label)

    def start_wifi_scan(self):
        if not self.worker.isRunning():  # 检查线程是否已经在运行
            self.worker.start()  # 启动线程

    def connect_to_wifi(self, ssid, password):
        # 如果已有连接线程运行，先终止
        if self.connect_worker and self.connect_worker.isRunning():
            self.connect_worker.terminate()

        # 创建新的连接线程
        self.connect_worker = ConnectWorker(self.model, ssid, password)
        self.connect_worker.progress_updated.connect(self.view.update_connect_progress)
        self.connect_worker.connect_done.connect(self.handle_connection_result)
        self.connect_worker.start()

    def handle_connection_result(self, success, ssid):
        self.view.reset_connect_progress()  # 重置进度条
        if success:
            ip_address = self.model.get_ip_address()
            if ip_address:
                self.ip_label.setText(f"已连接到 {ssid}，IP地址: {ip_address}")
            else:
                self.ip_label.setText("无法获取IP地址")
            QMessageBox.information(self.view, "成功", f"成功连接到 {ssid}")
        else:
            self.ip_label.setText("未连接到任何WiFi")
            QMessageBox.warning(self.view, "失败", f"无法连接到 {ssid}")

class WifiScannerWorker(QThread):
    wifi_scanned = pyqtSignal(list)  # 信号，传递扫描结果

    def __init__(self, model):
        super().__init__()
        self.model = model

    def run(self):
        wifi_list = self.model.scan_wifi()  # 执行扫描操作
        self.wifi_scanned.emit(wifi_list)  # 发出信号，传递扫描结果
