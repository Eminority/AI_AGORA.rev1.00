# AI_AGORA.rev1.00
# 1. Project Overview

## **1-1. Topic: YOLO11-Based Object Detection and AI Debate System**

<aside>

- **Technology**
    - Utilizing the YOLO11 object detection model to recognize objects and assign AI-based personalities and characteristics to them for logical debates.
    - Employing Natural Language Processing (NLP), deep learning, and reinforcement learning to generate meaningful conversations between objects and derive comprehensive conclusions.
- **Components**
    - **YOLO11**: Detects objects in images and stores object information in a database.
    - **AI Agents**: Assigned unique personalities and roles based on detected objects to participate in debates.
    - **Natural Language Processing (NLP) Model**: Generates logical conversations and debates between objects.
    - **AI Judgment System**: Analyzes debate outcomes and derives final conclusions.
- **Features**
    1. **Object Detection and Data Storage**
        - Uses YOLO11 to analyze images, converts detected objects into structured data, and stores them.
    2. **Object-Based AI Agent Generation**
        - Assigns AI-driven personalities and roles to detected objects, transforming them into interactive agents.
    3. **AI Debate Execution**
        - Conducts debates based on given topics, with each object presenting logical arguments.
    4. **AI Judgment System**
        - Analyzes the debate and automatically derives the optimal conclusion.
    5. **Results Visualization**
        - Visually represents debate content and AI judgment outcomes.
- **Key Targets**
    - AI-based simulation and debate research.
    - Development of conversational systems utilizing AI agents.
    - Research on the integration of object detection and artificial intelligence.
    - Potential applications in education, research, legal, and policy debate fields.
</aside>

## 1-2. What is a Multi-AI-Based Debate System?

1. **YOLO11 Object Detection** is used to recognize objects.
2. The recognized objects are converted into AI agents (Pro/Con).
3. Each agent possesses a unique personality based on **Natural Language Processing (NLP)** and holds an independent opinion on the debate topic.
4. The **AI Judge** analyzes the logical arguments in the debate and delivers a final verdict.

---

# 2. System Overview

## 2-1. System Process Architecture

![image.png](attachment:f68235cf-35c6-4756-a4ce-856c0a653add:image.png)

## 2-2 Data Flow Processing Method

<aside>

### **1) Data Input Stage**

1. **Image Upload from Web** → YOLO11 performs object detection.
2. Object detection results (Bounding Box & Class Label) are returned.

### **2) AI Profile Generation Stage**

1. Select the detected objects from the results.
2. **Assign AI personalities based on the selected objects.**

### **3) Debate Stage**

1. **Debate Creation**
    - **Each AI sets an initial stance on the given topic.**
    - User inputs a debate topic.
        - The debate starts only if the system deems the topic appropriate.
2. **Debate Execution**
    - AIs take turns presenting arguments and rebuttals.
    - LLM-based Natural Language Processing (NLP) is used.
    - An **LLM-based AI Judge** delivers a verdict.
3. **Debate Record Storage**
    - The logical flow of the AI arguments is recorded and analyzed.

### **4) Result Storage**

- The debate summary and final conclusions are stored in the database (DB).
</aside>

---

## **2-3 Overall Architecture Summary**

<aside>

1. **Object detection using YOLO11** → Convert detected objects into individual AI entities.
2. **Assign unique personalities and logical styles to each AI.**
3. **Conduct NLP-based debates** → Arguments and rebuttals.
4. **AI Judgment System analyzes logic and derives a final conclusion.**
5. **Provide results to the user (UI and data storage).**
</aside>

## 2-4. Test Vedio

[2025-02-19 11-56-04-cut-merged-1739935108008.mp4](attachment:6b976b9b-d6c7-454d-916d-26b90f3ed467:2025-02-19_11-56-04-cut-merged-1739935108008.mp4)

---

## **2.5 Development Stack**

### **1) Environment**

