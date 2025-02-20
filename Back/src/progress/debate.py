import time
from datetime import datetime
from .progress import Progress
import re

class Debate(Progress):
    """
    debate를 관리하는 클래스
    self.participants에 judge, pos, neg ai를 넣넣는다.
    self.data에 save할 데이터를 넣는다.
    method : progress
    method : evaluate
    """
    def __init__(self, participant:dict, data:dict):
        # {"judge": Participant, "pos": Participant, "neg": Participant} 형태.
        self.participant = participant

        # 총 11단계 진행
        self.max_step = 11

        self.data = data
        if self.data == None:
            # debate 필드 초기화
            self.data = {
                "participants": None,
                "topic": None,
                "status": {
                    "type": None,  # "in_progress" 또는 "end" 등
                    "step": 0     # 1부터 11까지 단계
                },
                "debate_log": [],
                "start_time": None,
                "end_time": None,
                "summary": {
                    "summary_pos": None,
                    "summary_neg": None,
                    "summary_arguments": None,
                    "summary_verdict": None
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
        result = {"timestamp": None, "speaker": "", "message": ""}

        # 유효하지 않은 토론이면 메시지 반환
        if debate["_id"] is None:
            result["speaker"] = "SYSTEM"
            result["message"] = "유효하지 않은 토론입니다."
            result["timestamp"] = datetime.now()
            return result

        # 단계(step)가 설정되어 있지 않다면 1로 초기화
        if "step" not in debate["status"]:
            debate["status"]["step"] = 1
        step = debate["status"]["step"]

        # 단계별 로직
        if step == 1:
            # 1. 판사가 주제 설명
            # self.ready_to_debate() -> crawling하는 단계가 필요함.
            result["speaker"] = "judge"
            result["message"] = self.judge.ai_instance.generate_text(
                f"""
                You are facilitating a debate on the topic: **"{self.data['topic']}"**. Your role is to introduce the discussion in a neutral manner, providing a brief, informative introduction to the topic without taking any stance.  

                ### **Instructions:**
                - Start by giving a **concise, objective summary** of the topic.
                - Avoid personal opinions or taking a side.
                - After introducing the topic, **invite the affirmative side to present their argument first**.

                ---

                ### **Example Structure**:

                **Introduction:**  
                "{self.data['topic']} is a widely debated issue with strong arguments on both sides. Supporters argue that  [Key argument of the affirmative side], while opponents believe that [Key argument of the negative side]. The discussion often revolves around factors such as [2-3 key points of debate]. Today, we will explore both perspectives in depth."

                **Prompting the Affirmative Side:**  
                "To begin, let's hear from the **affirmative side**. Please present your argument in support of {self.data['topic']}. What are the key reasons and evidence supporting your stance?"

                """
            )

        elif step == 2:
            # 2. 찬성 측 주장
            result["speaker"] = "pos"
            result["message"] = self.participant["pos"].ai_instance.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to argue in favor of this statement.  

            ### **Instructions:**  
            - Clearly state your **position** in support of the topic.  
            - Provide **at least three strong arguments** supporting your stance.  
            - Use **logical reasoning, real-world examples, and data** to reinforce your claims.  
            - Avoid general descriptions of the topic—focus only on defending your position.  

            ---

            ### **Your Response Format:**  

            1. **Main Argument #1**  
            - Explanation  
            - Supporting Evidence or Example  

            2. **Main Argument #2**  
            - Explanation  
            - Supporting Evidence or Example  

            3. **Main Argument #3**  
            - Explanation  
            - Supporting Evidence or Example  

            Be concise yet persuasive. Provide factual support where applicable.
            """
            )

        elif step == 3:
            # 3. 반대 측 주장
            result["speaker"] = "neg"
            result["message"] = self.participant["neg"].ai_instance.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to argue against this statement.  

            ### **Instructions:**  
            - Clearly state your **position** in opposition to the topic.  
            - Provide **at least three strong arguments** against the proposition.  
            - Use **logical reasoning, real-world examples, and data** to reinforce your claims.  
            - Avoid general descriptions of the topic—focus only on presenting counterarguments.  

            ---

            ### **Your Response Format:**  

            1. **Counterargument #1**  
            - Explanation  
            - Supporting Evidence or Example  

            2. **Counterargument #2**  
            - Explanation  
            - Supporting Evidence or Example  

            3. **Counterargument #3**  
            - Explanation  
            - Supporting Evidence or Example  

            Be concise yet persuasive. Provide factual support where applicable.
            """

            )

        elif step == 4:
            # 4. 판사가 변론 준비시간 1초 제공
            result["speaker"] = "judge"
            result["message"] = "Both sides have presented their initial arguments. Take a moment to prepare for rebuttals."
            time.sleep(1)

        elif step == 5:
            # 5. 반대 측 변론
            result["speaker"] = "neg"
            result["message"] = self.participant["neg"].ai_instance.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to **counter** the arguments made by the opposing (affirmative) side.  

            ### **Instructions:**  
            - Review the **most recent supporting argument** and formulate a **logical rebuttal**.  
            - Directly address each **key point** from the affirmative side.  
            - Use **evidence, logical reasoning, and real-world examples** to dismantle their claims.  
            - Do **not** introduce new arguments against the topic—focus solely on refuting the opposition.  

            ---

            ### **Your Response Format:**  

            "I've carefully considered the affirmative argument, but I must challenge it.  

            1. **Counterargument to Point #1:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            2. **Counterargument to Point #2:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            3. **Counterargument to Point #3:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            For these reasons, the affirmative stance is not as strong as it may seem."  

            **Debate Topic:** {self.data['topic']}  
            **Previous Statements:** {self.data['debate_log'][-3]}  
            """

            )

        elif step == 6:
            # 6. 찬성 측 변론
            result["speaker"] = "pos"
            result["message"] = self.participant["pos"].ai_instance.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to **counter** the arguments made by the opposing (negative) side.  

            ### **Instructions:**  
            - Review the **most recent opposing argument** and formulate a **logical rebuttal**.  
            - Directly address each **key point** from the negative side.  
            - Use **evidence, logical reasoning, and real-world examples** to dismantle their claims.  
            - Do **not** introduce new arguments in favor of your position—focus solely on refuting the opposition.  

            ---

            ### **Your Response Format:**  

            "I've carefully considered the opposing argument, but I must challenge it.  

            1. **Counterargument to Point #1:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            2. **Counterargument to Point #2:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            3. **Counterargument to Point #3:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            For these reasons, the opposition's stance is weaker than it appears."  

            **Debate Topic:** {self.data['topic']}  
            **Previous Statements:** {self.data['debate_log'][-3]}  
            """

            )

        elif step == 7:
            # 7. 판사가 최종 주장 시간 부여
            result["speaker"] = "judge"
            result["message"] = "We are approaching the final stage of the debate. Both sides will now have the opportunity to make their concluding remarks."
            time.sleep(1)

        elif step == 8:
            # 8. 찬성 측 최종 결론
            result["speaker"] = "pos"
            result["message"] = self.participant["pos"].ai_instance.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to **deliver the final statement in support of the affirmative position**.

            ### **Instructions:**  
            - Summarize the **strongest and most compelling arguments** made in favor of this position.  
            - Reinforce why the **affirmative stance remains the most logical and justified**.  
            - Address any counterarguments and explain why they do not weaken your position.  
            - Conclude with a **clear and persuasive final statement**.

            ---

            ### **Your Response Format:**  

            "Throughout this debate, we have demonstrated why **{self.data['topic']}** is the correct stance.

            1. **Key Argument #1 Recap:**  
            - "[Summarize the most critical point in favor of the topic]"  
            - "[Why this remains valid despite counterarguments]"  

            2. **Key Argument #2 Recap:**  
            - "[Summarize another crucial point in favor of the topic]"  
            - "[Why this remains strong and unshaken]"  

            3. **Key Argument #3 Recap:**  
            - "[Summarize a final major argument]"  
            - "[Why this still holds after debate]"  

            Even when challenged, our argument stood firm because **[decisive supporting point]**.  

            Given the discussion we've had, it is clear that **{self.data['topic']}** is the most logical and justified stance."

            **Debate Topic:** {self.data['topic']}  
            **Previous Statements:** {self.data['debate_log'][:-2]}  
            """

            )

        elif step == 9:
            # 9. 반대 측 최종 결론
            result["speaker"] = "neg"
            result["message"] = self.participant["neg"].ai_instance.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to **deliver the final statement in support of the negative position**.

            ### **Instructions:**  
            - Summarize the **strongest counterarguments** presented against the topic.  
            - Emphasize why the **opposing stance remains more rational and justified**.  
            - Address the affirmative side’s claims and explain why they are insufficient.  
            - Conclude with a **strong and persuasive closing statement**.

            ---

            ### **Your Response Format:**  

            "Throughout this debate, we have made it clear why **{self.data['topic']}** is flawed and should not be accepted.

            1. **Key Counterargument #1 Recap:**  
            - "[Summarize the strongest counterpoint against the topic]"  
            - "[Why this remains valid despite rebuttals]"  

            2. **Key Counterargument #2 Recap:**  
            - "[Summarize another major counterargument]"  
            - "[Why this undermines the affirmative position]"  

            3. **Key Counterargument #3 Recap:**  
            - "[Summarize a final critical point]"  
            - "[Why this is decisive in rejecting the topic]"  

            Despite the claims made by the affirmative side, their position **[highlight why it is weak or flawed]**.  

            Given the discussion we've had, it is evident that **{self.data['topic']}** is not as justified as it seems, making the opposing stance the more reasonable conclusion."

            **Debate Topic:** {self.data['topic']}  
            **Previous Statements:** {self.data['debate_log'][:-2]}  
            """

            )

        elif step == 10:
            # 10. 판사가 판결 준비시간(1초) 부여
            result["speaker"] = "judge"
            result["message"] = "The debate has now concluded. I will take a moment to review all arguments before making a final decision."
            time.sleep(1)

        
        elif step == 11:
            # 11. 판사가 최종 결론
            result["speaker"] = "judge"
            result["message"] = self.evaluate()
            debate["status"]["type"] = "end"
        
        else:
            result["speaker"] = "SYSTEM"
            result["message"] = "The debate has already concluded."
        
        debate["debate_log"].append(result)
        result["timestamp"] = datetime.now()
        self.save()

        if step < self.max_step:
            debate["status"]["step"] += 1

        return result

    def evaluate(self) -> str:
        # Generate the evaluation text from the judge
        result_text = self.judge.ai_instance.generate_text(
            f"""Statement: {self.data['debate_log']}\n\n
            The debate has reached its final stage. It’s time to determine which side presented a stronger case.

            Let’s go over the key points made by both sides:  
            - What were the strongest arguments presented?  
            - Did they provide strong, clear, and logical reasoning?  
            - How effectively did each side counter the opposing arguments?  

            Now, based on the overall performance, we need to make a final decision.  

            Looking at the logical strength, evidence, and ability to refute opposing claims, one side **must have presented a stronger case**.  

            Now, assign a final score ensuring the total is **100**. The stronger side should have a clear advantage.  

            For example, if the affirmative side was more convincing, you might say:  
            *"After careful evaluation, it’s clear that the affirmative side provided stronger reasoning and evidence. Final Score - Pro: 65, Con: 35."*

            **Important:** Avoid neutral conclusions. The match object is used to decide a clear outcome.  

            Now, make your decision in a similar manner.
            """
        )

        match = re.search(r'Final Score\s*-\s*Pro:\s*(\d+)', result_text)
        
        if match:
            pro_score = int(match.group(1))
            if pro_score > 50:
                self.data["result"] = "positive"
            elif pro_score < 50:
                self.data["result"] = "negative"
            else:
                self.data["result"] = "draw"
        else:
            self.data["result"] = "draw"
            
        return self.data["result"]
    
