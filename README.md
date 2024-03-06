<p align="center"><a href="https://freedium.cfd" target="_blank"><img src="https://avatars.githubusercontent.com/u/142643505?s=200&v=4" width="20%"></a></p>

<h1 align="center">Freedium: Your paywall breakthrough for Medium!</h1>

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/zhymabekroman)

## FAQ

### What is happened to GitHub organization?

Our whole Github organization is not public for now. Reddit community, that was beginning all of that unfourtunately also gone. So we have moved to Codeberg

### Why did we create Freedium?

In mid-June to mid-July 2023, Medium changed their paywall method, and all old paywall bypass methods we had stopped working. So I became obsessed with the idea of creating a service to bypass Medium's paywalled posts. Honestly I am not a big fan of Medium, but I sometimes read articles to improve my knowledge.

### How does Freedium work?

In the first version of Freedium, we reverse-engineered Medium.com's GraphQL endpoints and built our own parser and toolkits to show you unpaywalled Medium posts. Unfortunately, Medium closed this loophole and nowadays we just pay subscriptions and share access through Freedium. Sometimes we got a bugs because of the self-written parser, but we are working to make Freedium bug-free.

### What language are being used?

We use Python, with Jinja template builder, and some JS magic in Frontend :)

### Wow! I would like to contribute to Freedium. How can I do that?

We need volunteers who have Medium subscriptions because we might get banned by Medium. And if you developer you can start from the this (https://codeberg.org/Freedium-cfd/web) repository.

### Plans, future?

Speed up Freedium, and probably create open source Medium frontend in next life

## Tech stack:

- FastAPI, Gunicorn, Unicorn as worker,
- Tailwinds CSS v3
- Dragonfly (Redis like key-value database)
- Jinja2
- Python 3.9+
- Caddy
- Sentry

## Local run:

Requirements:

- Python 3.9+
- pip
- git

And probably any `Linux` based distro (like Arch btw).

```bash
git clone https://github.com/Freedium-cfd/web ./web
cd ./web
pip install -r requirements.txt
# for linux also do: pip install -r requirements-fast.txt
pip install ./database-lib
pip install ./core
pip install ./rl_string_helper

```

Now we need configure our Freedium instance. Copy `.env_template` to `.env` configuration file and set values, required for you.

If you have linux, execute `./script/start_dev.sh` and open in browser 'localhost:6752'. That will execute Caddy reverse proxy.
If you have other OS or want test without reverse proxy, you can execute server using command `python3 -m server server` and access by address 'localhost:7080':
