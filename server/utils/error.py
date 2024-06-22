import random

from fastapi.responses import HTMLResponse

from server import config, transponder_code_correlation, url_correlation
from server.services.jinja import base_template, error_template
from server.utils.logger_trace import trace
from server.utils.notify import send_message

# ChatGPT promt: Make this text more Humoristic in one sentenced text, 15 different with emojies as Python list: Sorry to hear that but we have some problem
ERROR_MSG_LIST = [
    "Oops! 🙈 Looks like we stumbled into a little problem!",
    "Sorry to hear that, but our problem factory is working overtime! 😅",
    "Oh no! 😱 We've cooked up some problems again!",
    "Whoops! Did someone order a problem? 🍕",
    "Yikes! 🤪 We've hit a snag bigger than my coffee addiction!",
    "Uh oh! 🚨 We've brewed a fresh pot of problems!",
    "Hold tight! 🎢 Our problem rollercoaster has just begun!",
    "Alert! 📢 We've encountered a wild problem in its natural habitat!",
    "Bummer! 😜 We've tripped over a problem cord!",
    "Oh dear! 🐻 Looks like we've poked the problem bear!",
    "Guess what? 🤔 We've got a problem, but we're smiling through it!",
    "Surprise! 🎉 We found a problem you didn't even know you needed!",
    "Heads up! 🙆‍♂️ We're dancing with a few problems today!",
    "Sorry to hear that, but it's just another manic problem day! 🎶",
    "Well, well, well... if it isn't another problem joining the party! 🥳"
]


@trace
async def generate_error(error_msg: str = None, title: str = "Error", status_code: int = 500, quiet: bool = False):
    if not error_msg:
        error_msg = random.choice(ERROR_MSG_LIST)

    if not quiet:
        send_message(f"📛 Error while processing url: <code>{url_correlation.get()}</code>, transponder_code: <code>{transponder_code_correlation.get()}</code>, error: <code>{error_msg}</code>")

    error_template_rendered = error_template.render(error_msg=error_msg, transponder_code=transponder_code_correlation.get())
    base_context = {
        "enable_ads_header": config.ENABLE_ADS_BANNER,
        "body_template": error_template_rendered,
        "title": title,
    }
    base_template_rendered = base_template.render(base_context, HOST_ADDRESS=config.HOST_ADDRESS)
    return HTMLResponse(base_template_rendered, status_code=status_code)
