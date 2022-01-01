from tortoise.models import Model
from tortoise import fields


class Installments(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()


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


class Authorities(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    governorate = fields.ForeignKeyField("models.Governorates")


class Users(Model):
    id = fields.IntField(pk=True)
    username = fields.TextField()
    password = fields.TextField()


class UserAuth(Model):
    id = fields.IntField(pk=True)
    auth = fields.ForeignKeyField("models.Authorities")
    user = fields.ForeignKeyField("models.Users")

    class Meta:
        table = "user_auth"


class Students(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    school = fields.TextField(null=True)
    branch = fields.ForeignKeyField("models.Branches", null=True)
    governorate = fields.ForeignKeyField("models.Governorates")
    institute = fields.ForeignKeyField("models.Institutes")
    first_phone = fields.IntField(null=True)
    second_phone = fields.IntField(null=True)
    code = fields.IntField(nul=True)
    telegram_user = fields.TextField(null=True)
    created_at = fields.DateField(null=True)
    note = fields.TextField(null=True)
    total_amount = fields.IntField(null=True)
    poster = fields.ForeignKeyField("models.Posters", null=True)


class StudentInstallments(Model):
    id = fields.IntField(pk=True)
    installment = fields.ForeignKeyField("models.Installments", null=True)
    date = fields.DateField(null=True)
    amount = fields.IntField(null=True)
    remaining_amount = fields.FloatField(null=True)
    invoice = fields.IntField(null=True)
    student = fields.ForeignKeyField("models.Students", null=True)

    class Meta:
        table = "student_installments"