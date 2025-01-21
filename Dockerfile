# 使用官方的 selenium/standalone-chrome 镜像
FROM selenium/standalone-chrome:latest

# 设置工作目录
WORKDIR /app

# 安装 Python 3 和 pip，以及 ffmpeg
USER root
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 设置pip使用清华大学镜像源并安装Python依赖
RUN pip3 install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    requests \
    feedparser \
    pytz \
    aiohttp \
    bs4 \
    tqdm \
    async-timeout \
    Flask \
    m3u8 \
    ffmpeg-python \
    gevent \
    selenium

# 拷贝当前目录所有文件到容器的 /app 目录下
COPY . .

# 暴露端口
EXPOSE 8989

# 启动应用
CMD ["python3.10", "app.py"]
