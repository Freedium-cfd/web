from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from server import maintenance_mode

HTML_RESPONSE_BODY = """
<!doctype html>
<title>Site Maintenance</title>
<style>
  body { text-align: center; padding: 150px; }
  h1 { font-size: 50px; }
  body { font: 20px Helvetica, sans-serif; color: #333; }
  article { display: block; text-align: left; width: 650px; margin: 0 auto; }
  a { color: #dc8100; text-decoration: none; }
  a:hover { color: #333; text-decoration: none; }
</style>

<article>
    <h1>We&rsquo;ll be back soon!</h1>
    <div>
        <p>Sorry for the inconvenience but we&rsquo;re performing some maintenance at the moment. If you need to you can always <a href="mailto:#admin@freedium.cfd">contact us</a>, otherwise we&rsquo;ll be back online shortly!</p>
        <p>&mdash; Freedium developers</p>
    </div>
</article>
"""

class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if maintenance_mode:
            return HTMLResponse(
                content=HTML_RESPONSE_BODY,
                status_code=503
            )
        response = await call_next(request)
        return response