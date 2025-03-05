import os
import json
import time
import re
from datetime import datetime

from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.exceptions import OutputParserException
from langchain.schema import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory

from .progress import Progress

class DebateMemoryWrapper:
    """
    DebateMemoryWrapper는 ConversationBufferMemory를 기반으로 대화 히스토리를 저장하며,
    스피커별 필터링, 라운드 관리 및 포맷팅된 히스토리 출력 기능을 제공합니다.
    """
    def __init__(self):
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.custom_history = []  # 각 메시지의 {'round', 'speaker', 'message'}를 저장
        self.current_round = 1

    def save_message(self, speaker: str, message: str, round_number: int = None):
        if round_number is None:
            round_number = self.current_round
        entry = {"timestamp": datetime.now(), "round": round_number, "speaker": speaker, "message": message}
        self.custom_history.append(entry)
        formatted = f"[Round {round_number}] {speaker}: {message}"
        sys_msg = SystemMessage(content=f"{speaker} 역할")
        human_msg = HumanMessage(content=formatted)
        self.memory.chat_memory.add_message(sys_msg)
        self.memory.chat_memory.add_message(human_msg)

    def load_all(self):
        return self.custom_history

    def load_by_speaker(self, speaker: str):
        return [msg for msg in self.custom_history if msg["speaker"].lower() == speaker.lower()]

    def increment_round(self):
        self.current_round += 1

    def format_history(self):
        return "\n".join([f"[Round {msg['round']}] {msg['speaker']}: {msg['message']}" for msg in self.custom_history])


