import requests
import yaml
import socket
import socks
import base64

def test_proxy(ip, port):
    try:
        socks.set_default_proxy(socks.SOCKS5, ip, int(port))
        socket.socket = socks.socksocket
        response = requests.get('http://ip-api.com/json', timeout=5)
        return response.status_code == 200
    except Exception:
        return False

url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=getproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=2000"
response = requests.get(url)
proxies = response.text.splitlines()

# 生成 Clash YAML 配置
clash_proxies = []
sub_lines = []
for idx, proxy in enumerate(proxies):
    try:
        ip, port = proxy.split(':')
        if test_proxy(ip, port):
            # Clash 格式
            clash_proxy = {
                'name': f'socks5-{idx}',
                'type': 'socks5',
                'server': ip,
                'port': int(port),
            }
            clash_proxies.append(clash_proxy)
            # Base64 编码的 socks5:// 链接
            node_str = f'socks5://{ip}:{port}#{f"socks5-{idx}"}'
            sub_lines.append(base64.b64encode(node_str.encode()).decode())
    except ValueError:
        continue

# 保存 Clash YAML 配置
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

# 保存 Base64 编码的 sub 文件
with open('sub', 'w') as f:
    f.write('\n'.join(sub_lines))
