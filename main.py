import logging
import sys, logging, os
import PySide6.QtWidgets as QtWidgets
import datetime
import Soyoc_core.config_editer as Soyoc_config
import Soyoc_core.main_window as Soyoc_window

class LoggerManager:
    """日志管理器"""
    def __init__(self, log_dir="./logs", log_level=logging.INFO, log_format=None, datefmt=None, max_logs=5):
        self.log_dir = log_dir
        self.log_level = log_level
        self.log_format = log_format or '[%(asctime)s][%(levelname)-8s] %(module)s: %(message)s'
        self.datefmt = datefmt or '%Y-%m-%d %H:%M:%S'
        self.max_logs = max_logs  # 最大日志文件数量
        self.logger = self.setup_logger()

    def setup_logger(self):
        """设置日志记录器"""
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)

        # 清理旧日志文件
        self.cleanup_old_logs()

        # 配置日志文件路径
        log_file = f"{self.log_dir}/log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

        # 配置日志记录器
        logging.basicConfig(
            filename=log_file,
            level=self.log_level,
            format=self.log_format,
            datefmt=self.datefmt,
            encoding='utf-8'
        )
        logger = logging.getLogger()

        # 添加控制台处理器（可选）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(logging.Formatter(self.log_format))
        logger.addHandler(console_handler)

        return logger

    def cleanup_old_logs(self):
        """清理旧日志文件，保留最近的 max_logs 个日志文件"""
        try:
            # 获取日志目录中的所有日志文件
            log_files = [f for f in os.listdir(self.log_dir) if f.startswith("log_") and f.endswith(".log")]

            # 按时间排序（从旧到新）
            log_files.sort()

            # 如果日志文件数量超过最大限制，则删除最早的日志文件
            if len(log_files) > self.max_logs:
                files_to_delete = log_files[:len(log_files) - self.max_logs]
                for file_name in files_to_delete:
                    file_path = os.path.join(self.log_dir, file_name)
                    os.remove(file_path)
                    print(f"Deleted old log file: {file_path}")
        except Exception as e:
            print(f"Error cleaning up old logs: {e}")

    def get_logger(self):
        """获取日志记录器"""
        return self.logger

if __name__ == "__main__":
    # 初始化日志管理器
    logger_manager = LoggerManager()
    logger = logger_manager.get_logger()

    # 启动 PyQt 应用
    app = QtWidgets.QApplication(sys.argv)

    # 获取当前脚本的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 当前脚本所在目录构建配置文件的绝对路径
    config_file_path = os.path.join(current_dir, "config.toml")  # 使用绝对路径读取配置文件
    config_editer = Soyoc_config.ConfigEditor(config_file_path)

    # 实例化主窗口
    main_window = Soyoc_window.MainWindow(config_editer)
    main_window.show()

    sys.exit(app.exec())