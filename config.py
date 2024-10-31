import yaml

# 从config.yaml里面获取全局变量
class Config:
    def __init__(self):
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                # 从里面读取 timeout
                self.timeout = self.config['timeout']
        except FileNotFoundError:
            print("配置文件未找到")
            self.config = {}
            self.timeout = None
        except Exception as e:
            print(f"读取配置文件时出错: {e}")
            self.config = {}
            self.timeout = None
    
    def set_global_variable(self, key, value):
        try:
            self.config[key] = value
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f)
            print('设置全局变量成功')
        except Exception as e:
            print(f"写入配置文件时出错: {e}")


cfg=Config()