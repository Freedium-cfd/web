from loguru import logger
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from server import config, ban_db, medium_parser
from server.utils.notify import send_message
from server.utils.logger_trace import trace

class ReportProblem(BaseModel):
    page: str
    description: str


class DeleteFromCache(BaseModel):
    key: str
    ADMIN_SECRET_KEY: str


@trace
async def report_problem(problem: ReportProblem):
    send_message(f"New problem report: \n{problem.description}\n\n{problem.page}")
    return JSONResponse({"message": "OK"}, status_code=200)


@trace
async def delete_from_cache(key_data: DeleteFromCache):
    if key_data.ADMIN_SECRET_KEY != config.ADMIN_SECRET_KEY:
        return JSONResponse({"message": f"Wrong secret key: {key_data.ADMIN_SECRET_KEY}"}, status_code=403)

    try:
        await medium_parser.delete_from_cache(key_data.key)
    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({"message": f"Couldn't delete from cache: {ex}"}, status_code=500)
    else:
        ban_db.set(key_data.key, 1)
        return JSONResponse({"message": "OK"}, status_code=200)
