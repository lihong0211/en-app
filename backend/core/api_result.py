import json


# 成功
def success(data=None):
    resp = json.dumps({"code": 200, "msg": "success", "data": data}, ensure_ascii=False)
    return resp


# 错误
def error(msg="系统错误", code=400, data=None):
    resp = json.dumps({"code": code, "msg": msg, "data": data}, ensure_ascii=False)
    return resp
