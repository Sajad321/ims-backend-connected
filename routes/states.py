import os
import signal
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends
from models.models import Institutes, Governorates, States, Students, Installments, StudentInstallments, \
    Users, UserAuth, TemporaryPatch, TemporaryDelete, Branches, Posters
from tortoise.transactions import in_transaction
from schemas.general import GeneralSchema
import hashlib
import datetime
from fastapi_pagination import paginate, Params as ps

# todo: complete sync_state
# todo: complete api sync with online interaction
states_router = APIRouter()


# GET `/states`
#
# - Get all states from the database.
# - Request Arguments: None
# - Returns: list of states.
#
# Example Response `{
#     "states": [
#         {
#             "id": 1,
#             "name": "منصور صيفي",
#         }
#     ],
#     "total_states": 11,
#     "success": true,
# }`
@states_router.get('/states')
async def get_states():
    query = await States.all().values('id', 'name')

    return {"success": True, "total_states": await States.all().count(), "states": query}


# POST `/states`
#
# - Add a state to the database.
# - Request Body: Name.
# - Returns: name of state.
#
# Example Request Payload `{
#     "name": "1"
# }`
@states_router.post('/states')
async def post_state(schema: GeneralSchema):
    async with in_transaction() as conn:
        unique_id = str(uuid4())
        new = States(name=schema.name, unique_id=unique_id)
        await new.save(using_db=conn)
        users = await Users.filter(super=1).all()
        for user in users:
            sup = UserAuth(state_id=new.id, user_id=user.id,
                           unique_id=str(uuid4()))
            await sup.save(using_db=conn)
            await Users.filter(super=1).update(sync_state=0)

        for user_id in schema.users:
            auth = UserAuth(state_id=new.id, user_id=user_id.id,
                            unique_id=str(uuid4()))
            await auth.save(using_db=conn)
            await Users.filter(id=user_id.id).update(sync_state=0)

    return {
        "success": True,
        "name": new.name
    }


# PATCH `/states/{state_id}`
#
# - Edit a state to the database.
# - Request Body: Name.
# - Returns: name of state.
#
# Example Request Payload `{
#     "name": "1"
# }`
#
# Example Response `{
#     "name": "1"
#     "success": true
# }`
@states_router.patch('/states/{state_id}')
async def patch_state(state_id, schema: GeneralSchema):
    await States.filter(id=state_id).update(name=schema.name)
    patch = await States.filter(id=state_id).first().values('unique_id')
    temporary = await TemporaryPatch.filter(unique_id=patch['unique_id']).first()
    async with in_transaction() as conn:
        if temporary is None:
            new = TemporaryPatch(unique_id=patch['unique_id'], model_id=2)
            await new.save(using_db=conn)
        for user in await Users.filter(super=0):
            await UserAuth.filter(state_id=state_id, user_id=user.id).delete()
        for user_id in schema.users:
            auth = UserAuth(state_id=state_id,
                            user_id=user_id.id, unique_id=str(uuid4()))
            await auth.save(using_db=conn)
            await Users.filter(id=user_id.id).update(sync_state=0)

    return {
        "success": True,
        "name": schema.name
    }


# DELETE `/states/<state_id>`
#
# - Delete a state from the database.
# - Request Arguments: None.
# - Returns: name of state.
#
# Example Response `{
#     "name": "ينمبلا",
#     "success": true
# }`
@states_router.delete('/states/{state_id}')
async def del_state(state_id):
    q = await States.filter(id=state_id).first()
    await States.filter(id=state_id).delete()
    await TemporaryPatch.filter(unique_id=q.unique_id).delete()
    async with in_transaction() as conn:
        new = TemporaryDelete(unique_id=q.unique_id, model_id=2)
        await new.save(using_db=conn)
    return {
        "success": True,
        "name": q.name
    }


class Params(ps):
    search: Optional[str] = None
    page: Optional[int] = 1
    number_of_students: int = 100


@states_router.get('/states/{state_id}/students')
async def get_state_students(state_id, params: Params = Depends()):

    if params.search is not None:
        count = await Students.filter(state_id=state_id, name__icontains=params.search).prefetch_related('branch', 'governorate', 'institute', 'state',
                                                                                                         'poster').all()
        students = await Students.filter(state_id=state_id, name__icontains=params.search).prefetch_related('branch', 'governorate', 'institute', 'state',
                                                                                                            'poster').all().limit(params.number_of_students).offset((params.page - 1) *
                                                                                                                                                                    params.number_of_students)
    else:
        count = await Students.filter(state_id=state_id).prefetch_related('branch', 'governorate', 'institute', 'state',
                                                                          'poster').all()
        students = await Students.filter(state_id=state_id).prefetch_related('branch', 'governorate', 'institute', 'state',
                                                                             'poster').all().limit(params.number_of_students).offset((params.page - 1) *
                                                                                                                                     params.number_of_students)
    count = len(count)
    students_list = []
    student_json = {}
    for stu in students:
        student_json['name'] = stu.name
        student_json['id'] = stu.id
        student_json['school'] = stu.school
        student_json['code_1'] = stu.code_1
        student_json['code_2'] = stu.code_2
        student_json['first_phone'] = stu.first_phone
        student_json['second_phone'] = stu.second_phone
        student_json['telegram_username'] = stu.telegram_user
        student_json['created_at'] = stu.created_at
        student_json['note'] = stu.note
        student_json['total_amount'] = stu.total_amount
        student_json['remaining_amount'] = stu.remaining_amount
        if stu.branch is not None:
            student_json['branch'] = {
                "id": stu.branch.id, 'name': stu.branch.name}
        if stu.governorate is not None:
            student_json['governorate'] = {
                "id": stu.governorate.id, "name": stu.governorate.name}
        if stu.institute is not None:
            student_json['institute'] = {
                'id': stu.institute.id, "name": stu.institute.name}
        if stu.state is not None:
            student_json['state'] = {
                'id': stu.state.id, 'name': stu.state.name}
        if stu.poster is not None:
            student_json['poster'] = {
                'id': stu.poster.id, 'name': stu.poster.name}
        student_install = await StudentInstallments.filter(student_id=stu.id).prefetch_related('installment').all()
        install_list = []
        for stu_install in student_install:
            single_install = {"date": stu_install.date, "amount": stu_install.amount,
                              "invoice": stu_install.invoice, "install_id": stu_install.installment.id, "received": stu_install.received,
                              "installment_name": stu_install.installment.name}
            install_list.append(single_install)
        student_json['installments'] = install_list
        students_list.append(student_json)
        student_json = {}
    if len(students) <= params.number_of_students:
        pages = 1
    else:
        pages = int(round(len(students) / params.number_of_students))

    return {"students": students_list, "success": True,
            "total_students": count,
            "page": params.page,
            "total_pages": pages}
