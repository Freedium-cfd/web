<p align="center"><a href="https://freedium.cfd" target="_blank"><img src="https://avatars.githubusercontent.com/u/142643505?s=200&v=4" width="20%"></a></p>

<h1 align="center">Freedium: Your paywall breakthrough for Medium!</h1>

<a href="https://www.patreon.com/Freedium">
    <img width="200px" height="50px" alt="Become a Patron" src="https://github.com/elsiehupp/patron-buttons/blob/master/svg/become_a_patron_4x1_black_logo_white_text_on_coral.svg?raw=True">
</a>

## Stack:

- Backend:
  - language: Python 3.9+
  - framework: Unicorn, FastAPI
- Frontend:
  - framework: Tailwinds CSS v3, Jinja2
  - monitoring: Sentry
- Database:
  - PostgreSQL, Dragonfly (Redis and Memcached compatible key-value database)
- Utils:
  - Caddy, Docker, Docker Compose, Cloudflare WARP proxy (wgcf)

## Project configuration:

There is three (3) docker-compose profiles:

- `min` - without 2 Cluster of Cloudflare WARP proxy, HAProxy proxy balancer, Plausible, Grafana.
- `local` - based on `min`, but with `freedium.local` exposed hostname, both 80 and 443 ports are exposed, with self-signed TLS certificate.
- `prod` - with all services for production.

### Requirements:

- Docker, Docker Compose, last version is preferred.
- Linux, preferably rolling release. We can't guarantee that Freedium instance will work on other OS. Tested on Ubuntu 22.04 and Fedora 39.
- git
- Preferably, fresh and clean brain.

### Local run:

To configure your Freedium instance, follow these steps:

1. Clone the repository:

   ```
   git clone https://codeberg.org/Freedium-cfd/web/ ./freedium-web --depth 1
   cd ./freedium-web
   ```

2. Create and configure the environment file:

   ```
   cp .env_template .env
   ```

   Open the `.env` file and adjust the values as needed for your setup.

3. (Optional) Set up the Docker network:

   ```
   sudo docker network create caddy_net
   ```

4. Change your hosts file:

   ```
   sudo nano /etc/hosts
   # or
   vim /etc/hosts
   # and when you are closed vim, type `:w !sudo tee %` to save file without executing vim in root mode
   ```

   Add the following line:

   ```
   127.0.0.1 freedium.local
   ```

5. Start the Freedium services (`min` profile):

   ```
   sudo docker compose --profile local -f ./docker-compose/docker-compose.yml up
   ```

   Stopping the services:

   ```
   sudo docker compose --profile local -f ./docker-compose/docker-compose.yml down
   ```

And now you can access local instance of Freedium by opening browser and type `https://freedium.local`. There is would be a warning about insecure connection, because we use self-signed TLS certificate. Ignore it.

### Production run:

All production services are running on `prod` profile. If you use Dockerized reverse proxy, you can specify network `caddy_freedium_net` with `external: true` option in networks section of your reverse proxy container. Specify `caddy_freedium` hostname with port `6752` (or `6753` for Plausible) in your reverse proxy configuration.

As alternative, you can directly change docker-compose configurations to use your reverse proxy. See `docker-compose` and `caddy` folders for more details.

## Architecture:

```mermaid
graph TB
    subgraph "Main Application"
        fw[freedium_web]
        cdy[caddy_freedium]
    end

    subgraph "Database Layer"
        rds[redis_service<br/>DragonFlyDB]
        pg[(postgres_freedium<br/>PostgreSQL)]
        pgadm[pgadmin4_freedium]
    end

    subgraph "Proxy Layer"
        hpb[haproxy-proxy-balancer]

        subgraph "WGCF Cluster 1"
            wg1[wgcf1]
            d1[dante_1]
            wh1[wgcf1_healthcare_service]
        end

        subgraph "WGCF Cluster 2"
            wg2[wgcf2]
            d2[dante_2]
            wh2[wgcf2_healthcare_service]
        end
    end

    subgraph "Analytics"
        pls[freedium_plausible]
        pldb[(plausible_db)]
        pledb[(plausible_events_db<br/>ClickHouse)]
    end

    subgraph "Utility"
        ah[autoheal]
    end

    %% Dependencies
    fw -->|depends_on| hpb
    d1 -->|depends_on| wg1
    d2 -->|depends_on| wg2
    wg2 -->|depends_on| wg1
    hpb -->|depends_on| wg1
    hpb -->|depends_on| wg2
    pls -->|depends_on| pldb
    pls -->|depends_on| pledb

    %% Network Connections
    subgraph "Networks"
        fn[freedium_net]
        cn[caddy_net]
        pn[plausible_net]
    end

    fw ---|freedium_net| fn
    cdy ---|freedium_net & caddy_net| fn
    rds ---|freedium_net| fn
    pg ---|freedium_net| fn
    pgadm ---|freedium_net| fn
    hpb ---|freedium_net| fn
    wg1 ---|freedium_net| fn
    wg2 ---|freedium_net| fn
    wh1 ---|freedium_net| fn
    wh2 ---|freedium_net| fn
    pls ---|all networks| fn

    %% Port Exposures
    cdy -->|":6752"| ext1[External Access]
    fw -->|":7080"| ext2[External Access]
    pgadm -->|":5433"| ext3[External Access]

    classDef service fill:#2ecc71,stroke:#27ae60,color:white
    classDef network fill:#3498db,stroke:#2980b9,color:white
    classDef database fill:#e74c3c,stroke:#c0392b,color:white
    classDef proxy fill:#f1c40f,stroke:#f39c12,color:black
    classDef utility fill:#9b59b6,stroke:#8e44ad,color:white
    classDef external fill:#95a5a6,stroke:#7f8c8d,color:white

    class fw,cdy,pls service
    class rds,pg,pldb,pledb database
    class hpb,wg1,wg2,d1,d2 proxy
    class ah,wh1,wh2 utility
    class fn,cn,pn network
    class ext1,ext2,ext3 external
```

## TODO:

- ~~Integrate library notifiers - https://github.com/liiight/notifiers~~ Use Graphana and Loki instead
- ~~Do not use 'shturman/dante' image, because it is does not have updates for a long time. (Probably) Use https://hub.docker.com/r/vimagick/dante/~~ Works, don't touch

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
