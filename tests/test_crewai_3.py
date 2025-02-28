import os
from dotenv import load_dotenv
import logging
import google.generativeai as genai  # Gemini API 관련 라이브러리
from crewai import Agent, Task, Crew, Process
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from typing import Any
from pydantic import PrivateAttr

# 환경 변수 및 로깅 설정
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key is None:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

genai.configure(api_key=gemini_api_key)

logger = logging.getLogger("crewai")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("crewai_output.txt", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

###############################################
# (A) Gemini 전용 LLM 클래스 (실제 API 호출 로깅 추가)
###############################################
class GeminiLLM:
    _is_custom = True
    def __init__(self, api_key):
        self.api_key = api_key
        self._supported_params = {"temperature": True, "max_tokens": True}
        self.model_name = "gemini/gemini-2.0-flash"
    @property
    def supported_params(self):
        return self._supported_params
    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            logger.debug("Empty prompt received in generate(), returning default response.")
            return "[Default response]"
        # 실제 API 호출 또는 시뮬레이션 응답 (여기서는 실제 호출 시 로깅을 강화)
        response = f"[Actual Gemini 응답: '{prompt}'에 대한 답변]"
        logger.debug(f"GeminiLLM.generate() - Prompt: {prompt} / Response: {response}")
        return response
    def call(self, prompt: str, **kwargs):
        try:
            response = self.generate(prompt)
            if not response or response.strip() == "":
                raise ValueError("Invalid response from LLM call - None or empty.")
            return {"choices": [{"message": {"content": response}}]}
        except Exception as e:
            logger.error(f"LLM call error for prompt '{prompt}': {e}")
            return {"choices": [{"message": {"content": "[Default response]"}}]}
    def __call__(self, prompt: str, **kwargs):
        return self.call(prompt, **kwargs)

###############################################
# (B) 기본 Agent 구현 (LoggingAgent 제거)
###############################################
class SimpleAgent(Agent):
    _internal_log: list = PrivateAttr(default_factory=list)
    _name: str = PrivateAttr()

    def __init__(self, name, role, goal, backstory, llm, allow_delegation):
        super().__init__(name=name, role=role, goal=goal, backstory=backstory, llm=llm, allow_delegation=allow_delegation)
        object.__setattr__(self, '_name', name)

    @property
    def name(self):
        return self._name

    def run_task(self, task_description):
        self._internal_log.append(f"Task: {task_description}")
        result = f"Short result from {self._name}"
        self._internal_log.append(f"Result: {result}")
        return result
###############################################
# (C) 에이전트 인스턴스 생성 (supervisor, buffett, gates, edison)
###############################################
gemini_llm = GeminiLLM(gemini_api_key)

supervisor_agent = SimpleAgent(
    name="King Sejong",
    role="대화 조정자",
    goal="각 agent가 최소 1회 발언하고, 두 번 이상 발언한 agent가 3명 이상이면 전체 작업 종료",
    backstory="발언은 최대한 간결하게.",
    llm=gemini_llm,
    allow_delegation=True,
)

agent_buffett = SimpleAgent(
    name="Warren_Buffett",
    role="시장 분석",
    goal="간단 시장 분석 결과 제시",
    backstory="최소 발언.",
    llm=gemini_llm,
    allow_delegation=True,
)

agent_gates = SimpleAgent(
    name="Bill_Gates",
    role="기술 분석",
    goal="짧은 기술 분석 결과 제시",
    backstory="간단 명료하게.",
    llm=gemini_llm,
    allow_delegation=True,
)

agent_edison = SimpleAgent(
    name="Edison",
    role="아이디어 개선",
    goal="간단 개선안 제시",
    backstory="최소 발언.",
    llm=gemini_llm,
    allow_delegation=True,
)

###############################################
# (D) Task 정의 (원본 템플릿 보존 및 동적 변수 주입)
###############################################
research_goal = """CrewAI를 사용한 Multi AI Agent 시스템 구현 아이디어
1. 데이터 수집 최소화.
2. TASK 간소화.
3. 전체 결과 간단 요약.
"""

def format_task_description(template: str, research_goal: str) -> str:
    return template.format(research_goal=research_goal)

supervisor_task = Task(
    description=format_task_description(" {research_goal}을 보고 연구 목표와 agent 발언을 받아 간단히 종합 보고서를 작성한다.", research_goal),
    agent=supervisor_agent,
    expected_output="종합 보고서"
)
market_task = Task(
    description=format_task_description(" {research_goal}을 보고 간단 시장 분석 제시", research_goal),
    agent=agent_buffett,
    expected_output="시장 분석 결과"
)
technical_task = Task(
    description=format_task_description(" {research_goal}을 보고 간단 기술 분석 제시", research_goal),
    agent=agent_gates,
    expected_output="기술 분석 결과"
)
improvement_task = Task(
    description=format_task_description(" {research_goal}을 보고 간단 개선안 제시", research_goal),
    agent=agent_edison,
    expected_output="개선안 결과"
)

###############################################
# (E) Crew 구성 (4개 에이전트, 4개 Task 사용)
###############################################
research_crew = Crew(
    agents=[agent_buffett, agent_gates, agent_edison, supervisor_agent],
    tasks=[market_task, technical_task, improvement_task, supervisor_task],
    process=Process.sequential,
    verbose=False
)

###############################################
# (F) LangGraph 기반 상태 관리 및 CrewAI 실행
###############################################
class CrewState(BaseModel):
    research_goal: str
    results: dict = {}

initial_state = CrewState(
    research_goal=research_goal,
    results={}
)

graph = StateGraph(state_schema=CrewState)
graph.state = initial_state

def execute_crewai(state: CrewState) -> CrewState:
    input_data = {"research_goal": state.research_goal}
    logger.debug(f"Input data for CrewAI: {input_data}")
    try:
        results = research_crew.kickoff(input_data)
    except Exception as e:
        logger.error(f"그래프 실행 중 오류 발생: {e}")
        results = {}
    state.results = results
    if supervisor_agent.name in results:
        state.results["final_note"] = "최종 요약 태스크 실행됨. 작업 종료."
    return state

graph.add_node("execute_crewai", execute_crewai)
graph.add_edge(START, "execute_crewai")
graph.add_edge("execute_crewai", END)

compiled = graph.compile()
try:
    final_state = compiled.invoke(initial_state.dict())
except Exception as e:
    logger.error(f"그래프 실행 중 오류 발생: {e}")
    final_state = initial_state
finally:
    try:
        final_state_dict = final_state.dict() if hasattr(final_state, "dict") else final_state
    except Exception as e:
        logger.error(f"최종 상태 dict 변환 오류: {e}")
        final_state_dict = {}
    results = final_state_dict.get("results", {})
    # 적극적으로 built-in 결과 접근
    task_output = results.get(supervisor_agent.name, "No Task Output")
    crew_output = results.get("final_note", "No Crew Output")
    final_report = "\n".join([f"{agent_name}: {output}" for agent_name, output in results.items()])
    try:
        with open("multi_agent_log.txt", "w", encoding="utf-8") as f:
            f.write("=== AI Co-Scientist Process Log ===\n\n")
            # 각 에이전트의 내부 로그 기록
            for agent in research_crew.agents:
                for line in agent.internal_log:
                    f.write(f"[{agent.name}] {line}\n")
            f.write("\n=== Final Report ===\n")
            f.write(final_report + "\n")
            f.write("\n=== Task Output ===\n")
            f.write(str(task_output) + "\n")
            f.write("\n=== Crew Output ===\n")
            f.write(str(crew_output) + "\n")
    except Exception as e:
        logger.error(f"파일 저장 중 오류 발생: {e}")
    print("\n=== Done! ===")
    print("전체 실행 로그와 최종 결과가 'multi_agent_log.txt'에 저장되었습니다.")
