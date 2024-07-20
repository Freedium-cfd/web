from jinja2 import Environment, DebugUndefined, FileSystemLoader

jinja_env = Environment()
jinja_safe_env = Environment(undefined=DebugUndefined)
template_env = Environment(loader=FileSystemLoader("./server/templates"))
template_safe_env = Environment(loader=FileSystemLoader("./server/templates"), undefined=DebugUndefined)

base_template = template_env.get_template("base.html")
main_template_raw = template_safe_env.get_template("main.html")
homepage_template = template_env.get_template("homepage.html")
error_template_raw = template_safe_env.get_template("error.html")

main_template_raw_rendered = main_template_raw.render()
main_template = jinja_env.from_string(main_template_raw_rendered)

error_template_raw_rendered = error_template_raw.render()
error_template = jinja_env.from_string(error_template_raw_rendered)
