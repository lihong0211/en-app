from marshmallow import fields
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.mysql import TEXT

from app.app import db
from model.common.my_model import MySchema, MyModel
from utils import get_datetime_now


class Doctor(db.Model, MyModel):
    __tablename__ = "doctor"
    phone = Column(String(15), nullable=False, comment="手机号")
    platform = Column(
        Integer, nullable=False, default=0, comment="平台：1、拼多多,2、阿里健康"
    )
    doctor_name = Column(String(30), nullable=False, comment="医生账户名称")
    phone_user_name = Column(String(30), nullable=False, comment="钉钉用户id")
    role = Column(
        Integer,
        nullable=False,
        default=1,
        comment="角色:1、人工医生，2、开方医生，3、引流医生",
    )
    remark = Column(String(200), nullable=False, comment="备注信息")
    work_group = Column(Integer, nullable=False, default=0, comment="工作组：1,2组等等")
    transfer_type = Column(
        Integer,
        nullable=False,
        default=0,
        comment="转诊类型： 0自动转诊，1 手动转诊，2 不转诊",
    )
    device_code = Column(String(30), nullable=False, default="", comment="设备号")
    transfer_id = Column(Integer, nullable=False, default=0, comment="转诊医生id")
    transfer_name = Column(
        String(30), nullable=False, default="", comment="转诊医生名称"
    )
    user_name = Column(String(30), nullable=False, default="", comment="医生名称")
    team = Column(String(50), nullable=False, default="", comment="团队名称")


class DoctorSchema(MySchema):
    phone = fields.String()
    platform = fields.Integer()
    doctor_name = fields.String()
    phone_user_name = fields.String()
    role = fields.Integer()
    remark = fields.String()
    work_group = fields.Integer()
    transfer_type = fields.Integer()
    device_code = fields.String()
    transfer_id = fields.Integer()
    transfer_name = fields.String()
    user_name = fields.String()
    team = fields.String()
