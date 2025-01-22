import json
import socket
import subprocess
import requests

from dynamic_config import DynamicConfig

config = DynamicConfig()
import asyncio
import time
import re
import os
import urllib.parse
import ipaddress
from urllib.parse import urlparse, quote

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WebScraper:
    def __init__(self, chrome_binary_path=None):
        # 配置 Chrome 选项
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')  # 启动无头模式
        self.chrome_options.add_argument('--disable-gpu')  # 禁用 GPU
        self.chrome_options.add_argument('--no-sandbox')  # 禁用沙盒

        if chrome_binary_path:
            self.chrome_options.binary_location = chrome_binary_path

        # 启动 WebDriver，指定 ChromeDriver 的路径
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 10)  # 动态等待
        self.url = None

    def visit_page(self, url):
        """访问指定的页面"""
        self.url = url
        self.driver.get(url)
        print(self.get_page_source())

    def search(self, query='五星体育'):
        """在输入框中输入查询并点击搜索"""
        for i in range(5):
            print(f"---{i+1}---")
            print(self.get_page_source())
            input_box = self.driver.find_element(By.ID, 'search')  # 根据页面上的 input 名称修改
            input_box.send_keys(query)
            if self.driver.current_url != self.url:
                self.visit_page(self.url)
                continue
            # 找到并点击搜索按钮
            self.find_clickable_element_with_retry((By.XPATH, '//input[@type="submit"]'))
            self.driver.execute_script("arguments[0].click();", search_button)
            time.sleep(2)
            # 等待搜索结果可见
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "result")))  # 根据实际的id定位结果元素
            break

    def get_page_source(self):
        """获取当前页面的 HTML 源代码"""
        return self.driver.page_source

    def navigate_page(self, page_number):
        """模拟分页操作（例如通过点击 '下一页' 按钮）"""
        # 假设页面有一个分页按钮，定位并点击对应页面
        pagination_button = self.driver.find_element(By.XPATH, f"//a[starts-with(@href, '?page={page_number}')]")
        if pagination_button:
            pagination_button.click()

        time.sleep(2)
        # 等待页面加载
        self.wait.until(EC.presence_of_element_located((By.ID, "result")))  # 根据实际情况定位

    def quit(self):
        """退出浏览器"""
        self.driver.quit()

    def find_clickable_element_with_retry(self, locator, timeout=10, retries=3):
        """
        Find the clickable element with retry
        """
        wait = WebDriverWait(self.driver, timeout)
        for _ in range(retries):
            try:
                return wait.until(EC.element_to_be_clickable(locator))
            except Exception:
                self.driver.refresh()
        return None


def getChannelItems():
    """
    Get the channel items from the source file
    """
    # Open the source file and read all lines.
    config.reload()
    open_file = None
    try:
        user_source_file = (
            "user_" + config.source_file
            if os.path.exists("user_" + config.source_file)
            else getattr(config, "source_file", "demo.txt")
        )
        with open(user_source_file, "r", encoding="utf-8-sig") as f:
            open_file = f
            lines = f.readlines()

        # Create a dictionary to store the channels.
        channels = {}
        current_category = ""
        pattern = r"^(.*?),(?!#genre#)(.*?)$"
        # total_channels = 0
        # max_channels = 200

        for line in lines:
            # if total_channels >= max_channels:
            #     break
            line = line.strip()
            if "#genre#" in line:
                # This is a new channel, create a new key in the dictionary.
                current_category = line.split(",")[0]
                channels[current_category] = {}
            else:
                # This is a url, add it to the list of urls for the current channel.
                match = re.search(pattern, line)
                if match:
                    if match.group(1) not in channels[current_category]:
                        channels[current_category][match.group(1)] = [match.group(2)]
                        # total_channels += 1
                    else:
                        channels[current_category][match.group(1)].append(
                            match.group(2)
                        )
        return channels
    finally:
        if open_file is not None:
            open_file.close()