- **IDE & Interpreter**: VSCode, Python 3.10 (Anaconda)
- **Framework**: FastAPI (Jinja2, Bootstrap 4, JavaScript, HTML, CSS)

### **2) Database**

- **Primary Storage**: MongoDB (MongoDB Atlas)
- **Vector Database**: FAISS

### **3) Core Libraries**

- **Computer Vision**: Ultralytics YOLO (Object Detection)
- **Natural Language Processing**: LangChain (Ollama, Google Gemini, Groq, WikipediaRetriever, HuggingFaceEmbeddings)
- **Web Crawling**: Selenium, BeautifulSoup4

---

# 3. Project Development Details

## 3-1. Create Profile

**YOLODetect**

- Uses the YOLO11n model to detect objects in images.
- Only objects above a confidence threshold are returned as a JSON-formatted list, including object names and bounding boxes.
    
    ![output.jpg](attachment:457cb826-0469-4bd3-a23c-dcb1331fab9f:output.jpg)
    
- **ProfileManager**
    - Manages AI object profiles.
    - **`create_profile`: Profile Creation**
        - Generates an AI profile using the uploaded image, YOLO-detected objects, and the selected AI model.
        - Stores the necessary information and loads the model only when needed.
    
    ![image.png](attachment:736c6b48-88d3-439f-9bee-dcf5ab16b40b:image.png)
    

- **DetectPersona**
    - 성격 부여
    - **Assigns Personality Traits**
    1. **Assigning Personality Based on Object Information**
        - Uses WikipediaRetriever to search for information on detected objects.
        - Extracts personality traits using the Gemini model based on retrieved data.
        - The prompt includes **"Describe the personality traits of {object_name} in only 1 sentence"** to ensure concise personality descriptions.
    2. **Optimizing Personality Reflection**
        - Inserts extracted personality data at the beginning of each prompt in the **"personality:"** format.
        - Initially, the personality traits were not sufficiently reflected in AI debates.
        - To enhance their presence, the instruction **"Reflect your personality in your argument"** was added to all prompts.
    3. **Stores Personality Data in the Database**

![image.png](attachment:9960072c-3213-4819-bf5e-f9e6c891c2e8:image.png)

---

## **3-2. Debate Creation & Execution**

- **CheckTopic**
    - Module for verifying debate topics.
    - Uses the Gemini model to determine whether a given topic is suitable for debate.
    - Returns **True** if the topic is appropriate, otherwise **False**.
    - Limits `max_token` to 5 for concise responses.
- **AI Object Management Modules**
    - **ParticipantFactory**
        - Generates AI debate participants.
        - **`make_participant`**: Creates participants
            - Finds the AI model based on input data, assigns a personality, and integrates it with the VectorStore.
    - **AI_Factory**
        - Generates AI instances using pre-configured API keys.
        - **`create_ai_instance`**: Creates AI objects
            - **AI_Instance**
                - Abstract Base Class (ABC) that provides a framework for generating different AI models.
                - **`generate_text_with_vectorstore`**: Generates responses
                    - Takes VectorStore data and prompts as input to produce responses.
            - **LLM Models Used:**
                - **Gemini-2.0-flash**
                    - Accessible via API.
                    - Enhanced inference performance as of December 2024.
                - **DeepSeek-R1-Distill-Qwen-32B**
                    - Accessible via Groq API.
                    - Strong in logical reasoning and mathematical problem-solving.
                - **LLaMA-3.3-70B-Versatile**
                    - Accessible via Groq API.
                    - Supports multilingual processing, but does not officially support Korean.
                - **ExaOne-3.5: 7.8B**
                    - Accessible via Ollama.
                    - High performance in English, Korean, and long-text processing.
                - **Mistral**
                    - Accessible via Ollama.
                    - Highly efficient and lightweight.
- **DebateDataProcessor**
    - Web-crawling module for collecting debate-related information.
    - If a topic is deemed suitable, this module retrieves relevant information from the web and provides it to participating AI LLMs.
        1. Uses **Google Custom Search API** to fetch relevant news article URLs.
        2. Crawls the content of retrieved URLs using **BeautifulSoup** and **Selenium**.
        3. Stores the extracted data in a list format (`articles_data`).
