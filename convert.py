import requests
import yaml
import re
import os
from urllib.parse import urlparse, unquote

# 基础配置
GITHUB_USER = "badhuamao"
URLS_FILE = "urls.txt"
OUTPUT_FILE = "clash.yaml"

def get_proxies_from_text(text):
    """提取纯文本中的 hysteria2 链接"""
    proxies = []
    # 匹配 hy2 或 hysteria2
    links = re.findall(r'(?:hysteria2|hy2)://[^\s"\'|]+', text)
    for link in links:
        try:
            parsed = urlparse(link)
            if '@' in parsed.netloc:
                auth, server_port = parsed.netloc.split('@')
                server, port = server_port.split(':')
                query = dict(q.split('=') for q in parsed.query.split('&') if '=' in q)
                name = unquote(parsed.fragment) if parsed.fragment else f"Hy2_{server}"
                
                proxies.append({
                    "name": name.strip(),
                    "type": "hysteria2",
                    "server": server,
                    "port": int(port),
                    "password": auth,
                    "sni": query.get('sni', server),
                    "skip-cert-verify": True,
                    "alpn": ["h3"]
                })
        except:
            continue
    return proxies

def main():
    all_proxies = []
    if not os.path.exists(URLS_FILE):
        return

    with open(URLS_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    headers = {'User-Agent': 'ClashforWindows/0.20.39'}

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            
            content = resp.text
            # 1. 尝试解析 YAML
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict) and 'proxies' in data:
                    all_proxies.extend(data['proxies'])
                    continue
            except:
                pass
            
            # 2. 如果 YAML 解析失败，尝试提取纯文本链接
            txt_nodes = get_proxies_from_text(content)
            if txt_nodes:
                all_proxies.extend(txt_nodes)
        except Exception as e:
            print(f"处理 {url} 出错: {e}")

    # 生成最终文件
    config = {
        "proxies": all_proxies,
        "proxy-groups": [{"name": "⚡️ 自动选择", "type": "url-test", "proxies": [p['name'] for p in all_proxies], "url": "http://www.gstatic.com/generate_204", "interval": 300}],
        "rules": ["MATCH,⚡️ 自动选择"]
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    main()
