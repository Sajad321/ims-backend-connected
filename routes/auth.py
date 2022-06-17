import os
import signal
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends
from models.models import Institutes, Governorates, States, Students, Installments, StudentInstallments, \
    Users, UserAuth, TemporaryPatch, TemporaryDelete, Branches, Posters
from tortoise.transactions import in_transaction
from schemas.general import GeneralSchema, Student, StudentInstall, User, Login
import hashlib
import datetime
from fastapi_pagination import paginate, Params as ps
import requests

# todo: complete sync_state
# todo: complete api sync with online interaction
auth_router = APIRouter()


# GET `/users`
#
# - Get users from database.
# - Request Arguments: None
# - Returns: list of students.
#
# Example Response `{
#   "users": [
#     {
#       "id": 1,
#       "username": "krvhrv",
#       "authority": [
#         {
#           "authority_id": 1,
#           "state": "الكويت",
#           "state_id": 1
#         }
#       ]
#     }
#   ],
#   "total_users": 1,
#   "success": true
# }'
@auth_router.get('/users')
async def get_users():
    users = await Users.all()
    result_list = []
    for user in users:
        result_json = {"id": user.id, "username": user.username,
                       'name': user.name, "super": user.super}
        authority = []
        auth = await UserAuth.filter(user_id=user.id).prefetch_related('state').all()
        for au in auth:
            auth_json = {"authority_id": au.id,
                         "name": au.state.name, "id": au.state.id}
            authority.append(auth_json)
        result_json['authority'] = authority
        result_list.append(result_json)
    return {
        "users": result_list,
        "total_users": await Users.all().count(),
        "success": True
    }


# POST `/users`
# - Add user in database.
# - Request Arguments: None
# - Returns: None.
# Example Request Payload `{
#     "username": "1",
#     "password": "22",
#     "authority": [
#         {
#             "state_id": 1,
#             "state": "نرس"
#         }
#     ],
# }`
# Example Response `{
#     "success": true
# }`
@auth_router.post('/users')
async def post_user(schema: User):
    async with in_transaction() as conn:
        unique_id = str(uuid4())
        password = hashlib.md5(schema.password.encode())
        new = Users(username=schema.username, password=password.hexdigest(
        ), unique_id=unique_id, name=schema.name)
        if schema.super:
            new = Users(username=schema.username, password=password.hexdigest(), unique_id=unique_id, name=schema.name,
                        super=1)
        await new.save(using_db=conn)
        if not schema.super:
            for state in schema.authority:
                unique_id = str(uuid4())
                auth = UserAuth(
                    user_id=new.id, state_id=state.id, unique_id=unique_id)
                await auth.save(using_db=conn)
        else:
            for state in await States.all():
                unique_id = str(uuid4())
                auth = UserAuth(
                    user_id=new.id, state_id=state.id, unique_id=unique_id)
                await auth.save(using_db=conn)
    return {
        "success": True
    }


# PATCH `/users/{user_id}`
# - Add user in database.
# - Request Arguments: None
# - Returns: None.
# Example Request Payload `{
#     "username": "1",
#     "password": "22",
#     "authority": [
#         {
#             "state_id": 1,
#             "state": "نرس"
#         }
#     ],
# }`
# Example Response `{
#     "success": true
# }`
@auth_router.patch('/users/{user_id}')
async def patch_user(user_id, schema: User):
    get_user = await Users.filter(id=user_id).first()
    password = hashlib.md5(schema.password.encode())
    await Users.filter(id=user_id).update(username=schema.username, password=password.hexdigest(), name=schema.name,
                                          sync_state=0, super=0)
    if schema.super:
        await Users.filter(id=user_id).update(username=schema.username, password=password.hexdigest(), name=schema.name,
                                              sync_state=0, super=1)
    # get_auth = await UserAuth.filter(user_id=get_user.id).first()
    await UserAuth.filter(user_id=get_user.id).delete()
    async with in_transaction() as conn:
        for state in schema.authority:
            unique_id = str(uuid4())
            auth = UserAuth(user_id=get_user.id,
                            state_id=state.id, unique_id=unique_id)
            await auth.save(using_db=conn)
    return {
        "success": True
    }


@auth_router.delete('/users/{user_id}')
async def del_user(user_id):
    get_user = await Users.filter(id=user_id).first()
    await Users.filter(id=user_id).delete()
    async with in_transaction() as conn:
        new = TemporaryDelete(unique_id=get_user.unique_id, model_id=4)
        await new.save(using_db=conn)
    return {
        "success": True, "user": get_user.name
    }


# POST - '/login'
# request body:
# {"username": krvhrv, "password": "1234"}
# response: {"success": True}
@auth_router.post('/login')
async def login(schema: Login):
    users = await Users.all()
    for user in users:
        if user.username == schema.username:
            password = schema.password.encode()
            password = hashlib.md5(password)
            if user.password == password.hexdigest():
                req = requests.post("http://127.0.0.1/jwt-api-token-auth/",
                                    json={
                                        "username": schema.username,
                                        "password": schema.password,
                                    },  headers={'Content-Type': 'application/json'})
                print(req)
                print(req.json())
                states = []
                auth = await UserAuth.filter(user_id=user.id).all().prefetch_related('state')
                for state in auth:
                    state = {"name": state.state.name, "id": state.state.id}
                    states.append(state)
                if req.status_code == 200:
                    return {
                        "success": True,
                        "token": str(uuid4()),
                        "username": user.username,
                        "name": user.name,
                        "password": user.password,
                        "authority": states,
                        "super": user.super,
                        "biotime": req.json()["token"]
                    }
            else:
                return {
                    "success": False
                }
