from jinja2 import Environment, DebugUndefined, FileSystemLoader

jinja_env = Environment(enable_async=True)
jinja_safe_env = Environment(undefined=DebugUndefined)
template_env = Environment(loader=FileSystemLoader("./server/templates"), enable_async=True)
template_safe_env = Environment(loader=FileSystemLoader("./server/templates"), undefined=DebugUndefined)

base_template = template_env.get_template("base.html")
url_line_template = template_env.get_template("url_line.html").render()
main_template_raw = template_safe_env.get_template("main.html")
postleter_template = template_env.get_template("postleter.html")
error_template_raw = template_safe_env.get_template("error.html")

main_template_raw_rendered = main_template_raw.render(url_line=url_line_template)
main_template = jinja_env.from_string(main_template_raw_rendered)

error_template_raw_rendered = error_template_raw.render(url_line=url_line_template)
error_template = jinja_env.from_string(error_template_raw_rendered)