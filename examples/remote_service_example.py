from dataclasses import dataclass
from typing import List, Optional
from doraemon.remote_service import BaseService


# curl -X POST "http://10.170.138.230:8096/question/filter/intent" -H "Content-Type: application/json" -H "traceId: 1234567890" -d '{
#     "question": "tace 测试",
#     "classifyIds": [],
#     "count": 1
# }'

@dataclass
class InputProto:
    question: str
    classifyIds: List
    count: int

@dataclass
class GeneralRemoteResponseIntentInfo:
    intentQuestionId: int
    intentQuestion: str
    intentQuestionVectorStr: str
    intentQuestionVector: List
    intentId: str
    intentName: str
    intentDescription: Optional[str]
    distance: float

@dataclass
class OutputProto:
    intentQuestions: List[GeneralRemoteResponseIntentInfo]  # 命中的意图
    msg: str  # 服务的返回信息，成功为 Success

# 创建 BaseService 的实例
service = BaseService(
    name="filter_intent_service",
    service_url="http://10.170.138.230:8096/question/filter/intent",
    service_method="post",
    input_proto=InputProto,
    output_proto=OutputProto
)

# 定义请求输入
inputs = {
    "question": "tace 测试",
    "classifyIds": [],
    "count": 1
}

# 定义请求头
headers = {
    "Content-Type": "application/json",
    "traceId": "1234567890"
}

result = service(
    json=inputs,
    timeout=30,
    headers=headers
)

# 输出结果
if result:
    print("成功获取响应:", result)
else:
    print("请求失败")
