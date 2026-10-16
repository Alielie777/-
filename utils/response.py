from fastapi.responses import JSONResponse
from starlette import status
from fastapi.encoders import jsonable_encoder


def success_response(message: str = "success", data=None):
    content = {"code": 200, "message": message, "data": data}

    # 目标：把任何的FastAPI、Pydantic、ORM对象都正常响应->code、message、data
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(content))
