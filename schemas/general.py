from pydantic import BaseModel
from typing import Optional, List


class Users(BaseModel):
    id: int

    class Config:
        orm_mode = True


class GeneralSchema(BaseModel):
    name: str
    users: Optional[List[Users]] = []

    class Config:
        orm_mode = True


class StudentInstall(BaseModel):
    install_id: int
    date: Optional[str] = None
    amount: Optional[float] = 0.0
    invoice: Optional[int] = None

    class Config:
        orm_mode = True


class Student(BaseModel):
    name: str
    school: Optional[str] = None
    branch_id: Optional[int] = None
    institute_id: Optional[int] = None
    governorate_id: Optional[int] = None
    first_phone: Optional[str] = None
    second_phone: Optional[str] = None
    poster_id: Optional[int] = None
    code_1: Optional[str] = None
    code_2: Optional[str] = None
    telegram_username: Optional[str] = None
    total_amount: Optional[float] = None
    remaining_amount: Optional[float] = None
    note: Optional[str] = None
    installments: List[StudentInstall]
    state_id: int

    class Config:
        orm_mode = True


class Authority(BaseModel):
    id: int

    class Config:
        orm_mode = True


class User(BaseModel):
    username: str
    password: str
    name: Optional[str] = None
    authority: Optional[List[Authority]]
    super: Optional[bool] = False

    class Config:
        orm_mode = True


class Login(BaseModel):
    username: str
    password: str

    class Config:
        orm_mode = True
