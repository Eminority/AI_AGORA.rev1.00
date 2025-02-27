import time
from datetime import datetime
from crewai import Agent, Task, Crew
import re
from pathlib import Path
from dotenv import load_dotenv
import os
from crewai.llm import LLM
class Debate_2_CrewAI:
    """
    Debate management class using crewai for agent-based orchestration.
    Agents: judge, pos (affirmative), neg (negative).
    Tasks: Each debate step is a task executed by the respective agent.
    Crew: Orchestrates the debate process.
    """
    def __init__(self, participant: dict, generate_text_config: dict, data: dict = None):
        # participant: {"judge": Participant, "pos": Participant, "neg": Participant}
        # generate_text_config: {"max_tokens": int, "k": int, "temperature": float}
        self.max_step = 11  # Total 11 steps in the debate
        self.generate_text_config = generate_text_config
        env_path = Path(__file__).resolve().parent.parent / "src" / ".env"
        load_dotenv(dotenv_path=env_path, override=True)

        # 환경 변수에서 AI_API_KEY 가져오기
        ai_api_key_str = os.getenv("AI_API_KEY")

        # Initialize debate data
        self.data = data if data else {
            "participants": None,
            "topic": None,
            "status": {"type": None, "step": 0},
            "debate_log": [],
            "start_time": None,
            "end_time": None,
            "summary": {"summary_pos": None, "summary_neg": None, "summary_arguments": None, "summary_verdict": None},
            "result": None
        }

        # Define Agents
        self.agents = {
            "judge": Agent(
                role="Debate Judge",
                goal="Facilitate the debate neutrally and evaluate arguments.",
                backstory="An impartial expert in debate moderation and logical analysis.",
                verbose=True,
                allow_delegation=False
            ),
            "pos": Agent(
                role="Affirmative Debater",
                goal="Argue in favor of the debate topic persuasively.",
                backstory="A skilled advocate supporting the affirmative stance.",
                verbose=True,
                allow_delegation=False
            ),
            "neg": Agent(
                role="Negative Debater",
                goal="Argue against the debate topic convincingly.",
                backstory="A proficient debater opposing the topic.",
                verbose=True,
                allow_delegation=False
            )
        }

    def generate_text(self, speaker: str, prompt: str) -> str:
        """Simulate text generation (replace with actual AI model call if needed)."""
        # Here, you’d typically call an AI model with generate_text_config.
        # For this example, we'll assume it's handled by crewai's agent's internal logic.
        return f"{speaker} response to: {prompt[:50]}..."

    def progress(self) -> dict:
        """Execute the debate steps as tasks managed by a Crew."""
        debate = self.data
        step = debate["status"]["step"]
        result = {"timestamp": None, "speaker": "", "message": "", "step": step}

        if debate.get("_id") is None:
            result.update({"speaker": "SYSTEM", "message": "Invalid debate.", "timestamp": datetime.now()})
            return result

        if step == 0:
            debate["status"]["step"] = 1
            step = 1

        # Define tasks based on the current step
        tasks = []
        if step == 1:
            tasks.append(Task(
                description=f"Introduce the debate topic: '{debate['topic']}' neutrally and invite the affirmative side.",
                agent=self.agents["judge"],
                expected_output=f"""
                Introduction: "{debate['topic']} is a widely debated issue..."
                Prompting: "Let’s hear from the affirmative side..."
                """
            ))
        elif step == 2:
            tasks.append(Task(
                description=f"Present three strong arguments in favor of '{debate['topic']}'.",
                agent=self.agents["pos"],
                expected_output="1. Main Argument #1...\n2. Main Argument #2...\n3. Main Argument #3..."
            ))
        elif step == 3:
            tasks.append(Task(
                description=f"Present three strong counterarguments against '{debate['topic']}'.",
                agent=self.agents["neg"],
                expected_output="1. Counterargument #1...\n2. Counterargument #2...\n3. Counterargument #3..."
            ))
        elif step == 4:
            tasks.append(Task(
                description="Grant a 1-second preparation time for rebuttals.",
                agent=self.agents["judge"],
                expected_output="Both sides have presented their arguments. Prepare for rebuttals."
            ))
        elif step == 5:
            tasks.append(Task(
                description=f"Rebut the affirmative arguments for '{debate['topic']}' based on: {debate['debate_log'][-3]}.",
                agent=self.agents["neg"],
                expected_output="Counterargument to Point #1...\nCounterargument to Point #2...\nCounterargument to Point #3..."
            ))
        elif step == 6:
            tasks.append(Task(
                description=f"Rebut the negative arguments for '{debate['topic']}' based on: {debate['debate_log'][-3]}.",
                agent=self.agents["pos"],
                expected_output="Counterargument to Point #1...\nCounterargument to Point #2...\nCounterargument to Point #3..."
            ))
        elif step == 7:
            tasks.append(Task(
                description="Announce the final statement phase with a 1-second pause.",
                agent=self.agents["judge"],
                expected_output="Both sides will now make their concluding remarks."
            ))
        elif step == 8:
            tasks.append(Task(
                description=f"Deliver a final affirmative conclusion for '{debate['topic']}' based on: {debate['debate_log'][:-2]}.",
                agent=self.agents["pos"],
                expected_output="Key Argument #1 Recap...\nKey Argument #2 Recap...\nKey Argument #3 Recap..."
            ))
        elif step == 9:
            tasks.append(Task(
                description=f"Deliver a final negative conclusion for '{debate['topic']}' based on: {debate['debate_log'][:-2]}.",
                agent=self.agents["neg"],
                expected_output="Key Counterargument #1 Recap...\nKey Counterargument #2 Recap...\nKey Counterargument #3 Recap..."
            ))
        elif step == 10:
            tasks.append(Task(
                description="Announce a 1-second pause for final evaluation.",
                agent=self.agents["judge"],
                expected_output="The debate has concluded. I will review all arguments."
            ))
        elif step == 11:
            tasks.append(Task(
                description="Evaluate the debate and deliver the final verdict.",
                agent=self.agents["judge"],
                expected_output=self.evaluate()['result']
            ))
        else:
            result.update({"speaker": "SYSTEM", "message": "The debate has already concluded."})
            debate["debate_log"].append(result)
            return result

        # Create and run the Crew
        crew = Crew(agents=list(self.agents.values()), tasks=tasks, verbose=True)
        output = crew.kickoff()

        # Process the task output
        result["speaker"] = tasks[0].agent.role.split()[1].lower()  # e.g., "judge", "pos", "neg"
        result["message"] = output if isinstance(output, str) else str(output)
        result["timestamp"] = datetime.now()

        if step in [4, 7, 10]:  # Steps with a 1-second pause
            time.sleep(1)

        debate["debate_log"].append(result)
        if step < self.max_step:
            debate["status"]["step"] += 1
        if step == 11:
            debate["status"]["type"] = "end"

        return result

    def evaluate(self) -> dict:
        """Evaluate the debate using crewai agents for logicality, rebuttal, and persuasion."""
        pos_log = next((msg for msg in self.data["debate_log"] if msg["speaker"] == "pos"), None)
        neg_log = next((msg for msg in self.data["debate_log"] if msg["speaker"] == "neg"), None)
        pos_rebuttal = next((msg for msg in self.data["debate_log"] if msg["step"] == 6), None)
        neg_rebuttal = next((msg for msg in self.data["debate_log"] if msg["step"] == 5), None)

        # Define evaluation agents
        eval_agents = {
            "logicality": Agent(
                role="Logicality Evaluator",
                goal="Assess the logical soundness of arguments.",
                backstory="An expert in logical reasoning.",
                verbose=True
            ),
            "rebuttal": Agent(
                role="Rebuttal Evaluator",
                goal="Evaluate the strength of rebuttals.",
                backstory="Specialist in counterargument analysis.",
                verbose=True
            ),
            "persuasion": Agent(
                role="Persuasion Evaluator",
                goal="Assess the persuasiveness of arguments.",
                backstory="Expert in rhetorical effectiveness.",
                verbose=True
            )
        }

        # Define evaluation tasks
        tasks = [
            Task(
                description=f"Evaluate logical soundness of pos: {pos_log} and neg: {neg_log}.",
                agent=eval_agents["logicality"],
                expected_output="Passage 1 Score (pos): X\nPassage 2 Score (neg): Y"
            ),
            Task(
                description=f"Evaluate rebuttal strength of pos: {pos_rebuttal} and neg: {neg_rebuttal}.",
                agent=eval_agents["rebuttal"],
                expected_output="Rebuttal 1 Score (pos): X\nRebuttal 2 Score (neg): Y"
            ),
            Task(
                description=f"Evaluate persuasiveness of pos: {pos_log} and neg: {neg_log}.",
                agent=eval_agents["persuasion"],
                expected_output="Passage 1 Score (pos): X\nPassage 2 Score (neg): Y"
            )
        ]

        # Run evaluation crew
        eval_crew = Crew(agents=list(eval_agents.values()), tasks=tasks, verbose=2)
        eval_results = eval_crew.kickoff()

        # Extract scores (simplified for this example; adjust based on actual output parsing)
        def extract_score(pattern, text):
            match = re.search(pattern, str(text))
            return int(match.group(1)) if match else 0

        logicality_pos = extract_score(r"Passage 1 Score \(pos\): (\d+)", eval_results[0])
        logicality_neg = extract_score(r"Passage 2 Score \(neg\): (\d+)", eval_results[0])
        rebuttal_pos = extract_score(r"Rebuttal 1 Score \(pos\): (\d+)", eval_results[1])
        rebuttal_neg = extract_score(r"Rebuttal 2 Score \(neg\): (\d+)", eval_results[1])
        persuasion_pos = extract_score(r"Passage 1 Score \(pos\): (\d+)", eval_results[2])
        persuasion_neg = extract_score(r"Passage 2 Score \(neg\): (\d+)", eval_results[2])

        # Calculate final scores
        weights = {"logicality": 0.4, "rebuttal": 0.35, "persuasion": 0.25}
        match_pos = (logicality_pos * weights["logicality"] + rebuttal_pos * weights["rebuttal"] + persuasion_pos * weights["persuasion"])
        match_neg = (logicality_neg * weights["logicality"] + rebuttal_neg * weights["rebuttal"] + persuasion_neg * weights["persuasion"])

        # Determine result
        self.data["result"] = "draw" if match_pos == match_neg else ("positive" if match_pos > match_neg else "negative")
        
        return {
            "result": self.data["result"],
            "logicality_pos": logicality_pos,
            "logicality_neg": logicality_neg,
            "rebuttal_pos": rebuttal_pos,
            "rebuttal_neg": rebuttal_neg,
            "persuasion_pos": persuasion_pos,
            "persuasion_neg": persuasion_neg,
            "match_pos": match_pos,
            "match_neg": match_neg
        }

# Example usage
# if __name__ == "__main__":
#     debate = Debate_2(
#         participant={"judge": None, "pos": None, "neg": None},
#         generate_text_config={"max_tokens": 500, "k": 50, "temperature": 0.7},
#         data={"topic": "AI should replace teachers", "_id": "123"}
#     )
#     for _ in range(debate.max_step):
#         result = debate.progress()
#         print(f"Step {result['step']}: {result['speaker']} - {result['message']}")