- **VectorStoreHandler**
    - Embeds the crawled data and stores it in a **FAISS** vector store.
        1. Uses **RecursiveCharacterTextSplitter** (LangChain) to split text into meaningful chunks.
        2. Converts text into embeddings using **Hugging Face’s embedding model**.
        3. Stores the resulting vector embeddings in **FAISS**, an efficient large-scale vector search algorithm.
- **DebateManager**
    - **Manages & Creates Debates**
    - Maintains debates as `{id: Debate}` in `debatepool`.
    - **`create_debate`**: Creates a debate
        - Takes **positive AI profile ID, negative AI profile ID, and debate topic** as input to create a **Debate** object and register it in `debatepool`.
- **Debate**
    - **Creates & Manages Debate Sessions**
    - **`create`**: Initializes a debate
        - Assigns **positive (Pro) and negative (Con) AI participants**.
        - **Pro & Con AI Agents**:
            - Generate logical arguments & rebuttals using **LLM models**.
            - Reflect distinct personalities in debate responses.
        - **Judge AI**:
            - Uses **Gemini** to **evaluate debates neutrally**.
            - Implements predefined **prompt engineering techniques** for fair judgment.
            - Initially used **`set_role`** to predefine roles (Pro, Con, Judge).
            - Later improved to **dynamically adjust roles based on debate progress**.
    - **`progress`**: Controls debate flow
        - Manages debate state using the **step variable** stored in MongoDB.
        - Logs AI-generated arguments in the **debate log** for transparency.

- **evaluate: debate judgement**
    - **Analyzes the debate log (debate) to determine the final winner:**
        - AI summarizes the debate and assesses the strengths of both sides.
        - A score-based judgment system is implemented.
    
    ### **How the Judgment System Works**
    
    A structured **evaluation system** ensures fairness in determining debate outcomes.
    
    - **The affirmative (Pro) side wins if its score exceeds 50.**
    - **The opposing (Con) side wins if the Pro score is below 50.**
    - **If the Pro score is exactly 50, the debate results in a tie.**
    
    A simple and clear scoring mechanism is established to maintain objectivity.
    
    ---
    
    ### **1. Judgment Algorithm Design**
    
    To ensure fairness, a **score-based evaluation system** is implemented:
    
    - **Pro Score > 50 → Affirmative (Pro) Wins**
    - **Pro Score < 50 → Opposing (Con) Wins**
    - **Pro Score = 50 → Draw**
    
    ---
    
    ### **2. Scoring Criteria**
    
    - Scores are determined based on **logical consistency, credibility of evidence, and effectiveness of rebuttals**.
    - Both Pro and Con arguments are assessed to provide a balanced judgment.
    
    ---
    
    ### **3. Example Final Verdicts**
    
    ### **Example 1: Pro Wins**
    
    ```python
    "After careful evaluation, it’s clear that the affirmative side provided stronger reasoning and evidence.
    Final Score - Pro: 65, Con: 35."
    ```
    
    - **Interpretation:** Pro score **65** > 50 → **Affirmative Wins**
    
    ### **Example 2: Con Wins**
    
    ```python
    "After thorough analysis, the opposing side demonstrated superior arguments and rebuttals.
    Final Score - Pro: 42, Con: 58."
    ```
    
    - **Interpretation:** Pro score **42** < 50 → **Opposing Wins**
    
    ### **Example 3: Draw**
    
    ```python
    "Both sides presented equally compelling arguments, leading to a balanced conclusion.
    Final Score - Pro: 50, Con: 50."
    ```
    
    - **Interpretation:** Pro score **50** → **Draw**
    
    ### **Final Insights**
    
    - Moves beyond simple role assignment by **clearly defining roles and guidelines at each debate stage**.
    - Leverages multiple **prompting techniques** to ensure **logical, structured, and engaging debates**.
    - Optimizes the **AI’s personality and role-based argumentation**, leading to more convincing and well-structured debates.
    
    ![image.png](attachment:cab3ae76-5815-4742-93ec-c82dfeb2b93b:image.png)
    

