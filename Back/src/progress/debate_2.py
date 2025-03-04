import time
from datetime import datetime
from .progress import Progress
import re

class Debate_2(Progress):
    """
    debate를 관리하는 클래스
    self.participants에 judge, pos, neg ai를 넣넣는다.
    self.data에 save할 데이터를 넣는다.
    generate_text_config에는 max_tokens, k, temperature 값을 저장한다.
    method : progress
    method : evaluate
    """
    def __init__(self, participant:dict, generate_text_config:dict, data:dict=None, ):
        # participant:{"judge": Participant, "pos": Participant, "neg": Participant} 형태.
        super().__init__(participant=participant,
                         generate_text_config=generate_text_config,
                         data=data)

        # 총 11단계 진행
        self.max_step = 11

        self.data = data
        if self.data == None:
            # debate 필드 초기화
            self.data = {
                "type": "debate_2",
                "participants": {position : {"id"   : data.id,
                                 "name" : data.name,
                                  "img" : data.img,
                                  "ai"  : data.ai_instance.model_name,
                                  "object_attribute": data.object_attribute}
                                  for position, data in participant.items()},
                "topic": None,
                "status": {
                    "type": None,  # "in_progress" 또는 "end" 등
                    "step": 0     # 1부터 11까지 단계
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


    def progress(self) -> dict:
        """
        11단계 순서:
        1) 판사가 주제 설명
        2) 찬성측 주장
        3) 반대측 주장
        4) 판사가 변론 준비시간(1초) 부여
        5) 반대측 변론
        6) 찬성측 변론
        7) 판사가 최종 주장 시간(1초) 부여
        8) 찬성측 최종 결론
        9) 반대측 최종 결론
        10) 판사가 판결 준비시간(1초) 부여
        11) 판사 최종 결론 (evaluate)
        """
        debate = self.data


        # 단계(step)가 설정되어 있지 않다면 1로 초기화
        if "step" not in debate["status"] or debate["status"]["step"] == 0:
            debate["status"]["step"] = 1
        step = debate["status"]["step"]

        result = {"timestamp": None, "speaker": "", "message": "", "step": step}

        # 유효하지 않은 토론이면 메시지 반환
        if debate["_id"] is None:
            result["speaker"] = "SYSTEM"
            result["message"] = "유효하지 않은 토론입니다."
            result["timestamp"] = datetime.now()
            return result


        # 단계별 로직
        if step == 1:
            # 1. 판사가 주제 설명
            # self.ready_to_debate() -> crawling하는 단계가 필요함.
            result["speaker"] = "judge_1"
            prompt =f"""
                당신은 **"{self.data['topic']}"** 주제에 대한 토론을 진행하는 역할을 맡았습니다. 중립적인 태도로 토론을 소개하며, 주제에 대한 간략하고 객관적인 소개를 제공해야 합니다. 특정 입장을 지지하거나 반대하는 표현을 사용하지 않도록 유의하세요.  

                ### **진행 방식:**
                - **주제를 간결하고 객관적으로 요약**하세요.
                - 개인적인 의견을 배제하고 중립적인 태도를 유지하세요.
                - 주제 소개 후, **찬성 측(affirmative side)이 먼저 주장을 펼칠 수 있도록 유도**하세요.

                ---

                ### **예시 구조**:

                **소개:**  
                "'{self.data['topic']}'는 다양한 시각에서 논의되는 주제입니다. 찬성하는 측에서는 [찬성 측의 주요 주장]을 근거로 주장하며, 반대하는 측에서는 [반대 측의 주요 주장]을 내세웁니다. 이 논쟁은 주로 [토론에서 중요한 2~3가지 핵심 쟁점]을 중심으로 진행됩니다. 오늘 우리는 이 주제에 대한 양측의 입장을 깊이 탐구해보겠습니다."
                
                "그럼 먼저, **찬성 측**의 의견을 들어보겠습니다. {self.data['topic']}에 대한 찬성 입장은 무엇이며, 이를 뒷받침하는 주요 근거와 증거는 무엇인가요?"
                """
            
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 2:
            # 2. 찬성 측 주장
            result["speaker"] = "pos"
            prompt =f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 이 주장에 찬성하는 입장에서 논증하는 것입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 주제에 대한 **찬성 입장을 명확하게 제시**하세요.  
            - 찬성하는 이유를 뒷받침할 **세 가지 이상의 강력한 논거**를 제시하세요.  
            - **논리적 근거, 현실 사례, 데이터** 등을 활용하여 주장을 강화하세요.  
            - 주제에 대한 일반적인 설명은 피하고, 오직 찬성하는 입장을 옹호하는 데 집중하세요.  

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
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            result["message"] = self.generate_text(result["speaker"], prompt)

        elif step == 3:
            # 3. 반대 측 주장
            result["speaker"] = "neg"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 이 주장에 반대하는 입장에서 논증하는 것입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 주제에 대한 **반대 입장을 명확하게 제시**하세요.  
            - 반대하는 이유를 뒷받침할 **세 가지 이상의 강력한 논거**를 제시하세요.  
            - **논리적 근거, 현실 사례, 데이터** 등을 활용하여 주장을 강화하세요.  
            - 주제에 대한 일반적인 설명은 피하고, 오직 반대하는 입장을 옹호하는 데 집중하세요.  

            ---

            ### **응답 형식:**  

            1. **반박 논거 #1**  
            - 설명  
            - 근거 또는 예시  

            2. **반박 논거 #2**  
            - 설명  
            - 근거 또는 예시  

            3. **반박 논거 #3**  
            - 설명  
            - 근거 또는 예시  

            간결하면서도 설득력 있게 작성하세요. 적용 가능한 경우, 사실적 근거를 제공하세요.
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            
            result["message"] = self.generate_text(result["speaker"], prompt)

        elif step == 4:
            # 4. 판사가 변론 준비시간 1초 제공
            result["speaker"] = "judge_1"
            result["message"] ="양측이 초기 주장을 제시하였습니다. 반론을 준비할 시간을 가지세요."
            time.sleep(1)

        elif step == 5:
            # 5. 반대 측 변론
            result["speaker"] = "neg"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 **반대 측 입장에서 찬성 측(affirmative)의 주장에 반박하는 것**입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - **가장 최근의 찬성 측 주장**을 검토하고 이에 대한 **논리적인 반박**을 제시하세요.  
            - 찬성 측의 **핵심 논점을 직접적으로 반박**하세요.  
            - **근거, 논리적 추론, 현실 사례**를 활용하여 상대 주장을 논파하세요.  
            - 새로운 반대 논거를 도입하지 말고, 오직 상대방의 주장을 반박하는 데 집중하세요.  

            ---

            ### **응답 형식:**  

            "찬성 측의 주장을 면밀히 검토해 보았지만, 다음과 같은 이유로 반박하고자 합니다.  

            1. **첫 번째 반박:**  
            - 찬성 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            2. **두 번째 반박:**  
            - 찬성 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            3. **세 번째 반박:**  
            - 찬성 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            이러한 이유로 찬성 측의 주장은 그리 강력하지 않습니다."  

            **토론 주제:** {self.data['topic']}  
            **이전 발언:** {self.data['debate_log'][-3]}  
            """

            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            
            result["message"] = self.generate_text(result["speaker"],prompt)
        elif step == 6:
            # 6. 찬성 측 변론
            result["speaker"] = "pos"
            prompt =  f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 **찬성 측 입장에서 반대 측(negative)의 주장에 반박하는 것**입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - **가장 최근의 반대 측 주장**을 검토하고 이에 대한 **논리적인 반박**을 제시하세요.  
            - 반대 측의 **핵심 논점을 직접적으로 반박**하세요.  
            - **근거, 논리적 추론, 현실 사례**를 활용하여 상대 주장을 논파하세요.  
            - 새로운 찬성 논거를 도입하지 말고, 오직 상대방의 주장을 반박하는 데 집중하세요.  

            ---

            ### **응답 형식:**  

            "반대 측의 주장을 면밀히 검토해 보았지만, 다음과 같은 이유로 반박하고자 합니다.  

            1. **첫 번째 반박:**  
            - 반대 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            2. **두 번째 반박:**  
            - 반대 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            3. **세 번째 반박:**  
            - 반대 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            이러한 이유로 반대 측의 주장은 그리 강력하지 않습니다."  

            **토론 주제:** {self.data['topic']}  
            **이전 발언:** {self.data['debate_log'][-3]}  
            """
            

            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 7:
            # 7. 판사가 최종 주장 시간 부여
            result["speaker"] = "judge_1"
            result["message"] = "이제 토론의 마지막 단계로 접어들고 있습니다. 양측 모두 최종 발언을 할 기회를 가지게 됩니다."
            time.sleep(1)

        elif step == 8:
            # 8. 찬성 측 최종 결론
            result["speaker"] = "pos"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 **찬성 측 입장에서 최종 발언을 하는 것**입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 찬성 측의 **가장 강력하고 설득력 있는 논거**를 요약하세요.  
            - **찬성 입장이 가장 논리적이고 정당한 이유**를 강조하세요.  
            - 반대 측의 반박을 언급하고, 왜 그것이 찬성 측의 입장을 약화시키지 않는지 설명하세요.  
            - **명확하고 설득력 있는 최종 결론**을 제시하세요.  

            ---

            ### **응답 형식:**  

            "이 토론을 통해 우리는 **{self.data['topic']}**이(가) 타당한 입장임을 명확히 입증하였습니다.  

            1. **핵심 논거 #1 요약:**  
            - "[가장 중요한 찬성 논거 요약]"  
            - "[반박에도 불구하고 여전히 유효한 이유]"  

            2. **핵심 논거 #2 요약:**  
            - "[또 다른 주요 찬성 논거 요약]"  
            - "[이 논거가 여전히 강력한 이유]"  

            3. **핵심 논거 #3 요약:**  
            - "[마지막 주요 논거 요약]"  
            - "[토론이 진행된 후에도 유지되는 이유]"  

            반대 측의 반박에도 불구하고, 우리의 주장은 **[결정적인 근거]** 때문에 흔들리지 않았습니다.  

            이번 토론을 통해 **{self.data['topic']}**이(가) 가장 논리적이고 정당한 입장이라는 것이 명확해졌습니다."  

            **토론 주제:** {self.data['topic']}  
            **이전 발언:** {self.data['debate_log'][:-2]}  
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."

            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 9:
            # 9. 반대 측 최종 결론
            result["speaker"] = "neg"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 **찬성 측 입장에서 최종 발언을 하는 것**입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 찬성 측의 **가장 강력하고 설득력 있는 논거**를 요약하세요.  
            - **찬성 입장이 가장 논리적이고 정당한 이유**를 강조하세요.  
            - 반대 측의 반박을 언급하고, 왜 그것이 찬성 측의 입장을 약화시키지 않는지 설명하세요.  
            - **명확하고 설득력 있는 최종 결론**을 제시하세요.  

            ---

            ### **응답 형식:**  

            "이 토론을 통해 우리는 **{self.data['topic']}**이(가) 타당한 입장임을 명확히 입증하였습니다.  

            1. **핵심 논거 #1 요약:**  
            - "[가장 중요한 찬성 논거 요약]"  
            - "[반박에도 불구하고 여전히 유효한 이유]"  

            2. **핵심 논거 #2 요약:**  
            - "[또 다른 주요 찬성 논거 요약]"  
            - "[이 논거가 여전히 강력한 이유]"  

            3. **핵심 논거 #3 요약:**  
            - "[마지막 주요 논거 요약]"  
            - "[토론이 진행된 후에도 유지되는 이유]"  

            반대 측의 반박에도 불구하고, 우리의 주장은 **[결정적인 근거]** 때문에 흔들리지 않았습니다.  

            이번 토론을 통해 **{self.data['topic']}**이(가) 가장 논리적이고 정당한 입장이라는 것이 명확해졌습니다."  

            **토론 주제:** {self.data['topic']}  
            **이전 발언:** {self.data['debate_log'][:-2]}  
            """

            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            
            
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 10:
            # 10. 판사가 판결 준비시간(1초) 부여
            result["speaker"] = "judge_1"
            result["message"] = "토론이 이제 종료되었습니다. 최종 결정을 내리기 전에 모든 주장을 검토하는 시간을 가지겠습니다."            
            time.sleep(1)

        
        elif step == 11:
            # 11. 판사가 최종 결론
            result["speaker"] = "judge_1"
            result["message"] = self.evaluate()
            debate["status"]["type"] = "end"
        
        else:
            result["speaker"] = "SYSTEM"
            result["message"] = "토론이 이미 종료되었습니다."



        
        debate["debate_log"].append(result)

        # if result["speaker"] == "pos":
        #     debate["debate_log_pos"].append(result["message"])



        result["timestamp"] = datetime.now()

        if step < self.max_step:
            debate["status"]["step"] += 1

        return result





    def evaluate(self):
        # 찬성, 반대측 각각 토론 로그
        pos_log = next((pos_message for pos_message in self.data["debate_log"] if pos_message["speaker"] == "pos"))
        neg_log = next((pos_message for pos_message in self.data["debate_log"] if pos_message["speaker"] == "neg"))
        # 찬성, 반대측 반박 로그 (step 5,6)
        pos_rebuttal = next((pos_message for pos_message in self.data["debate_log"] if pos_message["step"] == 6))
        neg_rebuttal = next((neg_message for neg_message in self.data["debate_log"] if neg_message["step"] == 5))

        
        # Generate the evaluation text from the judge
        prompt_logicality = f"""
        당신은 논리적 추론 및 논증 분석의 전문가입니다. 주어진 두 개의 글을 상호 비교하여 **논리적 타당성을 100점 척도로 평가**하는 것이 당신의 역할입니다.  

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

        **[글 1]**  
        {pos_log}  

        **[글 2]**  
        {neg_log}  

        ### **출력 형식:**  

        - **글 1 분석:** (논리적 강점과 약점에 대한 상세 분석)  
        - **글 1 논리적 타당성 점수 (pos): 점수**  

        - **글 2 분석:** (논리적 강점과 약점에 대한 상세 분석)  
        - **글 2 논리적 타당성 점수 (neg): 점수**  
        """



        prompt_rebuttal = f"""
        당신은 논증 분석 및 반박 효과성 평가의 전문가입니다. 주어진 두 개의 반박문을 상호 비교하여 **반박의 강도를 100점 척도로 평가**하는 것이 당신의 역할입니다.  

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

        **[반박문 1]**  
        {pos_rebuttal}  

        **[반박문 2]**  
        {neg_rebuttal}  

        ### **출력 형식:**  

        - **반박문 1 분석:** (논리적 강점과 약점에 대한 상세 분석)  
        - **반박문 1 강도 점수 (pos): 점수**  

        - **반박문 2 분석:** (논리적 강점과 약점에 대한 상세 분석)  
        - **반박문 2 강도 점수 (neg): 점수**  
        """



        prompt_persuasion = f"""
        당신은 논증 분석 및 설득력 평가의 전문가입니다. 주어진 두 개의 글을 비교하여 **설득력을 100점 척도로 평가**하는 것이 당신의 역할입니다.  

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

        **[글 1]**  
        {pos_log}  

        **[글 2]**  
        {neg_log}  

        ### **foramat:**  

        - **글 1 분석:** (설득력에 대한 상세 분석: 강점 및 약점)  
        - **글 1 설득력 점수 (pos): 점수**  

        - **글 2 분석:** (설득력에 대한 상세 분석: 강점 및 약점)  
        - **글 2 설득력 점수 (neg): 점수**  
        """
    

        def extract_score(pattern, text):
            """정규식을 사용하여 점수를 추출하고 정수로 변환하는 함수"""
            match = re.search(pattern, text)
            return int(match.group(1)) if match else 0  # 매칭이 안 되면 기본값 0 반환

        def calculate_score(judge, prompt):
            """텍스트 생성 후 점수를 추출하는 함수"""
            result_text = self.generate_text(judge, prompt)
            return extract_score(r'\(pos\)\:.*?(\d+)(?:\*|\/100)?', result_text), \
                extract_score(r'\(neg\)\:.*?(\d+)(?:\*|\/100)?', result_text)

        # 각 평가 기준에 대한 점수 추출
        logicality_pos, logicality_neg = calculate_score("judge_1", prompt_logicality)
        rebuttal_pos, rebuttal_neg = calculate_score("judge_2", prompt_rebuttal)
        persuasion_pos, persuasion_neg = calculate_score("judge_3", prompt_persuasion)

        # 최종 점수 계산
        weights = {"logicality": 0.4, "rebuttal": 0.35, "persuasion": 0.25}

        match_pos = (logicality_pos * weights["logicality"] + 
                    rebuttal_pos * weights["rebuttal"] + 
                    persuasion_pos * weights["persuasion"])

        match_neg = (logicality_neg * weights["logicality"] + 
                    rebuttal_neg * weights["rebuttal"] + 
                    persuasion_neg * weights["persuasion"])

        # 결과 출력
        print(f"logicality_pos: {logicality_pos}" )
        print(f"rebuttal_pos: {rebuttal_pos}" )
        print(f"persuasion_pos: {persuasion_pos}" )
        print(f"match_pos: {match_pos}")
        print(f"match_neg: {match_neg}")

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

        print(self.data["score"])

        return self.data["result"]