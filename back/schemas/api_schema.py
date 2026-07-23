from pydantic import BaseModel

class ApiResponse[T](BaseModel):
    success: bool
    message: str
    data: T