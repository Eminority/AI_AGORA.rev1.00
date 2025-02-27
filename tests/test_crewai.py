import os
import asyncio
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from pydantic import Field
from crewai import Agent as BaseAgent
from typing import Tuple

# 전역 로그 및 사용 metrics 저장
conversation_log = []
usage_metrics = {}

# .env 파일에서 환경 변수 로드
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")


###############################################
# (A) Gemini 전용 커스텀 LLM 클래스 (시뮬레이션)
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


def generate(self, prompt: str) -> Tuple[str, int]:
    response = f"[Simulated Gemini 응답: '{prompt}'에 대한 답변]"
    conversation_log.append(f"LLM Generate - Prompt: {prompt}")
    conversation_log.append(f"LLM Generate - Response: {response}")
    token_used = len(prompt) // 4  # 간단한 토큰 사용량 계산
    return response, token_used


    def call(self, prompt: str, **kwargs):
        response, token_used = self.generate(prompt)
        return {"choices": [{"message": {"content": response, "token_used": token_used}}]}
    
    def __call__(self, prompt: str, **kwargs):
        return self.call(prompt, **kwargs)

###############################################
# (B) LoggingAgent 정의 (콜백 및 사용 metrics 포함)
###############################################


class LoggingAgent(BaseAgent):
    allow_delegation: bool = Field(default=False)  # pydantic 필드로 미리 선언
    
    def execute_task(self, *args, **kwargs):
        name = self.model_dump().get("name", "Unknown")
        conversation_log.append(f"[시작] Agent '{name}' 작업 시작.")
        # 프롬프트는 kwargs 또는 기본값 사용
        prompt = kwargs.get("prompt", "기본 프롬프트")
        result = self.llm(prompt)
        token_used = result["choices"][0]["message"].get("token_used", 0)
        usage_metrics[name] = usage_metrics.get(name, 0) + token_used
        conversation_log.append(f"[완료] Agent '{name}' 작업 결과: {result['choices'][0]['message']['content']}")
        if "step_callback" in kwargs and callable(kwargs["step_callback"]):
            kwargs["step_callback"](self, result)
        return result

###############################################
# (C) 에이전트 생성
###############################################
# 0. 관리자 
agnet_sejong = LoggingAgent(
    name = "King Sejong",
    role = "대화 조정자",
    goal = "적절한 사람에게 태스크를 부여해서 목표를 이루도록 하는것",
    backstory= "성군 세종대왕. 적절한 인물을 적절하게 선택",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,

)

# 1. 아이디어 개념 정리 및 명료화
agent_disney = LoggingAgent(
    name="Walt_Disney",
    role="Concept Clarifier",
    goal="아이디어의 핵심 개념과 가치를 명확하게 정리한다.",
    backstory="월트 디즈니: 창의적 스토리텔러, 복잡한 아이디어를 단순하게 전달.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True
)
agent_jobs = LoggingAgent(
    name="Steve_Jobs",
    role="Concept Clarifier",
    goal="아이디어의 핵심을 직관적으로 표현한다.",
    backstory="스티브 잡스: 혁신적인 제품 비전을 단순화하는 능력 보유.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True
)

# 2. 시장 타당성 검토
agent_buffett = LoggingAgent(
    name="Warren_Buffett",
    role="Market Feasibility Reviewer",
    goal="아이디어의 시장성을 분석한다.",
    backstory="워렌 버핏: 오랜 투자 경험으로 시장을 객관적으로 평가.",
    llm=GeminiLLM(gemini_api_key)
)
agent_jackma = LoggingAgent(
    name="Jack_Ma",
    role="Market Feasibility Reviewer",
    goal="아이디어의 시장 기회를 분석한다.",
    backstory="잭 마: 알리바바 그룹 창립자로 혁신적 비즈니스 모델 평가 경험 풍부.",
    llm=GeminiLLM(gemini_api_key)
)

# 3. 기술적 타당성 분석
agent_gates = LoggingAgent(
    name="Bill_Gates",
    role="Technical Feasibility Analyzer",
    goal="아이디어의 기술적 구현 가능성을 분석한다.",
    backstory="빌 게이츠: 기술 혁신과 문제 해결의 대명사.",
    llm=GeminiLLM(gemini_api_key)
)
agent_turing = LoggingAgent(
    name="Alan_Turing",
    role="Technical Feasibility Analyzer",
    goal="아이디어의 기술적 근간을 분석한다.",
    backstory="앨런 튜링: 컴퓨터 과학의 아버지로 혁신적인 기술적 통찰 제공.",
    llm=GeminiLLM(gemini_api_key)
)

# 4. 위험 분석 및 리스크 관리 (미국인 제외)
agent_oppenheimer = LoggingAgent(
    name="Oppenheimer",
    role="Risk Analyst",
    goal="아이디어 실행 시 발생 가능한 위험 요소를 분석한다.",
    backstory="오펜하이머: 핵 개발 책임자로 위험 관리 경험 풍부.",
    llm=GeminiLLM(gemini_api_key)
)
agent_marx = LoggingAgent(
    name="Karl_Marx",
    role="Risk Analyst",
    goal="사회 및 경제 전반의 리스크를 분석한다.",
    backstory="카를 마르크스: 사회 경제 구조와 위험 분석에 대한 깊은 통찰 보유.",
    llm=GeminiLLM(gemini_api_key)
)
agent_bezos = LoggingAgent(
    name="Jeff_Bezos",
    role="Risk Analyst",
    goal="글로벌 시장에서 발생하는 리스크를 분석한다.",
    backstory="제프 베조스: 비즈니스 전략과 위기 대응에 뛰어난 인물.",
    llm=GeminiLLM(gemini_api_key)
)

