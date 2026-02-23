import sys
import os
import json
import random
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QMenu, 
                             QApplication, QGraphicsDropShadowEffect, QLineEdit)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QThread, QRect, QTime
from PySide6.QtGui import QPixmap, QCursor, QAction, QColor, QFont, QGuiApplication
from llm_client import LLMClient

# 自定义聊天输入框
class ChatInput(QLineEdit):
    submit_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 去掉独立的 Window 标志，使其成为真正的子控件
        self.setWindowFlags(Qt.WindowType.SubWindow)
        self.setPlaceholderText("想对我说什么？(回车发送)")
        self.setStyleSheet("""
            QLineEdit {
                background-color: #FFC0CB; /* 粉色背景 */
                color: #333;
                border: 2px solid #FF69B4; /* 深粉色边框 */
                border-radius: 15px;
                padding: 0 10px; /* 调整padding，垂直方向由高度决定，水平留空 */
                font-family: "Microsoft YaHei";
                font-size: 14px; /* 字体稍微大一点更清晰 */
            }
        """)
        self.setFixedSize(320, 40) # 加宽输入框
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            text = self.text().strip()
            if text:
                self.submit_signal.emit(text)
            self.hide()
            self.clear()
        elif event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.clear()
        else:
            super().keyPressEvent(event)
            
    def focusOutEvent(self, event):
        # 失去焦点时自动隐藏
        self.hide()
        super().focusOutEvent(event)

    def show_at(self, pos):
        # pos 是相对于父窗口的坐标（如果作为子控件）
        # 但因为是绝对定位，我们直接 move
        self.move(pos)
        self.show()
        self.setFocus()
        self.raise_() # 确保在最上层

# 对话线程，防止界面卡顿
class ChatThread(QThread):
    response_ready = Signal(str)

    def __init__(self, llm_client, user_input):
        super().__init__()
        self.llm_client = llm_client
        self.user_input = user_input

    def run(self):
        if self.llm_client:
            response = self.llm_client.chat(self.user_input)
            self.response_ready.emit(response)

