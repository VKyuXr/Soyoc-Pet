import PySide6.QtWidgets as QtWidgets
import PySide6.QtCore as QtCore
import PySide6.QtOpenGLWidgets as QtOpenGLWidgets
import PySide6.QtGui as QtGui
import live2d.v3 as live2d
import OpenGL.GL as GL
import Soyoc_core.live2d_manager as Soyoc_l2d_manager
import Soyoc_core.Soyoc_utils.audio_analyzer as Soyoc_audio
import math, random
import Soyoc_core.config_editor as Soyoc_config
import Soyoc_core.chat_window as Soyoc_chat

class Live2DWidget(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self, l2d_manager: Soyoc_l2d_manager.Live2DManager, config_editor: Soyoc_config.ConfigEditor) -> None:
        super().__init__()
        self.l2d_manager = l2d_manager
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.config_editor = config_editor
        self.config_editor.set_l2d_model_manager(self.l2d_manager)

        # 监听配置更新信号
        self.config_editor.config_updated.connect(self.on_config_updated)   # 连接信号

    def on_config_updated(self):
        """处理配置更新事件"""
        width, height = self.config_editor.l2d_size.width(), self.config_editor.l2d_size.height()
        self.resize(width, height)  # 调整窗口大小
        self.resizeGL(width, height)  # 手动调用 resizeGL 触发重绘

    def initializeGL(self) -> None:
        self.l2d_manager.l2d_and_glew_init()
        self.l2d_manager.load_l2d_model()

        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClearDepth(1.0)

        self.startTimer(int(1000 / self.config_editor.refresh_rate))

    def resizeGL(self, width: int, height: int):
        self.l2d_manager.model.Resize(width, height)

    def paintGL(self) -> None:
        live2d.clearBuffer()
        self.l2d_manager.model.Update()
        self.l2d_manager.params_update()
        self.l2d_manager.model.Draw()
        if self.l2d_manager.to_default > 0:
            self.l2d_manager.param_to_default()
            self.l2d_manager.to_default -= 1

    def timerEvent(self, event: QtCore.QTimerEvent):
        self.update()
    
    # 新增鼠标事件传递
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super().mousePressEvent(event)  # 正常处理事件
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

class MessageWindow(QtWidgets.QWidget):
    def __init__(self, message, font_size: int, parent=None):
        super().__init__(None)  # 关键修改：父窗口设为None
        self.main_window = parent  # 保留对主窗口的引用
        self.message = message  # 接收传递的消息内容
        self.duration = max(len(self.message) / 5 * 1000, 3000)

        # 设置窗口属性
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Window
        )
        self.setWindowOpacity(0.8)

        # 窗口内容
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.label = QtWidgets.QLabel(self)
        self.label.setMaximumWidth(400)
        self.label.setText(f"<div style=\"line-height: 25px;\">{self.message}</div>")
        # 设置字体大小
        font = QtGui.QFont()
        font.setPointSize(font_size)
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        # 调整窗口大小并定位
        self.label.setWordWrap(True)
        self.adjustSize()
        self.update_position()
        
        # 设置自动关闭定时器
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.start_fade_out)
        self.timer.start(self.duration)

    def update_position(self):
        if self.main_window:
            # 获取主窗口的屏幕位置
            main_pos = self.main_window.mapToGlobal(QtCore.QPoint(0, 0))
            # 计算居中位置
            x = main_pos.x() + self.main_window.width() // 2 - self.width() // 2
            y = main_pos.y() + (self.main_window.height() - self.height()) // 2
            self.move(x, y)

    def start_fade_out(self):
        # 创建透明度动画
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)  # 1秒淡出动画
        self.animation.setStartValue(self.windowOpacity())
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()

