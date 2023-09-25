# Freedium web site implementation

## Browser extension:
Huge thanks to `mathix420`

You can use this Violentmonkey/Tampermonkey user script to automatically redirect Medium pages to [Freedium](https://freedium.cfd/):
https://gist.github.com/mathix420/e0604ab0e916622972372711d2829555

## Bookmark:
Huge thanks to `blazeknifecatcher`. Source: https://www.reddit.com/r/paywall/comments/15jsr6z/bypass_mediumcom_paywall/

To create bookmark that redirects current Medium page to Freedium, create a new bookmark, but instead of adding the URL, add this:

```
javascript:window.location="https://freedium.cfd/"+encodeURIComponent(window.location)
```

This will make it so when you click on that bookmark button, it will open the bypassed version of it on freedium.cfd.

Alternatively, if you want the bookmarklet to open in a new tab instead of the current tab, use this:

```
javascript:(function(){window.open("https://freedium.cfd/"+encodeURIComponent(window.location))})();
```
This will make it so that when you click on that bookmark button, it will open the bypassed version of it.

## Execute local:
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
 - Speed up using Cython
 - Introducing Freedium as a fully functional open source frontend for Medium.com!
