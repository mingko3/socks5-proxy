import requests
import yaml

url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=getproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=2000"
response = requests.get(url)
proxies = response.text.splitlines()

clash_proxies = []
for idx, proxy in enumerate(proxies):
    try:
        ip, port = proxy.split(':')
        clash_proxy = {
            'name': f'socks5-{idx}',
            'type': 'socks5',
            'server': ip,
            'port': int(port),
        }
        clash_proxies.append(clash_proxy)
    except ValueError:
        continue

config = {'proxies': clash_proxies}
with open('proxy.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
