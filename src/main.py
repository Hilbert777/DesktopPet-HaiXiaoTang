import sys
import os
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer

# 确保src目录在路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pet_ui import PetUI
from settings_ui import SettingsDialog

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # 关闭窗口时不退出程序

    # 获取应用程序根目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        app_root = os.path.dirname(sys.executable)
    else:
        # 如果是脚本运行
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 绝对路径配置
    config_path = os.path.join(app_root, "modle", "config.json")
    
    # 创建宠物窗口
    pet = PetUI(config_path=config_path, app_root=app_root)
    pet.show()

    # 创建设置窗口
    settings_dialog = SettingsDialog(config_path=config_path)
    
    # 连接信号
    def show_settings():
        if settings_dialog.exec():
            # Apply changes
            pet.reload_settings()

    pet.open_settings.connect(show_settings)

    # 系统托盘图标
    tray_icon = QSystemTrayIcon(app)
    
    # 使用 3.png 作为图标
    icon_path = os.path.join(app_root, "image", "3.png")

    if os.path.exists(icon_path):
        tray_icon.setIcon(QIcon(icon_path))
    else:
        # 兜底
        print(f"Icon not found at {icon_path}")
        pass
        
    tray_menu = QMenu()
    
    show_action = QAction("显示桌宠", app)
    show_action.triggered.connect(pet.show)
    
    hide_action = QAction("隐藏桌宠", app)
    hide_action.triggered.connect(pet.hide)
    
    setting_action = QAction("设置", app)
    setting_action.triggered.connect(show_settings)
    
    quit_action = QAction("退出", app)
    quit_action.triggered.connect(app.quit)
    
    tray_menu.addAction(show_action)
    tray_menu.addAction(hide_action)
    tray_menu.addSeparator()
    tray_menu.addAction(setting_action)
    tray_menu.addAction(quit_action)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    
    # 将 sys.exit 放到这里，确保 QApplication 在 main 中完全控制生命周期
    exit_code = app.exec()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
