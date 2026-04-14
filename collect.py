import base64
import re
import requests

# --- 你提供的所有源 ---
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/Superspeed.yaml",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/latency",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun",
    "https://raw.githubusercontent.com/badhuamao/FasterVPN-Auto/refs/heads/main/proxies.yaml"
]

def smart_decode(text):
    """极致兼容的解码"""
    try:
        t = text.strip()
        missing_padding = len(t) % 4
        if missing_padding: t += '=' * (4 - missing_padding)
        return base64.b64decode(t).decode('utf-8', errors='ignore')
    except:
        return text

def main():
    all_nodes = []
    print("🚀 正在进行原始数据全量抓取...")

    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=15)
            content = smart_decode(r.text)
            
            # 使用最宽泛的正则，只要有 hysteria2:// 就抓出来
            links = re.findall(r'hysteria2://[^@\s]+@[^:\s]+:[0-9, \-]+[^\s]*', content)
            for link in links:
                # 简单解析出 ip 和 port 做个去重标识
                match = re.search(r'@([^:]+):(\d+)', link)
                if match:
                    all_nodes.append({"id": f"{match.group(1)}:{match.group(2)}", "raw": link})
            print(f"✅ 源 {url.split('/')[-1]} 提取成功")
        except:
            print(f"❌ 源 {url.split('/')[-1]} 连接跳过")

    # 去重
    unique_data = []
    seen = set()
    for n in all_nodes:
        if n['id'] not in seen:
            seen.add(n['id'])
            unique_data.append(n['raw'])

    # 构建极简 Clash YAML
    yaml_lines = ["proxies:"]
    proxy_names = []

    for i, link in enumerate(unique_data):
        # 从链接里扣数据
        m = re.search(r'hysteria2://([^@]+)@([^:/?#]+):([0-9, \-]{2,})', link)
        if m:
            auth, server, port = m.groups()
            name = f"🐻_{server}_{i}"
            proxy_names.append(name)
            # 采用最精简的参数，不加多余的 alpn 干扰电视内核判断
            yaml_lines.append(f"  - {{name: \"{name}\", type: hysteria2, server: {server}, port: {port}, password: {auth}, ssl-allow-insecure: true, sni: www.apple.com}}")

    yaml_lines.append("\nproxy-groups:\n  - name: \"BearHome-Auto\"\n    type: select\n    proxies:")
    for name in proxy_names:
        yaml_lines.append(f"      - \"{name}\"")
    
    yaml_lines.append("\nrules:\n  - MATCH,BearHome-Auto")

    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml_lines))
    
    print(f"🎉 任务完成！共计 {len(unique_data)} 个节点已入库。")

if __name__ == "__main__":
    main()
