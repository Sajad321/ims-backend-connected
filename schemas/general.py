from pydantic import BaseModel
from typing import Optional, List


class GeneralSchema(BaseModel):
    name: str

    class Config:
        orm_mode = True


class StudentInstall(BaseModel):
    install_id: int
    date: Optional[str] = None
    amount: float = 0.0
    invoice: Optional[int] = None

    class Config:
        orm_mode = True


class Student(BaseModel):
    name: str
    school: Optional[str] = None
    branch_id: Optional[int] = None
    institute_id: Optional[int] = None
    governorate_id: Optional[int] = None
    first_phone: Optional[int] = None
    second_phone: Optional[int] = None
    poster_id: Optional[int] = None
    code: Optional[int] = None
    telegram_username: Optional[str] = None
    total_amount: Optional[float] = None
    remaining_amount: Optional[float] = None
    note: Optional[str] = None
    created_at: Optional[str]
    installments: List[StudentInstall]
    state_id: int

    class Config:
        orm_mode = True


class Authority(BaseModel):
    state_id: int
    state: str

    class Config:
        orm_mode = True


class User(BaseModel):
    username: str
    password: str
    authority: List[Authority]

    class Config:
        orm_mode = True


class Login(BaseModel):
    username: str
    password: str

    class Config:
        orm_mode = True