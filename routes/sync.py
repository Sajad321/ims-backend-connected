from fastapi import APIRouter
import requests
from models.models import Installments, States, Users, UserAuth

sync_router = APIRouter()


async def get_users():
    users = await Users.filter(sync_state=0).all()
    result_list = []
    for user in users:
        result_json = {"password": user.password, "username": user.username, "unique_id": user.unique_id}
        authority = []
        auth = await UserAuth.filter(user_id=user.id).prefetch_related('state').all()
        for au in auth:
            auth_json = {"state_unique_id": au.state.unique_id, "unique_id": au.unique_id}
            authority.append(auth_json)
        result_json['authority'] = authority
        result_list.append(result_json)
    return result_list


@sync_router.get('/sync')
async def sync():
    installments = await Installments.filter(sync_state=0).all()
    for install in installments:
        req = requests.post("http://127.0.0.1:8080/installments",
                            json={"name": install.name, "unique_id": install.unique_id})
        if req.status_code == 200:
            await Installments.filter(id=install.id).update(sync_state=1)
    states = await States.filter(sync_state=0).all()
    for state in states:
        req = requests.post("http://127.0.0.1:8080/state", json={"name": state.name,
                                                                 "unique_id": state.unique_id})
        if req.status_code == 200:
            await States.filter(id=state.id).update(sync_state=1)
    users = await get_users()
    for user in users:
        req = requests.post('http://127.0.0.1:8080/users', json=user)
        if req.status_code == 200:
            await Users.filter(unique_id=user['unique_id']).update(sync_state=1)
    return {
        "success": True
    }
