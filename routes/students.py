import os
import signal
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, Response, UploadFile, File
from starlette.responses import StreamingResponse, FileResponse
from models.models import Institutes, Governorates, States, Students, Installments, StudentInstallments, \
    Users, UserAuth, TemporaryPatch, TemporaryDelete, Branches, Posters
from tortoise.transactions import in_transaction
from schemas.general import GeneralSchema, Student, StudentInstall, User, Login
import hashlib
import datetime
from fastapi_pagination import paginate, Params as ps
import requests
import os
import arabic_reshaper
from bidi.algorithm import get_display
import qrcode
from PIL import ImageDraw, ImageFont, Image
# import json

from io import BytesIO
from starlette.exceptions import HTTPException as StarletteHTTPException
import aiofiles

students_router = APIRouter()

# Function to generate qr image with student id and name embedded in it


def qr_gen(id_num, name, institute):
    id_num = str(id_num)
    arabic = name
    name = arabic_reshaper.reshape(arabic)
    name = get_display(name, upper_is_rtl=True)
    img = qrcode.make(id_num + "|" + "besmarty")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('arial.ttf', 20)
    draw.text((125, 335), name, font=font, align="left")
    imagname = '{}-{}.png'.format(id_num, arabic)
    my_path = './qr/' + institute + '/' + imagname
    img.save(os.path.join(os.getenv('LOCALAPPDATA'), "ims", my_path), 'PNG')
    return {
        "qrpath": my_path

    }


# async def save_files(file):
#     """
#     save multiple files of patient
#     """
#     path_data = directory()
#     path_data = os.path.join(path_data, 'clinic360')
#     if 'labs' not in os.listdir(path_data):
#         os.makedirs(os.path.join(path_data, 'labs'))
#     path_data = os.path.join(path_data, 'labs')
#     file_name = file.filename
#     file_type = file_name.split('.')
#     file_type = file_type[-1]
#     name = f'{str(uuid.uuid4().hex)}.{file_type}'
#     my_path = os.path.join(path_data, name)
#     return {
#         "path": '/clinic360/labs/{}'.format(name)
#     }


async def photo_save(photo, _id, name, institute):
    file_name = photo.filename
    file_type = file_name.split('.')
    file_type = file_type[-1]
    print(file_name)
    name = '{}-{}.jpg'.format(_id, name)
    my_path = './images/' + institute + '/' + name
    async with aiofiles.open(os.path.join(os.getenv('LOCALAPPDATA'), "ims", my_path), 'wb') as out_file:
        content = await photo.read()  # async read
        await out_file.write(content)  # async write
    return {
        "image_path": my_path
    }

# POST `/students`
# - Add a student to the database.
# - Request Arguments: None.
# - Returns: name of student.
# Example Request Payload `{
#     "name": "1",
#     "school": "1",
#     "state_id": int
#     "branch_id": "1",
#     "institute_id": "1",
#     "governorate_id": "1",
#     "first_phone": "1",
#     "second_phone": "1",
#     "poster_id": "1",
#     "code": "1",
#     "telegram_username": "1",
#     "total_amount": "1",
#     "installments":[{"install_id":int, "amount":float, "invoice":int, "date":str}, {}, {},{}]
#     "remaining_amount": "1",
#     "note": "1",
#     "created_at":str
# }`
# Example Response `{
#     "name": "جبار علي",
#     "success": true
# }`


@students_router.post('/students')
async def post_student(schema: Student):
    async with in_transaction() as conn:
        unique_id = str(uuid4())[0:18]
        date_now = datetime.datetime.now().strftime('%Y-%m-%d')
        poster_id = None
        if schema.poster_id != 0:
            poster_id = schema.poster_id
        new = Students(name=schema.name, school=schema.school, branch_id=schema.branch_id, dob=schema.dob,
                       governorate_id=schema.governorate_id, institute_id=schema.institute_id,
                       state_id=schema.state_id, first_phone=schema.first_phone,
                       second_phone=schema.second_phone, code_1=schema.code_1, code_2=schema.code_2,
                       telegram_user=schema.telegram_username, created_at=date_now, note=schema.note, total_amount=schema.total_amount,
                       remaining_amount=schema.remaining_amount, banned=schema.banned, poster_id=poster_id, unique_id=unique_id)
        await new.save(using_db=conn)
        institute = await Institutes.filter(id=schema.institute_id).first()
        # if photo is not None:
        #     photo = BytesIO(photo)
        #     image = photo_save(photo, unique_id, new.name,
        #                        institute.name)
        #     new.photo = image['image_path']
        if institute:
            qr = qr_gen(unique_id, schema.name, institute.name)
        await Students.filter(id=new.id).update(qr=qr['qrpath'])
        for student_install in schema.installments:
            unique_id2 = str(uuid4())
            new_student_install = StudentInstallments(installment_id=student_install.install_id,
                                                      date=student_install.date, received=student_install.received,
                                                      amount=student_install.amount, invoice=student_install.invoice,
                                                      student_id=new.id, unique_id=unique_id2)
            await new_student_install.save(using_db=conn)
    if institute:
        req = requests.post("http://127.0.0.1/personnel/api/employees/",
                            json={
                                "emp_code": unique_id,
                                "first_name": schema.name,
                                "area": [2],
                                "department": 1,
                            },  headers={'Content-Type': 'application/json', "Authorization": f"JWT {schema.token}"})
        print(req)
        print(req.json())
        if req.status_code == 201:
            return {"success": True,
                    "name": new.name, "id": new.id}
    return {"success": True,
            "name": new.name, "id": new.id}


