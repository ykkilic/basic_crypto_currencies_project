from pydantic import BaseModel

class UserRegisterSchema(BaseModel):
    first_name : str
    last_name : str
    email : str
    phone_number : str
    username : str
    password : str
    city : str
    country : str

class UserLoginSchema(BaseModel):
    email : str
    password : str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str
    role: str