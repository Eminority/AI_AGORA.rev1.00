import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool

# 환경 변수 로드
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
serp_api_key = os.getenv("SERP_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")
if not serp_api_key:
    raise ValueError("SERP_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

# SerperDevTool 초기화
search_tool = SerperDevTool(api_key=serp_api_key)

# Gemini LLM 클래스 정의
class GeminiLLM:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model_name = "gemini/gemini-2.0-flash"

    def generate(self, prompt: str) -> str:
        response = f"[Gemini 응답: '{prompt}'에 대한 답변]"
        return response

# 에이전트 정의
class ResearchAgent(Agent):
    def execute_task(self, *args, **kwargs):
        query = kwargs.get("query", "CrewAI의 기능")
        search_results = search_tool.run(search_query=query)
        return search_results

class WriterAgent(Agent):
    def execute_task(self, *args, **kwargs):
        research_info = kwargs.get("research_info", "")
        prompt = f"다음 정보를 기반으로 블로그 글을 작성하세요:\n{research_info}"
        response = self.llm.generate(prompt)
        return response

class ProofreaderAgent(Agent):
    def execute_task(self, *args, **kwargs):
        draft_content = kwargs.get("draft_content", "")
        prompt = f"다음 글을 검토하고 개선하세요:\n{draft_content}"
        response = self.llm.generate(prompt)
        return response

# Gemini LLM 인스턴스 생성
gemini_llm = GeminiLLM(gemini_api_key)

# 에이전트 인스턴스 생성
research_agent = ResearchAgent(
    name="Research_Agent",
    role="연구원",
    goal="CrewAI의 다양한 기능을 조사한다.",
    backstory="AI 시스템 전문가로서, 최신 기술 동향을 파악하는 데 능숙하다.",
    llm=None,  # 검색 도구만 사용
    tools=[search_tool]
)

writer_agent = WriterAgent(
    name="Writer_Agent",
    role="작가",
    goal="수집된 정보를 기반으로 블로그 글을 작성한다.",
    backstory="경험 많은 기술 블로거로서, 복잡한 개념을 쉽게 전달한다.",
    llm=gemini_llm
)

proofreader_agent = ProofreaderAgent(
    name="Proofreader_Agent",
    role="검토자",
    goal="작성된 글을 검토하고 개선한다.",
    backstory="문법과 스타일에 능통한 편집자.",
    llm=gemini_llm
)

# 작업 정의
research_task = Task(
    description="'{query}'에 대한 최신 정보를 조사하여 상세한 설명을 제공한다.",
    agent=research_agent,
    expected_output="사용자가 지정한 주제에 대한 최신 정보"
)

writing_task = Task(
    description="수집된 정보를 기반으로 블로그 글 초안을 작성한다.",
    agent=writer_agent,
    expected_output="CrewAI의 기능을 소개하는 블로그 글 초안"
)

proofreading_task = Task(
    description="작성된 블로그 글을 검토하고 개선한다.",
    agent=proofreader_agent,
    expected_output="최종 수정된 블로그 글"
)

# Crew 구성
blog_crew = Crew(
    agents=[research_agent, writer_agent, proofreader_agent],
    tasks=[research_task, writing_task, proofreading_task],
    process="sequential",  # 순차적으로 작업 수행
    verbose=True
)

# 실행
if __name__ == "__main__":
    topic = input("윤석렬 대통령 탄핵")  # 사용자가 직접 입력 가능
    if not topic.strip():
        topic = "CrewAI의 기능"  # 기본값

    result = blog_crew.kickoff(inputs={"query": topic})
    
    # 결과를 파일에 저장
    with open("blog_output.txt", "w", encoding="utf-8") as f:
        f.write("=== CrewAI 블로그 생성 결과 ===\n\n")
        f.write(f"주제: {topic}\n\n")
        f.write("생성된 콘텐츠:\n")
        f.write(str(result))
    
    print("최종 결과가 'blog_output.txt' 파일에 저장되었습니다.")
