from tortoise.models import Model
from tortoise import fields


class Installments(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    date = fields.DateField(null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced


class Branches(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()


class Governorates(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()


class Institutes(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()


class Posters(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()


# class Authorities(Model):
#     id = fields.IntField(pk=True)
#     name = fields.TextField()
#     state = fields.ForeignKeyField("models.States")


class Users(Model):
    id = fields.IntField(pk=True)
    username = fields.TextField()
    password = fields.TextField()
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)
    name = fields.TextField(null=True)
    super = fields.IntField(default=0)


class UserAuth(Model):
    id = fields.IntField(pk=True)
    state = fields.ForeignKeyField("models.States")
    user = fields.ForeignKeyField("models.Users")
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)

    class Meta:
        table = "user_auth"


class Students(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    school = fields.TextField(null=True)
    branch = fields.ForeignKeyField("models.Branches", null=True)
    governorate = fields.ForeignKeyField("models.Governorates", null=True)
    institute = fields.ForeignKeyField("models.Institutes", null=True)
    state = fields.ForeignKeyField("models.States", null=True)
    first_phone = fields.TextField(null=True)
    second_phone = fields.TextField(null=True)
    code_1 = fields.TextField(null=True)
    code_2 = fields.TextField(null=True)
    telegram_user = fields.TextField(null=True)
    created_at = fields.DateField(null=True)
    note = fields.TextField(null=True)
    total_amount = fields.FloatField(null=True)
    poster = fields.ForeignKeyField("models.Posters", null=True)
    remaining_amount = fields.FloatField(null=True)
    photo = fields.TextField(null=True)
    qr = fields.TextField(null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)


class StudentInstallments(Model):
    id = fields.IntField(pk=True)
    installment = fields.ForeignKeyField("models.Installments", null=True)
    date = fields.DateField(null=True)
    amount = fields.IntField(null=True)
    invoice = fields.IntField(null=True)
    student = fields.ForeignKeyField("models.Students", null=True)
    received = fields.IntField(default=0)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)

    class Meta:
        table = "student_installments"


class Attendance(Model):
    id = fields.IntField(pk=True)
    date = fields.TextField(null=True)
    institute = fields.ForeignKeyField('models.Institutes', null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced

    class Meta:
        table = "attendance"


class StudentAttendance(Model):
    id = fields.IntField(pk=True)
    student = fields.ForeignKeyField('models.Students', null=True)
    attendance = fields.ForeignKeyField('models.Attendance', null=True)
    attended = fields.IntField(default=0)
    time = fields.TextField(null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced

    class Meta:
        table = "student_attendance"


class States(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)


class TemporaryDelete(Model):
    id = fields.IntField(pk=True)
    unique_id = fields.TextField()
    model_id = fields.IntField()
    ''' 
    model_id = {"Students": 1, "states": 2, "student_installment": 3, "users": 4, "installments": 5}
    '''
    sync_state = fields.IntField(default=0)


class TemporaryPatch(Model):
    id = fields.IntField(pk=True)
    unique_id = fields.TextField()
    model_id = fields.IntField()
    ''' 
    model_id = {"Students": 1, "states": 2, "student_installment": 3, "users": 4, "installments": 5}
    '''
    sync_state = fields.IntField(default=0)
