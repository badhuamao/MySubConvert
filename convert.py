import json
import yaml
import requests
import os

# ================= 配置区域 =================
GITHUB_USER = "badhuamao" 
GITHUB_REPO = "MySubConvert"
# ===========================================

def convert():
    file_name = "urls.txt"
    if not os.path.exists(file_name):
        file_name = "URLS.TXT" if os.path.exists("URLS.TXT") else None
        if not file_name:
            print("错误：未找到 urls.txt")
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
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            content = response.text
            
            data = None
            # 策略：先尝试 JSON (Sing-box)，失败再尝试 YAML (Clash)
            try:
                data = json.loads(content)
                print(f"检测到 JSON 格式")
                outbounds = data.get('outbounds', [])
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
                            "sni": out.get("tls", {}).get("server_name") if out.get("tls") else out.get("server"),
                            "skip-cert-verify": out.get("tls", {}).get("insecure", False) if out.get("tls") else True,
                            "alpn": out.get("tls", {}).get("alpn", ["h3"]) if out.get("tls") else ["h3"]
                        }
                        unique_proxies[tag] = p
            except json.JSONDecodeError:
                try:
                    data = yaml.safe_load(content)
                    print(f"检测到 YAML 格式")
                    # Clash 格式通常在 'proxies' 列表里
                    proxies_list = data.get('proxies', [])
                    for out in proxies_list:
                        if out.get('type') == 'hysteria2':
                            tag = out.get("name", "Unnamed_HY2")
                            # 直接保存，因为 YAML 里的字段通常已经是 Clash 格式
                            unique_proxies[tag] = out
                except Exception as e:
                    print(f"YAML 解析也失败了: {e}")

        except Exception as e:
            print(f"处理源 {url} 出错: {e}")

    all_proxies = list(unique_proxies.values())
    if not all_proxies:
        print("未发现任何有效 HY2 节点")
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
            {"name": "🚀 HY2提纯订阅", "type": "select", "proxies": ["⚡ 自动测速"] + proxy_names + ["DIRECT"]},
            {"name": "⚡ 自动测速", "type": "url-test", "url": "http://cp.cloudflare.com/generate_204", "interval": 300, "proxies": proxy_names}
        ],
        "rules": ["MATCH,🚀 HY2提纯订阅"]
    }

    with open("clash.yaml", "w", encoding="utf-8") as f:
        yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)
    
    cdn_url = f"https://ghfast.top/https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/clash.yaml"
    print(f"\n✅ 转换成功！当前共有 {len(all_proxies)} 个 HY2 节点")
    print(f"🔗 加速订阅地址: {cdn_url}\n")

if __name__ == "__main__":
    convert()
