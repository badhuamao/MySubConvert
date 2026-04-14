import json
import base64
import re
import socket
import requests
from concurrent.futures import ThreadPoolExecutor

# --- 配置区 ---
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/Superspeed.yaml",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/latency"
]
TIMEOUT = 3  # 稍微延长超时时间
MAX_WORKERS = 50 

def decode_data(raw_text):
    """更强力的解码判断"""
    raw_text = raw_text.strip()
    # 尝试判断是否为 Base64
    if re.match(r'^[A-Za-z0-9+/=]+$', raw_text):
        try:
            missing_padding = len(raw_text) % 4
            if missing_padding: raw_text += '=' * (4 - missing_padding)
            return base64.b64decode(raw_text).decode('utf-8', errors='ignore')
        except:
            pass
    return raw_text

def check_alive(ip, port):
    """存活检测：如果节点太少，可以暂时关闭此功能或增加重试"""
    try:
        # 尝试建立连接
        with socket.create_connection((ip, port), timeout=TIMEOUT):
            return True
    except:
        return False

def main():
    all_links = []
    print("开始收割节点...")

    # 1. 抓取与提取
    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=10)
            content = decode_data(r.text)
            
            # 正则匹配：不仅匹配 hy2://，也匹配可能的配置块里的 server 和 port
            # 这里我们主要抓取 URI 格式，因为它们最稳定
            links = re.findall(r'hysteria2://[^\s#]+#?[^\s]*', content)
            all_links.extend(links)
            print(f"源 {url} 抓取到 {len(links)} 个潜在节点")
        except:
            print(f"源 {url} 请求失败")

    # 2. 去重与验证
    unique_links = list(set(all_links))
    final_nodes = []
    seen_addresses = set()

    def verify_node(link):
        # 匹配格式: hysteria2://auth@ip:port
        pattern = r'hysteria2://([^@]+)@([^:/?#]+):([0-9, \-]{2,})'
        match = re.search(pattern, link)
        if match:
            auth, ip, port_raw = match.groups()
            # 处理多端口或端口段，取第一个端口测试
            port = int(re.findall(r'\d+', port_raw)[0])
            
            addr_id = f"{ip}:{port}"
            if addr_id not in seen_addresses:
                # --- 注意：如果你觉得节点还是太少，可以把下面两行缩进注释掉，不进行存活检测 ---
                if check_alive(ip, port):
                    seen_addresses.add(addr_id)
                    return {"auth": auth, "ip": ip, "port": port_raw, "link": link}
        return None

    print(f"正在检测 {len(unique_links)} 个唯一节点...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(verify_node, unique_links))
        final_nodes = [r for r in results if r]

    # 3. 构建 Clash YAML (电视专用)
    yaml_content = ["proxies:",]
    proxy_names = []
    
    for node in final_nodes:
        name = f"🐻_{node['ip']}_{node['port']}"
        proxy_names.append(name)
        yaml_content.append(f"  - {{name: \"{name}\", type: hysteria2, server: {node['ip']}, port: {node['port']}, password: {node['auth']}, ssl-allow-insecure: true, sni: www.apple.com}}")

    yaml_content.append("\nproxy-groups:\n  - name: \"BearHome-Auto\"\n    type: select\n    proxies:")
    for name in proxy_names:
        yaml_content.append(f"      - \"{name}\"")
    
    yaml_content.append("\nrules:\n  - MATCH,BearHome-Auto")

    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml_content))
    
    print(f"任务完成！保留有效节点: {len(final_nodes)} 个")

if __name__ == "__main__":
    main()
