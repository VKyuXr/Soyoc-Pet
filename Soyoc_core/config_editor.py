import PySide6.QtWidgets as QtWidgets
import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui
import toml, os, json, logging
import Soyoc_core.live2d_manager as Soyoc_l2d_manager

class MotionLoader:
    def __init__(self, folder_path: str):
        """
        初始化 MotionLoader，读取指定文件夹下的 .model3.json 文件并解析 Motions 部分。
        
        :param folder_path: 包含 .model3.json 文件的文件夹路径
        """
        self.folder_path = folder_path
        self.motions = {}

        # 检查文件夹是否存在
        if not os.path.isdir(folder_path):
            raise ValueError(f"文件夹路径无效: {folder_path}")

        # 查找 .model3.json 文件
        model3_file = None
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".model3.json"):
                model3_file = file_name
                break

        if not model3_file:
            raise FileNotFoundError(f"未找到 .model3.json 文件: {folder_path}")

        # 读取并解析 .model3.json 文件
        model3_path = os.path.join(folder_path, model3_file)
        with open(model3_path, "r", encoding="utf-8") as f:
            model_data = json.load(f)

        # 提取 Motions 部分
        motions_data = model_data.get("FileReferences", {}).get("Motions", {})
        self.motions = self.parse_motions(motions_data)

    def parse_motions(self, motions_data: dict) -> dict:
        """
        解析 Motions 数据，提取动作文件名（不包含路径和扩展名）。
        
        :param motions_data: Motions 部分的字典数据
        :return: 动作文件名的字典
        """
        parsed_motions = {}
        for motion_type, motion_list in motions_data.items():
            parsed_motions[motion_type] = [
                self.extract_motion_name(motion["File"]) for motion in motion_list
            ]
        return parsed_motions

    def extract_motion_name(self, file_path: str) -> str:
        """
        提取 motion/ 后面和 .motion3.json 前面的部分。
        
        :param file_path: 动作文件的完整路径
        :return: 动作文件名
        """
        # 假设路径格式为 "motion/<name>.motion3.json"
        if file_path.startswith("motion/") and file_path.endswith(".motion3.json"):
            return file_path[len("motion/"):-len(".motion3.json")]
        else:
            raise ValueError(f"无效的文件路径格式: {file_path}")

    def get_motions(self) -> dict:
        """
        获取解析后的 Motions 数据。
        
        :return: 动作文件名的字典，格式为：
                {
                    "动作名字": {"group": "组名", "index": 索引},
                    ...
                }
        """
        result = {}
        # 遍历 self.motions 字典，构造目标格式
        for group, motions in self.motions.items():
            for index, motion in enumerate(motions):
                result[motion] = {
                    "group": group,
                    "index": index
                }
        return result

