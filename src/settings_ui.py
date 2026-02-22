import json
import os
import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QCheckBox, QPushButton, QFileDialog, 
                             QTabWidget, QWidget, QComboBox, QTextBrowser,
                             QSpinBox)
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config_path="modle/config.json"):
        super().__init__(parent)
        self.setWindowTitle("桌宠设置")
        self.resize(400, 300)
        self.config_path = config_path
        self.config = self.load_config()
        
        # 设置粉色主题
        self.setStyleSheet("""
            QDialog {
                background-color: #FFF0F5; /* LavenderBlush */
            }
            QLabel {
                font-family: "Microsoft YaHei";
                font-size: 14px;
                color: #333;
            }
            QPushButton {
                background-color: #FFB6C1; /* LightPink */
                border: 1px solid #FF69B4; /* HotPink */
                border-radius: 5px;
                padding: 5px 10px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
            QTabWidget::pane {
                border: 1px solid #FFB6C1;
                background-color: white;
            }
            QTabBar::tab {
                background: #FFE4E1; /* MistyRose */
                border: 1px solid #FFB6C1;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #FFB6C1;
                color: white;
            }
        """)

        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # --- 常规设置页 ---
        self.tab_general = QWidget()
        general_layout = QVBoxLayout()
        
        # 缩放设置
        scale_layout = QHBoxLayout()
        self.scale_label = QLabel(f"缩放比例: {self.config.get('pet_scale', 1.0):.1f}")
        scale_layout.addWidget(self.scale_label)
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(2, 50) # 0.2x to 5.0x
        self.scale_slider.setValue(int(self.config.get("pet_scale", 1.0) * 10))
        self.scale_slider.valueChanged.connect(self.update_scale_label)
        scale_layout.addWidget(self.scale_slider)
        general_layout.addLayout(scale_layout)
        
        # 透明度设置
        opacity_layout = QHBoxLayout()
        self.opacity_label = QLabel(f"透明度: {self.config.get('pet_opacity', 1.0):.1f}")
        opacity_layout.addWidget(self.opacity_label)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(2, 10) # 0.2 to 1.0
        self.opacity_slider.setValue(int(self.config.get("pet_opacity", 1.0) * 10))
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        general_layout.addLayout(opacity_layout)
        
        # 显示模式 (Display Priority)
        display_layout = QHBoxLayout()
        display_layout.addWidget(QLabel("显示模式:"))
        self.display_combo = QComboBox()
        self.display_combo.addItem("显示在最上层", "top")
        self.display_combo.addItem("仅在非全屏模式显示", "normal")
        self.display_combo.addItem("仅在桌面显示", "bottom")
        
        current_display = self.config.get("display_mode", "top")
        index = self.display_combo.findData(current_display)
        if index >= 0:
            self.display_combo.setCurrentIndex(index)
        display_layout.addWidget(self.display_combo)
        general_layout.addLayout(display_layout)

        # 开机自启
        self.autostart_check = QCheckBox("开机自动启动")
        self.autostart_check.setChecked(self.config.get("auto_start", False))
        general_layout.addWidget(self.autostart_check)

        # 专注时间设置 (分钟)
        focus_layout = QHBoxLayout()
        self.focus_label = QLabel("专注时长 (分钟):")
        focus_layout.addWidget(self.focus_label)
        
        self.focus_spin = QSpinBox()
        self.focus_spin.setRange(1, 180) # 1 - 180 分钟
        self.focus_spin.setValue(self.config.get("focus_minutes", 25))
        self.focus_spin.setSuffix(" 分钟") # 显示单位
        self.focus_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #FF69B4;
                border-radius: 5px;
            }
        """)
        focus_layout.addWidget(self.focus_spin)
        general_layout.addLayout(focus_layout)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型路径:"))
        self.model_path_btn = QPushButton("选择模型")
        self.model_path_btn.clicked.connect(self.choose_model)
        model_layout.addWidget(self.model_path_btn)
        general_layout.addLayout(model_layout)
        self.model_path = self.config.get("model_path", "")
        
        general_layout.addStretch()
        self.tab_general.setLayout(general_layout)
        self.tabs.addTab(self.tab_general, "常规设置")
        
        # --- 关于页 ---
        self.tab_about = QWidget()
        about_layout = QVBoxLayout()
        
        about_text = """
        <h2>HaiXiaoTang DesktopPet</h2>
        <p><b>版本:</b> 1.0.0</p>
        <p><b>作者:</b> Hilbert777</p>
        <p><b>描述:</b> 一个基于本地LLM的智能桌面宠物。</p>
        <p><b>GitHub:</b> <a href="https://github.com/Hilbert777">Hilbert777</a></p>
        <p><b>Bilibili:</b> <a href="https://space.bilibili.com/38380194">哈哈哈哈哈基鳄</a></p>
        <p><b>个人主页:</b> <a href="https://hilbert777.github.io/">Hilbert777</a></p>
        """
        self.about_browser = QTextBrowser()
        self.about_browser.setOpenExternalLinks(True)
        self.about_browser.setHtml(about_text)
        self.about_browser.setStyleSheet("background-color: transparent; border: none;")
        
        about_layout.addWidget(self.about_browser)
        self.tab_about.setLayout(about_layout)
        self.tabs.addTab(self.tab_about, "关于")
        
        main_layout.addWidget(self.tabs)
        
        # 保存按钮
        save_btn = QPushButton("保存并应用")
        save_btn.clicked.connect(self.save_settings)
        main_layout.addWidget(save_btn)
        
        self.setLayout(main_layout)

    def update_scale_label(self, value):
        self.scale_label.setText(f"缩放比例: {value / 10.0:.1f}")

    def update_opacity_label(self, value):
        self.opacity_label.setText(f"透明度: {value / 10.0:.1f}")

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding='utf-8') as f:
                return json.load(f)
        return {}

    def choose_model(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择GGUF模型文件", "", "GGUF Files (*.gguf);;All Files (*)")
        if file_name:
            self.model_path = file_name

    def save_settings(self):
        new_config = {
            "pet_scale": self.scale_slider.value() / 10.0,
            "pet_opacity": self.opacity_slider.value() / 10.0,
            "auto_start": self.autostart_check.isChecked(),
            "model_path": self.model_path,
            "focus_minutes": self.focus_spin.value(),
            "display_mode": self.display_combo.currentData()
        }
        
        # 保存到文件
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding='utf-8') as f:
            json.dump(new_config, f, indent=4)
            
        # 设置开机自启 (Windows)
        self.set_autostart(new_config["auto_start"])
        
        self.accept()
        
    def set_autostart(self, enable):
        if sys.platform != "win32":
            return
            
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "HaiXiaoTangPet"
        exe_path = sys.executable 
        # 注意：如果是脚本运行，这里可能需要指向 pythonw.exe + script path
        # 实际打包成exe后，sys.executable即为程序路径
        # 这里为了演示，假设是脚本路径，实际部署建议打包
        script_path = os.path.abspath(sys.argv[0])
        cmd = f'"{exe_path}" "{script_path}"'

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to set autostart: {e}")
