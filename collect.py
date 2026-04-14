import json
import base64
import re
import socket
import requests
from concurrent.futures import ThreadPoolExecutor

# --- 配置区 ---
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun"
]
TIMEOUT = 2
MAX_WORKERS = 100

def decode_data(raw_text):
    raw_text = raw_text.strip()
    try:
        missing_padding = len(raw_text) % 4
        if missing_padding: raw_text += '=' * (4 - missing_padding)
        return base64.b64decode(raw_text).decode('utf-8')
    except:
        return raw_text

def check_alive(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=TIMEOUT):
            return True
    except:
        return False

def main():
    all_links = []
    # 1. 抓取与初步提取
    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=15)
            decoded = decode_data(r.text)
            links = re.findall(r'hysteria2://[^\s]+', decoded)
            all_links.extend(links)
        except:
            pass

    # 2. 深度去重与存活检测
    unique_links = list(set(all_links))
    final_nodes = []
    seen_addresses = set()

    def verify_node(link):
        # 匹配格式: hysteria2://auth@ip:port
        pattern = r'hysteria2://([^@]+)@([^:/?]+):([0-9]+)'
        match = re.search(pattern, link)
        if match:
            auth, ip, port = match.group(1), match.group(2), int(match.group(3))
            addr_id = f"{ip}:{port}"
            if addr_id not in seen_addresses and check_alive(ip, port):
                seen_addresses.add(addr_id)
                # 返回提取好的信息
                return {"auth": auth, "ip": ip, "port": port}
        return None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(verify_node, unique_links))
        final_nodes = [r for r in results if r]

    # 3. 构建 Clash YAML 字符串
    # 电视端 Clash 必须要有 proxies, proxy-groups 和 rules 三要素
    yaml_content = [
        "proxies:",
    ]
    
    proxy_names = []
    for i, node in enumerate(final_nodes):
        name = f"🐻_{node['ip']}_{node['port']}"
        proxy_names.append(name)
        # 写入 Hysteria2 代理配置
        yaml_content.append(f"  - name: \"{name}\"")
        yaml_content.append(f"    type: hysteria2")
        yaml_content.append(f"    server: {node['ip']}")
        yaml_content.append(f"    port: {node['port']}")
        yaml_content.append(f"    password: {node['auth']}")
        yaml_content.append(f"    ssl-allow-insecure: true")
        yaml_content.append(f"    sni: www.apple.com") # 默认给个SNI增强兼容性

    # 代理组配置
    yaml_content.append("\nproxy-groups:")
    yaml_content.append("  - name: \"BearHome-Auto\"")
    yaml_content.append("    type: select")
    yaml_content.append("    proxies:")
    for name in proxy_names:
        yaml_content.append(f"      - \"{name}\"")
    
    # 基础规则
    yaml_content.append("\nrules:")
    yaml_content.append("  - MATCH,BearHome-Auto")

    # 4. 写入文件
    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml_content))
    
    print(f"成功生成 clash.yaml，共 {len(final_nodes)} 个活节点")

if __name__ == "__main__":
    main()
