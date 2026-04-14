import re
import yaml
import json
import base64
from urllib.parse import urlparse, unquote

def parse_link_to_dict(link):
    """专门处理散装链接的函数"""
    try:
        if link.startswith('hysteria2://') or link.startswith('hy2://'):
            parsed = urlparse(link)
            netloc_parts = parsed.netloc.split('@')
            auth = netloc_parts[0]
            server_port = netloc_parts[1].split(':')
            
            # 提取参数
            query = dict(q.split('=') for q in parsed.query.split('&') if '=' in q)
            name = unquote(parsed.fragment) or f"Hy2_{server_port[0]}"
            
            return {
                "name": name,
                "type": "hysteria2",
                "server": server_port[0],
                "port": int(server_port[1]),
                "password": auth,
                "sni": query.get('sni', server_port[0]),
                "skip-cert-verify": True, # 强制跳过证书检查，解决你截图中的不可用问题
                "obfs": query.get('obfs', 'none'),
                "obfs-password": query.get('obfs-password', '')
            }
        
        # 如果是 vmess (Base64)
        elif link.startswith('vmess://'):
            v2_raw = base64.b64decode(link[8:]).decode('utf-8')
            v2_json = json.loads(v2_raw)
            return {
                "name": v2_json.get('ps', 'vmess_node'),
                "type": "vmess",
                "server": v2_json.get('add'),
                "port": int(v2_json.get('port')),
                "uuid": v2_json.get('id'),
                "alterId": int(v2_json.get('aid', 0)),
                "cipher": "auto",
                "tls": v2_json.get('tls') == "tls",
                "network": v2_json.get('net', 'tcp')
            }
            
        # 更多协议 (vless, trojan) 可以在此添加...
    except Exception as e:
        print(f"解析链接失败: {e}")
    return None

def process_content(content):
    """主处理函数"""
    proxies = []
    
    # 尝试 1: 看看是不是标准的 YAML/JSON 订阅
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict) and 'proxies' in data:
            return data['proxies']
    except:
        pass

    # 尝试 2: 如果解析失败，按行处理，寻找协议链接
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 匹配各种协议开头的链接
        if any(line.startswith(p) for p in ['hysteria2://', 'hy2://', 'vmess://', 'vless://', 'trojan://']):
            node = parse_link_to_dict(line)
            if node:
                proxies.append(node)
                
    return proxies
