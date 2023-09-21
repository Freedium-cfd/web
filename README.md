# Freedium.cfd web site implementation

## Browser extension:

You can use this Violentmonkey/Tampermonkey user script to automatically redirect medium pages to [freedium.cfd](https://freedium.cfd/):
https://gist.github.com/mathix420/e0604ab0e916622972372711d2829555

## Start:
```bash
# Clone this repo and init all submodules:
git clone https://github.com/Freedium-cfd/web ~/web
cd ~/web
git submodule update --init
cd server/toolkits/core
git submodule update --init
cd ~/web
# Install Python3, for apt based distros:
sudo apt install python3
# Optionally: init venv
python3 -m venv venv
source venv/bin/activate
# Install all requirements
pip install -r requirements.txt
# if you have linux, execute `start_dev.sh` and open in browser 'localhost:6752'. That will execute Caddy reverse proxy.
# if you have other OS or want without reverse proxy, you can execute server module without reverse proxy and access by address '0.0.0.0:7080':
python3 -m server server
```

## TODO:
 - Add support for embed link preview & iframe support
 - Introducing Freedium as a fully functional open source frontend for Medium.com!
 - Speed up with Cython
