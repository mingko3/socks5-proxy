import requests
import yaml
import logging
from bs4 import BeautifulSoup
import base64

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_proxy(ip, port, proxy_type):
    """
    测试代理是否可用
    """
    if proxy_type == 'http':
        proxies = {'https': f'[invalid url, do not cite]
    elif proxy_type == 'socks5':
        proxies = {'https': f'socks5://{ip}:{port}'}
    else:
        return False
    try:
        response = requests.get('[invalid url, do not cite] proxies=proxies, timeout=10)
        logging.info(f"Proxy {ip}:{port} ({proxy_type}) test successful")
        return response.status_code == 200
    except Exception as e:
        logging.warning(f"Proxy {ip}:{port} ({proxy_type}) test failed: {str(e)}")
        return False

# 代理来源列表
proxy_sources = [
    {
        'name': 'OpenProxyList',
        'url': 'https://openproxylist.com/proxy/',
        'type': 'html'
    },
    {
        'name': 'RoosterkidSOCKS5',
        'url': 'https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5.txt',
        'type': 'text',
        'proxy_type': 'socks5'
    },
    {
        'name': 'RoosterkidHTTPS',
        'url': 'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS.txt',
        'type': 'text',
        'proxy_type': 'http'
    }
]

# 初始化代理列表
clash_proxies = []
sub_lines = []

# 处理每个代理来源
for source in proxy_sources:
    logging.info(f"Fetching proxies from {source['name']}")
    try:
        response = requests.get(source['url'], timeout=15)
        if response.status_code != 200:
            logging.warning(f"{source['name']} returned status code {response.status_code}")
            continue
        
        if source['type'] == 'text':
            # 处理文本文件（如 GitHub Raw 文件）
            proxies = response.text.splitlines()
            for idx, proxy in enumerate(proxies):
                try:
                    ip, port = proxy.split(':')
                    proxy_type = source['proxy_type']
                    # 测试代理（可选，根据需求启用或禁用）
                    # if test_proxy(ip, int(port), proxy_type):
                    name = f'{proxy_type}-{source["name"]}-{idx}'
                    clash_proxy = {
                        'name': name,
                        'type': proxy_type,
                        'server': ip,
                        'port': int(port),
                    }
                    clash_proxies.append(clash_proxy)
                    node_str = f'{proxy_type}://{ip}:{port}#{name}'
                    sub_lines.append(base64.b64encode(node_str.encode()).decode())
                    if len(clash_proxies) >= 50:  # 限制最大 50 个代理
                        break
                except ValueError:
                    logging.warning(f"Invalid proxy format from {source['name']}: {proxy}")
                    continue
        elif source['type'] == 'html':
            # 处理 HTML 页面（如 openproxylist.com）
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')  # 假设代理列表在第一个表格中
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                for idx, row in enumerate(rows):
                    cells = row.find_all('td')
                    if len(cells) >= 3:  # 假设 IP、Port、Type 是前三个列
                        ip = cells[0].text.strip()
                        port = cells[1].text.strip()
                        proxy_type_raw = cells[2].text.strip().lower()
                        if proxy_type_raw == 'socks5':
                            proxy_type = 'socks5'
                        elif proxy_type_raw in ['http', 'https']:
                            proxy_type = 'http'
                        else:
                            continue
                        try:
                            port = int(port)
                            # 测试代理（可选，根据需求启用或禁用）
                            # if test_proxy(ip, port, proxy_type):
                            name = f'{proxy_type}-{source["name"]}-{idx}'
                            clash_proxy = {
                                'name': name,
                                'type': proxy_type,
                                'server': ip,
                                'port': port,
                            }
                            clash_proxies.append(clash_proxy)
                            node_str = f'{proxy_type}://{ip}:{port}#{name}'
                            sub_lines.append(base64.b64encode(node_str.encode()).decode())
                            if len(clash_proxies) >= 50:  # 限制最大 50 个代理
                                break
                        except ValueError:
                            logging.warning(f"Invalid proxy format from {source['name']}: {ip}:{port}")
                            continue
            else:
                logging.warning(f"No table found in {source['name']} HTML")
    except Exception as e:
        logging.error(f"Failed to fetch from {source['name']}: {str(e)}")

# 如果没有可用代理，添加占位符
if not clash_proxies:
    logging.warning("No valid proxies found, adding placeholder")
    clash_proxies.append({
        'name': 'placeholder',
        'type': 'socks5',
        'server': '127.0.0.1',
        'port': 8080
    })
    sub_lines.append(base64.b64encode('socks5://127.0.0.1:8080#placeholder'.encode()).decode())

# 生成 Clash 配置文件
clash_config = {
    'proxies': clash_proxies,
    'proxy-groups': [
        {
            'name': 'auto',
            'type': 'select',
            'proxies': [proxy['name'] for proxy in clash_proxies] + ['DIRECT']
        },
        {
            'name': 'Proxy',
            'type': 'select',
            'proxies': [proxy['name'] for proxy in clash_proxies]
        }
    ],
    'rules': [
        'DOMAIN-SUFFIX,google.com,Proxy',
        'DOMAIN-SUFFIX,youtube.com,Proxy',
        'GEOIP,CN,DIRECT',
        'MATCH,Proxy'
    ]
}
with open('proxy.yaml', 'w') as f:
    yaml.dump(clash_config, f, default_flow_style=False, allow_unicode=True)

# 生成 Base64 编码的订阅文件
with open('sub', 'w') as f:
    f.write('\n'.join(sub_lines))

logging.info(f"Generated {len(clash_proxies)} proxies in proxy.yaml and sub")
