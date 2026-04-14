import base64
import re
import requests
from concurrent.futures import ThreadPoolExecutor

# --- 配置区 ---
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/Superspeed.yaml",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/latency",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun",
    "https://raw.githubusercontent.com/badhuamao/FasterVPN-Auto/refs/heads/main/proxies.yaml"
]

def smart_decode(text):
    """尝试 Base64 解码，失败则返回原内容"""
    try:
        # 清除可能的空格换行
        t = text.strip()
        missing_padding = len(t) % 4
        if missing_padding: t += '=' * (4 - missing_padding)
        return base64.b64decode(t).decode('utf-8', errors='ignore')
    except:
        return text

def main():
    all_raw_links = []
    print("🚀 启动强力收割模式（跳过存活检测）...")

    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=15)
            # 拿到内容先解一次码
            content = smart_decode(r.text)
            
            # 1. 提取 URI 格式 (hysteria2://...)
            links = re.findall(r'hysteria2://[^\s\'"<>#]+#?[^\s\'"<>]*', content)
            all_raw_links.extend(links)
            
            # 2. 针对 YAML 格式补充提取 (匹配 server: ip, port: num)
            # 有些源是 YAML 格式，正则提取 ip:port
            yaml_ips = re.findall(r'server:\s*([^\s]+)\s*port:\s*(\d+)', content)
            # 这里逻辑略复杂，暂时以 URI 提取为主，因为你的源大多包含 URI
            
            print(f"✅ 源 {url.split('/')[-1]}：提取到 {len(links)} 个节点")
        except:
            print(f"❌ 源 {url.split('/')[-1]}：连接超时")

    # 深度去重
    unique_links = list(set(all_raw_links))
    final_nodes = []
    seen_addrs = set()

    print(f"🔍 正在处理 {len(unique_links)} 个节点...")

    for link in unique_links:
        # 提取关键信息用于去重和构建配置
        match = re.search(r'hysteria2://([^@]+)@([^:/?#]+):([0-9, \-]{2,})', link)
        if match:
            auth, ip, port_raw = match.groups()
            # 统一取端口，防止多端口格式报错
            port = re.findall(r'\d+', port_raw)[0]
            
            addr = f"{ip}:{port}"
            if addr not in seen_addrs:
                seen_addrs.add(addr)
                final_nodes.append({
                    "name": f"🐻_{ip}_{port}",
                    "ip": ip, 
                    "port": port_raw, # 保留原始端口/端口段
                    "auth": auth
                })

    # 构建 Clash YAML
    yaml = [
        "proxies:",
    ]
    for n in final_nodes:
        # 使用最稳妥的单行 YAML 格式
        yaml.append(f"  - {{name: \"{n['name']}\", type: hysteria2, server: {n['ip']}, port: {n['port']}, password: {n['auth']}, ssl-allow-insecure: true, sni: www.bing.com, up: 20, down: 100}}")

    yaml.append("\nproxy-groups:\n  - name: \"BearHome-Auto\"\n    type: select\n    proxies:")
    for n in final_nodes:
        yaml.append(f"      - \"{n['name']}\"")
    
    yaml.append("\nrules:\n  - MATCH,BearHome-Auto")

    # 写入文件
    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml))
    
    print(f"🎉 任务完成！已强制保留 {len(final_nodes)} 个节点至 clash.yaml")

if __name__ == "__main__":
    main()
