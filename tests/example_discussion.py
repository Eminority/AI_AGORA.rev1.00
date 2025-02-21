# example_discussion.py

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew

# 전역 대화 기록 리스트 (LLM 호출 및 에이전트 실행 로그를 저장)
conversation_log = []

# .env 파일에서 환경 변수 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

# Gemini API 호출을 시뮬레이션하기 위한 래퍼 클래스 구현
class GeminiLLM:
    def __init__(self, api_key):
        self.api_key = api_key
        self._supported_params = {"temperature": True, "max_tokens": True}
        # litellm 라이브러리가 모델명을 "provider/model" 형식으로 기대하므로 올바른 형식으로 지정합니다.
        self.model_name = "gemini/gemini-2.0-flash"
        
    @property
    def supported_params(self):
        return self._supported_params

    def get_supported_params(self):
        return self._supported_params

    def generate(self, prompt: str) -> str:
        """
        실제 Gemini API 호출 대신, 입력 프롬프트에 대한 시뮬레이션 응답을 생성합니다.
        LLM 호출 시 프롬프트와 응답을 conversation_log에 기록합니다.
        """
        response = f"[Simulated Gemini 응답: '{prompt}'에 대한 답변]"
        conversation_log.append(f"LLM Generate - Prompt: {prompt}")
        conversation_log.append(f"LLM Generate - Response: {response}")
        return response

    def call(self, prompt: str, **kwargs):
        """
        CrewAI 내부에서 LLM 호출 시 사용하는 인터페이스.
        OpenAI API와 유사한 딕셔너리 구조로 응답을 반환합니다.
        """
        response = self.generate(prompt)
        return {"choices": [{"message": {"content": response}}]}

# LoggingAgent: Agent를 상속하여 작업 실행 전후의 로그를 남깁니다.
class LoggingAgent(Agent):
    def execute_task(self, *args, **kwargs):
        # pydantic 모델에서 에이전트 이름은 model_dump()로 접근
        name = self.model_dump().get("name", "Unknown")
        conversation_log.append(f"--- Agent {name} 시작 ---")
        result = super().execute_task(*args, **kwargs)
        conversation_log.append(f"--- Agent {name} 결과 ---")
        conversation_log.append(str(result))
        return result

# Gemini 모델 인스턴스 생성 (시뮬레이션 모드)
gemini_llm = GeminiLLM(GEMINI_API_KEY)

# LoggingAgent를 사용하여 각 에이전트를 생성 (필수 필드: name, role, goal, backstory, llm)
agent_pro = LoggingAgent(
    name="개",
    role="찬성",
    goal="산책의 중요성과 필요성을 주장.",
    backstory="말을 할 수 있게 된 개입니다. 활동적이고 밖에 나가는 것을 좋아합니다.",
    llm=gemini_llm
)

agent_con = LoggingAgent(
    name="고양이",
    role="반대",
    goal="산책보다는 집에 머물러 있어야 함을 주장합니다.",
    backstory="말을 할 수 있게 된 고양이입니다. 밖에 나가는 것보다 자신의 영역에 머무는 것을 선호합니다.",
    llm=gemini_llm
)

agent_moderator = LoggingAgent(
    name="판결",
    role="조정자",
    goal="토론 내용을 종합하여 최종 결정을 내린다.",
    backstory="다양한 토론 경험과 중립적인 판단력을 가진 조정자입니다. 단호하게 한 쪽 편의 의견을 채용합니다.",
    llm=gemini_llm
)

# Task 생성 – 토론 작업 시 description, agent, expected_output 필드를 반드시 지정합니다.
discussion_task = Task(
    description="산책의 필요성과 중요성에 대해 찬반 토론을 진행한다.",
    agent=agent_moderator,  # 찬성 측 에이전트가 첫 발언자로 참여
    expected_output="토론 진행 과정"
)

# Crew 생성 – process는 'sequential' (에이전트들이 순차적으로 토론)
discussion_crew = Crew(
    agents=[agent_pro, agent_con, agent_moderator],
    tasks=[discussion_task],
    process="sequential"
)

if __name__ == "__main__":
    # 토론 프로세스 실행 및 최종 결론 도출
    final_decision = discussion_crew.kickoff()
    
    # 최종 의사 결정 결과와 전체 대화 기록을 "discussion_log.txt" 파일에 저장합니다.
    with open("discussion_log.txt", "w", encoding="utf-8") as f:
        f.write("=== 토론 과정 ===\n")
        f.write(str(final_decision) + "\n\n")
        f.write("=== 토론 중간 대화 기록 ===\n")
        for line in conversation_log:
            f.write(line + "\n")
