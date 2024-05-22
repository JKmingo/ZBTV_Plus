import os
import threading
from flask import Flask, g
from gevent import pywsgi
from main import UpdateSource

try:
    import user_config as config
except ImportError:
    import config

app = Flask(__name__)

app.config['run_thread'] = None

@app.route('/')
def index():
    run_thread = app.config['run_thread']
    if run_thread is None or not run_thread.is_alive():
        us = UpdateSource()
        app.config['run_thread'] = threading.Thread(target=us.main)
        app.config['run_thread'].start()
    return "正在收集中，请稍候..."


@app.route('/tv')
def tv():
    user_final_file = getattr(config, "final_file", "result.txt")
    if os.path.exists(user_final_file):
        with open(user_final_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "结果还未生成，请稍候..."


if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 8989), app)
    server.serve_forever()
