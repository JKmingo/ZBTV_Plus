# docker中不要修改
source_file = "demo.txt"
final_file = "result.txt"

# 权重，用于测速，一般不需要修改
response_time_weight = 0.5
resolution_weight = 0.5

# 每个频道直播源数量
zb_urls_limit = 10

# 最大协程数
max_concurrent_tasks = 10

# 是否打开测速
open_sort = True
# 是否找不到源时保留demo的源
is_use_demo_if_none = True
# 1: 显示默认值，线路1 线路2，2：显示视频分辨率，如:1080x720
xianlu_type = 2
# ffmpeg解析视频时间，单位秒
ffmpeg_time = 10
# key: 地区，在http://tonkiang.us网站上搜索的关键词
# value: 订阅url，在https://github.com/xisohi/IPTV-Multicast-source中找自己想要的
search_dict = {
    "上海": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/xisohi/IPTV-Multicast-source/main/shanghai/telecom.txt"
}
# 在http://tonkiang.us网站上搜索的源的页数
search_page_num = 5
# url关键词黑名单
url_keywords_blacklist = []
# 忽略的关键词，比如在demo.txt中配置广东珠江,但在订阅中只有广东珠江高清,就需要忽略掉"高清"
search_ignore_key = ["高清", "4K"]
# crawl_type的默认值为1-只爬取http://tonkiang.us上组播源；2-只爬取crawl_urls中配置的网站；3-全部
crawl_type = "1"
# 收集其他大佬url中的直播源
crawl_urls = [
    "https://github.moeyy.xyz/https://raw.githubusercontent.com/PizazzGY/TVBox/main/live.txt"
]
# ipv6源检测有效性的代理地址，用于不支持ipv6网络的主机，若网络支持ipv6，这里填空""
ipv6_proxy = "http://www.ipv6proxy.net/go.php?u=" #此代理用于github，国内不一定能用
# ftp上传result.txt文件
ftp_host = ""
ftp_port = ""
ftp_user = ""
ftp_passwd = ""
ftp_remote_file = ""

# 凯速网上传文件配置
ks_token = ""
ks_file_id = "0"  # 文件目录id，0为根目录
ks_file_name = ""