def updateChannelUrlsTxt(cate, channelUrls):
    """
    Update the category and channel urls to the final file
    """
    try:
        with open("result_new.txt", "a", encoding="utf-8") as f:
            f.write(cate + ",#genre#\n")
            for name, urls in channelUrls.items():
                for url in urls:
                    if url is not None:
                        f.write(name + "," + url + "\n")
            f.write("\n")
    finally:
        f.close


def getChannelUrlsTxt(cate, channelUrls):
    res = cate + ",#genre#\n"
    for name, urls in channelUrls.items():
        for url in urls:
            if url is not None:
                res += name + "," + url + "\n"
    return res


def updateFile(final_file, old_file):
    """
    Update the file
    """
    if os.path.exists(old_file):
        if os.path.exists(final_file):
            os.remove(final_file)
            time.sleep(1)
        os.replace(old_file, final_file)


def getUrlInfo(result, channel_name):
    """
    Get the url, date and resolution
    """
    if channel_name.lower() not in str(result).lower():
        return None, None, None
    if channel_name.lower() == 'cctv-1':
        search = re.search(r'cctv-\d+', str(result), re.IGNORECASE)
        if not search:
            return None, None, None
        if search.group().lower() != channel_name.lower():
            return None, None, None
    elif channel_name.lower() == 'cctv-5':
        if "cctv-5+" in str(result).lower():
            return None, None, None
    elif channel_name.lower() == 'cctv-5+':
        if "cctv-5+" not in str(result).lower():
            return None, None, None
    url = date = resolution = None
    result_div = [div for div in result.children if div.name == "div"]
    for result_sub_div in result_div:

        img_tags = result_sub_div.find_all("img")
        if not img_tags:
            continue
        if "copy" not in str(result_sub_div):
            continue
        channel_text = result_sub_div.get_text(strip=True)
        url_match = re.search(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            channel_text,
        )
        if url_match:
            url = url_match.group()
        info_text = result_div[-1].get_text(strip=True)
        if info_text:
            date, resolution = (
                (info_text.partition(" ")[0] if info_text.partition(" ")[0] else None),
                (
                    info_text.partition(" ")[2].partition("•")[2]
                    if info_text.partition(" ")[2].partition("•")[2]
                    else None
                ),
            )
        break
    return url, date, resolution


async def check_stream_speed(url_info):
    config.reload()
    try:
        is_v6 = is_ipv6(url_info[0])
        if is_v6 and (os.getenv("ipv6_proxy") or config.ipv6_proxy):
            proxy = config.ipv6_proxy if config.ipv6_proxy else os.getenv("ipv6_proxy")
            url = proxy + quote(url_info[0])
            response = requests.get(url)
            if response.status_code == 200:
                if not url_info[2]:
                    url_info[2] = '1920x1080'
                if config.xianlu_type == 2:
                    url_info[0] = url_info[0] + f"${url_info[2]}|ipv6"
                return float("inf")
            else:
                return float("-inf")
        else:
            url = url_info[0]
        video_info = await ffmpeg_url(url, config.ffmpeg_time)
        if video_info is None:
            return float("-inf")
        frame, resolution = analyse_video_info(video_info)
        if frame is None:
            return float("-inf")
        if config.xianlu_type == 2 and resolution:
            url_info[0] = url_info[0] + f"${resolution}"
            if is_v6:
                url_info[0] = url_info[0] + "|ipv6"
        url_info[2] = resolution
        return frame
    except Exception as e:
        # traceback.print_exc()
        print(e)
        return float("-inf")


async def getSpeed(url_info):
    url, _, _ = url_info
    if "$" in url:
        url = url.split('$')[0]
    url = quote(url, safe=':/?&=$[]')
    url_info[0] = url
    try:
        speed = await check_stream_speed(url_info)
        return speed
    except Exception:
        return float("-inf")


async def limited_getSpeed(url_info, semaphore):
    async with semaphore:
        return await getSpeed(url_info)