# To change student's photo
@students_router.patch('/photo')
async def patch_photo(student_id: int, photo: UploadFile = File("photo")):
    # try:
    stud = await Students.filter(id=student_id).first()
    institute = await Institutes.filter(id=stud.institute_id).first()
    if stud.photo is not None:
        os.remove(os.path.join(os.getenv('LOCALAPPDATA'), "ims", stud.photo))
    print(photo)
    save = await photo_save(photo, stud.unique_id, stud.name, institute.name)
    await Students.filter(id=student_id).update(photo=save['image_path'])
    return {
        'success': True
    }
    # except:
    #     raise StarletteHTTPException(500, "internal Server Error")

# Patch `/students/{student_id}`
# - edit the student .
# - Request Arguments: None.
# - Returns: name of student.
# Example Request Payload `{
#     "name": "1",
#     "school": "1",
#     "state_id": int
#     "branch_id": "1",
#     "institute_id": "1",
#     "governorate_id": "1",
#     "first_phone": "1",
#     "second_phone": "1",
#     "poster_id": "1",
#     "code": "1",
#     "telegram_username": "1",
#     "total_amount": "1",
#     "installments":[{"install_id":int, "amount":float, "invoice":int, "date":str}, {}, {},{}]
#     "remaining_amount": "1",
#     "note": "1",
#     "created_at":str
# }`
# Example Response `{
#     "name": "جبار علي",
#     "success": true
# }`


@students_router.patch('/students/{student_id}')
async def patch_student(student_id, schema: Student):
    date_now = datetime.datetime.now().strftime('%Y-%m-%d')
    poster_id = None
    if schema.poster_id != 0:
        poster_id = schema.poster_id
    await Students.filter(id=student_id).update(name=schema.name, school=schema.school, dob=schema.dob,
                                                branch_id=schema.branch_id,
                                                governorate_id=schema.governorate_id,
                                                institute_id=schema.institute_id,
                                                state_id=schema.state_id,
                                                first_phone=schema.first_phone,
                                                second_phone=schema.second_phone,
                                                code_1=schema.code_1,
                                                code_2=schema.code_2,
                                                telegram_user=schema.telegram_username,
                                                note=schema.note,
                                                total_amount=schema.total_amount,
                                                remaining_amount=schema.remaining_amount,
                                                banned=schema.banned,
                                                poster_id=poster_id)
    name = await Students.filter(id=student_id).first().values('name', 'unique_id')
    async with in_transaction() as conn:
        new = TemporaryPatch(unique_id=name['unique_id'], model_id=1)
        await new.save(using_db=conn)
    institute = await Institutes.filter(id=schema.institute_id).first()
    # if photo is not None:
    #     photo = BytesIO(photo)
    #     image = photo_save(photo, unique_id, new.name,
    #                        institute.name)
    #     new.photo = image['image_path']
    if institute:
        qr = qr_gen(name['unique_id'], schema.name, institute.name)
    await Students.filter(id=student_id).update(qr=qr['qrpath'])
    for student_install in schema.installments:
        await StudentInstallments.filter(student_id=student_id, installment_id=student_install.install_id).update(
            received=student_install.received,
            date=student_install.date,
            amount=student_install.amount,
            invoice=student_install.invoice)
        q = await StudentInstallments.filter(student_id=student_id, installment_id=student_install.install_id
                                             ).first().values('unique_id')
        async with in_transaction() as coon:
            new = TemporaryPatch(unique_id=q['unique_id'], model_id=3)
            await new.save(using_db=coon)

    if institute:
        req = requests.get(f"http://127.0.0.1/personnel/api/employee/?emp_code={name['unique_id']}",  headers={
            'Content-Type': 'application/json', "Authorization": f"JWT {schema.token}"})
        print(req)
        json_data = req.json()
        json_data_id = json_data.get("data")[0].get("id")
        req = requests.patch(f"http://127.0.0.1/personnel/api/employees/{json_data_id}/",
                             json={
                                 "first_name": schema.name,
                                 "last_name": "",
                             },  headers={'Content-Type': 'application/json', "Authorization": f"JWT {schema.token}"})
        print(req)
        print(req.json())
        name = name['name']
    return {
        "success": True,
        "name": name, "id": student_id
    }


