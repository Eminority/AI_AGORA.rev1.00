import uuid
import time
from datetime import datetime
from db_module import MongoDBConnection
from .participants import ParticipantFactory
from .agora_ai import Agora_AI
from vectorstore_module import VectorStoreHandler
from crawling import DebateDataProcessor
import re

class Debate:
    def __init__(self, participant_factory: ParticipantFactory, debate_data_processor:DebateDataProcessor, db_connection: MongoDBConnection):
        self.judge = None
        self.pos = None
        self.neg = None
        self.db_connection = db_connection
        self.participant_factory = participant_factory
        self.debate_data_processor = debate_data_processor

        # debate 필드 초기화
        self.debate = {
            "participants": None,
            "topic": None,
            "status": {
                "type": None,  # "in_progress" 또는 "end" 등
                "step": 0,     # 1부터 11까지 단계
                "turn": None
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

        # 총 11단계 진행
        self.max_step = 11

    def set_judge(self):
        """판사 역할의 AI 인스턴스 생성 및 역할 설정"""
        gemini_instance = self.participant_factory.ai_factory.create_ai_instance("GEMINI")
        self.judge = Agora_AI(ai_type="GEMINI", ai_instance=gemini_instance, vector_handler=self.participant_factory.vector_handler)
#        self.judge.set_role("judge")

    def create(self, topic: str, participants: dict):
        """
        토론 생성: 새로운 토론(_id, topic, participants 등) 정보를 세팅하고
        DB에 저장한 뒤, 판사와 참가자들을 준비합니다.
        """
        if self.debate.get("_id") is not None or not participants:
            return False

        self.debate["topic"] = topic
        self.debate["participants"] = participants
        self.debate["status"] = {
            "type": "in_progress",  # 토론을 시작할 때 바로 in_progress로 설정
            "step": 1,              # 1단계부터 진행
            "turn": None
        }

        # _id 필드를 UUID로 생성하여 할당
        # create에 집어넣으면 자동으로 id 찍혀나오니까 생략해보기
        # self.debate["_id"] = str(uuid.uuid4())

        # DB에 삽입 후 실제 _id(또는 ObjectId) 값을 debate dict에 반영
        debate_id = self.db_connection.insert_data("debate",self.debate)
        self.debate["_id"] = debate_id
        # 참가자 생성 (pos, neg)
        self.pos = self.participant_factory.make_participant(participants["pos"])
        self.neg = self.participant_factory.make_participant(participants["neg"])

        # 판사 생성 및 등록
        self.set_judge()

        return True

    def progress(self):
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
        debate = self.debate
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
            self.ready_to_debate()
            result["speaker"] = "judge"
            result["message"] = self.judge.generate_text(
                f"""
                You are facilitating a debate on the topic: **"{self.debate['topic']}"**. Your role is to introduce the discussion in a neutral manner, providing a brief, informative introduction to the topic without taking any stance.  

                ### **Instructions:**
                - Start by giving a **concise, objective summary** of the topic.
                - Avoid personal opinions or taking a side.
                - After introducing the topic, **invite the affirmative side to present their argument first**.

                ---

                ### **Example Structure**:

                **Introduction:**  
                "{self.debate['topic']} is a widely debated issue with strong arguments on both sides. Supporters argue that  [Key argument of the affirmative side], while opponents believe that [Key argument of the negative side]. The discussion often revolves around factors such as [2-3 key points of debate]. Today, we will explore both perspectives in depth."

                **Prompting the Affirmative Side:**  
                "To begin, let's hear from the **affirmative side**. Please present your argument in support of {self.debate['topic']}. What are the key reasons and evidence supporting your stance?"

                """
            )

        elif step == 2:
            # 2. 찬성 측 주장
            result["speaker"] = "pos"
            result["message"] = self.pos.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.debate['topic']}"**. Your role is to argue in favor of this statement.  

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
            result["message"] = self.neg.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.debate['topic']}"**. Your role is to argue against this statement.  

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
            result["message"] = self.neg.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.debate['topic']}"**. Your role is to **counter** the arguments made by the opposing (affirmative) side.  

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

            **Debate Topic:** {self.debate['topic']}  
            **Previous Statements:** {self.debate['debate_log'][-3]}  
            """

            )

        elif step == 6:
            # 6. 찬성 측 변론
            result["speaker"] = "pos"
            result["message"] = self.pos.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.debate['topic']}"**. Your role is to **counter** the arguments made by the opposing (negative) side.  

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

            **Debate Topic:** {self.debate['topic']}  
            **Previous Statements:** {self.debate['debate_log'][-3]}  
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
            result["message"] = self.pos.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.debate['topic']}"**. Your role is to **deliver the final statement in support of the affirmative position**.

            ### **Instructions:**  
            - Summarize the **strongest and most compelling arguments** made in favor of this position.  
            - Reinforce why the **affirmative stance remains the most logical and justified**.  
            - Address any counterarguments and explain why they do not weaken your position.  
            - Conclude with a **clear and persuasive final statement**.

            ---

            ### **Your Response Format:**  

            "Throughout this debate, we have demonstrated why **{self.debate['topic']}** is the correct stance.

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

            Given the discussion we've had, it is clear that **{self.debate['topic']}** is the most logical and justified stance."

            **Debate Topic:** {self.debate['topic']}  
            **Previous Statements:** {self.debate['debate_log'][:-2]}  
            """

            )

        elif step == 9:
            # 9. 반대 측 최종 결론
            result["speaker"] = "neg"
            result["message"] = self.neg.generate_text(
            f"""
            You are participating in a debate on the topic: **"{self.debate['topic']}"**. Your role is to **deliver the final statement in support of the negative position**.

            ### **Instructions:**  
            - Summarize the **strongest counterarguments** presented against the topic.  
            - Emphasize why the **opposing stance remains more rational and justified**.  
            - Address the affirmative side’s claims and explain why they are insufficient.  
            - Conclude with a **strong and persuasive closing statement**.

            ---

            ### **Your Response Format:**  

            "Throughout this debate, we have made it clear why **{self.debate['topic']}** is flawed and should not be accepted.

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

            Given the discussion we've had, it is evident that **{self.debate['topic']}** is not as justified as it seems, making the opposing stance the more reasonable conclusion."

            **Debate Topic:** {self.debate['topic']}  
            **Previous Statements:** {self.debate['debate_log'][:-2]}  
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

    def ready_to_debate(self):
        """
        참가자와 판사가 토론 주제에 대해 자료를 수집 및 준비하는 함수.
        크롤링과 벡터 스토어 생성은 한 번만 수행한 후,
        그 결과(크롤링 데이터와 벡터스토어)를 모든 참가자에게 공유한다.
        """
        topic = self.debate["topic"]
        shared_crawled_data = None
        shared_vectorstore = None

        # [1] 한 참가자(우선순위: pos → neg → judge)를 통해 크롤링 및 벡터 스토어 생성
        
        if self.pos and hasattr(self.pos, 'agora_ai'):
            self.pos.agora_ai.crawling(debate_processor=self.debate_data_processor,topic=topic)
            shared_crawled_data = self.pos.agora_ai.crawled_data
            shared_vectorstore = self.pos.agora_ai.vectorstore

        elif self.neg and hasattr(self.neg, 'agora_ai'):
            self.neg.agora_ai.crawling(debate_processor=self.debate_data_processor,topic=topic)
            shared_crawled_data = self.neg.agora_ai.crawled_data
            shared_vectorstore = self.neg.agora_ai.vectorstore

        elif self.judge:
            if hasattr(self.judge, 'agora_ai'):
                self.judge.agora_ai.crawling(debate_processor=self.debate_data_processor,topic=topic)
                shared_crawled_data = self.judge.agora_ai.crawled_data
                shared_vectorstore = self.judge.agora_ai.vectorstore
            else:
                if hasattr(self.judge, 'crawling'):
                    self.judge.crawling(debate_processor=self.debate_data_processor,topic=topic)
                # getattr를 사용해 속성이 없으면 None을 기본값으로 사용
                shared_crawled_data = getattr(self.judge, 'crawled_data', None)
                shared_vectorstore = getattr(self.judge, 'vectorstore', None)
        else:
            print("[ERROR] 크롤링을 수행할 참가자가 없습니다.")
            return  # 더 이상 진행할 수 없으므로 함수 종료

        # [2] 크롤링 및 벡터 스토어 생성 결과를 모든 참가자에게 공유
        if shared_crawled_data is not None and shared_vectorstore is not None:
            # POS 공유
            if self.pos and hasattr(self.pos, 'agora_ai'):
                self.pos.agora_ai.crawled_data = shared_crawled_data
                self.pos.agora_ai.vectorstore = shared_vectorstore

            # NEG 공유
            if self.neg and hasattr(self.neg, 'agora_ai'):
                self.neg.agora_ai.crawled_data = shared_crawled_data
                self.neg.agora_ai.vectorstore = shared_vectorstore
            # JUDGE 공유
            if self.judge:
                if hasattr(self.judge, 'agora_ai'):
                    self.judge.agora_ai.crawled_data = shared_crawled_data
                    self.judge.agora_ai.vectorstore = shared_vectorstore
                else:
                    self.judge.crawled_data = shared_crawled_data
                    self.judge.vectorstore = shared_vectorstore
        else:
            print("크롤링이나 벡터 스토어 생성에 실패하여, 결과를 공유할 수 없습니다.")


    # def evaluate(self):
    #     """판사가 최종 판결문(결론)을 생성하고, 토론 내용을 요약"""
    #     self.debate["result"] = self.judge.generate_text(f"Statement: {self.debate['debate_log']} Judge's final verdict: First, explain the reason for the winner. Then, provide the final ruling: either 'positive' or 'negative'.")
    #     self.summarize()
    #     return self.debate["result"]

    def evaluate(self):
        # Generate the evaluation text from the judge
        result_text = self.judge.generate_text(
            f"""Statement: {self.debate['debate_log']}\n\n
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
                self.debate["result"] = "positive"
            elif pro_score < 50:
                self.debate["result"] = "negative"
            else:
                self.debate["result"] = "draw"
        else:
            self.debate["result"] = "draw"
            
        return self.debate["result"]
    

    def load(self):
        """데이터베이스에서 저장된 토론 정보를 불러와 현재 객체에 저장"""
        try:
            self.debate = self.db_connection.select_data_from_id("debate", self.debate["_id"])
        except Exception as e:
            print("load failed:", e)
            return False
        return True

    def save(self):
        """현재 토론 상태를 데이터베이스에 업데이트하여 저장"""
        self.db_connection.update_data("debate", self.debate)