class Debate_3(Progress):
    """
    Debate 클래스는 토론 진행 로직을 관리합니다.

    외부에서 주입되는 에이전트:
      - participant["pos"]: 찬성측 토론 에이전트
      - participant["neg"]: 반대측 토론 에이전트
      - participant["judge"]: 최종 판결을 내리는 토론 심판 에이전트
      - participant["judge_1"]: 논리 평가를 담당하는 심판 에이전트
      - participant["judge_2"]: 반론 평가를 담당하는 심판 에이전트
      - participant["judge_3"]: 설득력 평가를 담당하는 심판 에이전트
      - participant["progress_agent"]: 토론 진행 안내 메시지 생성 에이전트
      - participant["next_speaker_agent"]: 다음 발언자 결정 에이전트

    각 에이전트는 ai_instance라는 속성을 가지며, generate_text(user_prompt, max_tokens, temperature)를 제공해야 합니다.
    Progress의 progress()는 dict를, evaluate()는 최종 평가 결과(dict)를 반환하며,
    data JSON에는 debate_log와 status["step"]이 업데이트되고, topic은 data["topic"]에서 가져옵니다.
    """
    def __init__(self, participant: dict, generate_text_config: dict, data: dict = None):
        super().__init__(participant=participant,
                         data=data,
                         generate_text_config=generate_text_config)

        if not data:
            self.data = {
                "type": "debate_3",
                "participants": {position : {"id"   : data.id,
                                 "name" : data.name,
                                  "img" : data.img,
                                  "ai"  : data.ai_instance.model_name,
                                  "object_attribute": data.object_attribute}
                                  for position, data in participant.items()},
                "topic": None,
                "status": {
                    "type": "in_progress",  # "in_progress" 또는 "end" 등
                    "step": 0     
                },
                "debate_log": [],
                "score" : {
                    "logicality_pos": 0,
                    "logicality_neg": 0,
                    "rebuttal_pos": 0,
                    "rebuttal_neg": 0,
                    "persuasion_pos": 0,
                    "persuasion_neg": 0,
                    "match_pos": 0,
                    "match_neg": 0
                },
                "result": None
            }
        else:
            self.data = data

        self.topic = self.data.get("topic", "")

        response_schemas = [
            ResponseSchema(name="speaker", description="응답한 화자 (pos, neg, judge 등)"),
            ResponseSchema(name="message", description="생성된 메시지 내용")
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

         # judge_1 전용: 논리 평가 파서
        self.judge_logical_parser = StructuredOutputParser.from_response_schemas([
            ResponseSchema(name="logicality_pos", description="찬성측 논리성 평가 점수"),
            ResponseSchema(name="logicality_neg", description="반대측 논리성 평가 점수"),
            # ResponseSchema(name="message", description="논리 평가 메시지")
        ])

        # judge_2 전용: 반론 평가 파서
        self.judge_rebuttal_parser = StructuredOutputParser.from_response_schemas([
            ResponseSchema(name="rebuttal_pos", description="찬성측 반론 평가 점수"),
            ResponseSchema(name="rebuttal_neg", description="반대측 반론 평가 점수"),
            # ResponseSchema(name="message", description="반론 평가 메시지")
        ])

        # judge_3 전용: 설득력 평가 파서
        self.judge_persuasion_parser = StructuredOutputParser.from_response_schemas([
            ResponseSchema(name="persuasion_pos", description="찬성측 설득력 평가 점수"),
            ResponseSchema(name="persuasion_neg", description="반대측 설득력 평가 점수"),
            # ResponseSchema(name="message", description="설득력 평가 메시지")
        ])
        
        self.next_speaker_candidate_prompt = PromptTemplate(
            input_variables=["history", "candidates"],
            template="""
            지금까지의 토론 내용:
            {history}

            다음 발언자로 적합한 후보는 다음과 같습니다: {candidates}.
            토론 상황을 고려하여, 가장 적합한 발언자를 하나 선택하고, JSON 형식으로 반환하세요:
            ```json
            {{
                "speaker": "<선택한 후보>",
                "message": "다음 발언자로 <선택한 후보>가 적합합니다."
            }}
            ```
            """
        )

        self.claim_prompt = PromptTemplate(
            input_variables=["topic", "position", "persona"],
            template="""
            [SYSTEM: 당신은 {topic} 주제에 대한 토론 참여하고 있습니다. 당신의 역할은 이 주장에 {position} 입장에서 논증하는 것입니다.]
            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 주제에 대한 **{position}의 입장을 명확하게 제시**하세요.  
            - {position}의 이유를 뒷받침할 **세 가지 이상의 강력한 논거**를 제시하세요.  
            - **논리적 근거, 현실 사례, 데이터** 등을 활용하여 주장을 강화하세요.  
            - 주제에 대한 일반적인 설명은 피하고, 오직 {position} 입장을 옹호하는 데 집중하세요.  

            ---

            ### **응답 형식:**  

            1. **주요 논거 #1**  
            - 설명  
            - 근거 또는 예시  

            2. **주요 논거 #2**  
            - 설명  
            - 근거 또는 예시  

            3. **주요 논거 #3**  
            - 설명  
            - 근거 또는 예시  

            간결하면서도 설득력 있게 작성하세요. 적용 가능한 경우, 사실적 근거를 제공하세요.
            
            당신의 주장에서 독특한 특징을 강조하세요. {persona}의 관점에서 생각해 보세요.

            반드시 JSON 형식으로 응답하세요:
            ```json
            {{
                "speaker": "{position}",
                "message": "..."
            }}
            ```
            """
        )

        self.argument_prompt = PromptTemplate(
            input_variables=["topic", "position", "opponent_statements", "last_opp_statements", "persona"],
            template="""  
            [SYSTEM: 당신은 {topic} 주제에 대한 토론에 참여하고 있습니다. 역할은 {position}의 입장에서 상대의 주장을 반박하는 것입니다.]
            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 상대 측의 전체 발언 내역: {opponent_statements}  
            - 특히, **가장 최근의 발언 {last_opp_statements}**을 참고하여 이에 대한 **논리적인 반박**을 제시하세요.  
            - 상대 측의 **핵심 논점을 직접적으로 반박**하세요.  
            - **근거, 논리적 추론, 현실 사례**를 활용하여 상대 주장을 논파하세요.  
            - 새로운 {position} 측 논거를 도입하지 말고, 오직 상대방의 주장을 반박하는 데 집중하세요.  

            ---  

            ### **응답 형식:**  

            "상대 측의 주장을 면밀히 검토해 보았지만, 다음과 같은 이유로 반박하고자 합니다.  

            1. **첫 번째 반박:**  
            - {last_opp_statements} 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            2. **두 번째 반박:**  
            - {last_opp_statements} 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            3. **세 번째 반박:**  
            - {last_opp_statements} 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            이러한 이유로 {last_opp_statements}은 그리 강력하지 않습니다."  

            **토론 주제:** {topic}  
            **전체 상대 발언:** {opponent_statements}  
            **이전 상대 발언:** {last_opp_statements}

            당신의 주장에서 독특한 특징을 강조하세요. {persona}의 관점에서 생각해 보세요.

            반드시 JSON 형식으로 응답하세요:
            ```json
            {{"speaker": "{position}", "message": "..."}}
            ```  
            """
)

        self.judge_prompt = PromptTemplate(
            input_variables=["topic", "pos_statements", "neg_statements"],
            template="""
            [SYSTEM: 당신은 토론 심판입니다. 역할은 최종 판결을 내리는 것입니다.]
            주제: "{topic}"
            아래는 찬성측과 반대측의 발언 내역입니다.
            
            **찬성측 (Pos):**
            {pos_statements}
            
            **반대측 (Neg):**
            {neg_statements}
            
            
            이제 어느 쪽이 더 설득력 있는지, 그리고 그 이유는 무엇인지 상세하게 서술해 주세요.
            반드시 JSON 형식으로 응답하세요:
            ```json
            {{
               "speaker": "judge",
               "message": "최종 판결: [Pos/Neg]가 더 설득력이 있습니다. 이유: ..."
            }}
            ```
            """
        )

        # 추가된 심판 프롬프트: 논리 평가 (judge_1)
        self.judge_logical_prompt = PromptTemplate(
            input_variables=["topic", "pos_statements", "neg_statements"],
            template="""
            [SYSTEM: 당신은 논리 분석 전문가입니다. 아래의 찬성측과 반대측 발언을 상호 비교하여 **논리적 타당성을 100점 척도로 평가**하는 것이 당신의 역할입니다.]
            
            ### **전문가로서의 역할:**  
            - 당신은 논리적 일관성, 논증 구조, 논거의 강도를 평가하는 데 뛰어난 분석가입니다.  
            - **편견 없이, 논리적 근거만을 기준으로 평가**합니다.  
            - 체계적인 접근 방식을 통해 논리적 강점과 약점을 식별합니다.  

            ### **평가 기준:**  
            - 논증이 **일관되고 논리적으로 구조화**되어 있는가?  
            - **논리적 오류**(흑백논리, 순환논법, 논점 일탈 등)를 피하고 있는가?  
            - **충분한 근거를 제공**하며, 논리적 약점이 최소화되어 있는가?  

            ### **작업 지침:**  
            1. 각 글을 분석하고 **논리적으로 강한 부분**을 식별하세요.  
            2. **논리적 오류나 약점**이 있다면 구체적으로 지적하세요.  
            3. 분석을 **명확하고 간결하게 요약**하세요.  
            4. 최종적으로 **점수를 포함한 평가 결과**를 제공하세요.  

            주제: "{topic}"
            **찬성측 (Pos):**
            {pos_statements}
            **반대측 (Neg):**
            {neg_statements}

            각 측의 논리적 강점을 100점 만점으로 평가하여, 아래 JSON 형식으로 응답하세요:
            ```json
            {{
                "logicality_pos": <점수>,
                "logicality_neg": <점수>,
            }}
            ```"""
        )

        # 추가된 심판 프롬프트: 반론 평가 (judge_2)
        self.judge_rebuttal_prompt = PromptTemplate(
            input_variables=["topic", "pos_rebuttal", "neg_rebuttal"],
            template="""
            [SYSTEM: 당신은 반론 분석 전문가입니다. 아래의 찬성측과 반대측 반론을 상호 비교하여 **반박의 강도를 100점 척도로 평가**하는 것이 당신의 역할입니다.]
            
            ### **전문가로서의 역할:**  
            - 당신은 **반박 논거의 효과성**과 **논리적 반박의 강도**를 평가하는 데 전문성을 갖추고 있습니다.  
            - **객관적인 논리적 엄밀성을 바탕으로 공정하게 평가**합니다.  
            - 반박의 강점과 약점을 체계적으로 분석합니다.  

            ### **평가 기준:**  
            - 반박이 상대의 주장을 **직접적으로 반박하며 논파하는가?**  
            - **타당한 논리, 일관된 사고, 강력한 근거**를 활용하고 있는가?  
            - **허수아비 논법, 논점 일탈, 논리적 왜곡** 등의 오류를 피하고 있는가?  
            - 반박이 **명확하고 설득력 있게 구성**되어 있는가?  

            ### **작업 지침:**  
            1. 각 반박문의 **강점과 효과적인 논리적 반박 요소**를 분석하세요.  
            2. **논리적 약점이나 오류**가 있다면 명확히 지적하세요.  
            3. 반박의 **전반적인 효과성과 상대 주장을 얼마나 효과적으로 반박했는지** 요약하세요.  
            4. 최종적으로 **100점 척도의 반박 강도 점수를 포함한 평가**를 제공하세요.  

            주제: "{topic}"
            **찬성측 반론:**
            {pos_rebuttal}
            **반대측 반론:**
            {neg_rebuttal}

            각 측의 반론 효과성을 100점 만점으로 평가하여, 아래 JSON 형식으로 응답하세요:
            ```json
            {{
                "rebuttal_pos": <점수>,
                "rebuttal_neg": <점수>,
            }}
            ```"""
        )

        # 추가된 심판 프롬프트: 설득력 평가 (judge_3)
        self.judge_persuasion_prompt = PromptTemplate(
            input_variables=["topic", "pos_statements", "neg_statements"],
            template="""
            [SYSTEM: 당신은 설득력 평가 전문가입니다. 아래의 찬성측과 반대측 발언을 비교하여 **설득력을 100점 척도로 평가**하는 것이 당신의 역할입니다.]
            
            ### **전문가로서의 역할:**  
            - 당신은 **논증의 설득력**을 평가하는 데 전문성을 갖추고 있습니다.  
            - **논리적 타당성과 수사적(설득적) 효과**를 모두 고려하여 분석합니다.  
            - **체계적인 분석을 바탕으로 객관적으로 평가**하며, 편향되지 않은 결론을 도출합니다.  

            ### **평가 기준:**  
            - **명확성 & 일관성**: 주장이 명확하고 구조적으로 잘 정리되어 있는가?  
            - **논리적 타당성**: 논증이 논리적으로 타당하며 오류가 없는가?  
            - **근거 활용**: 데이터, 사례, 신뢰할 만한 출처를 효과적으로 활용하는가?  
            - **수사적 & 감성적 설득력**: 설득 전략을 효과적으로 활용하는가?  
            - **반론 대응력**: 예상되는 반박을 미리 고려하고 효과적으로 대응하는가?  

            ### **작업 지침:**  
            1. 각 글의 **설득력 있는 요소**를 분석하고 강조하세요.  
            2. **설득력의 약점 또는 부족한 부분**을 지적하세요.  
            3. 글이 **청중을 얼마나 효과적으로 설득하는지** 요약하세요.  
            4. 최종적으로 **100점 척도의 설득력 점수를 포함한 평가**를 제공하세요.  
            
            주제: "{topic}"
            **찬성측 (Pos):**
            {pos_statements}
            **반대측 (Neg):**
            {neg_statements}

            각 측의 설득력을 100점 만점으로 평가하여, 아래 JSON 형식으로 응답하세요:
            ```json
            {{
                "persuasion_pos": <점수>,
                "persuasion_neg": <점수>,
            }}
            ```"""
        )

        self.progress_round1_prompt = PromptTemplate(
            input_variables=["topic"],
            template="""
                당신은 **"{topic}"** 주제에 대한 토론을 진행하는 역할을 맡았습니다. 중립적인 태도로 토론을 소개하며, 주제에 대한 간략하고 객관적인 소개를 제공해야 합니다. 특정 입장을 지지하거나 반대하는 표현을 사용하지 않도록 유의하세요.  

                ### **진행 방식:**
                - **주제를 간결하고 객관적으로 요약**하세요.
                - 개인적인 의견을 배제하고 중립적인 태도를 유지하세요.
                - 주제 소개 후, **찬성 측(affirmative side)이 먼저 주장을 펼칠 수 있도록 유도**하세요.

                ---

                ### **예시 구조**:

                **소개:**  
                "'{topic}'는 다양한 시각에서 논의되는 주제입니다. 찬성하는 측에서는 [찬성 측의 주요 주장]을 근거로 주장하며, 반대하는 측에서는 [반대 측의 주요 주장]을 내세웁니다. 이 논쟁은 주로 [토론에서 중요한 2~3가지 핵심 쟁점]을 중심으로 진행됩니다. 오늘 우리는 이 주제에 대한 양측의 입장을 깊이 탐구해보겠습니다."
                
                "그럼 먼저, **찬성 측**의 의견을 들어보겠습니다. {topic}에 대한 찬성 입장은 무엇이며, 이를 뒷받침하는 주요 근거와 증거는 무엇인가요?"

            """
        )

        self.progress_round_prompt = PromptTemplate(
            input_variables=["pos_time", "neg_time"],
            template="""
            [SYSTEM: 당신은 토론 진행자입니다. 남은 발언 시간을 전달하는 것입니다. 참가자로서 발언하지 마십시오.]
            
            남은 발언 시간: 찬성 {pos_time:.2f}초, 반대 {neg_time:.2f}초.
            """
        )

        self.memory_manager = DebateMemoryWrapper()

    def generate_text(self, speaker: str, prompt: str) -> str:
        """
        SystemMessage와 HumanMessage를 생성하여, 이를 연결한 문자열을 user_prompt로 전달합니다.
        temperature, max_tokens 설정값도 반영합니다.
        """
        agent_obj = self.participant.get(speaker, {})
        if agent_obj:
            speaker_ai = agent_obj.ai_instance
        else:
            return ""
        
        system_msg = SystemMessage(content=f"{speaker} 역할")
        human_msg = HumanMessage(content=prompt)
        combined_prompt = system_msg.content + "\n" + human_msg.content
        return speaker_ai.generate_text(
            user_prompt=combined_prompt,
            max_tokens=self.generate_text_config["max_tokens"],
            temperature=self.generate_text_config["temperature"]
        )

    def next_speaker(self, is_final: bool = False) -> dict:
        history_str = self.memory_manager.format_history()
        candidates = "['judge']" if is_final else "['pos', 'neg']"
        prompt = self.next_speaker_candidate_prompt.format(history=history_str, candidates=candidates)
        result_text = self.generate_text("next_speaker_agent", prompt)
        try:
            parsed = self.output_parser.parse(result_text)
            next_speaker = parsed["speaker"]
            message = parsed["message"]
            if is_final and next_speaker != "judge":
                next_speaker = "judge"
                message = "최종 판결을 위해 judge가 선택되었습니다."
            elif not is_final and next_speaker.lower() not in ["pos", "neg"]:
                next_speaker = "neg"
        except OutputParserException:
            next_speaker = "neg" if not is_final else "judge"
            message = f"Defaulting to {next_speaker}."
        # self.memory_manager.save_message("System", f"Next speaker decided: {next_speaker}. {message}")
        return {"speaker": next_speaker, "message": message}

    def debate_turn(self, speaker: str, round_number: int) -> dict:
        if round_number == 1:
            prompt = self.claim_prompt.format(topic=self.data["topic"], position=speaker, persona = self.data["participants"][speaker]["name"])
        else:
            opponent = "neg" if speaker.lower() == "pos" else "pos"
            opp_msgs = self.memory_manager.load_by_speaker(opponent)
            opponent_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in opp_msgs])
            if opp_msgs:
                last_opp_statements = f"[Round {opp_msgs[-1]['round']}] {opp_msgs[-1]['message']}"
            else:
                last_opp_statements = ""
            prompt = self.argument_prompt.format(topic=self.data["topic"], position=speaker, opponent_statements=opponent_statements,
                                                 last_opp_statements=last_opp_statements, persona = self.data["participants"][speaker]["name"])
        result_text = self.generate_text(speaker, prompt)
        try:
            parsed = self.output_parser.parse(result_text)
            message = parsed["message"]
        except OutputParserException:
            message = "응답 파싱 실패"
        self.memory_manager.save_message(speaker, message)
        return {"speaker": speaker, "message": message}

    def evaluate(self, _) -> dict:
        # 모든 발언 불러오기
        pos_msgs = self.memory_manager.load_by_speaker("pos")
        neg_msgs = self.memory_manager.load_by_speaker("neg")
        pos_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in pos_msgs])
        neg_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in neg_msgs])

        # 1라운드의 주장 메시지를 제외한 반론 메시지 추출 (round > 1)
        pos_rebuttals = [msg for msg in pos_msgs if msg["round"] > 1]
        neg_rebuttals = [msg for msg in neg_msgs if msg["round"] > 1]
        pos_rebuttal = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in pos_rebuttals])
        neg_rebuttal = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in neg_rebuttals])

        # judge_1: 논리 평가
        prompt_logical = self.judge_logical_prompt.format(
            topic=self.data["topic"],
            pos_statements=pos_statements,
            neg_statements=neg_statements
        )
        result_logical_text = self.generate_text("judge_1", prompt_logical)
        try:
            parsed_logical = self.judge_logical_parser.parse(result_logical_text)
        except Exception:
            parsed_logical = {"logicality_pos": 0, "logicality_neg": 0, "message": "논리 평가 파싱 실패"}

        # judge_2: 반론 평가
        prompt_rebuttal = self.judge_rebuttal_prompt.format(
            topic=self.data["topic"],
            pos_rebuttal=pos_rebuttal,
            neg_rebuttal=neg_rebuttal
        )
        result_rebuttal_text = self.generate_text("judge_2", prompt_rebuttal)
        try:
            parsed_rebuttal = self.judge_rebuttal_parser.parse(result_rebuttal_text)
        except Exception:
            parsed_rebuttal = {"rebuttal_pos": 0, "rebuttal_neg": 0, "message": "반론 평가 파싱 실패"}

        # judge_3: 설득력 평가
        prompt_persuasion = self.judge_persuasion_prompt.format(
            topic=self.data["topic"],
            pos_statements=pos_statements,
            neg_statements=neg_statements
        )
        result_persuasion_text = self.generate_text("judge_3", prompt_persuasion)
        try:
            parsed_persuasion = self.judge_persuasion_parser.parse(result_persuasion_text)
        except Exception:
            parsed_persuasion = {"persuasion_pos": 0, "persuasion_neg": 0, "message": "설득력 평가 파싱 실패"}

        logicality_pos = int(parsed_logical.get("logicality_pos", 0))
        logicality_neg = int(parsed_logical.get("logicality_neg", 0))
        rebuttal_pos = int(parsed_rebuttal.get("rebuttal_pos", 0))
        rebuttal_neg = int(parsed_rebuttal.get("rebuttal_neg", 0))
        persuasion_pos = int(parsed_persuasion.get("persuasion_pos", 0))
        persuasion_neg = int(parsed_persuasion.get("persuasion_neg", 0))

        # 가중치 적용하여 최종 점수 계산
        match_pos = logicality_pos * 0.4 + rebuttal_pos * 0.35 + persuasion_pos * 0.25
        match_neg = logicality_neg * 0.4 + rebuttal_neg * 0.35 + persuasion_neg * 0.25

        # 결과 저장
        if match_pos:
            if match_pos > match_neg:
                self.data["result"] = "positive"
            elif match_pos < match_neg:
                self.data["result"] = "negative"
            else:
                self.data["result"] = "draw"
        else:
            self.data["result"] = "draw"

        self.data["score"] = {
            "logicality_pos": logicality_pos,
            "logicality_neg": logicality_neg,
            "rebuttal_pos": rebuttal_pos,
            "rebuttal_neg": rebuttal_neg,
            "persuasion_pos": persuasion_pos,
            "persuasion_neg": persuasion_neg,
            "match_pos": match_pos,
            "match_neg": match_neg
        }

        self.data["debate_log"] = self.memory_manager.load_all()
        self.data["status"]["type"] = "end"

        return self.data["result"]
            


    def progress(self) -> dict:
        debate = self.data
        result = {"timestamp": None, "speaker": "", "message": ""}

        if debate["_id"] is None:
            result["speaker"] = "SYSTEM"
            result["message"] = "유효하지 않은 토론입니다."
            result["timestamp"] = datetime.now()
            return result

        debate["topic"] = self.data["topic"]
        debate["status"]["step"] = self.memory_manager.current_round



        pos_time_remaining = 20.0
        neg_time_remaining = 20.0

        initial = self.next_speaker(is_final=False)
        self.memory_manager.save_message("Progress", f"초기 발언자: {initial['speaker']}")
        first_speaker = initial["speaker"]
        second_speaker = "neg" if first_speaker == "pos" else "pos"
        order = [first_speaker, second_speaker]

        round_number = 1
        max_round = 10  # 최대 라운드 수
        while round_number <= max_round:
            if round_number == 1:
                prompt = self.progress_round1_prompt.format(topic=self.data["topic"])
                prog_text = self.generate_text("progress_agent", prompt)
            else:
                prompt = self.progress_round_prompt.format(pos_time=pos_time_remaining, neg_time=neg_time_remaining)
                prog_text = self.generate_text("progress_agent", prompt)
            print(prog_text)
            self.memory_manager.save_message("Progress", prog_text)

            for speaker in order:
                start = time.time()
                turn = self.debate_turn(speaker, round_number)
                end = time.time()
                duration = end - start
                print(f"{turn['speaker']} : {turn['message']}")
                if speaker == "pos":
                    pos_time_remaining -= duration
                elif speaker == "neg":
                    neg_time_remaining -= duration
            if pos_time_remaining <= 0 or neg_time_remaining <= 0:
                final_spk = self.next_speaker(is_final=True)
                # self.memory_manager.save_message("Progress", final_spk["message"])
                break

            round_number += 1
            self.memory_manager.increment_round()
            debate["status"]["step"] = self.memory_manager.current_round

        final_eval = self.evaluate({})
        self.memory_manager.save_message("judge", final_eval)
        debate["end_time"] = datetime.now()
        debate["debate_log"] = self.memory_manager.load_all()
        debate["status"]["type"] = "end"  # 종료 상태로 설정
        result = {"timestamp": datetime.now(), "speaker": "judge", "message": final_eval}
        return result