class PetUI(QWidget):
    open_settings = Signal() # 信号：打开设置

    def __init__(self, config_path="modle/config.json", app_root=None):
        super().__init__()
        self.app_root = app_root if app_root else os.getcwd()
        self.config_path = config_path
        self.load_config()

        # 初始化UI
        self.init_ui()
        
        # 状态变量
        self.is_dragging = False
        self.drag_position = QPoint()
        
        # 初始化LLM
        self.llm_client = LLMClient(self.config.get("model_path", ""))
        # 异步加载模型，避免启动卡顿
        QTimer.singleShot(1000, self.init_llm)

        # 初始化聊天输入框
        # 此处 parent = self，意味着它是 PetUI 的直接子控件
        self.chat_input = ChatInput(self) 
        self.chat_input.submit_signal.connect(self.start_chat_thread)

    def load_config(self):
        # 待机动作定时器
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.update_idle_animation)
        self.idle_timer.start(10000) # 10秒切换一次
        
        # 初始动作的调用移到 init_ui 的最后，防止UI元素未创建
        
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {"pet_scale": 1.0, "pet_opacity": 1.0, "model_path": "", "display_mode": "top"}

        # --- 自动路径修复逻辑 ---
        current_model_path = self.config.get("model_path", "")
        
        # 1. 尝试将相对路径转换为绝对路径
        if current_model_path and not os.path.isabs(current_model_path):
             current_model_path = os.path.join(self.app_root, current_model_path)

        # 2. 如果路径不存在或为空，尝试在默认目录(app_root/modle)下自动搜索 .gguf 文件
        if not current_model_path or not os.path.exists(current_model_path):
            default_model_dir = os.path.join(self.app_root, "modle")
            if os.path.exists(default_model_dir):
                for file in os.listdir(default_model_dir):
                    if file.endswith(".gguf"):
                        # 找到第一个 gguf 文件作为默认模型
                        found_path = os.path.join(default_model_dir, file)
                        print(f"Auto-detected model: {found_path}")
                        current_model_path = found_path
                        # 更新配置(内存中更新)
                        self.config["model_path"] = current_model_path
                        # 同时保存一次配置，确保持久化修正
                        self.save_config() 
                        break
        
        # 确保传给 LLMClient 的是更新后的绝对路径
        if current_model_path:
             self.config["model_path"] = os.path.normpath(current_model_path)
             
    def save_config(self):
        """保存当前配置到文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def init_llm(self):
        print("Loading LLM...")
        if self.llm_client.load_model():
            self.show_bubble("我醒啦！随时可以找我聊天哦~")
        else:
            self.show_bubble("找不到大脑(模型)... 请在设置里检查路径。")

    def apply_window_flags(self):
        """根据配置应用窗口标志"""
        mode = self.config.get("display_mode", "top")
        
        # 基础标志: 无边框, 工具窗口
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        
        if mode == "top":
            flags |= Qt.WindowType.WindowStaysOnTopHint
        elif mode == "bottom":
             # 尝试设置在底层
             if hasattr(Qt.WindowType, "WindowStaysOnBottomHint"):
                 flags |= Qt.WindowType.WindowStaysOnBottomHint
        elif mode == "normal":
            # 普通窗口层级
            pass
            
        self.setWindowFlags(flags)
        
        # 如果当前是可见状态，更改flags后需要重新show才会生效
        if self.isVisible():
            self.show()

    def init_ui(self):
        # 应用窗口属性
        self.apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 布局
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # 默认位置：右下角
        screen = QGuiApplication.primaryScreen().availableGeometry()
        # 初始大小还没确定，先给个大概位置，稍后在 update_appearance 里微调
        self.move(screen.width() - 250, screen.height() - 250)

        # 气泡框 (默认隐藏)
        self.bubble = QLabel(self)
        self.bubble.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 192, 203, 220); /* 浅粉色背景 */
                border-radius: 10px;
                padding: 10px;
                color: black;
                font-family: "Microsoft YaHei";
                border: 1px solid #FF69B4; /* 深粉色边框 */
            }
        """)
        self.bubble.setWordWrap(True)
        self.bubble.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.bubble.hide()
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(2, 2)
        self.bubble.setGraphicsEffect(shadow)
        
        # 宠物图片
        self.image_label = QLabel(self)
        default_img = self.get_image_path("default.png")
        self.original_pixmap = QPixmap(default_img) # 默认图片
        # 初始Fallback，防止无图
        if self.original_pixmap.isNull():
             self.img_fallback()

        self.update_appearance()
        # 将气泡添加到布局最上方，并设置对齐方式
        self.layout.insertWidget(0, self.bubble, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        # 限制气泡最大宽度，确保自动换行生效
        self.bubble.setMaximumWidth(300)
        # 设置气泡最小宽度，防止太窄
        self.bubble.setMinimumWidth(150)
        
        # 气泡定时器
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.bubble.hide)
        
        # 将图片添加到布局底部
        self.layout.addWidget(self.image_label, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        
        # 初始化专注模式UI
        self.init_focus_ui()
        
        # 初始动作
        self.update_idle_animation()

    def init_focus_ui(self):
        # 专注倒计时标签
        self.focus_label = QLabel(self)
        self.focus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.focus_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 105, 180, 200); /* 深粉色背景 */
                color: white;
                border-radius: 12px;
                padding: 5px 15px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid white;
            }
        """)
        self.focus_label.hide()
        
        # 专注模式定时器
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.update_focus_timer)
        self.focus_remaining_seconds = 0
        
        # 添加到布局顶部 (气泡上方)
        self.layout.insertWidget(0, self.focus_label, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

    def start_focus_timer(self):
        """开启/关闭专注模式"""
        if self.focus_timer.isActive():
            # 停止
            self.focus_timer.stop()
            self.focus_label.hide()
            self.show_bubble("专注结束啦！要注意劳逸结合哦~")
            self.adjustSize()
        else:
            # 开始
            minutes = self.config.get("focus_minutes", 25)
            self.focus_remaining_seconds = minutes * 60
            self.update_focus_display()
            self.focus_label.show()
            self.focus_timer.start(1000) # 每秒更新
            self.show_bubble(f"开始专注！加油坚持 {minutes} 分钟哦！")
            # 几秒后隐藏气泡，只留倒计时
            QTimer.singleShot(3000, self.bubble.hide)
            self.adjustSize()
            
    def update_focus_timer(self):
        self.focus_remaining_seconds -= 1
        if self.focus_remaining_seconds <= 0:
            self.focus_timer.stop()
            self.focus_label.hide()
            self.show_bubble("好棒！专注目标达成！✿✿ヽ(°▽°)ノ✿")
            # 播放庆祝动画或音效
            self.set_chatting_animation()
            QTimer.singleShot(5000, self.resume_idle_animation)
        else:
            self.update_focus_display()
            
    def update_focus_display(self):
        minutes = self.focus_remaining_seconds // 60
        seconds = self.focus_remaining_seconds % 60
        self.focus_label.setText(f"{minutes:02d}:{seconds:02d}")

    def get_image_path(self, filename):
        return os.path.join(self.app_root, "image", filename)

    def update_appearance(self):
        scale = self.config.get("pet_scale", 1.0)
        opacity = self.config.get("pet_opacity", 1.0)
        
        if self.original_pixmap and not self.original_pixmap.isNull():
             # 限制基准大小：如果原图宽度超过 300px，则将其视为 1.0 倍缩放的基准
             # 这样可以防止高清原图直接填满屏幕
             base_width = self.original_pixmap.width()
             base_height = self.original_pixmap.height()
             
             MAX_BASE_WIDTH = 200 # 默认大小调小
             if base_width > MAX_BASE_WIDTH:
                 factor = MAX_BASE_WIDTH / base_width
                 base_width = int(base_width * factor)
                 base_height = int(base_height * factor)
             
             # 在限制后的基准大小上再应用用户的缩放设置
             width = int(base_width * scale)
             height = int(base_height * scale)
             
             scaled_pixmap = self.original_pixmap.scaled(
                width, height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
             )
             self.image_label.setPixmap(scaled_pixmap)
             self.setWindowOpacity(opacity)
             
             # 确保窗口宽度至少能容纳聊天输入框 (320px + margin)
             min_width = 340 
             final_width = max(width, min_width)
             
             self.resize(final_width, height + 50) # +50 for bubble space
             
             # 如果图片比窗口窄，需要确保图片居中 (layout 已经设置了 AlignHCenter，所以只要窗口够大就行)
    
    def on_llm_response(self, response):
        print(f"LLM Response: {response}") # 打印到终端调试
        if not response:
            response = "..."
        
        # 移除重复定义的 on_llm_response
        self.show_bubble(response)
        # 收到回复后，恢复待机动画
        QTimer.singleShot(3000, self.resume_idle_animation)

    def img_fallback(self):
        # 如果没有图片，创建一个简单的占位符
        self.original_pixmap = QPixmap(100, 100)
        self.original_pixmap.fill(Qt.GlobalColor.transparent)
        # 画一个圆
        from PySide6.QtGui import QPainter, QBrush
        painter = QPainter(self.original_pixmap)
        painter.setBrush(QBrush(Qt.GlobalColor.cyan))
        painter.drawEllipse(10, 10, 80, 80)
        painter.end()


    def load_image(self, path):
         """加载图片并更新显示"""
         if os.path.exists(path):
             self.original_pixmap = QPixmap(path)
         else:
             if self.original_pixmap.isNull():
                  self.img_fallback()
         self.update_appearance()

    def update_idle_animation(self):
         """更新待机动作 (1-8.png)"""
         # 定义待机动作列表
         idle_images = [f"{i}.png" for i in range(1, 8)]
         
         # 随机选择一个
         selected_img = random.choice(idle_images)
         img_path = self.get_image_path(selected_img)
         self.load_image(img_path)
         
         # 特殊彩蛋：当随机到 3.png 时显示 Ciallo
         if selected_img == "3.png":
             self.show_bubble("Ciallo～(∠・ω< )⌒★")

    def set_chatting_animation(self):
        """设置对话动作 (随机使用 9.png 或 12.png)"""
        chat_img = random.choice(["9.png", "12.png"])
        self.load_image(self.get_image_path(chat_img))
        # 对话期间暂停待机动画切换
        self.idle_timer.stop()
        
    def resume_idle_animation(self):
        """恢复待机动作"""
        self.idle_timer.start(10000)
        self.update_idle_animation()

    def show_bubble(self, text, duration=5000):
        self.bubble.setText(text)
        
        # 强制单行时不换行，多行时才换行，并预留缓冲空间
        # 简单的 adjustSize 有时在无边框窗口下计算不准
        fm = self.bubble.fontMetrics()
        width = fm.horizontalAdvance(text) + 40 # 加上padding
        
        if width > 300:
            self.bubble.setFixedWidth(300) # 固定最大宽，让它自己换行
            self.bubble.setWordWrap(True)
        else:
            self.bubble.setFixedWidth(max(100, width)) # 动态宽度
            self.bubble.setWordWrap(False) # 短文本不换行
            
        self.bubble.adjustSize()
        self.adjustSize()
        
        # 确保气泡完全可见
        self.bubble.show()
        self.bubble_timer.start(duration)

    # --- 鼠标事件处理 (拖动 & 点击) ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False

    # def on_llm_response(self, response):  <-- Removed duplicate
    #     self.show_bubble(response)
    #     QTimer.singleShot(3000, self.resume_idle_animation)

    def start_chat_thread(self, text):
        self.chat_thread = ChatThread(self.llm_client, text)
        self.chat_thread.response_ready.connect(self.on_llm_response)
        self.chat_thread.start()

    def mouseDoubleClickEvent(self, event):
        # 双击触发对话示例
        if event.button() == Qt.MouseButton.LeftButton:
            # 切换到对话动画
            self.set_chatting_animation()
            
            # 每次打开聊天输入框时，强制隐藏当前的气泡，防止重叠
            self.bubble.hide()
            
            # 将输入框直接放置在顶部 (0, 0) 下方一点，覆盖气泡位置
            # 由于现在是子控件，坐标是相对于 self (窗口内部左上角为 0,0)
            # 假设窗口高度足以容纳 input
            
            # 计算水平居中
            input_width = self.chat_input.width()
            x = (self.width() - input_width) // 2
            
            # 放置在顶部区域 (气泡可能会被遮挡，或者设计成在气泡下方)
            # 用户要求 "显示在桌宠头上方"，这通常意味着在气泡的位置
            y = 20 # 距离顶部 20px
            
            self.chat_input.show_at(QPoint(x, y))
            
            # 如果取消输入（比如按ESC），需要恢复待机动画，这里简单处理：如果是输入框隐藏了但没发消息，
            # 可以通过重写 ChatInput 的 hideEvent 来通知，或者简单起见，如果几秒没操作就恢复
            # 这里依赖输入后的回调或超时

    def show_context_menu(self, pos):
        menu = QMenu()
        
        chat_action = QAction("聊天", self)
        chat_action.triggered.connect(lambda: self.mouseDoubleClickEvent(
            type("Event", (object,), {"button": lambda: Qt.MouseButton.LeftButton})
        ))
        
        # 专注模式
        focus_text = "结束专注" if hasattr(self, "focus_timer") and self.focus_timer.isActive() else "开启专注"
        focus_action = QAction(focus_text, self)
        focus_action.triggered.connect(self.start_focus_timer)

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings.emit)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        
        menu.addAction(chat_action)
        menu.addSeparator()
        menu.addAction(focus_action)
        menu.addAction(settings_action)
        menu.addAction(quit_action)
        
        # 设置菜单样式
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #FF69B4;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                color: #333;
            }
            QMenu::item:selected {
                background-color: #FFC0CB;
            }
        """)
        
        menu.exec(pos)

    def reload_settings(self):
        """重新加载设置并应用"""
        self.load_config()
        self.update_appearance()
        self.apply_window_flags()
        # 如果模型路径变了，可能需要重载模型（这里暂不实现自动重载，需重启）
