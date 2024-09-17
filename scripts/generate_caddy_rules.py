from os import listdir
from os.path import isfile, join
from typing import List, Dict
from jinja2 import Template

# Constants
STATIC_DIR = "./static"
ACCESS_DENIED_PATHS: List[str] = [
    "websocket",
    "meta.json",
    "cdn-cgi/challenge-platform/scripts/jsd/main.js",
    "cdn-cgi/rum",
    "graphql/websocket",
    "onboarding/*",
    "wp-*",
    ".env",
    "api*",
    "apple-touch-icon-precomposed.png",
    "rss.xml",
    ".git/*",
    "apple-touch-icon-120x120.png",
    "apple-touch-icon-120x120-precomposed.png",
    "apple-touch-icon-152x152.png",
    "apple-touch-icon-152x152-precomposed.png",
    ".well-known/*",
    "cdn-cgi/challenge-platform/h/b/orchestrate/chl_page/v1",
    "cdn-cgi/challenge-platform/h/g/orchestrate/chl_page/v1",
]

CADDY_FILE_TEMPLATES: Dict[str, str] = {
    "CaddyfileDevTemplate": "CaddyfileDev",
    "CaddyfileProdTemplate": "CaddyfileProd",
}


def get_static_files(directory: str) -> List[str]:
    return [f for f in listdir(directory) if isfile(join(directory, f))]


def generate_static_file_rules(files: List[str]) -> List[str]:
    template = Template(
        """
    handle_path /{{ file }} {
        root * ./static/{{ file }}
        file_server
    }
    """
    )
    return [template.render(file=file) for file in files]


def generate_access_denied_rules(paths: List[str]) -> List[str]:
    template = Template(
        """
    handle_path /{{ file }} {
        respond "Access denied" 403
    }
    """
    )
    return [template.render(file=path) for path in paths]


def generate_caddy_rules() -> str:
    static_files = get_static_files(STATIC_DIR)
    static_rules = generate_static_file_rules(static_files)
    denied_rules = generate_access_denied_rules(ACCESS_DENIED_PATHS)
    return "\n".join(static_rules + denied_rules)


def render_caddy_file(template_path: str, output_path: str, rules: str) -> None:
    try:
        with open(template_path, "r") as file:
            template = Template(file.read())

        rendered_content = template.render(template=rules)

        with open(output_path, "w") as file:
            file.write(rendered_content)
    except IOError as e:
        print(f"Error processing {template_path}: {e}")


def main() -> None:
    rules = generate_caddy_rules()

    for template_file, output_file in CADDY_FILE_TEMPLATES.items():
        render_caddy_file(template_file, output_file, rules)


if __name__ == "__main__":
    main()