class MainWindow(QtWidgets.QMainWindow):
    # 定义一个带参数的信号，用于传递消息内容
    show_message_signal = QtCore.Signal(str)  # 信号类型为字符串

    def __init__(self, config_editor: Soyoc_config.ConfigEditor):
        super().__init__()
        self.config_editor: Soyoc_config.ConfigEditor = config_editor
        self.l2d_manager = Soyoc_l2d_manager.Live2DManager(self.config_editor)
        self.l2d_widget = Live2DWidget(self.l2d_manager, self.config_editor)
        self.n_beats_per_cycle = 4
        self.popups = []  # 存储所有弹出窗口
        self.chat_window = None

        self.setup_basic_init()
        self.setup_mouse_handling()
        self.setup_animation_and_audio()

        self.startTimer(int(1000 / self.config_editor.refresh_rate))

    def setup_basic_init(self):
        """基础窗口设置"""
        self.setCentralWidget(self.l2d_widget)
        self.resize(self.config_editor.l2d_size)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self.screen_size = QtWidgets.QApplication.primaryScreen().size()

        # 监听配置更新信号
        self.config_editor.config_updated.connect(self.update_size)
        self.config_editor.set_popup(self.open_message_window)
        # 连接信号到槽函数，并接收消息内容
        self.show_message_signal.connect(self.open_message_window)

    def setup_mouse_handling(self):
        """鼠标交互相关初始化"""
        # 鼠标跟踪设置
        self.setMouseTracking(True)
        self.last_mouse_pos_timer = None
        
        # 拖动系统初始化
        self.drag_start_pos = None
        self.drag_window_pos = None
        self.is_dragging = False
        
        # 长按计时器
        self.press_timer = QtCore.QTimer(self)
        self.press_timer.setSingleShot(True)
        self.press_timer.timeout.connect(self.start_drag)

    def setup_animation_and_audio(self):
        """动画和音频系统初始化"""
        # 动画实例配置
        self.animation = QtCore.QVariantAnimation(self)
        self.animation.setDuration(1000)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setLoopCount(-1)
        self.animation.valueChanged.connect(self.update_angle_y)
        
        # 音频分析系统
        self.audio_analyzer = Soyoc_audio.AudioAnalyzer(loudness_threshold=-70.0)
        self.audio_timer = QtCore.QTimer(self)
        self.audio_timer.timeout.connect(self.check_audio_conditions)
        self.audio_timer.start(100)

        self.standby_timer = QtCore.QTimer(self)
        self.standby_timer.timeout.connect(self.play_standby_motion)
        self.standby_timer.start(10000)

    def update_size(self):
        self.resize(self.config_editor.l2d_size)

    def contextMenuEvent(self, event: QtGui.QMouseEvent):
        # 创建上下文菜单
        context_menu = QtWidgets.QMenu(self)

        # 添加菜单项
        menu_chat = QtGui.QAction("聊天", self)
        menu_beats = QtGui.QAction("节奏跟随", self)
        menu_beats.setCheckable(True)  # 设置为复选框
        menu_beats.setChecked(self.config_editor.beats_enable)  # 设置为当前状态
        menu_setting = QtGui.QAction("设置", self)
        menu_exit = QtGui.QAction("退出", self)

        # 设置字体大小
        font = QtGui.QFont()
        font.setPointSize(10)  # 设置字体大小为 10
        menu_chat.setFont(font)
        menu_beats.setFont(font)
        menu_setting.setFont(font)
        menu_exit.setFont(font)

        # 连接动作到槽函数
        menu_chat.triggered.connect(self.open_chat_window)
        menu_beats.triggered.connect(self.beats_switch)
        menu_setting.triggered.connect(self.option_selected)
        menu_exit.triggered.connect(self.close)

        # 将动作添加到菜单
        context_menu.addAction(menu_chat)
        context_menu.addSeparator()  # 添加分隔符
        context_menu.addAction(menu_beats)
        context_menu.addSeparator()  # 添加分隔符
        context_menu.addAction(menu_setting)
        context_menu.addAction(menu_exit)

        # 在鼠标右键点击的位置显示菜单
        context_menu.exec(event.globalPos())

    def open_chat_window(self):
        """打开聊天页面"""
        if self.chat_window is None:
            self.chat_window = Soyoc_chat.ChatWindow(self.config_editor)  # 实例化设置页面
        self.chat_window.show()  # 显示设置页面

    def option_selected(self):
        """打开设置页面"""
        if self.config_editor is None:
            self.config_editor = Soyoc_config.ConfigEditor()  # 实例化设置页面
        self.config_editor.show()  # 显示设置页面

    def beats_switch(self, checked):
        """复选框状态变化的槽函数"""
        self.beats_enabled = checked  # 更新状态
        if checked:
            self.config_editor.beats_enable = True
        else:
            self.config_editor.beats_enable = False
            self.animation.stop()
            self.l2d_manager.set_state_true("track")
            self.audio_analyzer.period_reset()

    def closeEvent(self, event):
        """关闭事件处理"""
        self.audio_analyzer.stop()  # 停止音频分析器
        self.config_editor.close()
        if isinstance(self.chat_window, Soyoc_chat.ChatWindow):
            self.chat_window.close()
        super().closeEvent(event)

    def timerEvent(self, event: QtCore.QTimerEvent):
        x_l2d_center = self.pos().x() + self.config_editor.l2d_size.width() / 2
        y_l2d_center = self.pos().y() + self.config_editor.l2d_size.height() / 3
        dx = (QtGui.QCursor.pos().x() - x_l2d_center) / self.screen_size.width()
        dy = - (QtGui.QCursor.pos().y() - y_l2d_center) / self.screen_size.height()

        if self.l2d_manager.is_track():
            self.l2d_manager.model_params["ParamAngleX"] = dx * 30 * self.config_editor.tracking_sensitivity
            self.l2d_manager.model_params["ParamAngleY"] = dy * 30 * self.config_editor.tracking_sensitivity
            self.l2d_manager.model_params["ParamAngleZ"] = - dx * 30 * self.config_editor.tracking_sensitivity
            self.l2d_manager.model_params["ParamBodyAngleX"] = dx * 10 * self.config_editor.tracking_sensitivity
        self.l2d_manager.model_params["ParamEyeBallX"] = dx * 1 * self.config_editor.tracking_sensitivity
        self.l2d_manager.model_params["ParamEyeBallY"] = dy * 1 * self.config_editor.tracking_sensitivity

        # 新增逻辑：拖动状态下持续检测鼠标是否停止移动
        if self.is_dragging:
            current_pos = QtGui.QCursor.pos()  # 获取当前全局鼠标位置
            if self.last_mouse_pos_timer is not None:
                # 计算与上一次位置的差值
                delta = current_pos - self.last_mouse_pos_timer
                # 如果鼠标未移动，速度归零
                if delta.x() == 0 and delta.y() == 0:
                    self.l2d_manager.velocity = [0, 0]
            # 更新记录的位置
            self.last_mouse_pos_timer = current_pos
    
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # 如果点击发生在 Live2DWidget 上，允许拖拽
            self.drag_start_pos = event.globalPosition().toPoint()
            self.drag_window_pos = self.pos()
            self.press_timer.start(100)  # 启动长按计时器
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def start_drag(self):
        self.is_dragging = True
    
    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.is_dragging and self.drag_start_pos is not None:
            current_pos = event.globalPosition().toPoint()
            
            if hasattr(self, 'last_mouse_pos'):
                delta_relative = current_pos - self.last_mouse_pos
                self.l2d_manager.velocity = [delta_relative.x() / (1 / self.config_editor.refresh_rate), delta_relative.y() / (1 / self.config_editor.refresh_rate)]
            
            self.last_mouse_pos = current_pos

            delta = current_pos - self.drag_start_pos
            new_pos = self.drag_window_pos + delta
            self.move(new_pos)
            self.update_message_position()
            event.accept()
            # 同步更新定时器的位置记录
            self.last_mouse_pos_timer = current_pos
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtGui.Qt.MouseButton.LeftButton:
            self.press_timer.stop()
            if self.is_dragging:
                self.is_dragging = False
                self.drag_start_pos = None
                self.drag_window_pos = None
                self.l2d_manager.velocity = [0, 0]
            else:
                # self.show_message_signal.emit("哦？")
                self.config_editor.popup_message("哦？") # 测试用
                self.play_click_motion()
            event.accept()
            # 释放时清空定时器的位置记录
            self.last_mouse_pos_timer = None
        else:
            super().mouseReleaseEvent(event)

    def play_click_motion(self):
        """播放随机点击动作"""
        if not len(self.config_editor.click_action):
            return
        motion_name = random.choice(self.config_editor.click_action)["name"]
        self.l2d_manager.set_motion(motion_name)
        self.l2d_manager.set_state_true("motion")

    def play_standby_motion(self):
        """播放随机待机动作"""
        if not self.l2d_manager.is_track():
            return
        if random.random() < (1 - self.config_editor.standby_active_rate):
            return
        if not len(self.config_editor.standby_action):
            return
        motion_name = random.choice(self.config_editor.standby_action)["name"]
        self.l2d_manager.set_motion(motion_name)
        self.l2d_manager.set_state_true("motion")
    
    def check_audio_conditions(self):
        """检查音频条件并控制动画状态"""
        if not self.config_editor.beats_enable:
            return

        if not self.audio_analyzer.loudness_flag:
            if self.animation.state() == QtCore.QAbstractAnimation.State.Running:
                self.animation.stop()
                self.l2d_manager.set_state_true("track")
                self.audio_analyzer.period_reset()
            return
        elif self.l2d_manager.is_track():
            if not self.audio_analyzer.record_and_analyze_is_alive() and self.audio_analyzer.period == 0:
                self.audio_analyzer.start_detection()

        if self.audio_analyzer.period <= 0 or self.n_beats_per_cycle <= 0:
            return

        if self.l2d_manager.is_track():
            self.l2d_manager.set_state_true("music")

        # 更新动画参数
        new_duration = int(self.n_beats_per_cycle * self.audio_analyzer.period * 1000)
        if self.animation.duration() != new_duration:
            self.animation.setDuration(new_duration)

        if self.animation.state() != QtCore.QAbstractAnimation.State.Running:
            self.animation.start()

    def update_angle_y(self, t):
        """根据音频周期更新角度（镜像拼接 Sigmoid 实现循环）"""
        if self.audio_analyzer.period <= 0:
            return

        angle_y = math.cos(2 * math.pi / (1 / 2) * t)

        def swing_sigmoid(t, k = 30):
            if t < 0.5:
                return 2 * (1 / (1 + math.exp(- k * (t - 0.25))) - 0.5)
            else:
                return 2 * (1 - 1 / (1 + math.exp(- k * (t - 0.75))) - 0.5)
            
        angle_x = swing_sigmoid(t)

        # 更新模型参数
        if self.audio_analyzer.period < 0.8:
            self.l2d_manager.model_params["ParamAngleY"] = - 30 * angle_y
            self.l2d_manager.model_params["ParamAngleX"] = 30 * angle_x
            self.l2d_manager.model_params["ParamAngleZ"] = - 30 * angle_x  # Z轴同步X轴
            self.l2d_manager.model_params["ParamBodyAngleX"] = - 10 *  angle_x
        else:
            self.l2d_manager.model_params["ParamAngleZ"] = 20 * angle_x
            self.l2d_manager.model_params["ParamBodyAngleZ"] = 10 * angle_x

        self.l2d_widget.update()

    def open_message_window(self, message):
        """根据接收到的消息内容创建 MessageWindow"""
        message_window = MessageWindow(message, self.config_editor.message_size, self)  # 将消息传递给 MessageWindow
        message_window.destroyed.connect(lambda: self.popups.remove(message_window))
        self.popups.append(message_window)
        message_window.show()
    
    def update_message_position(self):
        for popup in self.popups:
            popup.update_position()