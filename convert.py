import requests
import yaml
import re
from urllib.parse import urlparse, unquote

def get_proxies_from_text(text):
    """
    专门对付第四条链接：从乱七八糟的文本里强行抠出 Hy2 链接
    """
    proxies = []
    # 正则表达式：匹配 hysteria2:// 或 hy2:// 开头的链接
    lines = re.findall(r'(?:hysteria2|hy2)://[^\s"\'|]+', text)
    
    for link in lines:
        try:
            parsed = urlparse(link)
            # 提取认证信息和服务器地址
            if '@' in parsed.netloc:
                auth, server_port = parsed.netloc.split('@')
                server, port = server_port.split(':')
            else:
                continue # 格式不对则跳过
            
            # 提取参数
            query = dict(q.split('=') for q in parsed.query.split('&') if '=' in q)
            name = unquote(parsed.fragment) if parsed.fragment else f"Hy2_{server}"
            
            # 构造 Clash 格式的字典
            node = {
                "name": name,
                "type": "hysteria2",
                "server": server,
                "port": int(port),
                "password": auth,
                "sni": query.get('sni', server),
                "skip-cert-verify": True, # 强制开启，解决你之前遇到的不可用问题
                "alpn": query.get('alpn', 'h3').split(','),
                "up": query.get('up', '100'),
                "down": query.get('down', '100')
            }
            # 如果有 obfs
            if query.get('obfs') and query.get('obfs') != 'none':
                node["obfs"] = query.get('obfs')
                node["obfs-password"] = query.get('obfs-password', '')
                
            proxies.append(node)
        except Exception as e:
            print(f"解析单个节点失败: {e}")
            continue
    return proxies

# 在你的主循环里，针对每个 URL 的处理逻辑：
# response = requests.get(url, headers=headers)
# if "hysteria2://" in response.text:
#     new_nodes = get_proxies_from_text(response.text)
#     all_proxies.extend(new_nodes)
