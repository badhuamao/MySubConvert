import requests
import yaml
import os

# 基础配置
URLS_FILE = "urls.txt"
OUTPUT_FILE = "clash.yaml"

def main():
    all_proxies = []
    
    # 检查 urls.txt 是否存在
    if not os.path.exists(URLS_FILE):
        print("未找到 urls.txt 文件")
        return

    # 读取链接列表
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    # 设置通用的 User-Agent 模拟 Clash 客户端抓取
    headers = {'User-Agent': 'ClashforWindows/0.20.39'}

    for url in urls:
        try:
            print(f"正在抓取: {url}")
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"抓取失败，状态码: {resp.status_code}")
                continue
            
            # 解析 YAML 内容
            data = yaml.safe_load(resp.text)
            if isinstance(data, dict) and 'proxies' in data:
                nodes = data['proxies']
                all_proxies.extend(nodes)
                print(f"成功获取 {len(nodes)} 个节点")
        except Exception as e:
            print(f"处理链接时出错: {e}")

    # 构造最终的 Clash 配置文件
    # 这里的 proxy-groups 和 rules 采用了最基础的直连/分流逻辑
    config = {
        "proxies": all_proxies,
        "proxy-groups": [
            {
                "name": "⚡️ 自动选择",
                "type": "url-test",
                "proxies": [p['name'] for p in all_proxies],
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300
            }
        ],
        "rules": [
            "MATCH,⚡️ 自动选择"
        ]
    }

    # 写入文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    print(f"解析完成，已写入 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