async def compareSpeedAndResolution(infoList):
    """
    Sort by speed and resolution
    """
    config.reload()
    if not infoList:
        return None
    semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
    # 使用信号量限制同时运行的协程数量
    response_times = await asyncio.gather(
        *[limited_getSpeed(url_info, semaphore) for url_info in infoList]
    )
    # response_times = await asyncio.gather(*[getSpeed(url_info) for url_info in infoList])
    valid_responses = [
        (info, rt) for info, rt in zip(infoList, response_times) if rt != float("-inf")
    ]

    def extract_resolution(resolution_str):
        numbers = re.findall(r"\d+x\d+", resolution_str)
        if numbers:
            width, height = map(int, numbers[0].split("x"))
            return width * height
        else:
            return 0

    default_response_time_weight = 0.5
    default_resolution_weight = 0.5
    response_time_weight = getattr(
        config, "response_time_weight", default_response_time_weight
    )
    resolution_weight = getattr(config, "resolution_weight", default_resolution_weight)
    # Check if weights are valid
    if not (
            0 <= response_time_weight <= 1
            and 0 <= resolution_weight <= 1
            and response_time_weight + resolution_weight == 1
    ):
        response_time_weight = default_response_time_weight
        resolution_weight = default_resolution_weight

    def combined_key(item):
        (_, _, resolution), response_time = item
        resolution_value = extract_resolution(resolution) if resolution else 0
        return (
                response_time_weight * response_time
                + resolution_weight * resolution_value
        )

    sorted_res = sorted(valid_responses, key=combined_key, reverse=True)
    return sorted_res


def getTotalUrls(data):
    """
    Get the total urls with filter by date and depulicate
    """
    config.reload()
    if len(data) > config.zb_urls_limit:
        total_urls = [url for (url, _, _), _ in data[:config.zb_urls_limit]]
    else:
        total_urls = [url for (url, _, _), _ in data]
    return list(dict.fromkeys(total_urls))


def getTotalUrlsFromInfoList(infoList):
    """
    Get the total urls from info list
    """
    config.reload()
    total_urls = [
        url for url, _, _ in infoList[: min(len(infoList), config.zb_urls_limit)]
    ]
    return list(dict.fromkeys(total_urls))


def is_ipv6(url):
    """
    Check if the url is ipv6
    """
    try:
        host = urllib.parse.urlparse(url).hostname
        ipaddress.IPv6Address(host)
        return True
    except ValueError:
        return False


def checkUrlIPVType(url):
    """
    Check if the url is compatible with the ipv type in the config
    """
    config.reload()
    ipv_type = getattr(config, "ipv_type", "ipv4")
    if ipv_type == "ipv4":
        return not is_ipv6(url)
    elif ipv_type == "ipv6":
        return is_ipv6(url)
    else:
        return True


def checkByDomainBlacklist(url):
    """
    Check by domain blacklist
    """
    config.reload()
    domain_blacklist = [
        urlparse(domain).netloc if urlparse(domain).scheme else domain
        for domain in getattr(config, "domain_blacklist", [])
    ]
    return urlparse(url).netloc not in domain_blacklist


def checkByURLKeywordsBlacklist(url):
    """
    Check by URL blacklist keywords
    """
    config.reload()
    url_keywords_blacklist = getattr(config, "url_keywords_blacklist", [])
    return not any(keyword in url for keyword in url_keywords_blacklist)


def filterUrlsByPatterns(urls):
    """
    Filter urls by patterns
    """
    urls = [url for url in urls if checkUrlIPVType(url)]
    urls = [url for url in urls if checkByDomainBlacklist(url)]
    urls = [url for url in urls if checkByURLKeywordsBlacklist(url)]
    return urls


def is_match_url(url):
    url_match = url.strip().startswith("http")
    if url_match:
        return True, url.strip()
    return False, None


