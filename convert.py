import json
import yaml
import requests

def convert():
    # 1. 读取 urls.txt
    try:
        with open("urls.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print("未找到 urls.txt")
        return

    unique_proxies = {}

    for url in urls:
        print(f"正在抓取: {url}")
        try:
            response = requests.get(url, timeout=30)
            sb_config = response.json()
            
            for out in sb_config.get('outbounds', []):
                # 核心改动：只保留 hysteria2 类型，其他的直接跳过
                if out.get('type') != 'hysteria2':
                    continue
                
                tag = out.get("tag")
                
                # 如果有重名节点，后抓到的覆盖先抓到的（或者你也可以选择保留第一个）
                p = {
                    "name": tag,
                    "server": out.get("server"),
                    "port": out.get("server_port"),
                    "type": "hysteria2",
                    "password": out.get("password"),
                    "up": str(out.get("up_mbps", 10)) + " Mbps",
                    "down": str(out.get("down_mbps", 100)) + " Mbps",
                    "sni": out.get("tls", {}).get("server_name"),
                    "skip-cert-verify": out.get("tls", {}).get("insecure", False),
                    "alpn": out.get("tls", {}).get("alpn", [])
                }

                # 处理 obfs
                if out.get("obfs"):
                    p["obfs"] = out["obfs"].get("type")
                    p["obfs-password"] = out["obfs"].get("password")
                
                unique_proxies[tag] = p

        except Exception as e:
            print(f"处理链接 {url} 出错: {e}")

    # 字典转列表
    all_proxies = list(unique_proxies.values())

    if not all_proxies:
        print("警告：未在源链接中发现任何 HY2 节点！")
        return

    # 2. 构造 Clash 结构
    proxy_names = [x["name"] for x in all_proxies]
    clash_config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "rule",
        "proxies": all_proxies,
        "proxy-groups": [
            {"name": "🚀 HY2节点选择", "type": "select", "proxies": ["⚡ 自动测速"] + proxy_names + ["DIRECT"]},
            {"name": "⚡ 自动测速", "type": "url-test", "url": "http://cp.cloudflare.com/generate_204", "interval": 300, "proxies": proxy_names}
        ],
        "rules": ["MATCH,🚀 HY2节点选择"]
    }

    with open("clash.yaml", "w", encoding="utf-8") as f:
        yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)
    print(f"转换成功！已过滤掉非 HY2 协议，当前共有 {len(all_proxies)} 个 HY2 节点。")

if __name__ == "__main__":
    convert()
