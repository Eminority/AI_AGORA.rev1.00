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
        entry = {"round": round_number, "speaker": speaker, "message": message}
        self.custom_history.append(entry)
        formatted = f"[Round {round_number}] {speaker}: {message}"
        sys_msg = SystemMessage(content=f"{speaker} 역할")
        human_msg = HumanMessage(content=formatted)
        self.memory.chat_memory.add_message(sys_msg)
        self.memory.chat_memory.add_message(human_msg)

    def load_all(self):
        return self.custom_history

    def load_by_speaker(self, speaker: str):
        return [msg for msg in self.custom_history if msg["speaker"] == speaker]

    def increment_round(self):
        self.current_round += 1

    def format_history(self):
        return "\n".join([f"[Round {msg['round']}] {msg['speaker']}: {msg['message']}" for msg in self.custom_history])


class Debate(Progress):
    """
    Debate 클래스는 토론 진행 로직을 관리합니다.

    외부에서 주입되는 에이전트:
      - participant["pos"]: 찬성측 토론 에이전트
      - participant["neg"]: 반대측 토론 에이전트
      - participant["judge"]: 심판 에이전트 (최종 평가)
      - participant["progress_agent"]: 토론 진행 안내 메시지 생성 에이전트
      - participant["next_speaker_agent"]: 다음 발언자 결정 에이전트

    각 에이전트는 ai_instance라는 속성을 가지며, generate_text(user_prompt, max_tokens, temperature)를 제공해야 합니다.
    Progress의 progress()는 dict를, evaluate()는 최종 메시지(str)를 반환하며,
    data JSON에는 debate_log와 status["step"]이 업데이트되고, topic은 data["topic"]에서 가져옵니다.
    """
    def __init__(self, participant: dict, generate_text_config: dict, data: dict = None):
        super().__init__(participant=participant,
                         data=data,
                         generate_text_config=generate_text_config)

        if data is None:
            self.data = {
                "participants": None,
                "topic": None,
                "status": {"type": "in_progress", "step": 1},
                "debate_log": [],
                "start_time": datetime.now(),
                "end_time": None,
                "summary": {
                    "summary_pos": None,
                    "summary_neg": None,
                    "summary_arguments": None,
                    "summary_verdict": None
                },
                "result": None,
            }
        else:
            self.data = data

        self.topic = self.data.get("topic", "")

        response_schemas = [
            ResponseSchema(name="speaker", description="응답한 화자 (Pos, Neg, Judge 등)"),
            ResponseSchema(name="message", description="생성된 메시지 내용")
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

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
            input_variables=["topic", "position"],
            template="""
            [SYSTEM: 당신은 토론 참가자입니다. 역할은 자신의 주장을 처음으로 제시하는 것입니다.]
            당신은 "{topic}" 토론에 참여하고 있습니다.
            이번 라운드에서는 자신의 주장을 처음으로 제시해 주세요.
            당신의 입장은 **{position}**입니다.
            주요 근거와 함께 자신의 주장을 명확하게 기술해 주세요.
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
            input_variables=["topic", "position", "opponent_statements"],
            template="""
            [SYSTEM: 당신은 토론 참가자입니다. 역할은 상대의 주장을 반박하는 것입니다.]
            당신은 "{topic}" 토론에 참여하고 있습니다.
            당신의 입장은 **{position}**입니다.
            상대측의 주장:
            {opponent_statements}
            위 내용을 바탕으로 논리적인 근거와 예시를 들어 반박해 주세요.
            또한 응답 시 형식화 된 구조로 작성하세요. 첫째, 둘째, 셋째 등으로 주장을 나누는 방법이 바람직합니다.
            반드시 JSON 형식으로 응답하세요:
            ```json
            {{
                "speaker": "{position}",
                "message": "..."
            }}
            ```
            """
        )

        self.evaluator_prompt = PromptTemplate(
            input_variables=["history"],
            template="""
            [SYSTEM: 당신은 토론 심판입니다. 역할은 라운드 평가를 진행하는 것입니다.]
            다음은 이번 라운드의 토론 발언 기록입니다:
            {history}

            각 참가자(찬성: "pos", 반대: "neg")의 발언을 아래 기준으로 평가해 주세요.
            1. 논리력 (0~10점)
            2. 신선도 (0~10점)
            3. 사실 기반 (0~10점)

            평가 결과는 반드시 JSON 형식으로 반환하세요. 예시:
            {{
                "evaluations": [
                    {{"participant": "pos", "logic_score": 8, "freshness_score": 6, "factuality_score": 9, "warning": ""}},
                    {{"participant": "neg", "logic_score": 7, "freshness_score": 5, "factuality_score": 8, "warning": "반복적입니다."}}
                ],
                "message": "라운드 평가 결과입니다."
            }}
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
               "speaker": "Judge",
               "message": "최종 판결: [Pos/Neg]가 더 설득력이 있습니다. 이유: ..."
            }}
            ```
            """
        )

        self.progress_round1_prompt = PromptTemplate(
            input_variables=["topic"],
            template="""
            [SYSTEM: 당신은 토론 진행자입니다. 역할은 라운드 안내 및 다음 발언자 소개입니다. 참가자로서 발언하지 마십시오.]
            Round 1 시작:
            주제: "{topic}"
            각 참가자께서는 자신의 주장을 처음으로 제시해 주세요.
            """
        )

        self.progress_round_prompt = PromptTemplate(
            input_variables=["evaluation", "pos_time", "neg_time"],
            template="""
            [SYSTEM: 당신은 토론 진행자입니다. 역할은 이전 라운드 평가 결과와 남은 발언 시간을 전달하는 것입니다. 참가자로서 발언하지 마십시오.]
            이번 라운드 평가 결과 {evaluation}를 요약해서 전달하세요.
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
        candidates = "['Judge']" if is_final else "['Pos', 'Neg']"
        prompt = self.next_speaker_candidate_prompt.format(history=history_str, candidates=candidates)
        result_text = self.generate_text("next_speaker_agent", prompt)
        try:
            parsed = self.output_parser.parse(result_text)
            next_speaker = parsed["speaker"]
            message = parsed["message"]
            if is_final and next_speaker != "Judge":
                next_speaker = "Judge"
                message = "최종 판결을 위해 Judge가 선택되었습니다."
            elif not is_final and next_speaker not in ["pos", "neg"]:
                next_speaker = "neg"
        except OutputParserException:
            next_speaker = "neg" if not is_final else "Judge"
            message = f"Defaulting to {next_speaker}."
        self.memory_manager.save_message("System", f"Next speaker decided: {next_speaker}. {message}")
        return {"speaker": next_speaker, "message": message}

    def debate_turn(self, speaker: str, round_number: int) -> dict:
        if round_number == 1:
            prompt = self.claim_prompt.format(topic=self.data["topic"], position=speaker)
        else:
            opponent = "neg" if speaker == "pos" else "pos"
            opp_msgs = self.memory_manager.load_by_speaker(opponent)
            opponent_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in opp_msgs])
            prompt = self.argument_prompt.format(topic=self.data["topic"], position=speaker, opponent_statements=opponent_statements)
        result_text = self.generate_text(speaker, prompt)
        try:
            parsed = self.output_parser.parse(result_text)
            message = parsed["message"]
        except OutputParserException:
            message = "응답 파싱 실패"
        self.memory_manager.save_message(speaker, message)
        return {"speaker": speaker, "message": message}

    def evaluate(self, _) -> str:
        pos_msgs = self.memory_manager.load_by_speaker("pos")
        neg_msgs = self.memory_manager.load_by_speaker("neg")
        pos_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in pos_msgs])
        neg_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in neg_msgs])
        prompt = self.judge_prompt.format(topic=self.data["topic"], pos_statements=pos_statements, neg_statements=neg_statements)
        result_text = self.generate_text("judge", prompt)
        try:
            parsed = self.output_parser.parse(result_text)
            message = parsed["message"]
        except OutputParserException:
            message = "최종 평가 응답 파싱 실패"
        self.memory_manager.save_message("Judge", message)
        self.data["debate_log"] = self.memory_manager.load_all()
        return message

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
            print(f"=== Round {round_number} 시작 ===")
            if round_number == 1:
                prompt = self.progress_round1_prompt.format(topic=self.data["topic"])
                prog_text = self.generate_text("progress_agent", prompt)
            else:
                prompt = self.progress_round_prompt.format(evaluation="이전 라운드 평가 참고", 
                                                           pos_time=pos_time_remaining, 
                                                           neg_time=neg_time_remaining)
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
                self.memory_manager.save_message("Progress", final_spk["message"])
                break

            round_number += 1
            self.memory_manager.increment_round()
            debate["status"]["step"] = self.memory_manager.current_round

        final_eval = self.evaluate({})
        self.memory_manager.save_message("Judge", final_eval)
        debate["end_time"] = datetime.now()
        debate["debate_log"] = self.memory_manager.load_all()
        debate["status"]["type"] = "end"  # 종료 상태로 설정
        result = {"timestamp": datetime.now(), "speaker": "Judge", "message": final_eval}
        return result
