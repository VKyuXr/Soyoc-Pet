import markdown
import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets
import PySide6.QtCore as QtCore
import Soyoc_core.Soyoc_utils.API_requster as Soyoc_API_requester

class MessageBubble(QtWidgets.QFrame):
    def __init__(self, text, align_right = False, tokens_info = None, parent = None):
        super().__init__(parent)
        self.align_right = align_right

        # 将 Markdown 转换为 HTML
        html_content = markdown.markdown(text)

        # 主布局
        layout = QtWidgets.QVBoxLayout(self)  # 使用垂直布局管理器
        layout.setContentsMargins(0, 0, 0, 0)  # 去除默认边距
        layout.setSpacing(5)  # 设置组件之间的间距

        # 消息气泡部分
        bubble_layout = QtWidgets.QHBoxLayout()  # 水平布局用于气泡对齐
        bubble_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(QtCore.Qt.TextFormat.RichText)  # 启用富文本支持
        self.label.setText(html_content)

        # 样式表：保留原有样式并添加 Markdown 样式
        self.label.setStyleSheet("""
            background: #666666;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-family: "Microsoft YaHei";
        """)

        if align_right:
            bubble_layout.addStretch()  # 右对齐时，左侧添加拉伸
        bubble_layout.addWidget(self.label)
        if not align_right:
            bubble_layout.addStretch()  # 左对齐时，右侧添加拉伸

        # 小字部分（仅当 align_right=False 时显示）
        self.sub_label = QtWidgets.QLabel(tokens_info)  # 默认小字内容
        self.sub_label.setStyleSheet("""
            color: gray;
            font-size: 10px;
            margin-left: 10px;  /* 仅左对齐时需要左边距 */
        """)
        self.sub_label.setVisible(not align_right)  # 仅在左对齐时显示

        # 添加到主布局
        layout.addLayout(bubble_layout)  # 添加气泡部分
        layout.addWidget(self.sub_label)  # 添加小字部分

    def resizeEvent(self, event):
        """动态调整宽度并保持HTML内容自适应"""
        self.label.setFixedWidth(int(self.width() * 0.7))
        super().resizeEvent(event)

class MessageManager:
    def __init__(self, system_prompt: str):
        self.messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]
    
    def append_user_content(self, content: str):
        self.messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

    def append_assistant_content(self, content: str):
        self.messages.append(
            {
                "role": "assistent",
                "content": content
            }
        )
    
    def get_messages(self):
        return self.messages
    
    def clear(self):
        self.messages = []

class APIWorker(QtCore.QObject):
    result = QtCore.Signal(str, str)
    finished = QtCore.Signal()

    def __init__(self, api_requester, messages):
        super().__init__()
        self.api_requester = api_requester
        self.messages = messages

    def run(self):
        try:
            reply, tokens = self.api_requester.request_API(self.messages)
            self.result.emit(reply, tokens)
        finally:
            self.finished.emit()