def filter_CCTV_key(key: str):
    key = re.sub(r'\[.*?\]', '', key)
    if "cctv" not in key.lower():
        return key
    chinese_pattern = re.compile("[\u4e00-\u9fa5]+")  # 匹配中文字符的 Unicode 范围
    filtered_text = chinese_pattern.sub('', key)  # 使用 sub 方法替换中文字符为空字符串
    result = re.sub(r'\[\d+\*\d+\]', '', filtered_text)
    if "-" not in result:
        result = result.replace("CCTV", "CCTV-")
    if result.upper().endswith("HD"):
        result = result[:-2]  # 去掉最后两个字符
    return result.strip()


def convert_kwargs_to_cmd_line_args(kwargs):
    """Helper function to build command line arguments out of dict."""
    args = []
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if isinstance(v, Iterable) and not isinstance(v, str):
            for value in v:
                args.append('-{}'.format(k))
                if value is not None:
                    args.append('{}'.format(value))
            continue
        args.append('-{}'.format(k))
        if v is not None:
            args.append('{}'.format(v))
    return args


def convert_kwargs_to_cmd_line_args(kwargs):
    """Helper function to build command line arguments out of dict."""
    args = []
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if isinstance(v, Iterable) and not isinstance(v, str):
            for value in v:
                args.append('-{}'.format(k))
                if value is not None:
                    args.append('{}'.format(value))
            continue
        args.append('-{}'.format(k))
        if v is not None:
            args.append('{}'.format(v))
    return args


def is_port_open(url, timeout=5):
    s = None
    try:
        parsed_url = urlparse(url)
        # 提取域名和端口号
        domain = parsed_url.hostname
        port = parsed_url.port
        # 创建 socket 对象
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置超时时间为
        s.settimeout(timeout)
        # 尝试连接到主机和端口
        s.connect((domain, port))
        # 如果连接成功，则关闭连接并返回 True
        return True
    except Exception as e:
        # 如果连接失败，则返回 False
        return False
    finally:
        if s is not None:
            s.close()


def ffmpeg_probe(filename, timeout, cmd='ffprobe', **kwargs):
    """Run ffprobe on the specified file and return a JSON representation of the output.

    Raises:
        :class:`ffmpeg.Error`: if ffprobe returns a non-zero exit code,
            an :class:`Error` is returned with a generic error message.
            The stderr output can be retrieved by accessing the
            ``stderr`` property of the exception.
    """
    args = [cmd, '-select_streams', 'v', '-show_streams', '-of', 'json']
    args += convert_kwargs_to_cmd_line_args(kwargs)
    args += [filename]
    p = None
    try:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        communicate_kwargs = {}
        if timeout is not None:
            communicate_kwargs['timeout'] = timeout
        out, err = p.communicate(**communicate_kwargs)
        if out:
            return json.loads(out.decode('utf-8'))
        return None
    except Exception:
        # traceback.print_exc()
        return None
    finally:
        graceful_exit(p)


def graceful_exit(process):
    if process is None:
        return
    try:
        process.terminate()
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()


def get_ip_address(rtp_url):
    pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})"
    # 使用正则表达式进行匹配
    match = re.search(pattern, rtp_url)
    # 如果匹配成功，则提取 IP 地址和端口号
    if match:
        return match.group(1)
    return None


def get_zubao_source_ip(result_div):
    a_elems = result_div.find_all("a")
    if a_elems is None or len(a_elems) == 0:
        return None
    img_div = a_elems[0].find_all("img")
    if not img_div:
        return None
    if "存活" not in str(result_div):
        return None
    pattern = r'\b((?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d{1,5})?|(?:\d{1,3}\.){1,3}\d{1,3}(?::\d{1,5})?)\b'
    # 使用 re.search() 查找第一个匹配的字符串
    match = re.search(pattern, a_elems[0].get_text(strip=True))
    if match:
        return match.group(0)
    return None


async def ffmpeg_url(url, timeout, cmd='ffmpeg'):
    args = [cmd, '-t', str(timeout), '-stats', '-i', url, '-f', 'null', '-']
    proc = None
    res = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        # 等待子进程执行完毕并获取输出
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout + 5)
        if out:
            res = out.decode('utf-8')
        if err:
            res = err.decode('utf-8')
        return res
    except asyncio.TimeoutError:
        # traceback.print_exc()
        if proc:
            proc.kill()
        return None
    except Exception:
        # traceback.print_exc()
        if proc:
            proc.kill()
        return None
    finally:
        if proc:
            await proc.wait()  # 等待子进程结束
        # print(res)
        return res


