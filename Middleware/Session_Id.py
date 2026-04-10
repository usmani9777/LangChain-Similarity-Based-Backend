import uuid
import logging
from fastapi import Request

logger = logging.getLogger(__name__)
SESSION_COOKIE = "session_id"

async def session_middleware(request: Request, call_next):
    session_id = request.cookies.get(SESSION_COOKIE)

    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(
            "New session created",
            extra={"session_id": session_id}
        )

    # ✅ SET STATE BEFORE DEPENDENCIES RUN
    request.state.session_id = session_id

    response = await call_next(request)

    # ✅ Only set cookie if it was newly created
    if SESSION_COOKIE not in request.cookies:
        response.set_cookie(
            key= SESSION_COOKIE,
            value= session_id,
            httponly=True,
            samesite="lax"
        )

    return response