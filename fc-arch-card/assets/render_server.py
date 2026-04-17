"""本地 HTTP 服务，用于提供 Mermaid 渲染页面。"""

import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path


class RenderHandler(http.server.SimpleHTTPRequestHandler):
    """自定义请求处理器，从 assets 目录提供文件。"""

    def __init__(self, *args, assets_dir=None, **kwargs):
        self.assets_dir = assets_dir or Path(__file__).parent
        super().__init__(*args, **kwargs)

    def translate_path(self, path):
        """重写路径解析，指向 assets 目录。"""
        # 移除开头的 /
        path = path.lstrip('/')
        # 构建完整路径
        return str(self.assets_dir / path)

    def log_message(self, format, *args):
        """静默日志输出。"""
        pass


class RenderServer:
    """渲染服务器，提供本地 HTTP 服务用于 Mermaid 渲染。"""

    def __init__(self, port=0, assets_dir=None):
        self.port = port
        self.assets_dir = assets_dir or Path(__file__).parent
        self.server = None
        self.thread = None
        self._actual_port = None

    def start(self):
        """启动服务器，返回实际端口号。"""
        handler = lambda *args, **kwargs: RenderHandler(
            *args, assets_dir=self.assets_dir, **kwargs
        )

        self.server = socketserver.TCPServer(("localhost", self.port), handler)
        self._actual_port = self.server.socket.getsockname()[1]

        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        return self._actual_port

    def stop(self):
        """停止服务器。"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=5)

    @property
    def actual_port(self):
        """获取实际分配的端口号。"""
        return self._actual_port

    def get_url(self, path=""):
        """获取完整 URL。"""
        return f"http://localhost:{self.actual_port}/{path}"


def start_server(assets_dir=None, port=0):
    """便捷函数：启动服务器并返回实例。

    Args:
        assets_dir: assets 目录路径，默认使用脚本所在目录
        port: 指定端口，0 表示自动分配

    Returns:
        RenderServer 实例
    """
    server = RenderServer(port=port, assets_dir=assets_dir)
    actual_port = server.start()
    return server


if __name__ == "__main__":
    # 测试模式
    import sys

    assets_dir = Path(__file__).parent
    if len(sys.argv) > 1:
        assets_dir = Path(sys.argv[1])

    server = RenderServer(assets_dir=assets_dir)
    port = server.start()
    print(f"Server started at http://localhost:{port}/")
    print(f"Serving files from: {assets_dir}")

    try:
        input("Press Enter to stop...")
    finally:
        server.stop()
        print("Server stopped.")
