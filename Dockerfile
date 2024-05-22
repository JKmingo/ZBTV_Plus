FROM python:3.8

# 安装ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# 将 Dockerfile 所在的目录设置为工作目录
WORKDIR /app

RUN pip install requests feedparser pytz aiohttp bs4 tqdm async-timeout Flask gevent

# 将 Dockerfile 所在目录下的所有文件复制到镜像中的 /app 目录下
COPY . .
EXPOSE 8899
CMD ["python3", "app.py"]
