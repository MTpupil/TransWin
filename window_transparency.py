import customtkinter as ctk
import win32gui
import win32con
import json
import os

class WindowTransparency:
    def __init__(self):
        self.windows = []
        self.selected_window = None
        self.config_file = os.path.join(os.path.dirname(__file__), 'transparency_config.json')
        
        # 创建主窗口
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("窗口透明度调节工具")
        self.root.geometry("400x500")
        
        # 窗口列表
        self.window_label = ctk.CTkLabel(self.root, text="选择窗口")
        self.window_label.pack(pady=5)
        
        self.window_frame = ctk.CTkScrollableFrame(self.root, height=200)
        self.window_frame.pack(fill="both", expand=True, padx=10, pady=5)
        

        
        # 窗口列表标签
        self.window_list_labels = []
        
        # 刷新按钮
        # 按钮容器
        self.button_frame = ctk.CTkFrame(self.root)
        self.button_frame.pack(pady=10)
        
        # 刷新按钮
        self.refresh_button = ctk.CTkButton(self.button_frame, text="刷新窗口列表", command=self.refresh_windows)
        self.refresh_button.pack(pady=0, side="left", padx=5)
        
        # 清除所有透明度按钮
        self.clear_button = ctk.CTkButton(self.button_frame, text="清除所有透明度", command=self.clear_all_transparency)
        self.clear_button.pack(pady=0, side="left", padx=5)
        
        # 滑块容器
        self.slider_frame = ctk.CTkFrame(self.root)
        self.slider_frame.pack(fill="x", padx=20, pady=(10,0))
        
        # 透明度滑块
        self.transparency_label = ctk.CTkLabel(self.slider_frame, text="透明度调节")
        self.transparency_label.pack(pady=(0,5))
        
        self.transparency_scale = ctk.CTkSlider(self.slider_frame, from_=0.1, to=1.0, command=self.set_transparency)
        self.transparency_scale.set(1.0)
        self.transparency_scale.pack(fill="x", pady=(0,20))
        
        # 透明度百分比显示
        self.percentage_label = ctk.CTkLabel(self.root, text="100%", font=("Arial", 14))
        self.percentage_label.pack(pady=(0,20))
        
        # 加载配置
        self.load_config()
        
        # 绑定事件
        # 不需要绑定事件，改为点击标签选择窗口
        
        # 初始刷新窗口列表
        self.refresh_windows()
        
        # 移除应用按钮，改为滑块实时调节
        self.transparency_scale.bind('<ButtonRelease-1>', lambda e: self.save_config())
    
    def refresh_windows(self):
        """刷新窗口列表"""
        self.windows = []
        for label in self.window_list_labels:
            label.destroy()
        self.window_list_labels = []
        
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                # 检查窗口样式，过滤掉无窗口应用
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                if not (style & (win32con.WS_OVERLAPPED | win32con.WS_POPUP)):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        self.windows.append({"hwnd": hwnd, "title": title})
                        label = ctk.CTkLabel(self.window_frame, text=title, cursor="hand2")
                        label.pack(fill="x", pady=2)
                        label.bind("<Button-1>", lambda e, h=hwnd, t=title: self.on_window_click(h, t))
                        self.window_list_labels.append(label)
        
        win32gui.EnumWindows(enum_windows_callback, None)
    
    def on_window_click(self, hwnd, title):
        """窗口点击事件"""
        self.selected_window = {"hwnd": hwnd, "title": title}
        self.window_label.configure(text=f"当前窗口: {title}")
        
        # 检查是否有该窗口的透明度记录
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    if "windows" in config and str(hwnd) in config["windows"]:
                        self.transparency_scale.set(config["windows"][str(hwnd)]["transparency"])
                        return
            except:
                pass
        
        # 默认透明度为1.0
        self.transparency_scale.set(1.0)
    
    def set_transparency(self, value):
        """设置窗口透明度"""
        if self.selected_window:
            try:
                hwnd = self.selected_window["hwnd"]
                alpha = int(float(value) * 255)
                
                # 设置窗口样式
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style | win32con.WS_EX_LAYERED)
                win32gui.SetLayeredWindowAttributes(hwnd, 0, alpha, win32con.LWA_ALPHA)
                
                # 更新百分比显示
                percentage = int(float(value) * 100)
                self.percentage_label.configure(text=f"{percentage}%")
                
                # 保存配置
                self.save_config()
            except Exception as e:
                print(f"设置透明度失败: {e}")
    
    def save_config(self):
        """保存配置"""
        if self.selected_window:
            config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                        if "windows" not in config:
                            config["windows"] = {}
                except:
                    config = {"windows": {}}
            else:
                config = {"windows": {}}
            
            # 更新当前窗口的透明度设置
            hwnd = str(self.selected_window["hwnd"])
            config["windows"][hwnd] = {
                "title": self.selected_window["title"],
                "transparency": float(self.transparency_scale.get())
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
    
    def clear_all_transparency(self):
        """清除所有窗口的透明度设置"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.transparency_scale.set(1.0)
        self.percentage_label.configure(text="100%")
        if self.selected_window:
            try:
                hwnd = self.selected_window["hwnd"]
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                                     win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & ~win32con.WS_EX_LAYERED)
            except Exception as e:
                print(f"清除透明度失败: {e}")
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                    # 设置透明度滑块
                    if "windows" in config and str(self.selected_window["hwnd"]) in config["windows"]:
                        self.transparency_scale.set(config["windows"][str(self.selected_window["hwnd"])]["transparency"])
            except:
                pass
    
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = WindowTransparency()
    app.run()