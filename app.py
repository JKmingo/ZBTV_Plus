import os
import shutil
import queue
import sys
import threading

from flask import Flask, jsonify, Response, request, redirect, render_template, url_for, flash
from gevent import pywsgi

import main
from dynamic_config import DynamicConfig
from main import UpdateSource, get_crawl_result, search_hotel_ip
from utils import get_previous_results
config = DynamicConfig()


app = Flask(__name__, template_folder=os.getcwd())
app.config['SECRET_KEY'] = 'secret!'

is_task_running = False
run_thread = None
thread_lock = threading.Lock()

messages = queue.Queue()


class StderrInterceptor:
    def __init__(self):
        self._buffer = []

    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        global messages
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        if exc_value:
            messages.put(str(exc_value))

    def write(self, data):
        global messages
        self._buffer.append(data)
        self._original_stdout.write(data)
        if data.strip():
            messages.put(data.strip())

    def flush(self):
        pass


def run_background_task():
    global is_task_running
    global run_thread
    with StderrInterceptor() as interceptor:
        config.reload()
        main.previous_result_dict = get_previous_results(config.final_file)
        crawl_result_dict = get_crawl_result()
        subscribe_dict, kw_zbip_dict, search_keyword_list = search_hotel_ip()
        UpdateSource(crawl_result_dict, subscribe_dict, kw_zbip_dict, search_keyword_list).main()
    is_task_running = False
    run_thread = None


def copy_output_files():
    source_directory = 'output'
    destination_directory = os.getcwd()
    if not os.path.exists(source_directory):
        return
    try:
        # 列出 output 目录下的所有文件
        files = [f for f in os.listdir(source_directory) if os.path.isfile(os.path.join(source_directory, f))]

        if files:
            for file in files:
                source_path = os.path.join(source_directory, file)
                destination_path = os.path.join(destination_directory, file)

                shutil.copy(source_path, destination_path)
                print(f"File copied from {source_path} to {destination_path}")
        else:
            print("No files found in the output directory")
    except Exception as e:
        print(f"Error occurred: {e}")

copy_output_files()

@app.route('/')
def index():
    global messages
    messages = queue.Queue()
    return render_template('index.html')


@app.route('/run')
def run():
    global is_task_running
    global run_thread
    if is_task_running:
        flash('正在执行中...')
        return redirect(url_for('index'))
    is_task_running = True
    with thread_lock:
        if run_thread is None:
            run_thread = threading.Thread(target=run_background_task)
            run_thread.start()
    flash('正在执行中...')
    return redirect(url_for('index'))


@app.route('/poll')
def poll():
    try:
        # 尝试在1秒内获取消息，如果没有则返回超时响应
        message = messages.get(timeout=1)
    except queue.Empty:
        message = None
    return jsonify(message=message)


@app.route('/tv')
def tv():
    config.reload()
    user_final_file = getattr(config, "final_file", "result.txt")
    if os.path.exists(user_final_file):
        with open(user_final_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, mimetype='text/plain')
    return "结果还未生成，请稍候..."


@app.route('/setconfig', methods=['GET', 'POST'])
def set_config():
    return set_file_content('config.py', 'set_config')


@app.route('/setdemo', methods=['GET', 'POST'])
def set_demo():
    return set_file_content('demo.txt', 'set_demo')


def set_file_content(file_path, method_name):
    if request.method == 'POST':
        # 获取用户提交的新内容
        new_content = request.form['file_content'].replace('\r\n', '\n')
        # 将新内容写入文件
        with open(file_path, 'w') as f:
            f.write(new_content)
        flash('保存成功')
        # 重定向到首页
        return redirect(url_for(method_name))

        # GET 请求时，读取文件内容并显示在页面中
    with open(file_path, 'r') as f:
        file_content = f.read()
    return render_template('config.html', file_content=file_content)

if __name__ == '__main__':
    服务器绑定 IPv4 和 IPv6 地址
    app.run(host='::', port=8989, debug=True)