def analyse_video_info(video_info):
    frame_size = float("-inf")
    resolution = None
    if video_info is not None:
        info_data = video_info.replace(" ", "")
        matches = re.findall(r"frame=(\d+).*?fps=([\d\.]+).*?speed=([\d\.]+)x", info_data)
        if matches:
            total_frame = 0
            total_fps = 0.0
            total_speed = 0.0
            count = 0
            # 遍历匹配结果并累加
            for m in matches:
                frame = int(m[0])
                fps = float(m[1])
                speed = float(m[2])
                total_frame += frame
                total_fps += fps
                total_speed += speed
                count += 1
            # 计算平均值
            avg_frame = total_frame / count if count > 0 else 0
            avg_fps = total_fps / count if count > 0 else 0
            avg_speed = total_speed / count if count > 0 else 0
            frame_size = avg_frame + avg_fps + avg_speed
        match = re.search(r'(\d{3,4}x\d{3,4})', video_info)
        if match:
            resolution = match.group(0)
    return frame_size, resolution


def find_matching_values(dictionary, partial_key):
    # 遍历字典键并找到包含部分字符串的键
    config.reload()
    result = []
    matching_keys = []
    for key in dictionary:
        if partial_key not in key:
            continue
        if not key.replace(partial_key, ""):
            matching_keys.append(key)
        elif key.replace(partial_key, "") in config.search_ignore_key:
            matching_keys.append(key)
    if not matching_keys:
        return None
    for m_key in matching_keys:
        result += dictionary[m_key]
    return result


def kaisu_upload(token, file_path, new_filename, file_id="0"):
    url = f"https://upload.kstore.space/upload/{file_id}?access_token={token}"
    # 打开文件并上传
    with open(file_path, 'rb') as file:
        if new_filename:
            files = {'file': (new_filename, file)}
        else:
            files = {'file': file}
        response = requests.post(url, files=files)

    # 检查响应
    if response.status_code == 200:
        file_id = response.json().get("data").get("id")
        data = {
            "fileId": file_id,
            "isDirect": 1
        }
        requests.post(f"https://api.kstore.space/api/v1/file/direct?access_token={token}", data=data)
        print("File uploaded on kaisu successfully")


def merge_urls_lists(urls_list1, urls_list2):
    if not urls_list1 and not urls_list2:
        return []
    if not urls_list2:
        return urls_list1
    if not urls_list1:
        return urls_list2
    # 使用有序字典来保留列表顺序
    result_dict = dict()
    key_set = set()
    # 添加第一个列表的元素到结果字典中，并去除重复项
    for url in urls_list1:
        key_set.add(url)
        if "$" in url:
            key_set.add(url.split("$")[0])
        result_dict[url] = None

    # 添加第二个列表的元素到结果字典中，并去除重复项
    for url in urls_list2:
        if "$" in url:
            url_key = url.split("$")[0]
        else:
            url_key = url
        if url_key in key_set:
            continue
        result_dict[url] = None

    # 输出结果列表
    return list(result_dict.keys())


def get_previous_results(file_path):
    # 定义一个空字典来存储频道名称和对应的URL列表
    channel_dict = {}
    if not os.path.exists(file_path):
        return channel_dict
    # 打开并读取文件
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            if "#genre#" in line:
                continue
            # 按逗号分割每行数据
            parts = line.strip().split(',')
            if len(parts) == 2:
                channel_name, url = parts
                # 如果频道名称已经在字典中，追加到URL列表
                if channel_name in channel_dict:
                    channel_dict[channel_name].append(url)
                # 如果频道名称不在字典中，创建一个新的列表
                else:
                    channel_dict[channel_name] = [url]
    return channel_dict
