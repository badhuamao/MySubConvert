import json
import yaml
import requests
import os

def convert():
    # 自动适配大小写文件名
    file_name = "urls.txt"
    if not os.path.exists(file_name):
        if os.path.exists("URLS.TXT"):
            file_name = "URLS.TXT"
        else:
            print("错误：找不到 urls.txt 或 URLS.TXT")
            return

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    unique_proxies = {}

    for url in urls:
        print(f"正在抓取: {url}")
        try:
            response = requests.get(url, timeout=30)
            sb_config = response.json()
            
            # 兼容性检查：确保有 outbounds 字段
            outbounds = sb_config.get('outbounds', [])
            for out in outbounds:
                if out.get('type') == 'hysteria2':
                    tag = out.get("tag", "Unnamed_HY2")
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
                    if out.get("obfs"):
                        p["obfs"] = out["obfs"].get("type")
                        p["obfs-password"] = out["obfs"].get("password")
                    
                    unique_proxies[tag] = p
        except Exception as e:
            print(f"解析 {url} 失败: {e}")

    all_proxies = list(unique_proxies.values())

    if not all_proxies:
        # 如果没搜到 HY2，创建一个占位节点防止 Clash 报错，或者直接退出
        print("警告：抓取结束，但未发现任何有效 HY2 节点")
        return

    # 构造 Clash 结构
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
    print(f"成功生成 clash.yaml，包含 {len(all_proxies)} 个 HY2 节点")

if __name__ == "__main__":
    convert()