# 5. 프로토타입 평가 및 사용자 피드백 수집
agent_musk = LoggingAgent(
    name="Elon_Musk",
    role="Prototype Evaluator",
    goal="프로토타입을 평가하고 사용자 피드백을 수집한다.",
    backstory="일론 머스크: 혁신적 제품 개선과 빠른 피드백 반영의 선두 주자.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True
)
agent_cook = LoggingAgent(
    name="Tim_Cook",
    role="Prototype Evaluator",
    goal="사용자 경험을 분석하고 프로토타입을 개선한다.",
    backstory="팀 쿡: 세심한 운영과 사용자 중심 개선에 강점을 가진 리더.",
    llm=GeminiLLM(gemini_api_key)
)

# 6. 더 발전시킬 수 있는 아이디어 제시
agent_edison = LoggingAgent(
    name="Edison",
    role="Idea Improver",
    goal="현재 아이디어를 발전시켜 더욱 혁신적인 방향으로 개선한다.",
    backstory="에디슨: 발명가로서 기존 아이디어를 새로운 형태로 발전시킨 경험 풍부.",
    llm=GeminiLLM(gemini_api_key)
)
agent_einstein = LoggingAgent(
    name="Einstein",
    role="Idea Improver",
    goal="아이디어의 근본 원리를 재검토하여 혁신적인 개선점을 제시한다.",
    backstory="아인슈타인: 창의적 문제 해결과 혁신적 사고의 대명사.",
    llm=GeminiLLM(gemini_api_key)
)

###############################################
# (D) 태스크 정의 (delegation_candidates 추가)
###############################################
def task_callback(task_result):
    print(f"[Task Callback] 작업 '{task_result.task.description}' 완료. 출력: {task_result.output}")

def step_callback(agent, result):
    print(f"[Step Callback] Agent '{agent.model_dump().get('name', 'Unknown')}' 실행 완료. 결과: {result['choices'][0]['message']['content']}")

# 1. 아이디어 개념 정리 및 명료화 (기본: Walt_Disney, 위임 후보: Steve_Jobs)
task1 = Task(
    description="아이디어 개념 정리 및 명료화",
    agent=agent_disney,
    expected_output="아이디어 핵심 개념 정리 결과",
    async_execution=False,
    delegation_candidates=[agent_jobs]
)

# 2. 시장 타당성 검토 (기본: Warren_Buffett, 위임 후보: Jack_Ma)
task2 = Task(
    description="시장 타당성 검토",
    agent=agent_buffett,
    expected_output="시장 분석 및 타당성 보고서",
    async_execution=True,
    delegation_candidates=[agent_jackma]
)

# 3. 기술적 타당성 분석 (기본: Bill_Gates, 위임 후보: Alan_Turing)
task3 = Task(
    description="기술적 타당성 분석",
    agent=agent_gates,
    expected_output="기술 구현 가능성 분석 결과",
    async_execution=False,
    delegation_candidates=[agent_turing]
)

# 4. 위험 분석 및 리스크 관리 (기본: Oppenheimer, 위임 후보: Karl_Marx, Jeff_Bezos)
task4 = Task(
    description="위험 분석 및 리스크 관리",
    agent=agent_oppenheimer,
    expected_output="잠재적 위험 및 리스크 관리 방안",
    async_execution=True,
    delegation_candidates=[agent_marx, agent_bezos]
)

# 5. 프로토타입 평가 및 사용자 피드백 수집 (기본: Elon_Musk, 위임 후보: Tim_Cook)
task5 = Task(
    description="프로토타입 평가 및 사용자 피드백 수집",
    agent=agent_musk,
    expected_output="프로토타입 평가 및 개선 의견",
    async_execution=False,
    delegation_candidates=[agent_cook]
)

# 6. 더 발전시킬 수 있는 아이디어 제시 (기본: Edison, 위임 후보: Einstein)
task6 = Task(
    description="더 발전시킬 수 있는 아이디어 제시",
    agent=agent_edison,
    expected_output="아이디어 개선 및 발전 방향",
    async_execution=True,
    delegation_candidates=[agent_einstein]
)

###############################################
# (E) Crew 구성
###############################################
os.environ["OPENAI_API_KEY"] = gemini_api_key

research_crew = Crew(
    agents=[
        agent_disney, agent_jobs,
        agent_buffett, agent_jackma,
        agent_gates, agent_turing,
        agent_oppenheimer, agent_marx, agent_bezos,
        agent_musk, agent_cook,
        agent_edison, agent_einstein
    ],
    tasks=[task1, task2, task3, task4, task5, task6],
    process= "sequential",  # 전체 프로세스는 순차적 실행 (비동기 태스크는 내부에서 병렬 처리)
    memory=True,
    task_callback=task_callback,
    step_callback=step_callback,
    manager_agent= agnet_sejong,
    verbose=True
)

###############################################
# (F) Crew 실행 (메인 함수)
###############################################
if __name__ == "__main__":
    inputs = {"idea": "crewai를 사용한 멀티 AI-agent 구현"}
    result = research_crew.kickoff(inputs=inputs)
    
    # 결과, 로그, 사용 metrics 파일 저장
    with open("idea_validation_log.txt", "w", encoding="utf-8") as f:
        f.write("=== 중간 대화 로그 ===\n")
        for line in conversation_log:
            f.write(line + "\n")
        f.write("\n=== 사용 Metrics (토큰 사용량) ===\n")
        for agent_name, tokens in usage_metrics.items():
            f.write(f"{agent_name}: {tokens} tokens\n")
        f.write("\n=== 최종 결과 ===\n")
        f.write(str(result) + "\n")
    
    print("실행 완료. 로그, 사용 metrics, 최종 결과가 'idea_validation_log.txt'에 저장되었습니다.")
