from medium_parser import jinja_env


def raw_render(**kwargs):
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key] = f"{{% raw %}}{value}{{% endraw %}}"

    return kwargs


def parse_markups(markups: list[str]):
    markups_out = []

    for markup in markups:
        if markup["type"] == "A":
            if markup["anchorType"] == "LINK":
                template = jinja_env.from_string(
                    '<a style="text-decoration: underline;" rel="{{rel}}" title="{{title}}" href="{{href}}" target="_blank">{{text}}</a>'
                )
                template = template.render(
                    raw_render(
                        rel=markup.get("rel", ""),
                        title=markup.get("title", ""),
                        href=markup["href"],
                    )
                )
            elif markup["anchorType"] == "USER":
                template = jinja_env.from_string(
                    '<a style="text-decoration: underline;" href="https://medium.com/u/{{userId}}">{{text}}</a>'
                )
                template = template.render(userId=markup["userId"])
            else:
                continue
        elif markup["type"] == "STRONG":
            template = "<strong>{{text}}</strong>"
        elif markup["type"] == "EM":
            template = "<em>{{text}}</em>"
        elif markup["type"] == "CODE":
            template = (
                "<code class='p-1.5 bg-gray-300 dark:bg-gray-600'>{{text}}</code>"
            )
        else:
            continue

        template = jinja_env.from_string(template)
        markup["template"] = template
        markups_out.append(markup)

    return markups_out
