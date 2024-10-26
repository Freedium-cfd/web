<p align="center"><a href="https://freedium.cfd" target="_blank"><img src="https://avatars.githubusercontent.com/u/142643505?s=200&v=4" width="20%"></a></p>

<h1 align="center">Freedium: Your paywall breakthrough for Medium!</h1>

<a href="https://www.patreon.com/Freedium">
    <img width="200px" height="50px" alt="Become a Patron" src="https://github.com/elsiehupp/patron-buttons/blob/master/svg/become_a_patron_4x1_black_logo_white_text_on_coral.svg?raw=True">
</a>

## FAQ

### Why did we create Freedium?

In mid-June to mid-July 2023, Medium changed their paywall method, and all old paywall bypass methods we had stopped working. So I became obsessed with the idea of creating a service to bypass Medium's paywalled posts. Honestly I am not a big fan of Medium, but I sometimes read articles to improve my knowledge.

### How does Freedium work?

In the first version of Freedium, we reverse-engineered Medium.com's GraphQL endpoints and built our own parser and toolkits to show you unpaywalled Medium posts. Unfortunately, Medium closed this loophole and nowadays we just pay subscriptions and share access through Freedium. Sometimes we got a bugs because of the self-written parser, but we are working to make Freedium bug-free.

### Wow! I would like to contribute to Freedium. How can I do that?

We need volunteers who have Medium subscriptions because we might get banned by Medium. And if you developer you can start from the this (https://codeberg.org/Freedium-cfd/web) repository.

### Plans, future?

Speed up Freedium, add support for more services than just Medium and (probably) create open source Medium frontend (in next life)

## Technologies:

- Backend: Python 3.9+, Unicorn, FastAPI, Jinja2, Sentry
- Frontend: Tailwinds CSS v3
- Database: PostgreSQL, Dragonfly (Redis and Memcached compatible key-value database)
- Utils: Caddy, Docker, Docker Compose, Cloudflare WARP proxy (wgcf)

## Local run:

Requirements:

- Docker
- git
- Linux. Officially, we can't guarantee that Freedium will work on other OS.

To configure your Freedium instance, follow these steps:

1. Clone the repository:

   ```
   git clone https://codeberg.org/Freedium-cfd/web/ ./web --depth 1
   cd ./web
   ```

2. Create and configure the environment file:

   ```
   cp .env_template .env
   ```

   Open the `.env` file and adjust the values as needed for your setup.

3. Set up the Docker network:

   ```
   sudo docker network create caddy_net
   ```

4. Start the Freedium services:
   ```
   sudo docker compose -f ./docker-compose/docker-compose.yml up
   ```

And now you can access local instance of Freedium by opening browser and type `http://localhost:6752`.

These steps will set up and run your local Freedium instance.

## TODO:

- Integrate library notifiers - https://github.com/liiight/notifiers
- Do not use 'shturman/dante' image, because it is does not have updates for a long time. (Probably) Use https://hub.docker.com/r/vimagick/dante/

## Roadmap

- [ ] Speed up parser logic, port to Cython or rewrite to Golang
- [ ] Make parse Medium format directly to Markdown, not HTML, in order to make it more universal. This helps to generate RSS feeds, PDF, HTML.
      OR we need write separate parser for different formats, like PDF, Markdown, etc.
- [ ] Add more services than just a Medium
- [ ] Rewrite frontend to Svelte
- [ ] Move frontend to Cloudflare Pages
- [ ] Integrate Grafana/Prometheus to monitor our services
- [ ] Add more metrics to our services to have ability to monitor it
- [ ] Make able translate posts to different languages using translatepy library

## New PDF Generation Feature

We have added a new feature that allows you to save Medium articles as PDFs. Here are the steps to use this feature:

1. Navigate to the article you want to save as a PDF.
2. Click on the "Save as PDF" button.
3. The article will be downloaded as a PDF file.

This feature is powered by the WeasyPrint library, which converts HTML content to PDF format. The implementation details can be found in the following files:

- `web/server/handlers/post.py`: Contains the endpoint for PDF generation.
- `web/server/templates/post.html`: Ensures compatibility with PDF rendering.
- `new-web/src/routes/[slug]/+page.svelte`: Adds the "Save as PDF" button and implements the function to call the PDF generation endpoint.
