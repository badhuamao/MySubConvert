import json
import yaml
import requests
import os

# ================= 配置区域 =================
# 建议修改为你自己的 GitHub 用户名和仓库名，方便日志输出
GITHUB_USER = "badhuamao" 
GITHUB_REPO = "MySubConvert"
# ===========================================

def convert():
    # 1. 自动适配文件名大小写
    file_name = "urls.txt"
    if not os.path.exists(file_name):
        if os.path.exists("URLS.TXT"):
            file_name = "URLS.TXT"
        else:
            print("错误：在仓库根目录未找到 urls.txt 或 URLS.TXT")
            return

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            # 读取链接并过滤掉空行和注释
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return

    unique_proxies = {}

    # 2. 遍历链接抓取节点
    for url in urls:
        print(f"正在抓取源: {url}")
        try:
            # 增加超时控制，防止某个源死掉导致整个任务卡死
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            sb_config = response.json()
            
            outbounds = sb_config.get('outbounds', [])
            for out in outbounds:
                # 核心逻辑：只保留 hysteria2 类型
                if out.get('type') == 'hysteria2':
                    tag = out.get("tag", "Unnamed_HY2")
                    
                    # 构造 Clash 节点格式
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
                        "alpn": out.get("tls", {}).get("alpn", ["h3"])
                    }
                    
                    # 只有当包含 obfs 字段时才添加
                    if out.get("obfs"):
                        p["obfs"] = out["obfs"].get("type")
                        p["obfs-password"] = out["obfs"].get("password")
                    
                    # 使用 tag 去重，后抓到的会覆盖前面的同名节点
                    unique_proxies[tag] = p
                    
        except Exception as e:
            print(f"解析源 {url} 失败: {e}")

    all_proxies = list(unique_proxies.values())

    # 3. 如果没搜到节点则退出
    if not all_proxies:
        print("！！！警告：所有源解析完毕，未发现任何有效 HY2 节点，不执行更新。")
        return

    # 4. 构造完整 Clash 配置文件
    proxy_names = [x["name"] for x in all_proxies]
    clash_config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "proxies": all_proxies,
        "proxy-groups": [
            {
                "name": "🚀 HY2提纯订阅",
                "type": "select",
                "proxies": ["⚡ 自动测速"] + proxy_names + ["DIRECT"]
            },
            {
                "name": "⚡ 自动测速",
                "type": "url-test",
                "url": "http://cp.cloudflare.com/generate_204",
                "interval": 300,
                "tolerance": 50,
                "proxies": proxy_names
            }
        ],
        "rules": [
            "MATCH,🚀 HY2提纯订阅"
        ]
    }

    # 5. 写入文件
    try:
        with open("clash.yaml", "w", encoding="utf-8") as f:
            yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)
        
        # 6. 日志输出加速地址
        cdn_url = f"https://ghfast.top/https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/clash.yaml"
        print("\n" + "="*50)
        print(f"✅ 转换成功！共计提取 {len(all_proxies)} 个 HY2 节点")
        print(f"🔗 你的加速订阅地址（直接复制到客户端）:")
        print(f"{cdn_url}")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"写入文件失败: {e}")

if __name__ == "__main__":
    convert()
