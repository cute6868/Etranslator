import tkinter as tk
from tkinter import messagebox
import webbrowser
import http.server
import socketserver
import threading
import os
import configparser
import sys

# 全局变量，用于存储服务器线程和服务器实例
server_thread = None
httpd = None


def get_resource_path(relative_path):
    """获取资源（图标、HTML 文件夹等）的正确路径，兼容开发和打包环境"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后路径
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_config():
    global PORT, HOST
    config_dir = get_resource_path('config')
    config_path = os.path.join(config_dir, 'config.ini')
    config = configparser.ConfigParser()
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")
        config.read(config_path)
        if 'Server' not in config:
            raise ValueError("配置文件中缺少 [Server] 部分")
        port_str = config.get('Server', 'port', fallback='80')
        try:
            PORT = int(port_str)
        except ValueError:
            raise ValueError(f"配置文件中 'port' 的值 '{port_str}' 不是有效的整数")
        HOST = config.get('Server', 'url', fallback='127.0.0.1')
    except Exception as e:
        message = f"读取配置文件时出错: {str(e)}"
        messagebox.showerror("配置文件读取错误", message)
        sys.exit(1)


# 读取配置文件
load_config()
# 拼接完整的 URL
URL = f"http://{HOST}:{PORT}"


# 自定义处理程序，用于设置超时时间并禁用日志输出
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(1)  # 设置连接超时时间为 1 秒

    def log_message(self, format, *args):
        # 重写日志输出方法，不输出任何信息
        return


# 启动服务器函数
def start_server():
    global server_thread, httpd
    # 获取安装目录下的 html 文件夹路径
    html_dir = get_resource_path('html')
    if not os.path.exists(html_dir):
        messagebox.showerror("错误", f"HTML 文件夹未找到: {html_dir}")
        return
    os.chdir(html_dir)

    Handler = CustomHandler
    try:
        httpd = socketserver.TCPServer(("", PORT), Handler)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.start()
        # 打开浏览器访问指定 URL
        webbrowser.open(URL)
        # 禁用启动按钮
        start_button.config(state=tk.DISABLED)
    except OSError as e:
        message = f"端口 {PORT} 已被占用，请关闭其他占用该端口的程序。错误详情: {str(e)}"
        messagebox.showerror("错误", message)


# 创建主窗口
root = tk.Tk()
# 修改窗口标题
root.title("Etranslator")
# 设置窗口固定大小
root.geometry("240x80")
root.resizable(False, False)

# 设置窗口图标
icon_path = get_resource_path("img/logo.ico")
try:
    root.iconbitmap(icon_path)
except Exception as e:
    messagebox.showerror("图标加载错误", str(e))

# 创建启动按钮
start_button = tk.Button(root, text="启动翻译服务", command=start_server, width=20, height=2)
start_button.pack(pady=20)


# 关闭窗口时停止服务器
def on_close():
    global server_thread, httpd

    def stop_server_safely():
        if httpd:
            try:
                # 尝试关闭服务器
                httpd.shutdown()
                httpd.server_close()
            except Exception as e:
                messagebox.showerror("关闭服务器错误", str(e))
        if server_thread:
            server_thread.join(timeout=1)
        root.destroy()

    # 在主线程中异步执行停止服务器操作
    root.after(0, stop_server_safely)


root.protocol("WM_DELETE_WINDOW", on_close)

# 让窗口居中显示
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - root.winfo_width()) // 2
y = (screen_height - root.winfo_height()) // 2
root.geometry(f"+{x}+{y}")

# 重定向标准输出和标准错误流到空设备
if not sys.stderr:
    sys.stderr = open(os.devnull, 'w')
if not sys.stdout:
    sys.stdout = open(os.devnull, 'w')

# 运行主循环
root.mainloop()
