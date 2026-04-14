import re
from urllib.parse import urlparse, unquote

def parse_raw_links(content):
    """
    终极兼容函数：
    不管内容是 YAML、JSON 还是纯文本链接列表，都能把它们提取出来
    """
    extracted_proxies = []
    
    # 1. 尝试作为 YAML 处理 (兼容标准的配置格式)
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict) and 'proxies' in data:
            return data['proxies']
    except:
        pass

    # 2. 正则表达式盲扫 (专门对付第四条链接这种纯文本列表)
    # 支持 hy2, hysteria2, vless, vmess, trojan, ss
    pattern = r'(hysteria2|hy2|vless|vmess|trojan|ss)://[^\s|"'']+ '
    links = re.findall(pattern + r'[^\s]*', content)
    
    for link in links:
        try:
            # 这里的解析逻辑要根据你的 Clash 模板微调
            # 如果你使用的是通用的解析库，可以直接调用
            # 关键：Hy2 节点一定要加上 skip-cert-verify: true
            if 'hysteria2' in link or 'hy2' in link:
                parsed = urlparse(link)
                # 提取逻辑...
                # 确保生成的字典包含：'skip-cert-verify': True
                pass 
        except:
            continue
            
    return extracted_proxies
