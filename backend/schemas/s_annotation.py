from pydantic import BaseModel

class AnnotationSchema(BaseModel):
    stock_symbol : str
    x_coord : float
    y_coord : float
    text : str
    