import pywifi
from pywifi import const, Profile
import time
from config import cfg
import socket

class WifiSearchModel:
    def __init__(self):
        self.wifi = pywifi.PyWiFi()
        self.iface = self.wifi.interfaces()[0]  # 获取第一个无线网卡

    def scan_wifi(self):
        self.iface.scan()
        time.sleep(2)  # 等待扫描完成
        scan_results = self.iface.scan_results()
        wifi_dict = {}

        for network in scan_results:
            ssid = network.ssid.encode('raw_unicode_escape').decode('utf-8', 'ignore') or "未知或隐藏的网络"  # 处理空SSID情况
            signal = network.signal
            bssid = network.bssid

            # 如果SSID已存在，则比较信号强度
            if ssid in wifi_dict:
                # 如果当前信号强度更强，则更新字典
                if signal > wifi_dict[ssid]["signal"]:
                    wifi_dict[ssid] = {
                        "signal": signal,
                        "bssid": bssid
                    }
            else:
                # 如果SSID不存在，则添加到字典
                wifi_dict[ssid] = {
                    "signal": signal,
                    "bssid": bssid
                }

        # 将字典转换为列表并按信号强度排序
        wifi_list = [{"ssid": ssid, "signal": info["signal"], "bssid": info["bssid"]} for ssid, info in wifi_dict.items()]
        return sorted(wifi_list, key=lambda x: x['signal'], reverse=True)  # 信号强度排序

    def connect_to_wifi(self, ssid, password=None):
        profile = Profile()
        profile.ssid = ssid

        if password:
            profile.auth = const.AUTH_ALG_OPEN
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
            profile.cipher = const.CIPHER_TYPE_CCMP
            profile.key = password
        else:
            profile.auth = const.AUTH_ALG_OPEN
            profile.akm.append(const.AKM_TYPE_NONE)
            profile.cipher = const.CIPHER_TYPE_NONE

        profile.disabled = False
        self.iface.disconnect()
        time.sleep(1)
        self.iface.remove_all_network_profiles()
        self.iface.add_network_profile(profile)

        # 连接到Wi-Fi并开始计时
        self.iface.connect(self.iface.add_network_profile(profile))

        for _ in range(cfg.timeout):  # cfg.timeout 为超时设定
            time.sleep(1)
            if self.iface.status() == const.IFACE_CONNECTED:
                return True  # 连接成功

        # 超时处理
        return False  # 连接超时，返回 False


    def get_ip_address(self):
        # 获取连接的IP地址
        try:
            # 获取主机名
            hostname = socket.gethostname()
            # 获取主机IP地址
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except Exception as e:
            print(f"Error getting IP address: {e}")
            return None
