import jinja2

from medium_parser import jinja_env_debug


def raw_render(**kwargs):
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key] = f"{{% raw %}}{value}{{% endraw %}}"

    return kwargs


def parse_markups(
    markups: list[dict[str, str | jinja2.Template]]
) -> list[dict[str, str | jinja2.Template]]:
    markups_out = []

    for markup in markups:
        if markup["type"] == "A":
            if markup["anchorType"] == "LINK":
                target: str = ""
                if not markup.get("href", "").startswith("#"):
                    target = "_blank"

                template = jinja_env_debug.from_string(
                    '<a style="text-decoration: underline;" rel="{{rel}}" title="{{title}}" href="{{href}}" target="{{target}}">{{text}}</a>'
                )
                template_rendered = template.render(
                    raw_render(
                        rel=markup.get("rel", ""),
                        target=target,
                        title=markup.get("title", ""),
                        href=markup["href"],
                    )
                )
            elif markup["anchorType"] == "USER":
                template = jinja_env_debug.from_string(
                    '<a style="text-decoration: underline;" href="https://medium.com/u/{{userId}}">{{text}}</a>'
                )
                template_rendered = template.render(userId=markup["userId"])
            else:
                continue
        elif markup["type"] == "STRONG":
            template_rendered = "<strong>{{text}}</strong>"
        elif markup["type"] == "EM":
            template_rendered = "<em>{{text}}</em>"
        elif markup["type"] == "CODE":
            template_rendered = (
                "<code class='p-1.5 bg-gray-300 dark:bg-gray-600'>{{text}}</code>"
            )
        else:
            continue

        template = jinja_env_debug.from_string(template_rendered)
        markup["template"] = template
        markups_out.append(markup)

    return markups_out
