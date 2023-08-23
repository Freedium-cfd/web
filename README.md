# Freedium.cfd web site implementation

## Start:
```bash
# Clone this repo and init all submodules:
git clone https://github.com/Freedium-cfd/web
git submodule update --init
# Install Python3, for apt based distros:
sudo apt install python3
# Optionally: init venv
python3 -m venv venv
source venv/bin/activate
# Install all requirements
pip install -r requirements.txt
# if you have linux, execute `start_dev.sh` and open in browser 'localhost:6752'. That will execute Caddy reverse proxy.
# if you have other OS, you can execute server module without reverse proxy and access by address 'localhost:7080'
```

## TODO:
 - Introducing Freedium as a fully functional open source frontend for Medium.com!
 - New main page with statistics and most interesting Medium posts
 - Add Docker Compose file
 - Add donations or ADs
 - Porting some parts to Golang
