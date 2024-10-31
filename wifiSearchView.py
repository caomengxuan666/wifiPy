import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel,
    QHeaderView, QProgressBar, QLineEdit, QCheckBox,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor, QPen
from config import cfg  # 假设config.py文件中定义了cfg对象并有timeout属性

class CustomProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signal_strength = 0

    def set_signal_strength(self, signal_strength):
        self.signal_strength = signal_strength
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        # 绘制进度条
        progress_width = int(self.rect().width() * self.value() / 100)
        if self.signal_strength > -60:
            color = QColor(0, 255, 0)  # 绿色
        elif self.signal_strength > -70:
            color = QColor(255, 255, 0)  # 黄色
        else:
            color = QColor(255, 0, 0)  # 红色
        painter.fillRect(0, 0, progress_width, self.rect().height(), color)

        # 绘制信号强度文本
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.signal_strength} dBm")

class WifiScannerView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("WiFi Scanner")
        self.resize(600, 400)

        # 设置窗口为置顶
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # 布局设置
        main_layout = QVBoxLayout()

        # 标题标签
        self.title = QLabel("扫描到的WiFi列表")
        self.title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title)

        # 表格设置
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # 增加一列用于连接按钮
        self.table.setHorizontalHeaderLabels(["SSID", "信号强度", "密码", "操作", "BSSID"])

        # 设置表头自适应宽度
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        main_layout.addWidget(self.table)

        # 连接进度条和刷新按钮的水平布局
        progress_refresh_layout = QHBoxLayout()

        # 连接进度条
        self.connect_progress_bar = CustomProgressBar(self)
        self.connect_progress_bar.setValue(0)
        progress_refresh_layout.addWidget(self.connect_progress_bar)

        # 刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_wifi_list)
        self.refresh_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 10px; border-radius: 5px;")
        progress_refresh_layout.addWidget(self.refresh_button)

        main_layout.addLayout(progress_refresh_layout)

        self.setLayout(main_layout)

        # 初始化计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_connect_progress)

        # 保存密码的字典
        self.passwords = {}
        self.password_inputs = {}
        self.password_visibility = {}

        # 加载已保存的数据
        self.load_saved_data()

    def display_wifi_list(self, wifi_list):
        """显示扫描到的WiFi列表"""
        self.table.setRowCount(len(wifi_list))  # 确保表格行数与WiFi列表长度一致

        for row, wifi in enumerate(wifi_list):
            ssid = wifi["ssid"] or "未知或隐藏的网络"
            self.table.setItem(row, 0, QTableWidgetItem(ssid))

            # 信号强度进度条
            progress_bar = CustomProgressBar(self)
            progress_bar.setValue(self.normalize_signal_strength(wifi["signal"]))
            progress_bar.set_signal_strength(wifi["signal"])
            self.set_progress_bar_color(progress_bar, wifi["signal"])
            self.table.setCellWidget(row, 1, progress_bar)

            # 密码输入框
            password_input = QLineEdit()
            password_input.setPlaceholderText("输入WiFi密码")
            password_input.setEchoMode(QLineEdit.Password)
            password_input.setFont(QFont("Arial", 12))  # 增大字体
            password_input.textChanged.connect(lambda text, s=ssid: self.save_password(s, text))

            show_hide_checkbox = QCheckBox("显示密码")
            show_hide_checkbox.stateChanged.connect(lambda state, p=password_input, s=ssid: self.toggle_password_visibility(p, state, s))

            # 布局密码输入框和显示复选框
            password_layout = QHBoxLayout()
            password_layout.addWidget(password_input)
            password_layout.addWidget(show_hide_checkbox)
            password_widget = QWidget()
            password_widget.setLayout(password_layout)
            self.table.setCellWidget(row, 2, password_widget)

            self.password_inputs[ssid] = password_input

            # 恢复已保存密码
            if ssid in self.passwords:
                password_input.setText(self.passwords[ssid])

            # 恢复密码显示状态
            if ssid in self.password_visibility and self.password_visibility[ssid]:
                show_hide_checkbox.setChecked(True)
                password_input.setEchoMode(QLineEdit.Normal)

            # 连接按钮
            connect_button = QPushButton("连接")
            connect_button.clicked.connect(lambda _, s=ssid, r=row: self.on_connect_button_click(s, r))
            self.table.setCellWidget(row, 3, connect_button)

            self.table.setItem(row, 4, QTableWidgetItem(wifi["bssid"]))

    def save_password(self, ssid, password):
        self.passwords[ssid] = password
        self.save_data_to_file()

    def toggle_password_visibility(self, password_input, state, ssid):
        """切换密码显示和隐藏"""
        if state == Qt.Checked:
            password_input.setEchoMode(QLineEdit.Normal)
            self.password_visibility[ssid] = True  # 记录密码为可见状态
        else:
            password_input.setEchoMode(QLineEdit.Password)
            self.password_visibility[ssid] = False  # 记录密码为不可见状态
        self.save_data_to_file()

    def on_connect_button_click(self, ssid, row):
        """处理连接按钮点击事件"""
        password = self.passwords.get(ssid, "")
        self.start_connect_progress(ssid, password)

    def start_connect_progress(self, ssid, password):
        """开始连接进度条"""
        self.connect_progress_bar.setValue(0)
        self.progress_step = 100 / (cfg.timeout * 10)
        self.timer.start(100)

        # 调用控制器连接WiFi
        self.controller.connect_to_wifi(ssid, password)

    def update_connect_progress(self):
        """每次计时器触发，更新连接进度条"""
        current_value = self.connect_progress_bar.value()
        if current_value < 100:
            self.connect_progress_bar.setValue(int(current_value + self.progress_step))  # 将结果转换为整数
        else:
            self.timer.stop()  # 完成后停止计时器

    def set_progress_bar_color(self, progress_bar, signal):
        if signal > -60:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
        elif signal > -70:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: yellow; }")
        else:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")

    def normalize_signal_strength(self, signal_strength):
        """将信号强度映射到 0 到 100 的范围"""
        if signal_strength <= -100:
            return 0
        elif signal_strength >= 0:
            return 100
        else:
            return (signal_strength + 100)

    def refresh_wifi_list(self):
        """刷新WiFi列表并保存密码"""
        # 遍历表格，保存当前输入的密码和显示状态
        for row in range(self.table.rowCount()):
            ssid_item = self.table.item(row, 0)
            if ssid_item:
                ssid = ssid_item.text()
                password_input = self.table.cellWidget(row, 2).layout().itemAt(0).widget()
                password = password_input.text()
                self.save_password(ssid, password)  # 保存密码

                show_hide_checkbox = self.table.cellWidget(row, 2).layout().itemAt(1).widget()
                self.password_visibility[ssid] = show_hide_checkbox.isChecked()  # 保存显示状态

        # 调用控制器的扫描方法
        self.controller.start_wifi_scan()

    def reset_connect_progress(self):
        """重置连接进度条"""
        self.connect_progress_bar.setValue(0)
        self.timer.stop()

    def save_data_to_file(self):
        """保存数据到文件"""
        data = {
            "passwords": self.passwords,
            "password_visibility": self.password_visibility
        }
        with open("saved_data.json", "w") as f:
            json.dump(data, f)

    def load_saved_data(self):
        """加载已保存的数据"""
        try:
            with open("saved_data.json", "r") as f:
                data = json.load(f)
                self.passwords = data.get("passwords", {})
                self.password_visibility = data.get("password_visibility", {})
        except FileNotFoundError:
            pass
