from fastapi import APIRouter
import requests
from models.models import Installments, States, Users, UserAuth, Students, StudentInstallments, TemporaryDelete

sync_router = APIRouter()


async def get_users() -> list:
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


async def get_del() -> dict:
    all_deleted = await TemporaryDelete.filter(sync_state=0).all()
    unique_id_students = []
    unique_id_students_install = []
    unique_id_states = []
    unique_id_users = []
    for deleted in all_deleted:
        if deleted.model_id == 1:
            unique_id_students.append(deleted.unique_id)
        elif deleted.model_id == 2:
            unique_id_states.append(deleted.unique_id)
        elif deleted.model_id == 3:
            unique_id_students_install.append(deleted.unique_id)
        elif deleted.model_id == 4:
            unique_id_users.append(deleted.unique_id)
        await TemporaryDelete.filter(id=deleted.id).update(sync_state=1)
    return {
        "unique_id_students": unique_id_students, "unique_id_students_install": unique_id_students_install,
        "unique_id_states": unique_id_states, "unique_id_users": unique_id_users
    }


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
    students = await Students.filter(sync_state=0).all().prefetch_related('state', 'branch', 'governorate', 'institute',
                                                                          'poster')
    for student in students:
        json_student = {"name": student.name, "school": student.school, "branch_id": student.branch.id,
                        "governorate_id": student.governorate.id, "institute_id": student.institute.id,
                        "state_unique_id": student.state.unique_id, "first_phone": student.first_phone,
                        "second_phone": student.second_phone, "code": student.code,
                        "telegram_user": student.telegram_user,
                        "created_at": str(student.created_at), "note": student.note,
                        "total_amount": student.total_amount,
                        "poster": student.poster.id, "remaining_amount": student.remaining_amount,
                        "unique_id": student.unique_id}
        req = requests.post('http://127.0.0.1:8080/student', json=json_student)
        if req.status_code == 200:
            await Students.filter(unique_id=json_student['unique_id']).update(sync_state=1)
    students = await Students.all().prefetch_related('state', 'branch', 'governorate', 'institute',
                                                     'poster')
    for student_install in students:
        stu_install = await StudentInstallments.filter(student_id=student_install.id, sync_state=0).all(). \
            prefetch_related(
            'installment')
        for insta in stu_install:
            json_install = {"date": str(insta.date), "amount": insta.amount, "unique_id": insta.unique_id,
                            "invoice": insta.invoice,
                            "install_unique_id": insta.installment.unique_id,
                            "student_unique_id": student_install.unique_id}
            req = requests.post('http://127.0.0.1:8080/student_installment', json=json_install)
            if req.status_code == 200:
                await StudentInstallments.filter(id=insta.id).update(sync_state=1)
    all_del = await get_del()
    req = requests.post('http://127.0.0.1:8080/del', json=all_del)

    return {
        "success": True
    }
