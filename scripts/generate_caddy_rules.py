from os import listdir
from os.path import isfile, join

from jinja2 import Template

OUTPUT_RULES = []


static_files = [f for f in listdir("./static") if isfile(join("./static", f))]

static_file_template = """
    handle_path /{{ file }} {
        root * ./static/{{ file }}
         file_server
    }
"""
static_file_template_jinja = Template(static_file_template)

for file in static_files:
    file_template = static_file_template_jinja.render(file=file)
    OUTPUT_RULES.append(file_template)


ACCESS_DENIED_PATHS = ["wp-*", ".env", "api*", "ads.txt"]

access_denied_paths_template = """
    handle_path /{{ file }} {
        respond "Access denied" 403
    }
"""

access_denied_paths_template_jinja = Template(access_denied_paths_template)

for denied_path in ACCESS_DENIED_PATHS:
    denied_path_template = access_denied_paths_template_jinja.render(file=denied_path)
    OUTPUT_RULES.append(denied_path_template)

HUMAN_OUTPUT_RULES = "\n".join(OUTPUT_RULES)

with open("scripts/output_rules.txt", "w") as file:
    file.write(HUMAN_OUTPUT_RULES)

caddy_file_templates = {
    "CaddyfileDevTemplate": "CaddyfileDev",
    "CaddyfileProdTemplate": "CaddyfileProd",
}

for caddy_file_template, output_caddy_file_template in caddy_file_templates.items():
    with open(caddy_file_template) as file:
        caddy_file = Template(file.read())
        caddy_file_rendered = caddy_file.render(template=HUMAN_OUTPUT_RULES)

    with open(output_caddy_file_template, "w") as file:
        file.write(caddy_file_rendered)
