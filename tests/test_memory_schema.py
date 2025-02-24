import os
import json
import google.auth
import google.auth.transport.requests
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage, messages_from_dict, messages_to_dict
from pydantic import BaseModel

# ✅ 환경 변수 설정 (gRPC 안정화)
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "1"
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_POLL_STRATEGY"] = "epoll1"

# ✅ .env 파일 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # 환경 변수에서 API 키 가져오기

# ✅ LangChain Gemini 모델 설정 (타임아웃 추가)
llm_ai1 = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    request_timeout=60  # ✅ 타임아웃 적용
)

llm_ai2 = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    request_timeout=60  # ✅ 타임아웃 적용
)

# ✅ 메시지 디버깅용 함수 (입력값이 올바른지 확인)
def print_messages(messages, tag="Messages"):
    print(f"\n=== {tag} ===")
    for msg in messages:
        print(json.dumps(msg.dict(), ensure_ascii=False, indent=2))

# ✅ DebateMemory 구현 (반대측 주장만 기억)
class DebateMemory(ConversationBufferMemory, BaseModel):
    class Config:
        extra = "allow"

    def __init__(self, speaker_role: str, **kwargs):
        super().__init__(**kwargs)
        self.speaker_role = speaker_role

    def filter_messages(self, messages):
        return [msg for msg in messages if "speaker" in msg and msg["speaker"] != self.speaker_role]

    def load_memory_variables(self, inputs):
        all_messages = self.chat_memory.messages
        filtered_messages = self.filter_messages(messages_to_dict(all_messages))
        return {"history": messages_from_dict(filtered_messages)}

    def save_context(self, inputs, outputs):
        input_message = {"speaker": inputs["speaker"], "content": inputs["input"]}
        output_message = {"speaker": inputs["speaker"], "content": outputs["output"]}

        if input_message["speaker"] != self.speaker_role:
            self.chat_memory.add_user_message(input_message["content"])
        if output_message["speaker"] != self.speaker_role:
            self.chat_memory.add_ai_message(output_message["content"])

# ✅ AI 모델 및 메모리 생성
ai1_memory = DebateMemory(speaker_role="AI1")
ai2_memory = DebateMemory(speaker_role="AI2")

# ✅ 각 AI의 원래 주장
ai1_original_claim = "지구는 정육면체 모양이다. 이것은 과학적으로 증명되었다."
ai2_original_claim = "지구는 평평하다. 중세 시대의 학자들도 이를 증명했다."

# ✅ AI의 역할을 정의하는 시스템 메시지
system_message_ai1 = SystemMessage(
    content=f"당신은 찬성 측 토론자입니다. 당신의 입장은: \"{ai1_original_claim}\" 상대방의 반박에도 불구하고, 자신의 주장을 강력히 유지하며, 상대방의 반론을 논리적으로 반박하세요."
)

system_message_ai2 = SystemMessage(
    content=f"당신은 반대 측 토론자입니다. 당신의 입장은: \"{ai2_original_claim}\" 상대방의 반박에도 불구하고, 자신의 주장을 강력히 유지하며, 상대방의 반론을 논리적으로 반박하세요."
)

# ✅ 초기 주장 저장
ai1_memory.save_context({"speaker": "AI1", "input": ai1_original_claim}, {"output": ai1_original_claim})
ai2_memory.save_context({"speaker": "AI2", "input": ai2_original_claim}, {"output": ai2_original_claim})

# ✅ AI1 첫 번째 주장
ai1_messages = [
    system_message_ai1,
    HumanMessage(content="토론을 시작합니다. 당신의 주장을 펼쳐 주세요."),
]
print_messages(ai1_messages, "AI1 Messages Before Invoke")  # ✅ 입력값 확인
ai1_response = llm_ai1.invoke(ai1_messages)
ai1_response_text = str(ai1_response.content) if hasattr(ai1_response, "content") and ai1_response.content else "AI1은 아직 주장하지 않았습니다."
ai1_memory.save_context({"speaker": "AI1", "input": ai1_response_text}, {"output": ai1_response_text})

# ✅ AI2 첫 번째 반박
ai2_messages = [
    system_message_ai2,
    HumanMessage(content=f"상대방(AI1)의 주장: {ai1_response_text}\n이에 대해 반박하세요."),
]
print_messages(ai2_messages, "AI2 Messages Before Invoke")  # ✅ 입력값 확인
ai2_response = llm_ai2.invoke(ai2_messages)
ai2_response_text = str(ai2_response.content) if hasattr(ai2_response, "content") and ai2_response.content else "AI2는 아직 반박하지 않았습니다."
ai2_memory.save_context({"speaker": "AI2", "input": ai2_response_text}, {"output": ai2_response_text})

# ✅ AI1 두 번째 반박 (이전 응답 확인 후 메시지 추가)
if isinstance(ai2_response_text, str) and ai2_response_text.strip():
    ai1_messages.append(HumanMessage(content=f"상대방(AI2)의 주장: {ai2_response_text}\n이에 대해 반박하세요."))  # ✅ HumanMessage로 변경
print_messages(ai1_messages, "AI1 Messages Before Second Invoke")  # ✅ 입력값 확인
ai1_response = llm_ai1.invoke(ai1_messages)
ai1_response_text = str(ai1_response.content) if hasattr(ai1_response, "content") and ai1_response.content else "AI1은 아직 추가 반박하지 않았습니다."
ai1_memory.save_context({"speaker": "AI1", "input": ai1_response_text}, {"output": ai1_response_text})

# ✅ AI2 두 번째 반박 (이전 응답 확인 후 메시지 추가)
if isinstance(ai1_response_text, str) and ai1_response_text.strip():
    ai2_messages.append(HumanMessage(content=f"상대방(AI1)의 주장: {ai1_response_text}\n이에 대해 반박하세요."))  # ✅ HumanMessage로 변경
print_messages(ai2_messages, "AI2 Messages Before Second Invoke")  # ✅ 입력값 확인
ai2_response = llm_ai2.invoke(ai2_messages)
ai2_response_text = str(ai2_response.content) if hasattr(ai2_response, "content") and ai2_response.content else "AI2는 아직 추가 반박하지 않았습니다."
ai2_memory.save_context({"speaker": "AI2", "input": ai2_response_text}, {"output": ai2_response_text})
