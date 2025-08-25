# base.py
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Session
from typing import Optional, Type, TypeVar, Any, Dict, List
from pydantic import BaseModel

# 定义类型变量
T = TypeVar("T", bound="MyModel")


def get_datetime_now():
    return datetime.now()


class MyModel:
    __tablename__ = "--"
    deleted_at_value = None
    id = Column(INTEGER(11), primary_key=True)
    create_at = Column(DateTime(), default=get_datetime_now, comment="创建时间")
    update_at = Column(DateTime(), default=get_datetime_now, comment="修改时间")
    deleted_at = Column(
        DateTime(), nullable=True, name="deleted_at", comment="删除时间"
    )

    @classmethod
    def get_by_id(cls: Type[T], session: Session, primary_key: int) -> Optional[T]:
        """根据ID获取记录"""
        return (
            session.query(cls)
            .filter(cls.id == primary_key, cls.deleted_at.is_(None))
            .first()
        )

    @classmethod
    def insert(
        cls: Type[T], session: Session, json_data: Dict[str, Any], commit: bool = True
    ) -> int:
        """插入记录"""
        item = cls.loads(json_data)
        session.add(item)
        session.flush()
        if commit:
            session.commit()
        return item.id

    @classmethod
    def loads(cls: Type[T], json_data: Dict[str, Any]) -> T:
        """从字典加载数据到模型实例"""
        item = cls()
        for key, value in json_data.items():
            if hasattr(cls, key) and value is not None:
                setattr(item, key, value)
        return item

    @classmethod
    def update(
        cls, session: Session, json_data: Dict[str, Any], commit: bool = True
    ) -> int:
        """更新记录"""
        update_cols = {}
        for key, value in json_data.items():
            if (
                hasattr(cls, key)
                and value is not None
                and key not in ["id", "create_at", "update_at", "deleted_at"]
            ):
                update_cols[key] = value

        session.query(cls).filter(cls.id == json_data["id"]).update(update_cols)
        if commit:
            session.commit()
        return json_data["id"]

    @classmethod
    def delete(cls, session: Session, primary_key: int, commit: bool = True) -> None:
        """软删除记录"""
        update_cols = {cls.deleted_at: datetime.now()}
        session.query(cls).filter(cls.id == primary_key).update(update_cols)
        if commit:
            session.commit()

    @classmethod
    def select_by(
        cls: Type[T], session: Session, criterion: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """根据条件查询记录"""
        if criterion is None:
            criterion = {}
        query = session.query(cls)
        order_by_val = None

        for key in criterion:
            val = criterion[key]
            if key == "order_by":
                order_by_val = val
                continue
            elif val is not None:
                if isinstance(val, list):
                    query = query.filter(getattr(cls, key).in_(val))
                elif isinstance(val, dict):
                    compare = val["type"]
                    compare_val = val.get("value", None)
                    if compare == "gt":
                        query = query.filter(getattr(cls, key) > compare_val)
                    elif compare == "gte":
                        query = query.filter(getattr(cls, key) >= compare_val)
                    elif compare == "lt":
                        query = query.filter(getattr(cls, key) < compare_val)
                    elif compare == "lte":
                        query = query.filter(getattr(cls, key) <= compare_val)
                    elif compare == "like":
                        query = query.filter(getattr(cls, key).like(f"%{compare_val}%"))
                    elif compare == "not in":
                        query = query.filter(getattr(cls, key).notin_(compare_val))
                    elif compare == "in":
                        query = query.filter(getattr(cls, key).in_(compare_val))
                    elif compare == "bt":
                        start = val.get("start", None)
                        end = val.get("end", None)
                        query = query.filter(
                            getattr(cls, key) >= start, getattr(cls, key) <= end
                        )
                else:
                    query = query.filter(getattr(cls, key) == val)

        if cls.deleted_at_value is None:
            query = query.filter(cls.deleted_at.is_(None))
        else:
            query = query.filter(cls.deleted_at == cls.deleted_at_value)

        if order_by_val is not None:
            if isinstance(order_by_val, dict):
                col = order_by_val["col"]
                sort = order_by_val["sort"]
                if sort == "desc":
                    query = query.order_by(getattr(cls, col).desc())
                else:
                    query = query.order_by(getattr(cls, col).asc())
            elif isinstance(order_by_val, list):
                for order_item in order_by_val:
                    col = order_item["col"]
                    sort = order_item["sort"]
                    if sort == "desc":
                        query = query.order_by(getattr(cls, col).desc())
                    else:
                        query = query.order_by(getattr(cls, col).asc())

        return query.all()

    @classmethod
    def select_one_by(
        cls: Type[T], session: Session, criterion: Dict[str, Any]
    ) -> Optional[T]:
        """根据条件查询单个记录"""
        query = cls.select_by(session, criterion)
        return query[0] if query else None

    @classmethod
    def batch_insert(
        cls: Type[T], session: Session, datas: List[Dict[str, Any]], commit: bool = True
    ) -> None:
        """批量插入记录"""
        if not datas:
            return

        items = [cls.loads(data) for data in datas]
        session.add_all(items)
        if commit:
            session.commit()
