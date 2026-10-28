#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DickOnTop 本地静态服务器。

比 `python -m http.server` 多做几件事：
- 自动跳过被占用的端口（8080、8081 ...）；
- 补齐 .webmanifest / .js 的 MIME 类型；
- 把 /favicon.ico、/apple-touch-icon.png 指向 icons 目录，避免 404；
- 浏览器或手机中断连接时不再打印大段 traceback；
- 本地调试统一 no-store，避免改了页面还被缓存。
"""

import os
import socket
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

if sys.version_info < (3, 7):
    print("需要 Python 3.7 或更高版本，当前版本：%s" % sys.version.split()[0])
    sys.exit(1)

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

ALIASES = {
    "/favicon.ico": "/icons/favicon-64.png",
    "/apple-touch-icon.png": "/icons/apple-touch-icon.png",
    "/apple-touch-icon-precomposed.png": "/icons/apple-touch-icon.png",
}

TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class Handler(SimpleHTTPRequestHandler):
    server_version = "DickOnTopLocal/1.0"

    def translate_path(self, path):
        clean = urllib.parse.urlsplit(path).path
        if clean in ALIASES:
            clean = ALIASES[clean]
        return super().translate_path(clean)

    def guess_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in TYPES:
            return TYPES[ext]
        return super().guess_type(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Service-Worker-Allowed", "/")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))
        sys.stdout.flush()

    def log_error(self, fmt, *args):
        # 404 只保留请求行，不打印 "code 404, message File not found"
        pass

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionError, TimeoutError):
            self.close_connection = True

    def handle(self):
        try:
            super().handle()
        except (ConnectionError, TimeoutError):
            self.close_connection = True


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # Windows 下 SO_REUSEADDR 会让两个进程同时绑同一端口，这里关掉
    allow_reuse_address = False

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionError, TimeoutError)):
            return
        super().handle_error(request, client_address)


def local_ips():
    ips = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            ips.append(sock.getsockname()[0])
        finally:
            sock.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith("127.") and not ip.startswith("169.254."):
                ips.append(ip)
    except OSError:
        pass
    return ips


def port_free(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("0.0.0.0", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def make_server():
    for port in range(8080, 8100):
        if not port_free(port):
            continue
        try:
            return Server(("0.0.0.0", port), Handler)
        except OSError:
            continue
    print("8080-8099 端口都被占用了，请关掉占用端口的程序后重试。")
    sys.exit(1)


def main():
    httpd = make_server()
    port = httpd.server_address[1]
    print("=" * 44)
    print("  DickOnTop 本地服务器")
    print("=" * 44)
    print("  电脑访问: http://localhost:%d" % port)
    print()
    print("  手机访问（同一 WiFi）:")
    ips = local_ips()
    if ips:
        for ip in ips:
            print("    http://%s:%d" % (ip, port))
    else:
        print("    没有检测到局域网 IP，请检查网络连接")
    print()
    print("  按 Ctrl+C 停止")
    print("=" * 44)
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
