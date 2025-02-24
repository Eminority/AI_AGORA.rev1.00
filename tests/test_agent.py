import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough, RunnableSequence
from pydantic import BaseModel

# ✅ 환경 변수 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ LangChain Gemini 모델 설정
llm_ai1 = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=60)
llm_ai2 = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=60)
llm_moderator = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=60)
llm_judge = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=60)

# ✅ 토론 메모리
class DebateMemory(ConversationBufferMemory, BaseModel):
    class Config:
        extra = "allow"

    def __init__(self, speaker_role: str, **kwargs):
        super().__init__(**kwargs)
        self.speaker_role = speaker_role

    def save_context(self, inputs, outputs):
        """발언자의 발언을 메모리에 저장"""
        input_message = {"speaker": inputs["speaker"], "content": inputs["input"]}
        output_message = {"speaker": inputs["speaker"], "content": outputs["output"]}
        self.chat_memory.add_user_message(input_message["content"])
        self.chat_memory.add_ai_message(output_message["content"])

    def load_memory_variables(self, inputs):
        """특정 발언자의 메시지만 불러오기"""
        return {
            "history": [
                msg for msg in self.chat_memory.messages
                if isinstance(msg, dict) and msg.get("speaker") == inputs.get("speaker")
            ]
        }

# ✅ AI1, AI2 메모리 생성
ai1_memory = DebateMemory(speaker_role="AI1")
ai2_memory = DebateMemory(speaker_role="AI2")

# ✅ 초기 주장
ai1_original_claim = "닭이 달걀보다 먼저다. 생물학적, 철학적 관점에서 이는 사실이다."
ai2_original_claim = "달걀이 닭보다 먼저다. 진화론적 증거가 이를 뒷받침한다."

# ✅ Memory에 초기 주장 저장
ai1_memory.save_context({"speaker": "AI1", "input": ai1_original_claim}, {"output": ai1_original_claim})
ai2_memory.save_context({"speaker": "AI2", "input": ai2_original_claim}, {"output": ai2_original_claim})

# ✅ 역할 시스템 메시지 (RunnableLambda 사용)
ai1_system_message = RunnableLambda(lambda _: SystemMessage(content="당신은 닭이 먼저라고 주장하는 토론자입니다. 논리를 유지하며 상대방의 반박을 논리적으로 반격하세요."))
ai2_system_message = RunnableLambda(lambda _: SystemMessage(content="당신은 달걀이 먼저라고 주장하는 토론자입니다. 논리를 유지하며 상대방의 반박을 논리적으로 반격하세요."))

# ✅ AI1과 AI2 체인용 프롬프트
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
    template="당신(AI1)의 주장은: {previous} \n상대방(AI2)의 주장: {opponent}\n이에 대해 반드시 반박하며, 상대방 주장의 약점을 논리적으로 지적하세요."
)

ai2_rebuttal_prompt = PromptTemplate(
    input_variables=["previous", "opponent"],
    template="당신(AI2)의 주장은: {previous} \n상대방(AI1)의 주장: {opponent}\n이에 대해 반드시 반박하며, 상대방 주장의 약점을 논리적으로 지적하세요."
)

# ✅ 중간 결과 출력 함수 (RunnableLambda 활용)
def print_response(label, response):
    """토론 진행 과정의 결과를 출력하는 함수"""
    content = response.content if isinstance(response, AIMessage) else response
    print(f"\n=== {label} ===\n{content}")
    return response

print_ai1_claim = RunnableLambda(lambda x: print_response("🟢 AI1 논리 전개", x))
print_ai2_claim = RunnableLambda(lambda x: print_response("🔵 AI2 논리 전개", x))
print_ai1_rebuttal = RunnableLambda(lambda x: print_response("🟢 AI1 반박", x))
print_ai2_rebuttal = RunnableLambda(lambda x: print_response("🔵 AI2 반박", x))

# ✅ AI1과 AI2 체인 생성 (RunnableSequence로 구성)
ai1_claim_chain = RunnableSequence(
    RunnablePassthrough(),
    ai1_system_message,
    ai1_claim_prompt,
    llm_ai1,
    print_ai1_claim
)

ai2_claim_chain = RunnableSequence(
    RunnablePassthrough(),
    ai2_system_message,
    ai2_claim_prompt,
    llm_ai2,
    print_ai2_claim
)

ai1_rebuttal_chain = RunnableSequence(
    RunnablePassthrough(),
    ai1_rebuttal_prompt,
    llm_ai1,
    print_ai1_rebuttal
)

ai2_rebuttal_chain = RunnableSequence(
    RunnablePassthrough(),
    ai2_rebuttal_prompt,
    llm_ai2,
    print_ai2_rebuttal
)

# ✅ Moderator Agent (토론 진행)
def moderate_debate(_):
    print("\n=== 토론 시작 ===")

    ai1_claim = ai1_claim_chain.invoke({"previous": ai1_original_claim})
    ai2_claim = ai2_claim_chain.invoke({"previous": ai2_original_claim})

    ai1_rebuttal = ai1_rebuttal_chain.invoke({"previous": ai1_claim.content, "opponent": ai2_claim.content})
    ai2_rebuttal = ai2_rebuttal_chain.invoke({"previous": ai2_claim.content, "opponent": ai1_claim.content})

    return {
        "ai1_claim": ai1_claim.content,
        "ai2_claim": ai2_claim.content,
        "ai1_rebuttal": ai1_rebuttal.content,
        "ai2_rebuttal": ai2_rebuttal.content,
    }

moderator_chain = RunnableLambda(moderate_debate)

# ✅ Judge Agent (토론 평가)
judge_prompt = PromptTemplate(
    input_variables=["ai1_claim", "ai2_claim", "ai1_rebuttal", "ai2_rebuttal"],
    template=(
        "당신은 AI 토론의 심판입니다.\n"
        "주제: 닭이 먼저인가, 달걀이 먼저인가?\n\n"
        "AI1 주장: {ai1_claim}\n"
        "AI2 주장: {ai2_claim}\n\n"
        "AI1 반박: {ai1_rebuttal}\n"
        "AI2 반박: {ai2_rebuttal}\n\n"
        "어느 주장이 더 논리적으로 타당한지 평가하세요."
    )
)

judge_chain = judge_prompt | llm_judge

# ✅ 토론 진행
moderated_result = moderator_chain.invoke({})
print("\n=== 최종 평가 ===")
debate_result = judge_chain.invoke(moderated_result)
print(debate_result.content)