![image.png](attachment:6372df91-eab4-4730-8603-34540fe75aaa:image.png)

**load, save: Data Management**

- Continuously updates debate data in **real-time**.
- Stores the final verdict in the database after the debate concludes.
- Tracks the progress of a specific debate using the **debate[_id]** value.
- The final verdict is stored in the following format.

- **Prompt Engineering**
    - Example of Used Prompt:

```python
  f"""
  You are participating in a debate on the topic: **"{self.debate['topic']}"**. Your role is to **counter** the arguments made by the opposing (affirmative) side.  

  ### **Instructions:**  
  - Review the **most recent supporting argument** and formulate a **logical rebuttal**.  
  - Directly address each **key point** from the affirmative side.  
  - Use **evidence, logical reasoning, and real-world examples** to dismantle their claims.  
  - Do **not** introduce new arguments against the topic—focus solely on refuting the opposition.  
  - **Reflect your personality in your argument**
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
```

- **Prompt Engineering Techniques Used**
    1. **Role-based Prompting**
        - Instructs the AI to take on a specific role.
        - **Application:**
            - `"You are participating in a debate... Your role is to **counter** the arguments made by the opposing (affirmative) side."`
            - Ensures that the AI maintains a consistent perspective when generating responses.
    2. **Few-shot Prompting**
        - Provides examples or structured formats to guide AI responses.
        - **Application:**
            - `"For these reasons, the affirmative stance is not as strong as it may seem."`
            - The AI follows a structured response format, ensuring coherence and logical flow.
    3. **Counterargument Prompting**
        - Directs the AI to summarize and rebut opposing claims logically.
        - **Application:**
            - `"Summary of the opposing claim: "[summary of the opposing argument]""`
            - `"Logical refutation: "[why this argument is flawed or incorrect]""`
            - `"Supporting evidence or example: "[real-world data or logical reasoning]""`
            - Encourages structured, evidence-based counterarguments rather than mere opinions.
    4. **Explicit Instruction Prompting**
        - Clearly outlines the debate format and response guidelines.
        - **Application:**
            - `"### **Instructions:**"`
            - Provides explicit directives such as:
                - `"Directly address each key point from the affirmative side."`
                - `"Use evidence, logical reasoning, and real-world examples."`
                - `"Do not introduce new arguments against the topic—focus solely on refuting the opposition."`
    5. **Context-aware Prompting**
        - Integrates previous debate statements to ensure contextual consistency.
        - **Application:**
            - `"**Previous Statements:** {self.debate['debate_log'][-3]}"`
            - Encourages the AI to reference earlier arguments and maintain logical continuity.
    6. **Incremental Prompting**
        - Guides the AI step by step in building a logical response.
        - **Application:**
            - `"1. **Counterargument to Point #1:**"`
            - `"2. **Counterargument to Point #2:**"`
            - `"3. **Counterargument to Point #3:**"`
            - This structure helps AI present arguments in a progressive and organized manner.
    7. **Guided Prompting**
        - Restricts the AI’s responses within a predefined scope.
        - **Application:**
            - `"Do **not** introduce new arguments against the topic—focus solely on refuting the opposition."`
            - Prevents deviation from the core rebuttal task.
    8. **Structured Output Prompting**
        - Ensures AI follows a specific response format.
        - **Application:**
            - `"### **Your Response Format:**"`
            - Provides a rigid structure that promotes clear and structured debate responses.
    9. **Summary Prompting**
        - Requires AI to summarize the opponent’s argument before rebutting.
        - **Application:**
            - `"Summary of the opposing claim: "[summary of the opposing argument]""`
            - Helps in maintaining a logical and structured counterargument.
    

<aside>

### **< 11-Step Debate Progression >**

