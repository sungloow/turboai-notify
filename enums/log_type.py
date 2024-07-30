from enum import Enum

class LogType(Enum):
    def __new__(cls, code, description):
        obj = object.__new__(cls)
        obj.code = code
        obj.description = description
        return obj

    ALL = (0, "全部")
    RECHARGE = (1, "充值")
    CONSUME = (2, "消费")
    MANAGE = (3, "管理")
    SYSTEM = (4, "系统")