class ChatWindow(QtWidgets.QWidget):
    reply_received = QtCore.Signal(str)
    api_response = QtCore.Signal(str, str)  # 新增响应信号

    def __init__(self, config_editor):
        super().__init__()
        self.config_editer = config_editor
        self.init_ui()
        self.drag_pos = None
        self.message_manager = MessageManager(self.config_editer.system_prompt)
        self.api_requester = Soyoc_API_requester.APIRequster(self.config_editer)
        self.waiting_bubble = None  # 新增等待气泡引用

        self.reply_received.connect(self.add_reply_message)
        self.api_response.connect(self.handle_api_result)  # 连接新信号

    def init_ui(self):
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(200, 200, 600, 600)
        self.setWindowOpacity(0.95)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        # main_layout.setContentsMargins(5, 5, 5, 5)
        # main_layout.setSpacing(5)

        # 标题栏
        self.header = self.create_header()
        main_layout.addWidget(self.header)

        # 消息区域
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.content = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content)
        self.content_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        # self.content_layout.setSpacing(10)
        self.scroll_area.setWidget(self.content)
        main_layout.addWidget(self.scroll_area)

        # 输入区域
        self.footer = self.create_footer()
        main_layout.addWidget(self.footer)

    def create_header(self):
        header = QtWidgets.QWidget()
        header.setFixedHeight(40)
        layout = QtWidgets.QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QtWidgets.QLabel("对话窗口")
        title.setFont(QtGui.QFont("Microsoft YaHei", 16))
        title.setContentsMargins(5, 0, 0, 0)
        
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.setFont(QtGui.QFont("Microsoft YaHei", 12))
        close_btn.setFixedSize(60, 30)
        close_btn.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addWidget(close_btn)
        return header

    def create_footer(self):
        footer = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(footer)
        layout.setContentsMargins(0, 0, 0, 0)

        btn_extra = QtWidgets.QPushButton("选项")
        btn_extra.setFont(QtGui.QFont("Microsoft YaHei", 12))
        btn_extra.setFixedSize(80, 40)
        
        self.input_box = QtWidgets.QTextEdit()
        self.input_box.setPlaceholderText("输入消息...")
        self.input_box.setMinimumHeight(40)
        self.input_box.setMaximumHeight(100)
        self.input_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.input_box.textChanged.connect(self.adjust_input_height)

        self.send_button = QtWidgets.QPushButton("发送")  # 记录按钮引用
        self.send_button.setFont(QtGui.QFont("Microsoft YaHei", 12))
        self.send_button.setFixedSize(80, 40)
        self.send_button.clicked.connect(self.send_message)

        layout.addWidget(btn_extra, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.input_box)
        layout.addWidget(self.send_button, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)

        QtCore.QTimer.singleShot(0, self.initial_adjust_height)
        return footer
    
    def initial_adjust_height(self):
        """初始高度调整"""
        self.adjust_input_height()
        # 强制布局更新
        self.footer.layout().invalidate()
        self.footer.updateGeometry()

    def adjust_input_height(self):
        """优化后的高度计算"""
        doc = self.input_box.document()
        height = doc.size().height() + 2 * doc.documentMargin()
        
        # 增加字体高度补偿（更精确的计算）
        font_metrics = QtGui.QFontMetrics(doc.defaultFont())
        line_height = font_metrics.lineSpacing()
        min_lines = max(1, int(height / line_height))
        
        # 动态计算理想高度
        ideal_height = line_height * min_lines + 2 * doc.documentMargin()
        new_height = min(max(ideal_height, 40), 100)
        
        if self.input_box.height() != new_height:
            self.input_box.setFixedHeight(new_height)
            # 延迟布局更新
            QtCore.QTimer.singleShot(10, self.update_footer_layout)

    def update_footer_layout(self):
        """更新底部布局"""
        self.footer.layout().activate()
        self.update()

    # 新增方法：添加回复消息
    def add_reply_message(self, text):
        """ 外部通过信号发送消息时调用 """
        self.content_layout.addWidget(MessageBubble(f"{text}", False))
        self.scroll_to_bottom()

    def send_message(self):
        text = self.input_box.toPlainText().strip()
        self.input_box.clear()
        if not text:
            return

        # 添加用户消息
        self.content_layout.addWidget(MessageBubble(text, True))
        self.message_manager.append_user_content(text)
        
        # 添加等待气泡并禁用按钮
        self.send_button.setEnabled(False)
        self.waiting_bubble = MessageBubble("正在思考中...", False, "等待响应...")
        self.content_layout.addWidget(self.waiting_bubble)
        self.scroll_to_bottom()

        # 启动线程执行API请求
        self.start_api_thread()

    def start_api_thread(self):
        # 创建工作者线程
        self.thread = QtCore.QThread()
        self.worker = APIWorker(self.api_requester, self.message_manager.get_messages())
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.result.connect(self.handle_api_result)
        
        self.thread.start()

    def handle_api_result(self, reply_message, tokens_info):
        # 移除等待气泡
        if self.waiting_bubble:
            self.content_layout.removeWidget(self.waiting_bubble)
            self.waiting_bubble.deleteLater()
            self.waiting_bubble = None
            
        # 添加助理回复
        self.content_layout.addWidget(MessageBubble(reply_message, False, tokens_info))
        self.message_manager.append_assistant_content(reply_message)
        self.scroll_to_bottom()
        
        # 重新启用发送按钮
        self.send_button.setEnabled(True)

    def scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # 窗口拖动功能
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.header.underMouse():
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.drag_pos:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.pos() + delta)
            self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None