from fastapi import Request

from effective_mobile_fast_api.api_v1.auth.config import Production
from effective_mobile_fast_api.api_v1.auth.security import decode_jwt_token, generate_and_set_tokens


async def auth_middleware(request: Request, call_next):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    user_id = decode_jwt_token(access_token)

    if user_id:
        # access_token валиден — продолжаем
        request.state.user_id = user_id
        response = await call_next(request)
        return response

    # access_token не валиден, проверяем refresh_token (тоже JWT, без БД)
    user_id = decode_jwt_token(refresh_token)
    if user_id:
        request.state.user_id = user_id
        response = await call_next(request)
        generate_and_set_tokens(response, str(user_id), secure=Production)
        return response

    # Нет валидных токенов — анонимный запрос
    response = await call_next(request)
    return response
