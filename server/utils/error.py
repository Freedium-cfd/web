import random

from fastapi.responses import HTMLResponse

from server import (
    base_template,
    config,
    error_template,
    minify_html,
    transponder_code_correlation,
)
from server.utils.logger_trace import trace

# ChatGPT promt: Make this text more Humoristic in one sentenced text: Sorry to hear that but we have some problem
ERROR_MSG_LIST = [
    "Don't worry, we'll get it right next time.",
    "Oh boy, looks like our software had a \"funny\" moment, but don't fret, we're on it! 😄",
    "Apologies for the techno-tantrum, but rest assured, we're sending in the IT comedians to fix this tech-tango! 😄",
    "Oopsie daisy, our code seems to have taken a joyride on the rollercoaster of errors, but don't worry, we'll catch it and bring it back to the land of functionality soon enough! 😄",
    "My apologies, but it seems our computer system decided to have a little dance-off with the bugs, but don't worry, we're calling in the tech wizards to put on their disco shoes and show those glitches who's boss! 😄",
    "Well, butter my biscuits! Our system seems to be playing hide-and-seek, but rest assured, we'll kick it back into gear and make it behave like a good ol' obedient AI! 🤖💨",
    "Oh snap! Our tech gremlins must be at it again, causing mischief in our system! But don't worry, we've summoned the laughter brigade to fix this issue pronto! 😂🔧",
    "Well, it seems like our tech gremlins decided to throw a party, but rest assured, we've sent them home and the issue will be history in a jiffy! 😄",
    "Oh snap, our code might have taken a little vacation, but don't worry, we'll whip it back into shape and have things running smoother than a buttered penguin on ice! 😅",
    "Oopsie-daisy, we've got a teeny-tiny glitch, but fear not, we're onto it! 😄",
    "Houston, we've had a minor hiccup, but our tech wizards are already casting spells to fix it! 🧙‍♂️",
    "Hold on to your hats, folks! Our code decided to pull a little prank, but we're laughing with it while we sort it out! 😂",
    "Well, butter my biscuits, we've got ourselves a minor blip, but we'll have it wrangled faster than a rodeo cowboy! 🤠",
    "Whoopsie-doodle, a wild gremlin must've sneaked into our system, but our expert team is hot on its tail! 🔍",
    "Looks like our code is feeling a bit mischievous, but we're sending it to comedy school to learn some better jokes! 🎭",
    "Drumroll, please! Our software's doing a quirky dance, but we promise to get it back to the right beat! 🥁",
    "Oh, it's just a classic case of computer shenanigans, but we've got the ultimate joke-cracking team on the case! 😆",
]


@trace
async def generate_error(error_msg: str = None, title: str = "Error", status_code: int = 500):
    if not error_msg:
        error_msg = random.choice(ERROR_MSG_LIST)

    error_template_rendered = await error_template.render_async(error_msg=error_msg, transponder_code=transponder_code_correlation.get())
    base_context = {
        "enable_ads_header": config.ENABLE_ADS_BANNER,
        "body_template": error_template_rendered,
        "title": title,
    }
    base_template_rendered = await base_template.render_async(base_context)
    minified_result = minify_html(base_template_rendered)
    return HTMLResponse(minified_result, status_code=status_code)

