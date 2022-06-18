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

# todo: complete sync_state
# todo: complete api sync with online interaction
general_router = APIRouter()


@general_router.get('/shutdown')
async def shutdown():
    pid = os.getpid()
    os.kill(pid, signal.CTRL_C_EVENT)


@general_router.get('/governorates')
async def get_governorates():
    return {
        "success": True,
        "governorates": await Governorates.all()
    }


@general_router.get('/branches')
async def get_branches():
    return {
        "branches": await Branches.all(),
        "success": True
    }


@general_router.get('/posters')
async def get_posters():
    return {
        "posters": await Posters.all(),
        "success": True
    }


@general_router.get('/institutes')
async def get_institutes():
    return {
        "institutes": await Institutes.all()
    }


@general_router.get('/installments')
async def get_installments():
    return {
        "installments": await Installments.all()
    }


@general_router.patch('/installments/{installment_id}')
async def patch_installments(installment_id: int, date: str):
    try:
        await Installments.filter(id=installment_id).update(date=date)
        q = await Installments.filter(id=installment_id).first().values('unique_id')
        async with in_transaction() as coon:
            new = TemporaryPatch(unique_id=q['unique_id'], model_id=5)
            await new.save(using_db=coon)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")

# @general_router.patch('/ss')
# async def sss():
#     await Students.all().update(sync_state=1)
#     await StudentInstallments.all().update(sync_state=1)
#     await States.all().update(sync_state=1)
#     return {
#         "success": True
#     }
