import base64
import re
import socket
import requests
from concurrent.futures import ThreadPoolExecutor

# --- 配置区：把图里报错的源都加上了 ---
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/Superspeed.yaml",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/latency",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun",
    "https://raw.githubusercontent.com/badhuamao/FasterVPN-Auto/refs/heads/main/proxies.yaml"
]

TIMEOUT = 3 
MAX_WORKERS = 50

def smart_decode(text):
    """万能解码：如果是Base64就解，不是就原样返回"""
    text = text.strip()
    try:
        # 尝试补齐并解码
        missing_padding = len(text) % 4
        if missing_padding: text += '=' * (4 - missing_padding)
        return base64.b64decode(text).decode('utf-8', errors='ignore')
    except:
        return text

def check_alive(ip, port):
    """TCP探测存活"""
    try:
        with socket.create_connection((ip, port), timeout=TIMEOUT):
            return True
    except:
        return False

def main():
    all_raw_links = []
    print("🚀 开始全量收割...")

    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=10)
            content = smart_decode(r.text)
            
            # 使用超级正则：只要包含 hysteria2:// 的全部抓出来
            links = re.findall(r'hysteria2://[^\s\'"<>#]+#?[^\s\'"<>]*', content)
            all_raw_links.extend(links)
            print(f"✅ 源 {url.split('/')[-1]}：提取到 {len(links)} 个节点")
        except:
            print(f"❌ 源 {url.split('/')[-1]}：连接失败")

    # 去重
    unique_links = list(set(all_raw_links))
    final_nodes = []
    seen_addrs = set()

    def process_node(link):
        # 匹配 auth@ip:port
        match = re.search(r'hysteria2://([^@]+)@([^:/?#]+):([0-9]+)', link)
        if match:
            auth, ip, port = match.groups()
            addr = f"{ip}:{port}"
            if addr not in seen_addrs:
                # --- 核心改进：如果不通，先不删，确保电视有节点可用 ---
                # 如果你想严格删死节点，保留下面 if；如果想节点多，就注释掉 if
                if check_alive(ip, int(port)):
                    seen_addrs.add(addr)
                    return {"name": f"🐻_{ip}_{port}", "ip": ip, "port": port, "auth": auth}
        return None

    print(f"🔍 正在检测 {len(unique_links)} 个唯一节点...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        results = list(exe.map(process_node, unique_links))
        final_nodes = [r for r in results if r]

    # 构建电视专用 Clash 格式
    yaml = ["proxies:"]
    for n in final_nodes:
        yaml.append(f"  - {{name: \"{n['name']}\", type: hysteria2, server: {n['ip']}, port: {n['port']}, password: {n['auth']}, ssl-allow-insecure: true, sni: www.apple.com}}")

    yaml.append("\nproxy-groups:\n  - name: \"BearHome-Auto\"\n    type: select\n    proxies:")
    for n in final_nodes:
        yaml.append(f"      - \"{n['name']}\"")
    
    yaml.append("\nrules:\n  - MATCH,BearHome-Auto")

    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml))
    
    print(f"🎉 大功告成！共有 {len(final_nodes)} 个节点存活并推送到 clash.yaml")

if __name__ == "__main__":
    main()
