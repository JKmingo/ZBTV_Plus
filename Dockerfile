FROM debian:11-slim

# 更换阿里源
RUN set -eux; \
    DEBIAN_CODENAME=$(awk -F= '/^VERSION_CODENAME=/{print $2}' /etc/os-release); \
    echo "deb http://mirrors.aliyun.com/debian/ $DEBIAN_CODENAME main contrib non-free" > /etc/apt/sources.list; \
    echo "deb-src http://mirrors.aliyun.com/debian/ $DEBIAN_CODENAME main contrib non-free" >> /etc/apt/sources.list; \
    echo "deb http://mirrors.aliyun.com/debian-security $DEBIAN_CODENAME-security main contrib non-free" >> /etc/apt/sources.list; \
    echo "deb-src http://mirrors.aliyun.com/debian-security $DEBIAN_CODENAME-security main contrib non-free" >> /etc/apt/sources.list; \
    echo "deb http://mirrors.aliyun.com/debian/ $DEBIAN_CODENAME-updates main contrib non-free" >> /etc/apt/sources.list; \
    echo "deb-src http://mirrors.aliyun.com/debian/ $DEBIAN_CODENAME-updates main contrib non-free" >> /etc/apt/sources.list;

# 安装 Python 3.10 和 ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip ffmpeg

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
    gevent

# 设置工作目录
WORKDIR /app

# 拷贝当前目录所有文件到容器的 /app 目录下
COPY . .

# 暴露端口
EXPOSE 8989

# 启动应用
CMD ["python3.10", "app.py"]
