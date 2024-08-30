import os


class DynamicConfig:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        """
        动态加载配置文件，将变量存储到 config 属性中。
        """
        config = {}
        try:
            # 尝试加载用户配置文件
            module_path = 'user_config.py'
            if os.path.exists(module_path):
                with open(module_path, 'r') as file:
                    exec(file.read(), config)
            else:
                # 加载默认配置文件
                with open('config.py', 'r') as file:
                    exec(file.read(), config)
        except Exception as e:
            raise ImportError(f"Could not load configuration file: {e}")

        # 过滤掉内置变量（如 __builtins__）
        self.config = {k: v for k, v in config.items() if not k.startswith('__')}

    def __getattr__(self, name):
        """
        当使用 config.ftp_port 这样的方式访问变量时，调用此方法。
        """
        return self.config.get(name, None)

    def __getitem__(self, name):
        """
        当使用 getattr(config, "ftp_port", None) 这样的方式访问变量时，调用此方法。
        """
        return self.config.get(name, None)

    def reload(self):
        """
        当配置文件更改时，调用此方法重新加载配置。
        """
        self.load_config()

