import os
import json
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain_core.runnables import RunnableSequence
from pydantic import BaseModel

# ✅ 환경 변수 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ LangChain Gemini 모델 설정
llm_ai1 = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=60)
llm_ai2 = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=60)

# ✅ 토론 메모리 (발언자 정보 저장 포함)
class DebateMemory(ConversationBufferMemory, BaseModel):
    class Config:
        extra = "allow"

    def __init__(self, speaker_role: str, **kwargs):
        super().__init__(**kwargs)
        self.speaker_role = speaker_role

    def save_context(self, inputs, outputs):
        """메모리에 대화를 저장할 때 발언자(speaker) 정보도 함께 저장"""
        input_message = {"speaker": inputs["speaker"], "content": inputs["input"]}
        output_message = {"speaker": inputs["speaker"], "content": outputs["output"]}

        if input_message["speaker"] != self.speaker_role:
            self.chat_memory.add_user_message(input_message["content"])
        if output_message["speaker"] != self.speaker_role:
            self.chat_memory.add_ai_message(output_message["content"])

    def load_memory_variables(self, inputs):
        """특정 화자의 메시지만 불러올 수 있도록 설정"""
        all_messages = self.chat_memory.messages
        return {
            "history": [
                msg for msg in all_messages if isinstance(msg, dict) and msg.get("speaker") == inputs.get("speaker")
            ]
        }

# ✅ AI1, AI2 메모리 생성
ai1_memory = DebateMemory(speaker_role="AI1")
ai2_memory = DebateMemory(speaker_role="AI2")

# ✅ AI1, AI2의 초기 주장 설정
ai1_original_claim = "지구는 정육면체 모양이다. 이것은 과학적으로 증명되었다."
ai2_original_claim = "지구는 평평하다. 중세 시대의 학자들도 이를 증명했다."

# ✅ AI1, AI2 초기 주장을 Memory에 저장
ai1_memory.save_context({"speaker": "AI1", "input": ai1_original_claim}, {"output": ai1_original_claim})
ai2_memory.save_context({"speaker": "AI2", "input": ai2_original_claim}, {"output": ai2_original_claim})

# ✅ AI1, AI2 체인용 프롬프트 설정 (자신의 주장 + 반박 포함)
ai1_claim_prompt = PromptTemplate(
    input_variables=["previous"],
    template="당신(AI1)의 주장은: {previous} \n이를 논리적으로 전개하여 설명하세요."
)

ai2_claim_prompt = PromptTemplate(
    input_variables=["previous"],
    template="당신(AI2)의 주장은: {previous} \n이를 논리적으로 전개하여 설명하세요."
)

ai1_rebuttal_prompt = PromptTemplate(
    input_variables=["previous", "opponent"],
    template="상대방(AI2)의 주장: {opponent} \n당신(AI1)의 주장은: {previous} \n이에 대해 반드시 직접 반박하며, 상대방 주장의 약점을 논리적으로 지적하세요."
)

ai2_rebuttal_prompt = PromptTemplate(
    input_variables=["previous", "opponent"],
    template="상대방(AI1)의 주장: {opponent} \n당신(AI2)의 주장은: {previous} \n이에 대해 반드시 직접 반박하며, 상대방 주장의 약점을 논리적으로 지적하세요."
)

# ✅ Runnable로 AI1과 AI2 체인 생성 (메모리 포함)
ai1_claim_chain = ai1_claim_prompt | llm_ai1
ai2_claim_chain = ai2_claim_prompt | llm_ai2
ai1_rebuttal_chain = ai1_rebuttal_prompt | llm_ai1
ai2_rebuttal_chain = ai2_rebuttal_prompt | llm_ai2

# ✅ Memory를 포함하는 RunnableLambda 생성
def update_memory(memory, inputs, speaker):
    memory.save_context({"speaker": speaker, "input": inputs["previous"]}, {"output": inputs.get("opponent", inputs["previous"])})
    return inputs  # 체인에 그대로 반환

ai1_memory_runnable = RunnableLambda(lambda x: update_memory(ai1_memory, x, "AI1"))
ai2_memory_runnable = RunnableLambda(lambda x: update_memory(ai2_memory, x, "AI2"))

# ✅ 중간 결과 출력 함수
def print_response(label, response):
    print(f"\n=== {label} ===\n{response}")
    return response  # 반환값 유지

print_ai1_claim = RunnableLambda(lambda x: print_response("🟢 AI1 논리 전개", x))
print_ai2_claim = RunnableLambda(lambda x: print_response("🔵 AI2 논리 전개", x))
print_ai1_rebuttal = RunnableLambda(lambda x: print_response("🟢 AI1 반박", x))
print_ai2_rebuttal = RunnableLambda(lambda x: print_response("🔵 AI2 반박", x))

# ✅ AI1 주장 → AI2 주장 → AI1 반박 → AI2 반박 순서로 체인 연결
debate_chain = (
    RunnablePassthrough()
    | ai1_claim_chain  # AI1 주장
    | print_ai1_claim
    | RunnableLambda(lambda x: {"previous": ai2_original_claim})  # AI2 주장 시작
    | ai2_claim_chain
    | print_ai2_claim
    | RunnableLambda(lambda x: {"previous": x, "opponent": ai1_original_claim})  # AI1이 반박할 수 있도록 AI2의 결과를 전달
    | ai1_rebuttal_chain
    | print_ai1_rebuttal
    | RunnableLambda(lambda x: {"previous": x, "opponent": x})  # AI2가 반박할 수 있도록 AI1의 결과를 전달
    | ai2_rebuttal_chain
    | print_ai2_rebuttal
)

# ✅ 토론 시작
print("\n=== 토론 시작 ===")
debate_result = debate_chain.invoke({"previous": ai1_original_claim})

print("\n=== 최종 토론 결과 ===")
print(debate_result)
