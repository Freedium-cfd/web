import random

from fastapi.responses import HTMLResponse

from server import (
    base_template,
    config,
    error_template,
    transponder_code_correlation,
    url_correlation
)
from server.utils.logger_trace import trace
from server.utils.notify import send_message

# ChatGPT promt: Make this text more Humoristic in one sentenced text, 15 different with emojies as Python list: Sorry to hear that but we have some problem
ERROR_MSG_LIST = [
    "Sorry to hear that, but we've got a problem that's bigger than my inability to resist a donut! 🍩",
    "Apologies for the inconvenience, but we've hit a snag - it's not as funny as my cat chasing its tail, but it's a problem nonetheless! 🐱",
    "Sorry to hear that, but we've encountered a problem - it's not as entertaining as a clown at a circus, but it's there! 🎪",
    "Oops! We've stumbled upon a problem, but don't worry, it's not as disastrous as my cooking! 🍳",
    "Sorry to hear that, but we've got a problem that's more stubborn than a mule on a Monday morning! 🐴",
    "Apologies, but we've run into a problem - it's not as amusing as my grandma's dance moves, but it's a problem! 👵💃",
    "Sorry to hear that, but we've got a problem that's more tangled than my headphone wires! 🎧",
    "Oops! We've hit a problem, but don't worry, it's not as catastrophic as my last blind date! 💔",
    "Sorry to hear that, but we've got a problem that's more elusive than a sock in a washing machine! 🧦",
    "Apologies, but we've run into a problem - it's not as hilarious as my attempt at yoga, but it's a problem! 🧘‍♂️",
    "Sorry to hear that, but we've got a problem that's more confusing than a chameleon in a bag of Skittles! 🦎🌈",
    "Oops! We've encountered a problem, but don't worry, it's not as disastrous as my attempt at karaoke! 🎤",
    "Sorry to hear that, but we've got a problem that's more stubborn than a toddler refusing to eat their veggies! 👶🥦",
    "Apologies, but we've run into a problem - it's not as amusing as my dog trying to catch its tail, but it's a problem! 🐶",
    "Sorry to hear that, but we've got a problem that's more elusive than the end of a rainbow! 🌈"
]


@trace
async def generate_error(error_msg: str = None, title: str = "Error", status_code: int = 500, quiet: bool = False):
    if not error_msg:
        error_msg = random.choice(ERROR_MSG_LIST)

    """
    if not quiet:
        await send_message(
            f"📛 Error while processing url: <code>{url_correlation.get()}</code>, transponder_code: <code>{transponder_code_correlation.get()}</code>, error: <code>{error_msg}</code>"
        )
    """

    error_template_rendered = await error_template.render_async(error_msg=error_msg, transponder_code=transponder_code_correlation.get())
    base_context = {
        "enable_ads_header": config.ENABLE_ADS_BANNER,
        "body_template": error_template_rendered,
        "title": title,
    }
    base_template_rendered = await base_template.render_async(base_context, HOST_ADDRESS=config.HOST_ADDRESS)
    return HTMLResponse(base_template_rendered, status_code=status_code)

