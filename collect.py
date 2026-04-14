import base64
import re
import requests

# --- 回归到只有两条链接的状态 ---
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun"
]

def smart_decode(text):
    """自动判断并解码 Base64"""
    try:
        t = text.strip()
        missing_padding = len(t) % 4
        if missing_padding: t += '=' * (4 - missing_padding)
        return base64.b64decode(t).decode('utf-8', errors='ignore')
    except:
        return text

def main():
    all_links = []
    print("🚀 正在恢复双源解析模式...")

    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=15)
            # 关键：先解一次码，防止内容被 Base64 包裹
            content = smart_decode(r.text)
            
            # 使用最稳的正则提取 URI
            links = re.findall(r'hysteria2://[^@\s]+@[^:\s]+:[0-9]+', content)
            all_links.extend(links)
            print(f"✅ 源 {url.split('/')[-1]} 提取到 {len(links)} 个节点")
        except:
            print(f"❌ 访问失败: {url}")

    # 去重
    unique_links = list(set(all_links))
    
    # 构建 Clash YAML
    yaml = ["proxies:"]
    proxy_names = []
    for i, link in enumerate(unique_links):
        match = re.search(r'hysteria2://([^@]+)@([^:]+):(\d+)', link)
        if match:
            auth, ip, port = match.groups()
            name = f"🐻_{ip}_{i}"
            proxy_names.append(name)
            # 仅保留最基础参数，确保 NekoBox 能够识别
            yaml.append(f"  - {{name: \"{name}\", type: hysteria2, server: {ip}, port: {port}, password: {auth}, ssl-allow-insecure: true}}")

    yaml.append("\nproxy-groups:\n  - name: \"BearHome-Auto\"\n    type: select\n    proxies:")
    for name in proxy_names:
        yaml.append(f"      - \"{name}\"")
    
    yaml.append("\nrules:\n  - MATCH,BearHome-Auto")

    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml))
    
    print(f"🎉 恢复完成！当前共有 {len(unique_links)} 个节点。")

if __name__ == "__main__":
    main()
