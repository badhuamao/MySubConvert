import base64
import re
import requests

# 【只保留第一条原始链接】
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list"
]

def main():
    all_links = []
    print("正在进行回归测试：仅处理原始第一条链接...")

    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=15)
            text = r.text
            # 1. 先直接搜
            links = re.findall(r'hysteria2://[^@\s]+@[^:\s]+:[0-9]+', text)
            
            # 2. 如果直接搜不到，尝试解 Base64 后再搜
            if not links:
                try:
                    missing_padding = len(text.strip()) % 4
                    decoded = base64.b64decode(text.strip() + '=' * missing_padding).decode('utf-8', errors='ignore')
                    links = re.findall(r'hysteria2://[^@\s]+@[^:\s]+:[0-9]+', decoded)
                except:
                    pass
            all_links.extend(links)
        except:
            print("连接原始链接失败")

    # 去重
    unique_links = list(set(all_links))
    
    # 构造最简单的 Clash 格式
    yaml = ["proxies:"]
    proxy_names = []
    for i, link in enumerate(unique_links):
        match = re.search(r'hysteria2://([^@]+)@([^:]+):(\d+)', link)
        if match:
            auth, ip, port = match.groups()
            name = f"🐻_{ip}_{i}"
            proxy_names.append(name)
            yaml.append(f"  - {{name: \"{name}\", type: hysteria2, server: {ip}, port: {port}, password: {auth}, ssl-allow-insecure: true, skip-cert-verify: true}}")

    yaml.append("\nproxy-groups:\n  - name: \"BearHome-Auto\"\n    type: select\n    proxies:")
    for name in proxy_names:
        yaml.append(f"      - \"{name}\"")
    yaml.append("\nrules:\n  - MATCH,BearHome-Auto")

    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml))
    
    print(f"回归测试完成，共抓取到 {len(unique_links)} 个节点。")

if __name__ == "__main__":
    main()
