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

class Live2DWidget(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self, l2d_manager: Soyoc_l2d_manager.Live2DManager, config_editor: Soyoc_config.ConfigEditor) -> None:
        super().__init__()
        self.l2d_manager = l2d_manager
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.config_editor = config_editor
        self.config_editor.set_l2d_model_manager(self.l2d_manager)

        # 监听配置更新信号
        self.config_editor.config_updated.connect(self.on_config_updated)   # 连接信号 [[9]]

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

    def timerEvent(self, event: QtCore.QTimerEvent):
        self.update()
    
    # 新增鼠标事件传递
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super().mousePressEvent(event)  # 正常处理事件
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config_editor: Soyoc_config.ConfigEditor):
        super().__init__()
        self.config_editor: Soyoc_config.ConfigEditor = config_editor
        self.l2d_manager = Soyoc_l2d_manager.Live2DManager(self.config_editor)
        self.l2d_widget = Live2DWidget(self.l2d_manager, self.config_editor)
        self.n_beats_per_cycle = 4

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
        self.config_editor.config_updated.connect(self.update_size)   # 连接信号 [[9]]

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
        action1 = QtGui.QAction("设置", self)
        action2 = QtGui.QAction("节奏跟随", self)
        action2.setCheckable(True)  # 设置为复选框
        action2.setChecked(self.config_editor.beats_enable)  # 设置为当前状态
        action3 = QtGui.QAction("退出", self)

        # 设置字体大小
        font = QtGui.QFont()
        font.setPointSize(10)  # 设置字体大小为 10
        action1.setFont(font)
        action2.setFont(font)
        action3.setFont(font)

        # 连接动作到槽函数
        action1.triggered.connect(self.option_selected)
        action2.triggered.connect(self.beats_switch)
        action3.triggered.connect(self.close)

        # 将动作添加到菜单
        context_menu.addAction(action1)
        context_menu.addSeparator()  # 添加分隔符
        context_menu.addAction(action2)
        context_menu.addSeparator()  # 添加分隔符
        context_menu.addAction(action3)

        # 在鼠标右键点击的位置显示菜单
        context_menu.exec(event.globalPos())

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
        """播放随机点击动作"""
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
            self.l2d_manager.model_params["ParamAngleY"] = - 20 * angle_y
            self.l2d_manager.model_params["ParamAngleX"] = 20 * angle_x
            self.l2d_manager.model_params["ParamAngleZ"] = - 20 * angle_x  # Z轴同步X轴
            self.l2d_manager.model_params["ParamBodyAngleX"] = - 6 *  angle_x
        else:
            self.l2d_manager.model_params["ParamAngleZ"] = 10 * angle_x
            self.l2d_manager.model_params["ParamBodyAngleZ"] = 6 * angle_x

        self.l2d_widget.update()