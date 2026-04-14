import json
import base64
import re
import socket
import requests
from concurrent.futures import ThreadPoolExecutor

# --- 配置区 ---
# 填入你所有的源链接（支持各种格式）
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun"
]

TIMEOUT = 2  # 连接测试超时（秒），建议不要太长，否则 Action 跑太久
MAX_WORKERS = 100  # 并发检测，Action 环境下 100 没问题

def decode_data(raw_text):
    """自动处理并解码 Base64，如果是明文则直接返回"""
    raw_text = raw_text.strip()
    try:
        # 尝试补齐 Base64 填充符号
        missing_padding = len(raw_text) % 4
        if missing_padding:
            raw_text += '=' * (4 - missing_padding)
        return base64.b64decode(raw_text).decode('utf-8')
    except:
        return raw_text

def check_alive(ip, port):
    """最核心的删死节点逻辑：TCP 握手"""
    try:
        # 针对 Hysteria2，我们探测其主要 TCP/UDP 端口是否连通
        with socket.create_connection((ip, port), timeout=TIMEOUT):
            return True
    except:
        return False

def extract_hy2_uris(content):
    """正则提取所有 Hysteria2 链接"""
    # 这个正则能精准抓取 hysteria2:// 到行尾或空格的内容
    return re.findall(r'hysteria2://[^\s]+', content)

def main():
    all_links = []
    
    # 1. 抓取
    for url in SOURCE_URLS:
        try:
            print(f"正在获取: {url}")
            r = requests.get(url, timeout=15)
            decoded_content = decode_data(r.text)
            links = extract_hy2_uris(decoded_content)
            all_links.extend(links)
        except Exception as e:
            print(f"抓取失败: {url} -> {e}")

    # 2. 初步去重（去除完全一模一样的字符串）
    unique_links = list(set(all_links))
    print(f"去重前: {len(all_links)} | 字符去重后: {len(unique_links)}")

    # 3. 深度去重 + 存活检测
    final_nodes = []
    seen_addresses = set()  # 用于存储 ip:port 组合

    def verify_node(link):
        # 解析链接中的 IP 和 端口
        # 格式示例: hysteria2://auth@1.2.3.4:443?params#name
        pattern = r'hysteria2://[^@]+@([^:/?]+):([0-9]+)'
        match = re.search(pattern, link)
        if match:
            ip, port = match.group(1), int(match.group(2))
            addr_id = f"{ip}:{port}"
            
            # 物理去重：如果这个 IP+端口 已经出现过了，就跳过
            if addr_id in seen_addresses:
                return None
            
            # 存活检测
            if check_alive(ip, port):
                seen_addresses.add(addr_id) # 标记为已处理
                return link
        return None

    print("正在进行多线程存活检测...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(verify_node, unique_links))
        final_nodes = [r for r in results if r]

    # 4. 写入文件
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_nodes))
    
    print(f"任务完成！保留有效节点: {len(final_nodes)} 个")

if __name__ == "__main__":
    main()
