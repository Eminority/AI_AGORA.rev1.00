import os
from dotenv import load_dotenv
import logging
import google.generativeai as genai  # Google Gemini API 관련 라이브러리
import litellm  # litellm를 사용하여 LLM 호출 시 provider 정보를 전달합니다.
from crewai import Agent, Task, Crew, Process

# 전역 로그 리스트 (LLM 호출 및 에이전트 실행 로그를 저장)
conversation_log = []

# .env 파일에서 환경 변수 로드
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key is None:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

# Gemini API 설정
genai.configure(api_key=gemini_api_key)

# 로깅 설정: 터미널 출력과 파일 저장
logger = logging.getLogger("crewai")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler("crewai_output.txt", encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


###############################################
# (A) Gemini 전용 커스텀 LLM 클래스
###############################################
class GeminiLLM:
    _is_custom = True  # 커스텀 LLM임을 명시
    def __init__(self, api_key):
        self.api_key = api_key
        self._supported_params = {"temperature": True, "max_tokens": True}
        self.model_name = "gemini/gemini-2.0-flash"

    @property
    def supported_params(self):
        return self._supported_params

    def get_supported_params(self):
        return self._supported_params

    def generate(self, prompt: str) -> str:
        """
        실제 Gemini API 호출 대신, 입력 프롬프트에 대한 시뮬레이션 응답을 생성합니다.
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

    def __call__(self, prompt: str, **kwargs):
        """
        객체를 함수처럼 호출할 수 있도록 __call__ 메서드를 오버라이드합니다.
        """
        return self.call(prompt, **kwargs)


###############################################
# (B) LoggingAgent 정의 (CrewAI Agent 확장)
###############################################
class LoggingAgent(Agent):
    """
    각 Agent가 작업 시작 및 결과, 그리고 발언(LLM 호출 등)을 로그로 남기며,
    터미널, 전역 conversation_log, 그리고 별도 텍스트 파일("agent_utterances.txt")에 저장한다.
    """
    def __init__(self, name, role, goal, backstory, llm, allow_delegation):
        super().__init__(name=name, role=role, goal=goal, backstory=backstory, llm=llm, allow_delegation=allow_delegation)
        # 추가 재할당은 하지 않습니다.
    
    def log(self, message):
        # pydantic 모델의 데이터를 딕셔너리로 가져와 "name" 필드를 사용합니다.
        agent_name = self.dict().get("name", "unknown")
        full_message = f"[{agent_name}] {message}"
        logger.info(full_message)
        conversation_log.append(full_message)
        # 에이전트 발언을 별도의 텍스트 파일에 즉시 저장
        with open("agent_utterances.txt", "a", encoding="utf-8") as f:
            f.write(full_message + "\n")
    
    def run_task(self, task_description):
        self.log(f"Task 시작: {task_description}")
        result = f"Result of '{task_description}' from {self.dict().get('name', 'unknown')}"
        self.log(f"Task 결과: {result}")
        return result


###############################################
# (C) 에이전트 정의
###############################################
# Supervisor Agent: 전체 연구 과정을 기획하고 특화 에이전트에게 작업을 배분
supervisor_agent = LoggingAgent(
    name="King Sejong",
    role="대화 조정자",
    goal="적절한 사람에게 태스크를 부여해서 목표를 이루도록 하는 것",
    backstory="성군 세종대왕. 적절한 인물을 적절하게 선택함. 자신의 의견은 최소한으로 발언함.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)

agent_disney = LoggingAgent(
    name="Walt_Disney",
    role="아이디어 정리 도우미",
    goal="아이디어의 핵심 개념과 가치를 명확하게 정리한다.",
    backstory="월트 디즈니: 창의적 스토리텔러, 복잡한 아이디어를 단순하게 전달.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)

agent_buffett = LoggingAgent(
    name="Warren_Buffett",
    role="시장 분석가",
    goal="아이디어의 시장성을 분석하여 자신의 견해를 간단히 발언.",
    backstory="워렌 버핏: 오랜 투자 경험으로 시장을 객관적으로 평가.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)

agent_gates = LoggingAgent(
    name="Bill_Gates",
    role="기술 타당성 분석가",
    goal="아이디어의 기술적 구현 가능성을 분석하여 자신의 견해를 간단하게 발언함.",
    backstory="빌 게이츠: 기술 혁신과 문제 해결의 대명사.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)

agent_oppenheimer = LoggingAgent(
    name="Oppenheimer",
    role="리스크 분석가",
    goal="아이디어 실행 시 발생 가능한 위험 요소를 분석하여 자신의 견해를 간단하게 발언함.",
    backstory="오펜하이머: 핵 개발 책임자로 위험 관리 경험 풍부.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)

agent_musk = LoggingAgent(
    name="Elon_Musk",
    role="프로토타입 평가자, 사용자 피드백 수집가",
    goal="프로토타입을 평가하고 사용자 피드백을 수집하여 간단히 보고함.",
    backstory="일론 머스크: 혁신적 제품 개선과 빠른 피드백 반영의 선두 주자.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)

agent_edison = LoggingAgent(
    name="Edison",
    role="아이디어 개선자",
    goal="현재 아이디어를 발전시켜 더욱 혁신적인 방향의 개선안을 간단히 정리하여 발언.",
    backstory="에디슨: 발명가로서 기존 아이디어를 새로운 형태로 발전시킨 경험 풍부.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)

###############################################
# (D) 작업(Task) 정의 (각 태스크에 입력값 {research_goal} 적용)
###############################################
supervisor_task = Task(
    description=
    """
    연구 목표 '{research_goal}'와 각 agent의 발언을 받아들인 후. 다음의 task에 적절히 분배. 
    모든 task가 한바퀴 돌았다면 작업을 종료함.
    """,
    agent=supervisor_agent,
    expected_output="각 에이전트의 결과물을 종합한 보고서"
)

classifier_task = Task(
    description="연구 목표 '{research_goal}'에 대한 아이디어 개념을 정리한다.",
    agent=agent_disney,
    expected_output="명료화된 아이디어"
)

market_task = Task(
    description="아이디어 '{research_goal}'의 시장 분석을 정리한다.",
    agent=agent_buffett,
    expected_output="개선사항 및 고려사항"
)

technical_task = Task(
    description="아이디어 '{research_goal}'의 기술적 타당성을 정리한다.",
    agent=agent_gates,
    expected_output="사용해야할 기술과 아이디어의 불가능한 부분을 정리한 보고서."
)

risk_task = Task(
    description="아이디어 '{research_goal}'의 위험성과 위기 분석을 실시한다.",
    agent=agent_oppenheimer,
    expected_output="아이디어의 위험성에 대한 간단한 보고서."
)

user_task = Task(
    description="아이디어 '{research_goal}'를 사용한 가상 시나리오에 따른 사용자 피드백을 실시한다.",
    agent=agent_musk,
    expected_output="프로토타입 사용 보고서 및 사용자 피드백"
)

improve_task = Task(
    description="아이디어 '{research_goal}'의 개선 사항을 고려하여 아이디어를 발전시킨다.",
    agent=agent_edison,
    expected_output="아이디어 개선안 보고서."
)

###############################################
# (E) Crew 구성 (manager_agent는 agents 리스트에서 제외)
###############################################
research_crew = Crew(
    agents=[
        agent_buffett,
        agent_disney,
        agent_edison,
        agent_gates,
        agent_oppenheimer,
        agent_musk
    ],
    tasks=[
        supervisor_task,
        classifier_task,
        market_task,
        technical_task,
        risk_task,
        user_task,
        improve_task
    ],
    process="sequential",
    manager_agent=supervisor_agent,     # Supervisor Agent가 매니저로 지정됨
    verbose=True
)

###############################################
# (F) 실행 예시 (main 함수)
###############################################
if __name__ == "__main__":
    input_data  = {"research_goal" : """CrewAI를 사용한 Multi AI Agent 시스템 구현 아이디어
                   1. 유명인들의 행동과 발언, 검색 가능한 데이터를 모아 LLM에게 인격을 형성.
                   2. 각 LLM별로 해야할 TASK를 분배.
                   3. LangChain으로 Task의 순서를 최적화.
                   4. 유명인이 내가 하는 말을 듣고 대답해주는 Multi ai agent 시스템 구현.
                   """}
    supervisor_agent.log("연구 시작")
    
    # 태스크 실행 결과 수집
    results = research_crew.kickoff(input_data)
    
    # 각 에이전트의 결과를 종합하여 최종 보고서 작성
    final_report = "\n".join([f"{agent_name}: {result}" for agent_name, result in results.items()])
    supervisor_agent.log("최종 보고서 작성 완료")
    supervisor_agent.log("\n" + final_report)
    
    # 최종 보고서를 메모장(텍스트 파일)에 저장
    with open("co_scientist_log.txt", "w", encoding="utf-8") as f:
        f.write("=== AI Co-Scientist Process Log ===\n\n")
        for line in conversation_log:
            f.write(line + "\n")
        f.write("\n=== Final Result ===\n")
        f.write(final_report + "\n")
    
    print("\n=== Done! ===")
    print("전체 실행 로그와 최종 결과가 'co_scientist_log.txt'에 저장되었습니다.")