class TitleBar(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent_window: ConfigEditor = parent
        bar_layout = QtWidgets.QHBoxLayout()
        bar_layout.setContentsMargins(0, 5, 0, 5)
        self.setLayout(bar_layout)

        self.is_dragging = False  # 标记是否正在拖动
        self.drag_start_position = None  # 鼠标按下时的初始位置

        # 标题标签
        title_label = QtWidgets.QLabel("设置")
        title_font = QtGui.QFont("Microsoft YaHei", 16)  # 设置字体大小
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")  # 设置文字颜色
        bar_layout.addWidget(title_label)
    
        # 关闭按钮
        close_button = QtWidgets.QPushButton("关闭")
        close_button.setFont(QtGui.QFont("Microsoft YaHei", 12))
        close_button.setFixedSize(60, 30)
        close_button.clicked.connect(self.parent_window.close)
        bar_layout.addWidget(close_button)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """鼠标按下事件"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        """鼠标移动事件"""
        if self.is_dragging and self.drag_start_position is not None:
            new_position = event.globalPosition().toPoint() - self.drag_start_position
            self.parent_window.move(new_position)  # 更新窗口位置
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """鼠标释放事件"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.drag_start_position = None
            event.accept()

class GeneralPage(QtWidgets.QWidget):
    def __init__(self, config_editor):
        super().__init__()
        self.config_editor: ConfigEditor = config_editor
        self.init_ui()

    def init_ui(self):
        """初始化通用设置"""
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)  # 允许内容自适应大小
        layout.addWidget(scroll_area)

        content_widget = QtWidgets.QWidget()
        scroll_area.setWidget(content_widget)

        form_layout = QtWidgets.QFormLayout()
        content_widget.setLayout(form_layout)

        # 刷新率滑条
        refresh_rate_slider_layout = QtWidgets.QHBoxLayout()

        self.refresh_rate_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.refresh_rate_slider.setFixedHeight(30)
        self.refresh_rate_slider.setRange(30, 240)
        self.refresh_rate_slider.setValue(self.config_editor.refresh_rate)
        self.refresh_rate_slider.valueChanged.connect(self.update_refresh_rate)
        refresh_rate_slider_layout.addWidget(self.refresh_rate_slider)

        self.refresh_rate_label = QtWidgets.QLabel(str(self.config_editor.refresh_rate))
        self.refresh_rate_label.setFixedHeight(30)
        self.refresh_rate_label.setFixedWidth(50)
        refresh_rate_slider_layout.addWidget(self.refresh_rate_label)

        form_layout.addRow("动画刷新率", refresh_rate_slider_layout)

        # Live2D 尺寸滑条
        model_size_slider_layout = QtWidgets.QHBoxLayout()

        self.model_size_slider_scale_factor = 10
        self.model_size_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.model_size_slider.setFixedHeight(30)
        self.model_size_slider.setRange(1 * self.model_size_slider_scale_factor, 5 * self.model_size_slider_scale_factor)
        self.model_size_slider.setValue(self.config_editor.l2d_size.width() // 100 * self.model_size_slider_scale_factor)
        self.model_size_slider.valueChanged.connect(self.update_l2d_size)
        model_size_slider_layout.addWidget(self.model_size_slider)

        self.model_size_label = QtWidgets.QLabel(str(self.model_size_slider.value() / self.model_size_slider_scale_factor))
        self.model_size_label.setFixedHeight(30)
        self.model_size_label.setFixedWidth(50)
        model_size_slider_layout.addWidget(self.model_size_label)

        form_layout.addRow("模型尺寸", model_size_slider_layout)

        # 信息字体尺寸滑条
        message_size_slider_layout = QtWidgets.QHBoxLayout()

        self.message_size_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.message_size_slider.setFixedHeight(30)
        self.message_size_slider.setRange(10, 50)
        self.message_size_slider.setValue(self.config_editor.message_size)
        self.message_size_slider.valueChanged.connect(self.update_message_size)
        message_size_slider_layout.addWidget(self.message_size_slider)

        self.message_size_label = QtWidgets.QLabel(str(self.message_size_slider.value()))
        self.message_size_label.setFixedHeight(30)
        self.message_size_label.setFixedWidth(50)
        message_size_slider_layout.addWidget(self.message_size_label)

        form_layout.addRow("弹出字体尺寸", message_size_slider_layout)

    def update_refresh_rate(self):
        """更新刷新率配置"""
        self.config_editor.refresh_rate = self.refresh_rate_slider.value()
        self.refresh_rate_label.setText(str(self.config_editor.refresh_rate))
        self.config_editor.config["general"]["refresh_rate"] = self.config_editor.refresh_rate

    def update_l2d_size(self):
        """更新 Live2D 尺寸配置"""
        base_size = [100, 300]  # 基础尺寸系数
        value = self.model_size_slider.value() / self.model_size_slider_scale_factor
        self.config_editor.l2d_size = QtCore.QSize(value * base_size[0], value * base_size[1])
        self.model_size_label.setText(str(value))
        self.config_editor.config["general"]["l2d_size"] = [value * base_size[0], value * base_size[1]]

    def update_message_size(self):
        self.config_editor.message_size = self.message_size_slider.value()
        self.message_size_label.setText(str(self.config_editor.message_size))
        self.config_editor.config["general"]["message"] = self.config_editor.message_size

class Live2DPage(QtWidgets.QWidget):
    def __init__(self, config_editor):
        super().__init__()
        self.config_editor: ConfigEditor = config_editor
        self.init_ui()

    def init_ui(self):
        """初始化 Live2D 设置"""
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)  # 允许内容自适应大小
        layout.addWidget(scroll_area)

        content_widget = QtWidgets.QWidget()
        scroll_area.setWidget(content_widget)

        form_layout = QtWidgets.QFormLayout()
        content_widget.setLayout(form_layout)

        # Live2D 模型路径选择
        self.l2d_model_select_layout = QtWidgets.QHBoxLayout()

        self.l2d_model_input = QtWidgets.QLineEdit()
        self.l2d_model_input.setFixedHeight(30)
        self.l2d_model_input.setText(self.config_editor.l2d_model)
        self.l2d_model_select_layout.addWidget(self.l2d_model_input)

        self.select_folder_button = QtWidgets.QPushButton("浏览")
        self.select_folder_button.setFixedHeight(30)
        self.select_folder_button.setFixedWidth(80)
        self.select_folder_button.clicked.connect(self.select_l2d_model_folder)
        self.l2d_model_select_layout.addWidget(self.select_folder_button)
        form_layout.addRow("Live2D 模型位置", self.l2d_model_select_layout)

        # 动作表格
        self.motion_table = QtWidgets.QTableWidget()
        self.motion_table.setFixedHeight(240)
        self.motion_table.setColumnCount(4)  # 四列
        self.motion_table.setHorizontalHeaderLabels(["演示", "动作", "待机", "左键点击"])
        self.motion_table.setSelectionMode(QtWidgets.QTableWidget.SelectionMode.NoSelection)

        header = self.motion_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)  # 固定第一列宽度
        header.resizeSection(0, 60)  # 设置第一列宽度为 80
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)  # 第二列拉伸
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)  # 第三列拉伸
        header.resizeSection(2, 100)  # 设置第一列宽度为 80
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)  # 第四列拉伸
        header.resizeSection(3, 100)  # 设置第一列宽度为 80
        form_layout.addRow(self.motion_table)
        # 初始化表格数据
        self.populate_motion_table()

        # 待机动作发生率滑条
        standby_active_rate_slider_layout = QtWidgets.QHBoxLayout()

        self.standby_active_rate_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.standby_active_rate_slider.setFixedHeight(30)
        self.standby_active_rate_slider_scale_factor = 100
        self.standby_active_rate_slider.setRange(0 * self.standby_active_rate_slider_scale_factor, 1 * self.standby_active_rate_slider_scale_factor)
        self.standby_active_rate_slider.setValue(self.config_editor.standby_active_rate * self.standby_active_rate_slider_scale_factor)
        self.standby_active_rate_slider.valueChanged.connect(self.update_standby_active_rate)
        standby_active_rate_slider_layout.addWidget(self.standby_active_rate_slider)

        self.standby_active_rate_label = QtWidgets.QLabel(str(self.config_editor.standby_active_rate))
        self.standby_active_rate_label.setFixedHeight(30)
        self.standby_active_rate_label.setFixedWidth(50)
        standby_active_rate_slider_layout.addWidget(self.standby_active_rate_label)

        form_layout.addRow("待机动作频率", standby_active_rate_slider_layout)

        # 鼠标跟随灵敏度滑条
        tracking_sensitivity_slider_layout = QtWidgets.QHBoxLayout()

        self.tracking_sensitivity_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.tracking_sensitivity_slider.setFixedHeight(30)
        self.tracking_sensitivity_slider_scale_factor = 100
        self.tracking_sensitivity_slider.setRange(0 * self.tracking_sensitivity_slider_scale_factor, 3 * self.tracking_sensitivity_slider_scale_factor)
        self.tracking_sensitivity_slider.setValue(self.config_editor.standby_active_rate * self.tracking_sensitivity_slider_scale_factor)
        self.tracking_sensitivity_slider.valueChanged.connect(self.update_tracking_sensitivity)
        tracking_sensitivity_slider_layout.addWidget(self.tracking_sensitivity_slider)

        self.tracking_sensitivity_label = QtWidgets.QLabel(str(self.config_editor.tracking_sensitivity))
        self.tracking_sensitivity_label.setFixedHeight(30)
        self.tracking_sensitivity_label.setFixedWidth(50)
        tracking_sensitivity_slider_layout.addWidget(self.tracking_sensitivity_label)

        form_layout.addRow("鼠标跟随灵敏度", tracking_sensitivity_slider_layout)

        # 自动呼吸按钮
        auto_breath_layout = QtWidgets.QHBoxLayout()
        auto_breath_layout.addStretch()
        self.auto_breath_button = QtWidgets.QPushButton("开" if self.config_editor.auto_breath else "关")
        self.auto_breath_button.setFixedHeight(30)
        self.auto_breath_button.setFixedWidth(50)
        self.auto_breath_button.setCheckable(True)  # 设置为可切换按钮
        self.auto_breath_button.setChecked(self.config_editor.auto_breath)
        self.auto_breath_button.clicked.connect(self.toggle_auto_breath)
        auto_breath_layout.addWidget(self.auto_breath_button)
        form_layout.addRow("自动呼吸", auto_breath_layout)

        # 自动眨眼按钮
        auto_blink_layout = QtWidgets.QHBoxLayout()
        auto_blink_layout.addStretch()
        self.auto_blink_button = QtWidgets.QPushButton("开" if self.config_editor.auto_blink else "关")
        self.auto_blink_button.setFixedHeight(30)
        self.auto_blink_button.setFixedWidth(50)
        self.auto_blink_button.setCheckable(True)  # 设置为可切换按钮
        self.auto_blink_button.setChecked(self.config_editor.auto_blink)
        self.auto_blink_button.clicked.connect(self.toggle_auto_blink)
        auto_blink_layout.addWidget(self.auto_blink_button)
        form_layout.addRow("自动眨眼", auto_blink_layout)

    def select_l2d_model_folder(self):
        """打开文件资源管理器选择文件夹，并检查是否存在 .moc3 文件"""
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select L2D Model Folder")
        
        if folder_path:
            # 检查文件夹中是否存在 .moc3 文件
            has_moc3_file = any(file.endswith(".moc3") for file in os.listdir(folder_path))
            
            if has_moc3_file:
                # 如果存在 .moc3 文件，更新配置和输入框
                self.config_editor.l2d_model = folder_path
                self.l2d_model_input.setText(folder_path)
            else:
                # 如果不存在 .moc3 文件，弹出提示框
                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid Folder",
                    "The selected folder does not contain any .moc3 file.",
                    QtWidgets.QMessageBox.StandardButton.Ok
                )

    def populate_motion_table(self):
        """填充动作表格"""
        motions_data = self.config_editor.motions
        self.motion_table.setRowCount(len(motions_data))

        for row, (motion_name, motion_info) in enumerate(motions_data.items()):
            # 第一列：演示按钮
            demo_button = QtWidgets.QPushButton("播放")
            demo_button.setCheckable(True)
            demo_button.clicked.connect(lambda _, name=motion_name, button=demo_button: self.play_motion(name, button))
            self.motion_table.setCellWidget(row, 0, demo_button)

            # 第二列：动作名字
            motion_name_item = QtWidgets.QTableWidgetItem(motion_name)
            self.motion_table.setItem(row, 1, motion_name_item)

            # 第三列：待机动作复选框
            standby_checkbox = QtWidgets.QCheckBox()
            if motion_name in [motion['name'] for motion in self.config_editor.standby_action]:
                standby_checkbox.setChecked(True)
            else:
                standby_checkbox.setChecked(False)
            standby_checkbox.stateChanged.connect(
                lambda state, name=motion_name, group=motion_info["group"], index=motion_info["index"]:
                    self.update_config(state, name, group, index, "standby")
            )
            self.motion_table.setCellWidget(row, 2, self.center_widget(standby_checkbox))

            # 第四列：点击动作复选框
            click_checkbox = QtWidgets.QCheckBox()
            if motion_name in [motion['name'] for motion in self.config_editor.click_action]:
                click_checkbox.setChecked(True)
            else:
                click_checkbox.setChecked(False)
            click_checkbox.stateChanged.connect(
                lambda state, name=motion_name, group=motion_info["group"], index=motion_info["index"]:
                    self.update_config(state, name, group, index, "click")
            )
            self.motion_table.setCellWidget(row, 3, self.center_widget(click_checkbox))

    def center_widget(self, widget):
        """将小部件居中放置在单元格中"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(widget)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)
        return container

    def play_motion(self, motion_name, button):
        self.config_editor.l2d_manager.set_motion(motion_name)
        self.config_editor.l2d_manager.set_state_true("motion")
        button.setChecked(False)

    def update_config(self, state, motion_name, group, index, action_type):
        """
        更新配置
        :param state: 复选框的状态 (Qt.Checked 或 Qt.Unchecked)
        :param motion_name: 动作名字
        :param group: 动作组名
        :param index: 动作索引
        :param action_type: 动作类型 ("standby" 或 "click")
        """
        config: list = self.config_editor.standby_action if action_type == "standby" else self.config_editor.click_action
        action_entry = {"name": motion_name, "group": group, "index": index}

        if state == QtCore.Qt.CheckState.Checked.value:
            if action_entry not in config:
                config.append(action_entry)
                logging.info(f"添加 {action_type} 动作: {motion_name} ({group}, {index})")
        else:
            if action_entry in config:
                config.remove(action_entry)
                logging.info(f"移除 {action_type} 动作: {motion_name} ({group}, {index})")
        key = "standby_action" if action_type == "standby" else "click_action"
        self.config_editor.config["l2d"][key] = config

    def update_standby_active_rate(self):
        """更新待机动作触发概率配置"""
        self.config_editor.standby_active_rate = self.standby_active_rate_slider.value() / self.standby_active_rate_slider_scale_factor
        self.standby_active_rate_label.setText(str(self.config_editor.standby_active_rate))
        self.config_editor.config["l2d"]["standby_active_rate"] = self.config_editor.standby_active_rate

    def update_tracking_sensitivity(self):
        """更新鼠标跟随灵敏度配置"""
        self.config_editor.tracking_sensitivity = self.tracking_sensitivity_slider.value() / self.tracking_sensitivity_slider_scale_factor
        self.tracking_sensitivity_label.setText(str(self.config_editor.tracking_sensitivity))
        self.config_editor.config["l2d"]["tracking_sensitivity"] = self.config_editor.tracking_sensitivity

    def toggle_auto_breath(self):
        """切换自动呼吸状态"""
        self.config_editor.auto_breath = not self.config_editor.auto_breath
        self.auto_breath_button.setText("开" if self.config_editor.auto_breath else "关")
        self.auto_breath_button.setChecked(self.config_editor.auto_breath)
        self.config_editor.config["l2d"]["auto_breath"] = self.config_editor.auto_breath

    def toggle_auto_blink(self):
        """切换自动眨眼状态"""
        self.config_editor.auto_blink = not self.config_editor.auto_blink
        self.auto_blink_button.setText("开" if self.config_editor.auto_blink else "关")
        self.auto_blink_button.setChecked(self.config_editor.auto_blink)
        self.config_editor.config["l2d"]["auto_blink"] = self.config_editor.auto_blink

class LLMPage(QtWidgets.QWidget):
    API_data = {
        "SiliconFlow API": {
            "id": "siliconflow",
            "model": [
                {"DeepSeek-R1": "deepseek-ai/DeepSeek-R1"},
                {"DeepSeek-V3": "deepseek-ai/DeepSeek-V3"},
                {"QwQ-32B": "Qwen/QwQ-32B"}
            ],
        },
        "DeepSeek API": {
            "id": "deepseek",
            "model": [
                {"DeepSeek-R1": "deepseek-reasoner"},
                {"DeepSeek-V3": "deepseek-chat"},
            ],
        },
    }

    def __init__(self, config_editor):
        super().__init__()
        self.config_editor = config_editor
        self.init_ui()

    def init_ui(self):
        """初始化大语言模型配置"""
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)  # 允许内容自适应大小
        layout.addWidget(scroll_area)

        content_widget = QtWidgets.QWidget()
        scroll_area.setWidget(content_widget)

        form_layout = QtWidgets.QFormLayout()
        content_widget.setLayout(form_layout)

        # API 提供商下拉框
        self.platform_combo = QtWidgets.QComboBox()
        # self.platform_combo.setFixedHeight(30)
        self.platform_combo.addItem("请选择 API 提供商", userData=None)
        for api_name in self.API_data.keys():
            self.platform_combo.addItem(api_name, userData=self.API_data[api_name]["id"])
        # 检查配置中是否有 target_platform，默认选择
        saved_platform_id = self.config_editor.config["llm"].get("target_platform")
        if saved_platform_id:
            index = self.platform_combo.findData(saved_platform_id)
            if index != -1:
                self.platform_combo.setCurrentIndex(index)
        else:
            self.platform_combo.setCurrentIndex(0)  # 默认选择 "请选择 API 提供商"

        self.platform_combo.currentIndexChanged.connect(self.update_models)
        form_layout.addRow("API 提供商", self.platform_combo)

        # 模型下拉框
        self.model_combo = QtWidgets.QComboBox()
        # self.model_combo.setFixedHeight(30)
        self.model_combo.addItem("请选择模型", userData=None)
        # 检查配置中是否有 target_model，默认选择
        saved_model_id = self.config_editor.config["llm"].get("target_model")
        if saved_platform_id and saved_model_id:
            models = self.API_data.get(next((k for k, v in self.API_data.items() if v["id"] == saved_platform_id), {}), {}).get("model", [])
            for model in models:
                model_name, model_id = list(model.items())[0]
                self.model_combo.addItem(model_name, userData=model_id)
                if model_id == saved_model_id:
                    self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
        else:
            self.model_combo.setCurrentIndex(0)  # 默认选择 "请选择模型"
        self.model_combo.currentIndexChanged.connect(self.update_model_and_config)
        form_layout.addRow("模型", self.model_combo)

        # API Key 输入框
        self.api_key_input = QtWidgets.QLineEdit()
        # self.api_key_input.setFixedHeight(30)
        saved_api_key = self.config_editor.config["llm"].get("api_key", "")
        self.api_key_input.setText(saved_api_key)
        self.api_key_input.setPlaceholderText("请输入 API Key")
        self.api_key_input.textChanged.connect(self.update_api_key)
        form_layout.addRow("API Key", self.api_key_input)

        # 系统提示词输入框 (多行文本框)
        self.system_prompt_input = QtWidgets.QTextEdit()
        # self.system_prompt_input.setFixedHeight(100)  # 设置固定高度
        saved_system_prompt = self.config_editor.config["llm"].get("system_prompt", "")
        self.system_prompt_input.setText(saved_system_prompt)
        self.system_prompt_input.setPlaceholderText("请输入系统提示词")
        self.system_prompt_input.textChanged.connect(self.update_system_prompt)
        form_layout.addRow("系统提示词", self.system_prompt_input)

    def update_models(self):
        """根据选择的 API 提供商更新模型下拉框"""
        # 清空当前模型列表
        self.model_combo.clear()
        self.model_combo.addItem("请选择模型", userData=None)

        # 获取当前选中的 API 提供商的 id
        selected_platform_id = self.platform_combo.currentData()
        if selected_platform_id:
            self.config_editor.config["llm"]["target_platform"] = selected_platform_id

            # 查找对应的平台名称
            selected_platform_name = next((k for k, v in self.API_data.items() if v["id"] == selected_platform_id), None)
            if selected_platform_name:
                models = self.API_data[selected_platform_name]["model"]
                for model in models:
                    model_name, model_id = list(model.items())[0]
                    self.model_combo.addItem(model_name, userData=model_id)

    def update_model_and_config(self):
        """更新选中的模型到配置中"""
        selected_model_id = self.model_combo.currentData()
        if selected_model_id:
            # 更新配置中的 target_model
            self.config_editor.config["llm"]["target_model"] = selected_model_id

    def update_api_key(self):
        """更新 API Key 到配置中"""
        api_key = self.api_key_input.text()
        self.config_editor.config["llm"]["api_key"] = api_key

    def update_system_prompt(self):
        """更新系统提示词到配置中"""
        system_prompt = self.system_prompt_input.toPlainText()
        self.config_editor.config["llm"]["system_prompt"] = system_prompt

class ConfigEditor(QtWidgets.QWidget):
    config_updated = QtCore.Signal()

    def __init__(self, main_dir):
        super().__init__()
        self.main_dir = main_dir
        self.config_file = os.path.join(self.main_dir, "config.toml")
        
        self.config = self._load_toml_config(self.config_file)

        self._init_config_var()
        self.motion_loader = MotionLoader(self.l2d_model)
        self.motions = self.motion_loader.get_motions()
        self._init_ui()

        self.popup_massage: function = None

    def _load_toml_config(self, file_path: str):
        """加载 toml 配置文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return toml.load(file)
        except FileNotFoundError:
            logging.warning(f"配置文件 {file_path} 未找到，使用默认配置。")
            return {}
        
    def _init_config_var(self):
        """实例化实例变量"""
        # 加载菜单配置
        menu_config: dict = self.config.get("menu")
        self.beats_enable = menu_config.get("beats_enable", False)

        # 加载通用配置
        general_config: dict = self.config.get("general")
        self.refresh_rate = general_config.get("refresh_rate", 60)
        config_l2d_size = general_config.get("l2d_size", [300, 600])
        self.l2d_size = QtCore.QSize(config_l2d_size[0], config_l2d_size[1])
        self.message_size = general_config.get("message_size", 12)

        # 加载 Live2D 配置
        l2d_config: dict = self.config.get("l2d")
        self.l2d_model = l2d_config.get("l2d_model", os.path.join("model", "hiyori_free_t08"))
        self.standby_action = l2d_config.get("standby_action", [])
        self.click_action = l2d_config.get("click_action", [])
        self.auto_breath = l2d_config.get("auto_breath", "True") == "True"  # str 转 bool
        self.auto_blink = l2d_config.get("auto_blink", "True") == "True"    # str 转 bool
        self.tracking_sensitivity = l2d_config.get("tracking_sensitivity", 1)
        self.standby_active_rate = l2d_config.get("standby_active_rate", 1)

        # 加载大模型配置
        llm_config: dict = self.config.get("llm")
        self.target_platform = llm_config.get("target_platform", "")
        self.target_model = llm_config.get("target_model", "")
        self.api_key = llm_config.get("api_key", "")
        self.system_prompt = llm_config.get("system_prompt", "")

    def _init_ui(self):
        """初始化界面"""
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)

        # 设置窗口透明度
        self.setWindowOpacity(0.95)  # 设置为 90% 不透明度（可以根据需要调整）

        font = QtGui.QFont("Microsoft YaHei", 12)
        self.setFont(font)

        self.setWindowTitle("设置")
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        window_width, window_height = 600, 500
        self.setGeometry(
            (screen.width() - window_width) // 2,
            (screen.height() - window_height) // 2,
            window_width,
            window_height,
        )

        # 主布局
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        ## 标题栏
        title_bar = TitleBar(self)
        main_layout.addWidget(title_bar)

        ## 内容布局
        content_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(content_layout)

        ### 左侧菜单
        menu_list = QtWidgets.QListWidget()
        menu_list.setFixedWidth(100)
        menu_list.addItems(["通用", "Live2D", "大模型"])
        menu_list.currentRowChanged.connect(self.switch_section)
        content_layout.addWidget(menu_list)

        for i in range(menu_list.count()):
            item = menu_list.item(i)
            item.setSizeHint(QtCore.QSize(0, 30))  # 宽度 100，高度 40
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        ### 右侧堆栈窗口
        self.stacked_widget = QtWidgets.QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        general_page = GeneralPage(self)
        self.stacked_widget.addWidget(general_page)
        l2d_page = Live2DPage(self)
        self.stacked_widget.addWidget(l2d_page)
        llm_page = LLMPage(self)
        self.stacked_widget.addWidget(llm_page)

        ## 按钮布局
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        ### 应用按钮
        apply_button = QtWidgets.QPushButton("应用")
        apply_button.setFont(QtGui.QFont("Microsoft YaHei", 12))
        apply_button.setFixedWidth(120)
        apply_button.setFixedHeight(30)
        apply_button.clicked.connect(self.apply_changes)  # 绑定回调函数
        button_layout.addWidget(apply_button)

        ### 确定按钮
        OK_button = QtWidgets.QPushButton("确定")
        OK_button.setFont(QtGui.QFont("Microsoft YaHei", 12))
        OK_button.setFixedWidth(120)
        OK_button.setFixedHeight(30)
        OK_button.clicked.connect(self.OK_changes)  # 绑定回调函数
        button_layout.addWidget(OK_button)

        # 初始化时默认选中第一项
        menu_list.setCurrentRow(0)  # 默认选中“通用”

    def set_popup(self, popup_function: callable):
        self.popup_message = popup_function

    def switch_section(self, index):
        """切换到指定部分"""
        self.stacked_widget.setCurrentIndex(index)

    def set_l2d_model_manager(self, l2d_manager: Soyoc_l2d_manager):
        self.l2d_manager = l2d_manager

    def apply_changes(self):
        """点击“应用”按钮后保存配置并隐藏窗口"""
        self.config_updated.emit()

    def OK_changes(self):
        """点击“确定”按钮后保存配置并隐藏窗口"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config_file)
        self._save_toml_config(config_path)

        self.hide()

        self.config_updated.emit()

    def _save_toml_config(self, file_path: str):
        """保存配置到 toml 文件"""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                toml.dump(self.config, file)
            logging.info(f"配置已成功保存到 {file_path}")
        except Exception as e:
            logging.info(f"保存配置文件失败: {e}")