# DELETE `/students/<student_id>`
#
# - Delete a student from the database.
# - Request Arguments: None.
# - Returns: name of students.
#
# Example Response `{
#     "name": "جبار علي",
#     "success": true
# }`
@students_router.delete('/students/{student_id}')
async def del_student(student_id, token):
    student = await Students.filter(id=student_id).first().values('name', "institute_id", 'unique_id')
    name = student['name']
    await Students.filter(id=student_id).delete()
    await TemporaryPatch.filter(unique_id=student['unique_id']).delete()

    async with in_transaction() as conn:
        new = TemporaryDelete(unique_id=student['unique_id'], model_id=1)
        await new.save(using_db=conn)
    if student["institute_id"]:
        req = requests.get(f"http://127.0.0.1/personnel/api/employee/?emp_code={student['unique_id']}",  headers={
            'Content-Type': 'application/json', "Authorization": f"JWT {token}"})
        print(req)
        json_data = req.json()
        json_data_id = json_data.get("data")[0].get("id")
        req = requests.delete(f"http://127.0.0.1/personnel/api/employees/{json_data_id}/",  headers={
            'Content-Type': 'application/json', "Authorization": f"JWT {token}"})
    return {
        "success": True,
        "name": name
    }


# GET '/students'
# = get students bulky
# Response:
# "students":[
#   {
#     "name": "حسين فاضل",
#     "id": 1,
#     "school": "المستقبل",
#     "code": 7879,
#     "first_phone": 886786,
#     "second_phone": 56789,
#     "telegram_user": "string",
#     "created_at": null,
#     "note": "string",
#     "total_amount": 1000,
#     "remaining_amount": 0,
#     "branch": {
#       "id": 1,
#       "name": "احيائي"
#     },
#     "governorate": {
#       "id": 1,
#       "name": "بغداد"
#     },
#     "institute": {
#       "id": 1,
#       "name": "البنوك"
#     },
#     "state": {
#       "id": 1,
#       "name": "بغداد عربي انكليزي"
#     },
#     "poster": {
#       "id": 1,
#       "name": "اخضر"
#     },
#     "installments": [
#       {
#         "id": 1,
#         "date": null,
#         "amount": 0,
#         "invoice": 0,
#         "installment_id": 1,
#         "installment_name": "القسط الاول"
#       },
#       {
#         "id": 2,
#         "date": null,
#         "amount": 0,
#         "invoice": 0,
#         "installment_id": 2,
#         "installment_name": "القسط الثاني"
#       }
#     ]
#   }
# ],
# "success":True}
class Params(ps):
    search: Optional[str] = None
    page: Optional[int] = 1
    number_of_students: int = 100


@students_router.get('/students')
async def get_students():
    students = await Students.all().prefetch_related('branch', 'governorate', 'institute', 'state', 'poster').all()
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
            single_install = {"install_id": stu_install.installment.id, "date": stu_install.date, "amount": stu_install.amount,
                              "invoice": stu_install.invoice, "installment_id": stu_install.installment.id, "received": stu_install.received,
                              "installment_name": stu_install.installment.name}
            install_list.append(single_install)
        student_json['installments'] = install_list
        students_list.append(student_json)
        student_json = {}

    return {"students": students_list, "success": True}


@students_router.get('/students-names')
async def get_students_names():
    students = await Students.all().values("id", "name")

    return {"students": students, "success": True}

# To get student image & qr by id


@students_router.get('/photo')
async def get_photo(student_id):
    try:
        query = await Students.filter(id=student_id).first()
        image_path = query.photo

        return FileResponse(os.path.join(
            os.getenv('LOCALAPPDATA'), "ims", image_path))

    except:
        raise StarletteHTTPException(404, "Not Found")


@students_router.get('/qr')
async def get_qr(student_id):
    # try:
    query = await Students.filter(id=student_id).first()
    qr_path = query.qr
    img = Image.open(os.path.join(
        os.getenv('LOCALAPPDATA'), "ims", qr_path))
    buf = BytesIO()
    img.save(buf, 'png')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

    # except:
    #     raise StarletteHTTPException(404, "Not Found")
