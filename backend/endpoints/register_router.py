from fastapi import APIRouter, Depends, HTTPException, status
from models.models import Users, Roles
from schemas.s_user import UserRegisterSchema
from services.database import get_db, Session

router = APIRouter()

@router.post("/save")
async def register(data : UserRegisterSchema, db : Session = Depends(get_db)):
    try:
        print(data)
        user = db.query(Users).filter(Users.email == data.email).first()
        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        new_user_role = db.query(Roles).filter(Roles.role_name == "user").first()

        new_user = Users(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone_number=data.phone_number,
            username=data.username,
            password=data.password,
            city=data.city,
            country=data.country,
            role_id=new_user_role.role_id,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {'status_code' : 200, "detail" : "User registered successfully"}
    except Exception as e:
        return {'status_code' : 500, "detail" : "Internal Server Error", "error" : str(e)}
    