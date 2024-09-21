# source: https://github.com/thorio/KGrabber/issues/35#issuecomment-1164056688
# curl -L --user-agent "Mozilla/5.0" --cipher AES256-SHA256 --tls-max 1.2 "<url>"

import sys

async def main():
    # Create a default SSL context
    ssl_context = ssl.create_default_context()

    # Disable TLS versions older than 1.2
    ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_3 # ??? - --tls-max

    # Set cipher suite
    ssl_context.set_ciphers('AES256-SHA')

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0'}

    # Configure aiohttp ClientSession with custom SSL context and User-Agent
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get('https://github.zhaoqumao.com/veggiemonk/awesome-docker', ssl=ssl_context) as response:
            print(await response.text())
            print(response.status)


### 

# Port to Python 3.10+
# https://github.com/fedora-infra/fedora-messaging/pull/250/commits/f3439350de7f55d42f4350e662392e9ffbdde028

ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH) # ??? - purpose
if sys.version_info >= (3, 7):
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
else:
    ssl_context.options |= ssl.OP_NO_SSLv2
    ssl_context.options |= ssl.OP_NO_SSLv3
    ssl_context.options |= ssl.OP_NO_TLSv1
    ssl_context.options |= ssl.OP_NO_TLSv1_1