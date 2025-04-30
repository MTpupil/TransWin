import customtkinter as ctk
import win32gui
import win32con
import json
import os


from pynput import mouse, keyboard
import threading

class WindowTransparency:
    def __init__(self):
        self.windows = []
        self.selected_window = None
        self.config_file = os.path.join(os.getenv('APPDATA'), 'TransWin', 'TransWin_config.json')
        
        # 创建主窗口
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("TransWin by.MTpupil")
        self.root.geometry("400x500")
        # 设置窗口图标，如果不存在则使用默认
        icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
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
        
        # 热键开关
        self.hotkey_frame = ctk.CTkFrame(self.root)
        self.hotkey_frame.pack(fill="x", padx=20, pady=(10,0))
        
        self.hotkey_label = ctk.CTkLabel(self.hotkey_frame, text="Ctrl+滚轮调节透明度", font=("Arial", 12))
        self.hotkey_label.pack(side="left", padx=(0,10))
        
        self.hotkey_switch = ctk.CTkSwitch(self.hotkey_frame, text="", width=100, height=20, switch_width=40, switch_height=20,
                                          command=lambda: self.save_config())
        self.hotkey_switch.pack(side="left")
        
        # 启动热键监听线程
        self.hook_manager = None
        self.hook_thread = None
        self.start_hotkey_listener()
        
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
                percentage = int(float(value) * 100)
                
                # 设置窗口样式
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                # 清除之前的WS_EX_TRANSPARENT样式
                style &= ~win32con.WS_EX_TRANSPARENT
                # 当透明度低于等于15%时，启用鼠标穿透
                if percentage <= 15:
                    style |= win32con.WS_EX_TRANSPARENT
                
                # 设置窗口样式和透明度
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style | win32con.WS_EX_LAYERED)
                win32gui.SetLayeredWindowAttributes(hwnd, 0, alpha, win32con.LWA_ALPHA)
                
                # 更新百分比显示
                self.percentage_label.configure(text=f"{percentage}%")
                
                # 保存配置
                self.save_config()
            except Exception as e:
                print(f"设置透明度失败: {e}")
    
    def save_config(self):
        """保存配置"""
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
        if self.selected_window:
            hwnd = str(self.selected_window["hwnd"])
            config["windows"][hwnd] = {
                "title": self.selected_window["title"],
                "transparency": float(self.transparency_scale.get())
            }
        
        # 保存热键开关状态
        if hasattr(self, 'hotkey_switch'):
            config["hotkey_enabled"] = 1 if self.hotkey_switch.get() else 0
            # 确保即使没有选中窗口也会保存开关状态
            if "windows" not in config:
                config["windows"] = {}
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
            # 强制更新文件修改时间
            os.utime(self.config_file, None)
    
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
                    
                    # 设置热键开关状态
                    if "hotkey_enabled" in config:
                        if config["hotkey_enabled"]:
                            self.hotkey_switch.select()
                        else:
                            self.hotkey_switch.deselect()
                    
                    # 设置透明度滑块
                    if "windows" in config and self.selected_window and str(self.selected_window["hwnd"]) in config["windows"]:
                        self.transparency_scale.set(config["windows"][str(self.selected_window["hwnd"])]["transparency"])
            except Exception as e:
                print(f"加载配置失败: {e}")
    
    def run(self):
        self.root.mainloop()
        
    def start_hotkey_listener(self):
        """启动热键监听线程"""
        def on_move(x, y):
            pass
            
        def on_click(x, y, button, pressed):
            pass
            
        def on_scroll(x, y, dx, dy):
            if not self.hotkey_switch.get():
                return
                
            if hasattr(self, 'ctrl_pressed') and self.ctrl_pressed:
                def enum_child_windows(parent_hwnd, child_windows):
                    def callback(hwnd, _):
                        if win32gui.IsWindowVisible(hwnd):
                            child_windows.append(hwnd)
                        return True
                    win32gui.EnumChildWindows(parent_hwnd, callback, None)
                
                # 获取鼠标位置下的窗口句柄
                hwnd = win32gui.WindowFromPoint((x, y))
                if hwnd:
                    # 获取所有相关窗口句柄
                    windows = [hwnd]
                    # 获取父窗口
                    parent = win32gui.GetParent(hwnd)
                    while parent and parent != 0:
                        windows.append(parent)
                        parent = win32gui.GetParent(parent)
                    # 获取子窗口
                    child_windows = []
                    enum_child_windows(hwnd, child_windows)
                    windows.extend(child_windows)
                    
                    # 遍历所有窗口，找到第一个非透明的窗口
                    target_hwnd = None
                    for window in windows:
                        if win32gui.IsWindowVisible(window):
                            style = win32gui.GetWindowLong(window, win32con.GWL_EXSTYLE)
                            if not (style & win32con.WS_EX_TRANSPARENT):
                                target_hwnd = window
                                break
                    
                    # 如果找不到非透明窗口，使用顶级窗口
                    if not target_hwnd:
                        target_hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
                    
                    current_value = self.transparency_scale.get()
                    if dy > 0:
                        new_value = min(1.0, current_value + 0.05)
                    else:
                        new_value = max(0.1, current_value - 0.05)
                    
                    self.selected_window = {"hwnd": target_hwnd, "title": win32gui.GetWindowText(target_hwnd)}
                    self.window_label.configure(text=f"当前窗口: {win32gui.GetWindowText(target_hwnd)}")
                    self.transparency_scale.set(new_value)
                    self.set_transparency(new_value)
                    # 清除选中的窗口，这样下次滚轮时会重新获取鼠标位置下的窗口
                    self.selected_window = None
        
        def on_press(key):
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
        
        def on_release(key):
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
        
        self.mouse_listener = mouse.Listener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll)
            
        self.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release)
            
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
    

if __name__ == '__main__':
    app = WindowTransparency()
    app.run()