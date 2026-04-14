import base64
import re
import requests

# --- 配置区：你的源链接 ---
SOURCE_URLS = [
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/Superspeed.yaml",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/latency",
    "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/list",
    "https://extract.ashly.dpdns.org/?pw=autorun",
    "https://raw.githubusercontent.com/badhuamao/FasterVPN-Auto/refs/heads/main/proxies.yaml"
]

def smart_decode(text):
    """自动尝试解码内容"""
    try:
        t = text.strip()
        # 补齐 Base64 填充
        missing_padding = len(t) % 4
        if missing_padding: t += '=' * (4 - missing_padding)
        return base64.b64decode(t).decode('utf-8', errors='ignore')
    except:
        return text

def main():
    all_raw_links = []
    print("🚀 正在执行全量暴力收割，不进行任何测速过滤...")

    # 1. 抓取所有内容
    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=15)
            # 对内容尝试解码（如果是 Base64 订阅）
            content = smart_decode(r.text)
            
            # 暴力提取所有符合 hy2 链接格式的内容
            links = re.findall(r'hysteria2://[^\s\'"<>#]+#?[^\s\'"<>]*', content)
            all_raw_links.extend(links)
            print(f"✅ 从源 [{url.split('/')[-1]}] 提取到 {len(links)} 个节点")
        except Exception as e:
            print(f"❌ 访问失败 [{url.split('/')[-1]}]: {e}")

    # 2. 深度去重
    unique_links = list(set(all_raw_links))
    final_nodes = []
    seen_addrs = set()

    for link in unique_links:
        # 匹配格式: hysteria2://auth@ip:port
        match = re.search(r'hysteria2://([^@]+)@([^:/?#\s]+):([0-9, \-]{2,})', link)
        if match:
            auth, ip, port_raw = match.groups()
            # 用于去重的 ID
            addr_id = f"{ip}:{port_raw}"
            
            if addr_id not in seen_addrs:
                seen_addrs.add(addr_id)
                final_nodes.append({
                    "ip": ip,
                    "port": port_raw,
                    "auth": auth
                })

    # 3. 构造电视端最兼容的 Clash YAML 字符串
    yaml = ["proxies:"]
    proxy_names = []
    
    for n in final_nodes:
        node_name = f"🐻_{n['ip']}_{n['port']}"
        proxy_names.append(node_name)
        # 添加标准参数，确保电视端兼容性
        yaml.append(f"  - {{name: \"{node_name}\", type: hysteria2, server: {n['ip']}, port: {n['port']}, password: {n['auth']}, ssl-allow-insecure: true, sni: www.bing.com, alpn: [h3]}}")

    # 代理组配置
    yaml.append("\nproxy-groups:")
    yaml.append("  - name: \"BearHome-Auto\"")
    yaml.append("    type: select")
    yaml.append("    proxies:")
    for name in proxy_names:
        yaml.append(f"      - \"{name}\"")
    
    # 基础规则
    yaml.append("\nrules:")
    yaml.append("  - MATCH,BearHome-Auto")

    # 4. 写入 clash.yaml
    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml))
    
    print(f"🎉 任务完成！共计 {len(final_nodes)} 个节点已直接写入 clash.yaml")

if __name__ == "__main__":
    main()
