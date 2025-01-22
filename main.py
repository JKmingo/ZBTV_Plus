import re
from ftplib import FTP
import requests
import shutil
from dynamic_config import DynamicConfig

config = DynamicConfig()
import asyncio
from bs4 import BeautifulSoup
from utils import (
    getChannelItems,
    updateChannelUrlsTxt,
    updateFile,
    compareSpeedAndResolution,
    getTotalUrls,
    filter_CCTV_key,
    get_zubao_source_ip,
    find_matching_values,
    kaisu_upload,
    getTotalUrlsFromInfoList,
    getChannelUrlsTxt,
    get_previous_results,
    merge_urls_lists, checkByURLKeywordsBlacklist
)
import logging
import os
from tqdm import tqdm
from urllib.parse import quote, urlencode

# logging.basicConfig(
#     filename="result_new.log",
#     filemode="a",
#     format="%(message)s",
#     level=logging.INFO,
#     encoding='utf-8'
# )
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("result_new.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

post_headers = {
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}

# post_headers = {
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#     'Content-Type': 'application/x-www-form-urlencoded',
#     'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
# }

previous_result_dict = {}
channel_result_dict = {}


def get_crawl_result():
    config.reload()
    crawl_result_dict = {}
    if config.crawl_type in ["2", "3"]:
        for conf_url in config.crawl_urls:
            try:
                if conf_url.strip().startswith("http:"):
                    crawl_response = requests.get(conf_url.strip(), verify=False)
                else:
                    crawl_response = requests.get(conf_url.strip())
            except Exception:
                continue
            crawl_response.encoding = 'utf-8'
            if crawl_response.status_code != 200:
                continue
            crawl_data = crawl_response.text.split('\n')  # 按行分割数据
            for line in crawl_data:
                parts = line.split(',')  # 按逗号分割每一行
                if len(parts) == 2:
                    key = parts[0].strip() \
                        .replace("「", "").replace("」", "") \
                        .replace("电视台", "").replace("IPV6", "").replace("IPV4", "")
                    key = filter_CCTV_key(key)
                    value = parts[1].strip()
                    if " " in key:
                        key = key.replace(" ", "")
                    if config.search_ignore_key:
                        for ignore_kw in config.search_ignore_key:
                            key = key.replace(ignore_kw, "")
                    if key in crawl_result_dict:
                        crawl_result_dict[key].append(value)
                    else:
                        crawl_result_dict[key] = [value]
    return crawl_result_dict


def search_hotel_ip():
    config.reload()
    subscribe_dict = {}
    kw_zbip_dict = {}
    search_keyword_list = []
    if config.crawl_type in ["1", "3"]:
        for area, subscribe_url in config.search_dict.items():
            if subscribe_url.startswith("http:"):
                subscribe_response = requests.get(subscribe_url.strip(), verify=False)
            else:
                subscribe_response = requests.get(subscribe_url.strip())
            subscribe_response.encoding = 'utf-8'
            if subscribe_response.status_code != 200:
                continue
            subscribe_data = subscribe_response.text.split('\n')  # 按行分割数据

            search_area = None
            for line in subscribe_data:
                parts = line.split(',')  # 按逗号分割每一行
                if len(parts) == 2:
                    if parts[1].strip() == "#genre#":
                        search_area = parts[0].strip() if parts[0].strip().startswith(area) else area + parts[0].strip()
                        search_keyword_list.append(search_area)
                        continue
                    key = filter_CCTV_key(parts[0].strip())
                    value = parts[1].strip()
                    if f"{search_area}|{key}" in subscribe_dict:
                        subscribe_dict[f"{search_area}|{key}"].append(value)
                    else:
                        subscribe_dict[f"{search_area}|{key}"] = [value]

        for search_kw in search_keyword_list:
            zubo_source_ips = set()
            total_page_size = None
            next_page_url = None
            session = requests.Session()
            tk_resp = session.get("https://up.myzy.us.kg/https://tonkiang.us/hoteliptv.php", headers=post_headers, timeout=30)
            soup = BeautifulSoup(tk_resp.text, "html.parser")
            input_tag = soup.find("input", id="search")
            # 获取 name 的值
            if input_tag and "name" in input_tag.attrs:
                name_value = input_tag["name"]
                print("Name 值:", name_value)
            else:
                name_value = 'b8f54'
                print("未找到 id='search' 的 input 标签")
            area_dict = {
                '上海': '五星体育',
                '上海电信': '五星体育',
                '上海移动': '五星体育',
                '上海联通': '五星体育',
            }
            post_form = {
                name_value: area_dict.get(search_kw, search_kw)
            }
            for page in range(1, config.search_page_num + 1):
                try:
                    print(f"搜索关键字[{search_kw}]，第[{page}]页...")
                    max_retries = 5
                    if page == 1:
                        for attempt in range(max_retries):
                            try:
                                response = session.post("https://tonkiang.us/hoteliptv.php", headers=post_headers,
                                                        data=post_form, timeout=30)
                                break
                            except requests.exceptions.RequestException as e:
                                print(f"请求失败，正在进行第[{attempt + 1}]次重试...")
                        else:
                            print(f"尝试[{max_retries}]后仍然失败！！！")
                    else:
                        page_url = f"https://tonkiang.us/hoteliptv.php{next_page_url}"
                        for attempt in range(max_retries):
                            try:
                                response = session.get(page_url, timeout=30)
                                break
                            except requests.exceptions.RequestException as e:
                                print(f"请求失败，正在进行第[{attempt + 1}]次重试...")
                        else:
                            print(f"尝试[{max_retries}]后仍然失败！！！")
                    response.encoding = "UTF-8"
                    soup = BeautifulSoup(response.text, "html.parser")
                    results = soup.find_all("div", class_="result")
                    # 用于存储符合条件的IP地址和端口
                    # 遍历每个结果
                    for result in results:
                        if "失效" in result.get_text(strip=True):
                            continue
                        # 查找IP和端口
                        a_tag = result.find("a")
                        if not a_tag:
                            continue
                        ip_tag = a_tag.find("b")
                        if not ip_tag:
                            continue
                        ip_port = ip_tag.get_text(strip=True)  # 提取IP:Port
                        # 查找状态信息（可能存在时间和上线信息）
                        status_tag = result.find("div", style="font-size: 11px; color: #aaa;")
                        if status_tag:
                            status_text = status_tag.get_text(strip=True)  # 提取状态信息
                            # 判断是否包含“上线”或“存活”
                            if "上线" in status_text or "存活" in status_text:
                                zubo_source_ips.add(ip_port)

                    if total_page_size is None:
                        a_tags = soup.find_all("a")
                        page_urls = []
                        for a_tag in a_tags:
                            href_value = a_tag.get("href")
                            if not href_value:
                                continue
                            if not href_value.startswith(f"?page="):
                                continue
                            page_urls.append(href_value)
                        total_page_size = 10
                        if page_urls:
                            m = re.findall(r'page=(\d+)', page_urls[-1])
                            if m:
                                total_page_size = int(m[0])
                                next_page_url = page_urls[-1].replace(f"page={total_page_size}", f"page={page + 1}")
                    if total_page_size is None or page >= total_page_size:
                        break
                except Exception as e:
                    # traceback.print_exc()
                    print(f"Error on page {page}: {e}")
                    continue

            if len(zubo_source_ips) == 0:
                continue
            kw_zbip_dict[search_kw] = zubo_source_ips
    return subscribe_dict, kw_zbip_dict, search_keyword_list


class UpdateSource:

    def __init__(self, crawl_result_dict, subscribe_dict, kw_zbip_dict, search_keyword_list):
        self.crawl_result_dict = crawl_result_dict
        self.subscribe_dict = subscribe_dict
        self.kw_zbip_dict = kw_zbip_dict
        self.search_keyword_list = search_keyword_list

    async def visitPage(self, channelItems):
        total_channels = sum(len(channelObj) for _, channelObj in channelItems.items())
        pbar = tqdm(total=total_channels)

        for cate, channelObj in channelItems.items():
            channelUrls = {}
            channelObjKeys = channelObj.keys()
            for name in channelObjKeys:
                pbar.set_description(
                    f"Processing {name}, {total_channels - pbar.n} channels remaining"
                )

                infoList = []
                if config.crawl_type in ["1", "3"]:
                    for search_keyword in self.search_keyword_list:
                        sub_ips = find_matching_values(self.subscribe_dict, f"{search_keyword}|{filter_CCTV_key(name)}")
                        # sub_ips = subscribe_dict.get(f"{search_keyword}|{filter_CCTV_key(name)}", None)
                        if not sub_ips:
                            continue
                        kw_zbip_list = self.kw_zbip_dict.get(search_keyword, None)
                        if not kw_zbip_list:
                            continue
                        for zb_ip in kw_zbip_list:
                            for sub_ip in sub_ips:
                                if not sub_ip.startswith("rtp://"):
                                    continue
                                rtp_url = sub_ip.replace("rtp:/", f"http://{zb_ip}/rtp")
                                if not checkByURLKeywordsBlacklist(rtp_url):
                                    continue
                                if "#" in rtp_url:
                                    urls = rtp_url.split("#")
                                    infoList.append([urls[0], None, None])
                                    infoList.append([urls[1], None, None])
                                else:
                                    infoList.append([rtp_url, None, None])
                if config.crawl_type in ["2", "3"]:
                    key_name = filter_CCTV_key(name)
                    tv_urls = self.crawl_result_dict.get(key_name, None)
                    if tv_urls is not None:
                        for tv_url in tv_urls:
                            if not checkByURLKeywordsBlacklist(tv_url):
                                continue
                            infoList.append([tv_url, None, None])
                try:
                    print(f"[{name}]有{len(infoList)}个直播源进行检测...")
                    channelUrls[name] = getTotalUrlsFromInfoList(infoList)
                    if config.open_sort:
                        sorted_data = await compareSpeedAndResolution(infoList)
                        if sorted_data:
                            channelUrls[name] = (
                                    getTotalUrls(sorted_data) or channelObj[name]
                            )
                            for (url, date, resolution), response_time in sorted_data:
                                logger.info(
                                    f"Name: {name}, URL: {url}, Date: {date}, Resolution: {resolution}, Response Time: {response_time}fps"
                                )
                    if len(channelUrls.get(name, [])) < config.zb_urls_limit:
                        previous_result_channels = previous_result_dict.get(name, [])
                        if previous_result_channels:
                            channelUrls[name] = merge_urls_lists(channelUrls.get(name, []),
                                                                 previous_result_channels
                                                                 )[:config.zb_urls_limit]
                    if not channelUrls.get(name, None) and config.is_use_demo_if_none:
                        channelUrls[name] = channelObj[name]
                except Exception as e:
                    print(f"Error on sorting: {e}")
                    continue
                finally:
                    pbar.update()
            channel_result_dict[cate] = getChannelUrlsTxt(cate, channelUrls)
            # await asyncio.sleep(1)
        pbar.close()

    def main(self):
        config.reload()
        channels = getChannelItems()
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     futures = []
        #     for key, channelObj in channels.items():
        #         futures.append(executor.submit(asyncio.run, self.visitPage({key: channelObj})))
        #     concurrent.futures.wait(futures)
        for key, channelObj in channels.items():
            asyncio.run(self.visitPage({key: channelObj}))

        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
        user_final_file = getattr(config, "final_file", "result.txt")
        user_log_file = (
            "user_result.log" if os.path.exists("user_config.py") else "result.log"
        )
        # updateFile(user_final_file, "result_new.txt")
        updateFile(user_log_file, "result_new.log")
        channel_result_list = []
        for key, channelObj in channels.items():
            channel_result_list.append(channel_result_dict.get(key, ""))
        with open(user_final_file, "w", encoding="utf-8") as f:
            f.write(
                "\n".join(channel_result_list) + "\n"
            )  # 写入文件，并换行
        if os.path.exists('output'):
            shutil.copy(user_final_file, 'output')
        print(f"Update completed! Please check the {user_final_file} file!")

        ftp = None
        try:
            ftp_host = getattr(config, "ftp_host", None)
            ftp_host = ftp_host if ftp_host else os.getenv('ftp_host')
            ftp_port = getattr(config, "ftp_port", None)
            ftp_port = ftp_port if ftp_port else os.getenv('ftp_port')
            ftp_user = getattr(config, "ftp_user", None)
            ftp_user = ftp_user if ftp_user else os.getenv('ftp_user')
            ftp_passwd = getattr(config, "ftp_passwd", None)
            ftp_passwd = ftp_passwd if ftp_passwd else os.getenv('ftp_passwd')
            ftp_remote_file = getattr(config, "ftp_remote_file", None)
            ftp_remote_file = ftp_remote_file if ftp_remote_file else os.getenv('ftp_remote_file')

            if ftp_host and ftp_port and ftp_user and ftp_passwd and ftp_remote_file:
                ftp = FTP()
                ftp.connect(ftp_host, int(ftp_port))
                ftp.login(user=ftp_user, passwd=ftp_passwd)
                with open(user_final_file, 'rb') as file:
                    up_res = ftp.storbinary(f'STOR {ftp_remote_file}', file)
                    if up_res.startswith('226 Transfer complete'):
                        print('result upload success！')
                    else:
                        print('result upload fail!')

            ks_token = getattr(config, "ks_token", None)
            ks_token = ks_token if ks_token else os.getenv('ks_token')
            ks_file_id = getattr(config, "ks_file_id", None)
            ks_file_id = ks_file_id if ks_file_id else os.getenv('ks_file_id')
            ks_file_name = getattr(config, "ks_file_name", None)
            ks_file_name = ks_file_name if ks_file_name else os.getenv('ks_file_name')
            if ks_token and ks_file_id:
                kaisu_upload(ks_token, user_final_file, ks_file_name, ks_file_id)
        finally:
            if ftp is not None:
                ftp.quit()


if __name__ == '__main__':
    previous_result_dict = get_previous_results(config.final_file)
    crawl_result_dict = get_crawl_result()
    subscribe_dict, kw_zbip_dict, search_keyword_list = search_hotel_ip()
    UpdateSource(crawl_result_dict, subscribe_dict, kw_zbip_dict, search_keyword_list).main()