1. **Judge introduces the topic**
2. **Pro side presents their argument**
3. **Con side presents their argument**
4. **Judge allows time for rebuttal preparation**
5. **Con side presents rebuttal**
6. **Pro side presents rebuttal**
7. **Judge grants final argument time**
8. **Pro side delivers final argument**
9. **Con side delivers final argument**
10. **Judge evaluates and prepares final decision**
11. **Judge announces the final verdict**
</aside>

---

## **3-3. Storage Method**

- **MongoDBConnection**
    - Creates and registers a MongoClient object based on a configured URI.
    - Accepts collections and data for searching, inserting, and updating information.
    - Uses JSON-based storage, allowing flexible data transformation.

---

# **4. Future Improvements & Expansion Potential**

## **4-1. Improvements**

- **Reducing Debate Loading Time**
    - Pre-loads the topic and initiates the debate on the server before the user enters the debate page.
    - Adds a typing effect to make the debate appear more natural.
- **Enhancing Judgment Criteria**
    - Implements logic benchmarks and standardized debate evaluation criteria.
- **Code Optimization**
    - The current code structure is complex.
    - Plans to modularize or integrate roles for better clarity.
- **More Flexible System Design**
    - Currently, processes, roles, and AI instance counts are fixed.
    - Future designs will allow automatic adaptation based on the debate topic.

## **4.2 Expansion Potential**

### **1) Utilizing Generative AI**

- Adds a feature for generating profile pictures using Image-to-Image generative AI.

### **2) Image-to-Text Model Implementation**

- Enables prior knowledge learning through image-based processing.

### **3) Virtual Character Creation**

- Develops AI-generated virtual characters for debate participation.
    - Allows speech and personality injection based on specific figures.

### **4) AI Reinforcement Learning**

- Automates debates to refine logical argumentation styles in LLMs.

### **5) Multi-AI Debate**

- Currently, the system consists of three AI roles: Pro, Con, and Judge.
    - Future updates may allow multiple AIs to participate simultaneously.

### **6) AI Agent Expansion**

- The debate currently follows a predefined algorithm.
- Expands the system to allow AI agents to determine the next speaker dynamically.

### **7) Complex Reasoning Model**

- Develops an advanced reasoning model where multiple AIs debate to derive conclusions.
- Each AI contributes arguments based on its assigned role to reach a final decision.

4o

---

# **5. Project Retrospective**

## **The Importance of Technology Integration and Scalability**

This project required the seamless integration of various technologies, including object detection, AI interactions, and AI model comparisons. From YOLO11n-based object detection to the integration of RAG, GEMINI, Ollama, Deepseek-R1, and GPT-3.5 Turbo, I once again realized the importance of designing an architecture that prioritizes scalability and maintainability.

## **Optimization of Data Storage and Management**

While using MongoDB to store object detection and AI inference results, I found that as the volume of data increased, optimizing search speed and storage structure became crucial. Particularly, as logs for AI model comparisons accumulated, indexing and query optimization became essential challenges, reinforcing the need for a flexible database design.

## **Real-time System Performance Optimization**

Since the system required real-time interactions between object detection and AI, improving response speed was a critical task. To achieve this, I implemented asynchronous API processing, caching, and model loading optimizations. This experience reaffirmed that improving performance is not just about raw speed but about ensuring users perceive a fast and seamless experience.

## **Challenges and Growth as a Project Manager**

As the project manager, I took on responsibilities beyond backend development, including schedule management, technical direction setting, and establishing a collaborative environment. Initially, the team started with six members, but as the project progressed, only three remained.

During this transition, I faced challenges such as the burden of quickly acquiring and sharing key technologies, redistributing roles among remaining team members, and making strategic decisions to minimize delays. To keep the team motivated while ensuring project continuity, I streamlined workflows, prioritized essential features, and implemented practical solutions.

Through this experience, I learned that rather than simply increasing development speed, risk management and maximizing team capabilities are far more important. Additionally, I realized that long-term maintainability and scalability ultimately determine a project's success.
