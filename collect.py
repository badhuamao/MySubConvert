import base64
import re
import requests

SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/Superspeed.yaml",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/latency",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun",
    "https://raw.githubusercontent.com/badhuamao/FasterVPN-Auto/refs/heads/main/proxies.yaml"
]

def smart_decode(text):
    try:
        t = text.strip()
        missing_padding = len(t) % 4
        if missing_padding: t += '=' * (4 - missing_padding)
        return base64.b64decode(t).decode('utf-8', errors='ignore')
    except:
        return text

def main():
    all_raw_links = []
    print("🚀 正在注入强力伪装参数...")

    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=15)
            content = smart_decode(r.text)
            # 暴力提取所有 hy2 链接
            links = re.findall(r'hysteria2://[^\s\'"<>#]+#?[^\s\'"<>]*', content)
            all_raw_links.extend(links)
        except:
            pass

    unique_links = list(set(all_raw_links))
    final_nodes = []
    seen_addrs = set()

    for link in unique_links:
        # 更加兼容的正则，处理各种字符情况
        match = re.search(r'hysteria2://([^@]+)@([^:/?#\s]+):([0-9, \-]{2,})', link)
        if match:
            auth, ip, port_raw = match.groups()
            port = re.findall(r'\d+', port_raw)[0]
            addr = f"{ip}:{port}"
            
            if addr not in seen_addrs:
                seen_addrs.add(addr)
                final_nodes.append({"ip": ip, "port": port_raw, "auth": auth})

    # 构建电视端最兼容的 YAML 格式
    yaml = ["proxies:"]
    for n in final_nodes:
        node_name = f"🐻_{n['ip']}_{n['port']}"
        # 核心修复点：增加了 sni, skip-cert-verify, 和正确的 alpn
        yaml.append(f"  - {{name: \"{node_name}\", type: hysteria2, server: {n['ip']}, port: {n['port']}, password: {n['auth']}, ssl-allow-insecure: true, sni: www.bing.com, alpn: [h3]}}")

    yaml.append("\nproxy-groups:\n  - name: \"BearHome-Auto\"\n    type: select\n    proxies:")
    for n in final_nodes:
        yaml.append(f"      - \"🐻_{n['ip']}_{n['port']}\"")
    
    yaml.append("\nrules:\n  - MATCH,BearHome-Auto")

    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml))
    
    print(f"🎉 成功！已将 {len(final_nodes)} 个带伪装节点推送到 clash.yaml")

if __name__ == "__main__":
    main()
