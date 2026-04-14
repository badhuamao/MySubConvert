import json
import yaml
import requests

def convert():
    # 目标 Sing-box RAW 链接
    url = "https://raw.githubusercontent.com/Supprise0901/Fetch/refs/heads/main/Superspeed.yaml"
    
    try:
        response = requests.get(url, timeout=30)
        sb_config = response.json()
        
        proxies = []
        
        for out in sb_config.get('outbounds', []):
            # 过滤掉非节点 outbound
            if out.get('type') in ['direct', 'block', 'dns', 'selector', 'urltest']:
                continue
                
            p = {
                "name": out.get("tag"),
                "server": out.get("server"),
                "port": out.get("server_port"),
            }

            # Hysteria2
            if out.get('type') == 'hysteria2':
                p.update({
                    "type": "hysteria2",
                    "password": out.get("password"),
                    "up": str(out.get("up_mbps", 10)) + " Mbps",
                    "down": str(out.get("down_mbps", 100)) + " Mbps",
                    "sni": out.get("tls", {}).get("server_name"),
                    "skip-cert-verify": out.get("tls", {}).get("insecure", False),
                    "alpn": out.get("tls", {}).get("alpn", [])
                })
                if out.get("obfs"):
                    p["obfs"] = out["obfs"].get("type")
                    p["obfs-password"] = out["obfs"].get("password")

            # Trojan
            elif out.get('type') == 'trojan':
                p.update({
                    "type": "trojan",
                    "password": out.get("password"),
                    "sni": out.get("tls", {}).get("server_name"),
                    "skip-cert-verify": out.get("tls", {}).get("insecure", False)
                })

            # VLESS
            elif out.get('type') == 'vless':
                p.update({
                    "type": "vless",
                    "uuid": out.get("uuid"),
                    "tls": out.get("tls", {}).get("enabled", False),
                    "sni": out.get("tls", {}).get("server_name"),
                    "skip-cert-verify": out.get("tls", {}).get("insecure", False),
                    "network": out.get("transport", {}).get("type"),
                    "udp": True
                })
                if p["network"] == "ws":
                    p["ws-opts"] = {
                        "path": out["transport"].get("path"),
                        "headers": out["transport"].get("headers", {})
                    }
            
            if "type" in p:
                proxies.append(p)

        # 构造 Clash 结构
        proxy_names = [x["name"] for x in proxies]
        clash_config = {
            "port": 7890,
            "socks-port": 7891,
            "allow-lan": True,
            "mode": "rule",
            "log-level": "info",
            "proxies": proxies,
            "proxy-groups": [
                {"name": "🚀 节点选择", "type": "select", "proxies": ["⚡ 自动测速"] + proxy_names + ["DIRECT"]},
                {"name": "⚡ 自动测速", "type": "url-test", "url": "http://cp.cloudflare.com/generate_204", "interval": 300, "proxies": proxy_names}
            ],
            "rules": ["MATCH,🚀 节点选择"]
        }

        with open("clash.yaml", "w", encoding="utf-8") as f:
            yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)
        print("转换成功！")

    except Exception as e:
        print(f"转换失败: {e}")

if __name__ == "__main__":
    convert()
