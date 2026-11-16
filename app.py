import streamlit as st
from pathlib import Path
import pandas as pd
import re

from resume_parser import extract_text_from_pdf
from ats_scoring import calculate_ats_score
from jd_matcher import extract_skills


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Resume Screening with RAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "required_skills" not in st.session_state:
    st.session_state.required_skills = []

if "screening_error" not in st.session_state:
    st.session_state.screening_error = ""


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0e1117;
    }

    .main-title {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2px;
    }

    .subtitle {
        font-size: 15px;
        color: #9ca3af;
        margin-bottom: 15px;
    }

    section[data-testid="stSidebar"] {
        background-color: #181b23;
    }

    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 15px;
    }

    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 42px;
    }

    .section-title {
        font-size: 26px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🤖 AI Resume Screening System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'RAG-powered Resume Screening • ATS Scoring • Candidate Ranking • '
    'Analytics • AI Chatbot'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Settings")

    with st.form('resume_folder_form'):
        
        resume_folder = st.text_input(
        "Resume Folder",
        value="resumes",
        help= "Enter the folder patrh and press enter to start screening."

        )
        
        auto_screen_button = st.form_submit_button(
        "Apply Folder & Screen Resumes",
        use_container_width= True
        
        )

    if auto_screen_button:

        st.success(f"Resume folder set to: {resume_folder}")

    st.divider()

    st.subheader("🔄 Screening Pipeline")

    st.write("📄 Resume Parsing")
    st.write("🧩 Text Extraction")
    st.write("🧠 RAG Retrieval")
    st.write("🎯 Skill Matching")
    st.write("📊 ATS Scoring")
    st.write("🏆 Candidate Ranking")

    st.divider()

    st.subheader("📌 Shortlisting Rule")

    st.info(
        "Candidates with ATS Score ≥ 70% are considered shortlisted."
    )

    st.divider()

    if st.button(
        "🗑️ Clear All",
        use_container_width=True
    ):

        st.session_state.results = []
        st.session_state.chat_history = []
        st.session_state.required_skills = []
        st.session_state.screening_error = ""

        st.rerun()


# ============================================================
# MAIN SCREENING AREA
# ============================================================

left, right = st.columns(
    [1, 2],
    gap="large"
)


# ============================================================
# LEFT COLUMN
# ============================================================

with left:

    st.subheader("📋 Job Description")

    jd_text = st.text_area(
        "Enter Job Description",
        height=300,
        placeholder="""Example:

Python Developer

We are looking for a Python Developer
with 2+ years of experience.

Required Skills:

Python
SQL
Pandas
NumPy
Machine Learning
Power BI
Deep Learning
ANN
CNN
NLP
LLM
llama
GENAI
Git
GitHub
Hugging Face

Good analytical and problem-solving skills.""",
        label_visibility="collapsed"
    )

    st.write("")

    st.subheader("📁 Resume Folder")

    resume_path = Path(resume_folder)

    # ========================================================
    # FIND RESUMES
    # ========================================================

    if not resume_path.exists():

        st.warning(
            f"⚠️ Resume folder '{resume_folder}' does not exist."
        )

        st.info(
            "Create a 'resumes' folder and place PDF resumes inside it."
        )

        resume_files = []

    else:

        resume_files = sorted(
            resume_path.glob("*.pdf")
        )

        if not resume_files:

            st.warning(
                "⚠️ No PDF resumes found."
            )

        else:

            st.success(
                f"✅ {len(resume_files)} resumes found"
            )

    # ========================================================
    # SELECT RESUMES
    # ========================================================

    if resume_files:

        selected_resumes = st.multiselect(
            "Select resumes",
            resume_files,
            default=resume_files,
            format_func=lambda file: file.name
        )

    else:

        selected_resumes = []

    st.write("")

    # ========================================================
    # SCREEN BUTTON
    # ========================================================

    manual_screen_button = st.button(
        
        "🔍 SCREEN RESUMES",
        type="primary",
        use_container_width=True

    )

    screen_button = (

        auto_screen_button or manual_screen_button
        
    )


# ============================================================
# SCREEN RESUMES
# ============================================================

if screen_button:

    # ========================================================
    # VALIDATION
    # ========================================================

    if not jd_text.strip():

        st.session_state.screening_error = (
            "⚠️ Please enter a Job Description before screening resumes."
        )

    elif not selected_resumes:

        st.session_state.screening_error = (
            "⚠️ Please select at least one resume."
        )

    else:

        st.session_state.screening_error = ""

        # ====================================================
        # EXTRACT JOB DESCRIPTION SKILLS
        # ====================================================

        try:

            required_skills = extract_skills(
                jd_text
            )

            st.session_state.required_skills = (
                required_skills
            )

        except Exception as error:

            st.session_state.screening_error = (
                f"❌ JD skill extraction error: {error}"
            )

            st.session_state.required_skills = []

        # ====================================================
        # SCREENING
        # ====================================================

        if st.session_state.required_skills:

            results = []

            progress = st.progress(0)

            status = st.empty()

            for index, resume_file in enumerate(
                selected_resumes
            ):

                status.write(
                    f"🔍 Processing {resume_file.name}..."
                )

                # =============================================
                # EXTRACT RESUME TEXT
                # =============================================

                try:

                    resume_text = extract_text_from_pdf(
                        str(resume_file)
                    )

                except Exception as error:

                    st.warning(
                        f"Could not read {resume_file.name}: {error}"
                    )

                    progress.progress(
                        (index + 1) /
                        len(selected_resumes)
                    )

                    continue

                if not resume_text:

                    st.warning(
                        f"No text found in {resume_file.name}"
                    )

                    progress.progress(
                        (index + 1) /
                        len(selected_resumes)
                    )

                    continue

                # =============================================
                # ATS SCORING
                # =============================================

                try:

                    ats_result = calculate_ats_score(
                        resume_text,
                        st.session_state.required_skills
                    )

                except Exception:

                    ats_result = 0

                score = 0

                matched_skills = []

                missing_skills = []

                # =============================================
                # PROCESS ATS RESULT
                # =============================================

                if isinstance(
                    ats_result,
                    dict
                ):

                    score = ats_result.get(
                        "score",
                        0
                    )

                    matched_skills = ats_result.get(
                        "matched_skills",
                        []
                    )

                    missing_skills = ats_result.get(
                        "missing_skills",
                        []
                    )

                elif isinstance(
                    ats_result,
                    tuple
                ):

                    if len(ats_result) >= 1:
                        score = ats_result[0]

                    if len(ats_result) >= 2:
                        matched_skills = ats_result[1]

                    if len(ats_result) >= 3:
                        missing_skills = ats_result[2]

                else:

                    score = ats_result

                # =============================================
                # SKILL MATCHING
                # =============================================

                resume_lower = resume_text.lower()

                matched_skills = [
                    skill
                    for skill in st.session_state.required_skills
                    if skill.lower() in resume_lower
                ]

                missing_skills = [
                    skill
                    for skill in st.session_state.required_skills
                    if skill.lower() not in resume_lower
                ]

                # =============================================
                # ATS SCORE
                # =============================================

                if st.session_state.required_skills:

                    score = (
                        len(matched_skills)
                        /
                        len(
                            st.session_state.required_skills
                        )
                    ) * 100

                else:

                    score = 0

                # =============================================
                # EXPERIENCE
                # =============================================

                experience_matches = re.findall(
                    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
                    resume_text.lower()
                )

                if experience_matches:

                    experience = max(
                        float(value)
                        for value in experience_matches
                    )

                else:

                    experience = 0

                # =============================================
                # CANDIDATE NAME
                # =============================================

                candidate_name = resume_file.stem

                # =============================================
                # SAVE RESULT
                # =============================================

                results.append({

                    "Rank": 0,

                    "Candidate":
                        candidate_name,

                    "Resume":
                        resume_file.name,

                    "ATS Score":
                        round(
                            float(score),
                            1
                        ),

                    "Experience":
                        experience,

                    "Matched Skills":
                        matched_skills,

                    "Missing Skills":
                        missing_skills,

                    "Resume Text":
                        resume_text

                })

                # =============================================
                # PROGRESS
                # =============================================

                progress.progress(
                    (index + 1) /
                    len(selected_resumes)
                )

            # =================================================
            # RANK CANDIDATES
            # =================================================

            results.sort(
                key=lambda candidate:
                candidate["ATS Score"],
                reverse=True
            )

            for rank, candidate in enumerate(
                results,
                start=1
            ):

                candidate["Rank"] = rank

            # =================================================
            # SAVE RESULTS
            # =================================================

            st.session_state.results = results

            status.success(
                "✅ Resume screening completed successfully!"
            )

            progress.empty()

        else:

            st.session_state.screening_error = (
                "⚠️ No skills were detected in the Job Description."
            )


# ============================================================
# ERROR
# ============================================================

if st.session_state.screening_error:

    st.error(
        st.session_state.screening_error
    )


# ============================================================
# CURRENT RESULTS
# ============================================================

results = st.session_state.results

required_skills = st.session_state.required_skills


# ============================================================
# METRICS
# ============================================================

if results:

    average_ats = (
        sum(
            candidate["ATS Score"]
            for candidate in results
        )
        /
        len(results)
    )

    highest_ats = max(
        candidate["ATS Score"]
        for candidate in results
    )

    shortlisted_candidates = [
        candidate
        for candidate in results
        if candidate["ATS Score"] >= 70
    ]

    total_matched = sum(
        len(
            candidate["Matched Skills"]
        )
        for candidate in results
    )

    total_required = sum(
        len(
            candidate["Matched Skills"]
        )
        +
        len(
            candidate["Missing Skills"]
        )
        for candidate in results
    )

    if total_required > 0:

        skill_match = (
            total_matched /
            total_required *
            100
        )

    else:

        skill_match = 0

    qualification_fit = average_ats

else:

    average_ats = 0
    highest_ats = 0
    shortlisted_candidates = []
    skill_match = 0
    qualification_fit = 0


# ============================================================
# RIGHT COLUMN / ATS ANALYTICS
# ============================================================

with right:

    st.markdown(
        '<div class="section-title">📊 ATS Insights</div>',
        unsafe_allow_html=True
    )

    # ========================================================
    # METRICS
    # ========================================================

    metric1, metric2 = st.columns(2)

    with metric1:

        st.metric(
            "🎯 Average ATS Score",
            f"{average_ats:.0f}%"
        )

    with metric2:

        st.metric(
            "🏆 Highest ATS Score",
            f"{highest_ats:.0f}%"
        )

    st.write("")

    # ========================================================
    # SKILL ANALYSIS
    # ========================================================

    st.subheader(
        "📈 ATS Skill Analysis"
    )

    if results and required_skills:

        skill_data = []

        for skill in required_skills:

            matched_count = 0

            for candidate in results:

                candidate_skills = [
                    item.lower()
                    for item
                    in candidate["Matched Skills"]
                ]

                if skill.lower() in candidate_skills:

                    matched_count += 1

            match_percentage = (
                matched_count /
                len(results) *
                100
            )

            skill_data.append({

                "Skill":
                    skill,

                "Match %":
                    round(
                        match_percentage,
                        1
                    )

            })

        skill_df = pd.DataFrame(
            skill_data
        )

        if not skill_df.empty:

            st.bar_chart(
                skill_df.set_index(
                    "Skill"
                )
            )

        else:

            st.info(
                "No skill analysis available."
            )

    else:

        st.info(
            "Run resume screening to display ATS analytics."
        )

    # ========================================================
    # POWER BI ANALYTICS
    # ========================================================

    st.markdown(
        '<div class="section-title">📊 Power BI Analytics</div>',
        unsafe_allow_html=True
    )

    st.subheader(
        "🏆 Top Candidates"
    )

    if results:

        for candidate in results[:5]:

            candidate_col, score_col = st.columns(
                [4, 1]
            )

            with candidate_col:

                st.write(
                    f"**#{candidate['Rank']} "
                    f"{candidate['Candidate']}**"
                )

            with score_col:

                st.write(
                    f"**{candidate['ATS Score']:.0f}%**"
                )

            st.progress(
                min(
                    candidate["ATS Score"] / 100,
                    1.0
                )
            )

    else:

        st.info(
            "No candidates available."
        )

    st.write("")

    # ========================================================
    # POWER BI KPI
    # ========================================================

    analytics1, analytics2 = st.columns(2)

    with analytics1:

        st.metric(
            "🎯 Skill Match Overview",
            f"{skill_match:.0f}%"
        )

    with analytics2:

        st.metric(
            "🎓 Qualification Fit",
            f"{qualification_fit:.0f}%"
        )

    analytics3, analytics4 = st.columns(2)

    with analytics3:

        st.metric(
            "📄 Resumes Processed",
            len(results)
        )

    with analytics4:

        st.metric(
            "✅ Shortlisted Candidates",
            len(shortlisted_candidates)
        )


# ============================================================
# CANDIDATE DETAILS
# ============================================================

if results:

    st.divider()

    st.header(
        "👥 Candidate Details"
    )

    # ========================================================
    # SUMMARY TABLE
    # ========================================================

    table_data = []

    for candidate in results:

        table_data.append({

            "Rank":
                candidate["Rank"],

            "Candidate":
                candidate["Candidate"],

            "ATS Score":
                f"{candidate['ATS Score']:.1f}%",

            "Experience":
                f"{candidate['Experience']} years",

            "Matched Skills":
                len(
                    candidate["Matched Skills"]
                ),

            "Missing Skills":
                len(
                    candidate["Missing Skills"]
                )

        })

    summary_df = pd.DataFrame(
        table_data
    )

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # CANDIDATE PROFILES
    # ========================================================

    st.subheader(
        "🔎 Candidate Profiles"
    )

    for candidate in results:

        rank = candidate["Rank"]

        if rank == 1:
            icon = "🥇"

        elif rank == 2:
            icon = "🥈"

        elif rank == 3:
            icon = "🥉"

        else:
            icon = "👤"

        with st.expander(
            f"{icon} Rank {rank} | "
            f"{candidate['Candidate']} | "
            f"{candidate['ATS Score']:.1f}%"
        ):

            score1, score2, score3 = st.columns(3)

            with score1:

                st.metric(
                    "ATS Score",
                    f"{candidate['ATS Score']:.1f}%"
                )

            with score2:

                st.metric(
                    "Experience",
                    f"{candidate['Experience']} years"
                )

            with score3:

                st.metric(
                    "Matched Skills",
                    len(
                        candidate["Matched Skills"]
                    )
                )

            st.write(
                "#### ✅ Matched Skills"
            )

            if candidate["Matched Skills"]:

                st.success(
                    ", ".join(
                        candidate["Matched Skills"]
                    )
                )

            else:

                st.info(
                    "No matched skills."
                )

            st.write(
                "#### ❌ Missing Skills"
            )

            if candidate["Missing Skills"]:

                st.error(
                    ", ".join(
                        candidate["Missing Skills"]
                    )
                )

            else:

                st.success(
                    "All required skills matched."
                )

            with st.expander(
                "📄 View Resume Content"
            ):

                st.text( 
                    candidate["Resume Text"]
                )


# ============================================================
# CHATBOT — KEEP THIS AT THE BOTTOM
# ============================================================


# ============================================================
# CHATBOT HEADER
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">💬 AI Resume Screening Chatbot</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Ask questions about candidates, ATS scores, skills, "
    "experience, and screening results."
)


# ============================================================
# CHATBOT HELPERS
# ============================================================

def format_candidate_list(candidates):
    """Format candidates with their ATS scores."""
    return "\n".join(
        f"- **{candidate['Candidate']}** — "
        f"ATS Score: {candidate['ATS Score']:.1f}%"
        for candidate in candidates
    )

# ============================================================
# COMPLETE DATA SCIENCE & AI SKILLS
# ============================================================

ALL_DS_AI_SKILLS = [

    # Python and Programming
    "Python", "Python3", "R", "Java", "C", "C++", "C#",
    "JavaScript", "TypeScript", "Scala", "Julia", "Go",

    # Python Libraries
    "NumPy", "Pandas", "Polars", "SciPy", "Statsmodels",
    "Matplotlib", "Seaborn", "Plotly", "Bokeh",
    "Scikit-learn", "TensorFlow", "Keras", "PyTorch",
    "JAX", "XGBoost", "LightGBM", "CatBoost",
    "OpenCV", "NLTK", "spaCy", "Gensim",
    "Transformers", "Hugging Face",

    # SQL and Databases
    "SQL", "MySQL", "PostgreSQL", "SQLite", "Oracle",
    "SQL Server", "MongoDB", "Cassandra", "Redis",
    "DynamoDB", "Elasticsearch", "NoSQL",
    "Joins", "Subqueries", "CTE", "Window Functions",
    "Stored Procedures", "Query Optimization",

    # Data Science and Data Analytics
    "Data Science", "Data Analysis", "Data Analytics",
    "Exploratory Data Analysis", "EDA",
    "Data Cleaning", "Data Wrangling", "Data Preprocessing",
    "Data Visualization", "Feature Engineering",
    "Feature Selection", "Missing Value Treatment",
    "Outlier Detection", "Correlation Analysis",
    "Hypothesis Testing", "A/B Testing",
    "Statistical Analysis", "Descriptive Statistics",
    "Inferential Statistics", "Probability",
    "Linear Algebra", "Calculus", "Time Series Analysis",
    "Forecasting",

    # Business Intelligence
    "Power BI", "Tableau", "Excel", "Advanced Excel",
    "DAX", "Power Query", "Power Pivot",
    "Data Modeling", "Dashboard Development",
    "KPI Reporting", "Business Intelligence",
    "Looker", "Qlik Sense",

    # Machine Learning
    "Machine Learning", "Supervised Learning",
    "Unsupervised Learning", "Reinforcement Learning",
    "Linear Regression", "Logistic Regression",
    "Decision Tree", "Random Forest",
    "Gradient Boosting", "XGBoost", "LightGBM",
    "CatBoost", "Support Vector Machine", "SVM",
    "K Nearest Neighbors", "KNN", "Naive Bayes",
    "K Means", "Hierarchical Clustering", "DBSCAN",
    "PCA", "Principal Component Analysis",
    "Dimensionality Reduction", "Ensemble Learning",
    "Bagging", "Boosting", "Hyperparameter Tuning",
    "Grid Search", "Random Search", "Cross Validation",
    "Bias Variance Tradeoff", "Model Evaluation",
    "Model Deployment", "Model Interpretability",
    "SHAP", "LIME", "Precision", "Recall",
    "F1 Score", "Confusion Matrix", "ROC AUC",

    # Deep Learning
    "Deep Learning", "ANN", "Artificial Neural Network",
    "CNN", "Convolutional Neural Network",
    "RNN", "Recurrent Neural Network",
    "LSTM", "GRU", "Autoencoder", "GAN",
    "Generative Adversarial Network",
    "Transformer Architecture", "Backpropagation",
    "Gradient Descent", "Activation Functions",
    "Neural Networks", "Transfer Learning",
    "Fine Tuning", "Batch Normalization", "Dropout",

    # Computer Vision
    "Computer Vision", "Image Processing",
    "Object Detection", "Image Classification",
    "Image Segmentation", "YOLO",
    "Face Recognition", "OCR",
    "Optical Character Recognition",
    "Image Augmentation", "Vision Transformer", "ViT",

    # NLP
    "NLP", "Natural Language Processing",
    "Text Mining", "Text Classification",
    "Sentiment Analysis", "Text Summarization",
    "Named Entity Recognition", "NER",
    "Tokenization", "Stemming", "Lemmatization",
    "Word Embeddings", "Word2Vec", "GloVe",
    "TF-IDF", "Bag of Words", "Language Modeling",
    "Machine Translation", "Question Answering",
    "Text Generation", "BERT", "RoBERTa", "T5",

    # Generative AI and LLM
    "Generative AI", "Gen AI", "GenAI",
    "LLM", "LLMs", "Large Language Model",
    "Large Language Models", "GPT", "GPT-4", "GPT-4o",
    "OpenAI", "ChatGPT", "Claude", "Gemini",
    "Llama", "Mistral", "Gemma",
    "Prompt Engineering", "Prompt Design",
    "Zero Shot Prompting", "Few Shot Prompting",
    "Chain of Thought", "Prompt Chaining",
    "LLM Fine Tuning", "PEFT", "LoRA", "QLoRA",
    "Quantization", "Instruction Tuning",

    # RAG and Vector Databases
    "RAG", "Retrieval Augmented Generation",
    "Embeddings", "Text Embeddings",
    "Vector Database", "Vector Databases",
    "Vector Store", "Vector Stores",
    "FAISS", "ChromaDB", "Chroma",
    "Pinecone", "Weaviate", "Milvus", "Qdrant",
    "Semantic Search", "Similarity Search",
    "Chunking", "Document Retrieval",
    "Hybrid Search", "Reranking",
    "Retriever", "Contextual Retrieval",

    # LangChain and Frameworks
    "LangChain", "LangGraph", "LangSmith",
    "LlamaIndex", "Haystack", "LCEL",
    "LLM Chains", "Conversation Memory",
    "Chat Memory", "Document Loaders",
    "Text Splitters", "Output Parsers", "Tool Calling",

    # Agentic AI
    "Agentic AI", "AI Agents", "AI Agent",
    "Multi Agent Systems", "Multi Agent",
    "Autonomous Agents", "Agent Workflows",
    "Agent Orchestration", "Tool Use",
    "Function Calling", "Planning Agents",
    "ReAct", "Reflection", "CrewAI",
    "AutoGen", "AutoGPT", "OpenAI Agents SDK",
    "MCP", "Model Context Protocol",

    # MLOps and LLMOps
    "MLOps", "LLMOps", "Model Monitoring",
    "MLflow", "Kubeflow", "Weights and Biases",
    "WandB", "DVC", "Model Registry",
    "Experiment Tracking", "Feature Store",
    "Model Serving", "Inference", "ONNX", "BentoML",

    # Cloud and Deployment
    "AWS", "Microsoft Azure", "Azure",
    "Google Cloud", "GCP", "Azure Machine Learning",
    "Amazon SageMaker", "Vertex AI",
    "Docker", "Kubernetes", "Git", "GitHub", "GitLab",
    "CI/CD", "Jenkins", "GitHub Actions",
    "Linux", "REST API", "REST APIs",
    "API Development", "Postman", "Microservices",

    # Big Data and Data Engineering
    "Big Data", "Apache Spark", "PySpark",
    "Hadoop", "Hive", "Kafka", "Airflow",
    "Apache Airflow", "ETL", "ELT",
    "Data Pipelines", "Data Warehousing",
    "Snowflake", "Databricks", "Delta Lake",
    "Apache Flink", "dbt",

    # Web Frameworks and Applications
    "FastAPI", "Flask", "Django",
    "Streamlit", "Gradio"
]


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {

    "Python": ["python3"],
    "Power BI": ["powerbi"],
    "Scikit-learn": ["sklearn", "scikit learn"],
    "EDA": ["exploratory data analysis"],
    "Machine Learning": ["ml"],
    "Deep Learning": ["dl"],
    "ANN": [
        "artificial neural network",
        "artificial neural networks"
    ],
    "CNN": [
        "convolutional neural network",
        "convolutional neural networks"
    ],
    "RNN": [
        "recurrent neural network",
        "recurrent neural networks"
    ],
    "SVM": ["support vector machine", "support vector machines"],
    "KNN": ["k nearest neighbor", "k-nearest neighbors"],
    "NLP": ["natural language processing"],
    "NER": ["named entity recognition"],
    "Gen AI": [
        "gen ai", "genai",
        "generative artificial intelligence"
    ],
    "LLM": [
        "llms", "large language model",
        "large language models"
    ],
    "RAG": [
        "retrieval augmented generation",
        "retrieval-augmented generation"
    ],
    "Vector Database": [
        "vector databases", "vector db",
        "vector store", "vector stores"
    ],
    "Hugging Face": ["huggingface"],
    "LangChain": ["lang chain"],
    "LangGraph": ["lang graph"],
    "Agentic AI": ["agentic artificial intelligence"],
    "AI Agents": ["ai agent", "autonomous agents"],
    "MCP": ["model context protocol"],
    "OpenAI": ["open ai"],
    "Power Query": ["powerquery"],
    "Power Pivot": ["powerpivot"],
    "PySpark": ["pyspark"],
    "Google Cloud": ["google cloud platform"],
    "Amazon SageMaker": ["sagemaker"],
    "Weights and Biases": ["wandb", "weights & biases"],
    "CI/CD": [
        "continuous integration",
        "continuous deployment"
    ]
}

# ============================================================
# SKILL MATCHING UTILITIES
# ============================================================

def contains_skill(text, skill):

    pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

    return bool(
        re.search(pattern, str(text), flags=re.IGNORECASE)
    )


def get_skill_variations(skill):

    return [skill] + SKILL_ALIASES.get(skill, [])


# ============================================================
# DETECT SKILLS FROM USER QUESTION
# ============================================================

def get_skills_from_question(question, available_skills=None):

    found_skills = []

    skills_to_check = available_skills or ALL_DS_AI_SKILLS

    for skill in sorted(skills_to_check, key=len, reverse=True):

        for variation in get_skill_variations(skill):

            if contains_skill(question, variation):

                if skill not in found_skills:
                    found_skills.append(skill)

                break

    return found_skills


# ============================================================
# CHECK SKILL IN RESUME
# ============================================================

def resume_has_skill(resume_text, skill):

    for variation in get_skill_variations(skill):

        if contains_skill(resume_text, variation):
            return True

    return False


# ============================================================
# FIND CANDIDATES WITH ALL REQUESTED SKILLS
# ============================================================

def find_candidates_with_all_skills(candidates, found_skills):

    matching_candidates = []

    for candidate in candidates:

        resume_text = candidate.get("Resume Text", "")

        if all(
            resume_has_skill(resume_text, skill)
            for skill in found_skills
        ):

            matching_candidates.append(candidate)

    return matching_candidates

# def get_skills_from_question(question, available_skills):
#     """
#     Detect every required skill mentioned in the user's question.
#     Supports questions such as:
#     'Who has Python and SQL?'
#     'Show candidates with Python, SQL and Power BI.'
#     'Who has ANN , CNN or Deep Learning?'
#     'ANN','CNN','Deep Learning'
#     'Who has NLP'
#     'Who has Gen AI'
#     'Who has Agentic AI'
#     'Who has Machine Learning?'
#     'Who has Random Forest and XGBoost?'
#     'Who has ANN and CNN?'
#     'Who has Deep Learning?'
#     'Who has NLP and BERT?'
#     'Who has TensorFlow and PyTorch?'
#     'Who has Gen AI?'
#     'Who has Generative AI and LLM?'
#     'Who has Prompt Engineering?'
#     'Who has LangChain and LangGraph?'
#     'Who has RAG and Vector Database?'
#     'Who has FAISS and ChromaDB?'
#     'Who has Agentic AI?'
#     'Who has AI Agents?'
#     'Who has Hugging Face?'
#     'Who has Streamlit and FastAPI?'
#     """
#     question_lower = question.casefold()
#     found_skills = []

#     # Check longer skill names first, such as Machine Learning
#     # and Power BI, while retaining the original skill labels.
#     for skill in sorted(
#         available_skills,
#         key=len,
#         reverse=True,
#     ):
#         pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

#         if re.search(pattern, question_lower, flags=re.IGNORECASE):
#             found_skills.append(skill)

#     return found_skills

# def find_candidates_with_all_skills(candidates, found_skills):
#     """Return candidates who have ALL requested skills."""
#     matching_candidates = []

#     for candidate in candidates:
#         candidate_skills = {
#             skill.casefold()
#             for skill in candidate["Matched Skills"]
#         }

#         if all(
#             skill.casefold() in candidate_skills
#             for skill in found_skills
#         ):
#             matching_candidates.append(candidate)

#     return matching_candidates


# ============================================================
# CHATBOT FUNCTION
# ============================================================

@st.fragment
def resume_chatbot():

    # --------------------------------------------------------
    # DISPLAY CHAT HISTORY
    # --------------------------------------------------------

    chat_container = st.container(
        height=350,
        border=True,
    )

    with chat_container:
        if not st.session_state.chat_history:
            st.info(
                "👋 Screen the resumes first, then ask me "
                "questions about the candidates."
            )
        else:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    question = st.chat_input(
        "Ask something about the resumes...",
        key="resume_chat_input",
    )

    if not question:
        return

    # Save the user's message.
    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": question,
        }
    )

    current_results = st.session_state.results
    current_skills = st.session_state.required_skills
    question_lower = question.casefold()

    # --------------------------------------------------------
    # CHECK SCREENING RESULTS
    # --------------------------------------------------------

    if not current_results:
        answer = (
            "⚠️ **No screening results are available yet.**\n\n"
            "Please enter a Job Description and click "
            "**SCREEN RESUMES** first."
        )

    # --------------------------------------------------------
    # PROCESS QUESTION
    # --------------------------------------------------------

    else:
        answer = None

        # ----------------------------------------------------
        # BEST CANDIDATE
        # ----------------------------------------------------

        if (
            "best candidate" in question_lower
            or "top candidate" in question_lower
        ):
            candidate = current_results[0]

            answer = (
                f"🏆 **{candidate['Candidate']}** is the top "
                f"candidate with an ATS score of "
                f"**{candidate['ATS Score']:.1f}%**."
            )

        # ----------------------------------------------------
        # HIGHEST ATS SCORE
        # ----------------------------------------------------

        elif (
            "highest score" in question_lower
            or "highest ats" in question_lower
        ):
            candidate = max(
                current_results,
                key=lambda item: item["ATS Score"],
            )

            answer = (
                f"🏆 **{candidate['Candidate']}** has the highest "
                f"ATS score of **{candidate['ATS Score']:.1f}%**."
            )

        # ----------------------------------------------------
        # AVERAGE ATS SCORE
        # ----------------------------------------------------

        elif "average" in question_lower:
            average_score = sum(
                candidate["ATS Score"]
                for candidate in current_results
            ) / len(current_results)

            answer = (
                f"📊 The average ATS score is "
                f"**{average_score:.1f}%**."
            )

        # ----------------------------------------------------
        # SHORTLIST CANDIDATES
        # ----------------------------------------------------

        elif (
            "shortlist" in question_lower
            or "shortlisted" in question_lower
        ):
            shortlisted = [
                candidate
                for candidate in current_results
                if candidate["ATS Score"] >= 70
            ]

            if shortlisted:
                answer = (
                    "### ✅ Shortlisted Candidates\n\n"
                    + format_candidate_list(shortlisted)
                )
            else:
                answer = (
                    "No candidates reached the **70%** "
                    "shortlist threshold."
                )

        # ----------------------------------------------------
        # MISSING SKILLS
        # ----------------------------------------------------

        elif (
            "missing skills" in question_lower
            or "missing skill" in question_lower
        ):
            missing_count = {}

            for candidate in current_results:
                for skill in candidate["Missing Skills"]:
                    missing_count[skill] = (
                        missing_count.get(skill, 0) + 1
                    )

            if missing_count:
                sorted_missing = sorted(
                    missing_count.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )

                answer = (
                    "### ❌ Missing Skills\n\n"
                    + "\n".join(
                        f"- **{skill}** — {count} candidate(s)"
                        for skill, count in sorted_missing
                    )
                )
            else:
                answer = "✅ No missing skills were detected."

        # ----------------------------------------------------
        # EXPERIENCE
        # ----------------------------------------------------

        elif (
            "experience" in question_lower
            or "years" in question_lower
        ):
            answer = (
                "### 💼 Candidate Experience\n\n"
                + "\n".join(
                    f"- **{candidate['Candidate']}** — "
                    f"{candidate['Experience']} years"
                    for candidate in current_results
                )
            )

        # ----------------------------------------------------
        # COMPARE CANDIDATES
        # ----------------------------------------------------

        elif (
            "compare" in question_lower
            or "comparison" in question_lower
        ):
            comparison_data = []

            for candidate in current_results:
                comparison_data.append(
                    {
                        "Candidate": candidate["Candidate"],
                        "ATS Score": (
                            f"{candidate['ATS Score']:.1f}%"
                        ),
                        "Experience": candidate["Experience"],
                        "Matched Skills": len(
                            candidate["Matched Skills"]
                        ),
                        "Missing Skills": len(
                            candidate["Missing Skills"]
                        ),
                    }
                )

            comparison_df = pd.DataFrame(comparison_data)

            answer = (
                "### 📊 Candidate Comparison\n\n"
                + comparison_df.to_markdown(index=False)
            )

        # ----------------------------------------------------
        # MULTIPLE-SKILL MATCHING
        # ----------------------------------------------------
        # This must be the final fallback after the intent
        # checks above. Do not put a separate "else:" before
        # found_skills.

        else:
            found_skills = get_skills_from_question(
                question,
                ALL_DS_AI_SKILLS,
            )

            if found_skills:
                matching_candidates = find_candidates_with_all_skills(
                    current_results,
                    found_skills,
                )

                skill_names = " and ".join(found_skills)

                if matching_candidates:
                    answer = (
                        f"### 👥 Candidates with {skill_names}\n\n"
                        + format_candidate_list(matching_candidates)
                    )
                else:
                    answer = (
                        "No candidates were found with **all** "
                        "these skills: "
                        + ", ".join(found_skills)
                    )

            else:
                answer = (
                    "I can help you with questions like:\n\n"
                    "- 🏆 Who is the best candidate?\n\n"
                    "- 📊 What is the average ATS score?\n\n"
                    "- 🥇 Who has the highest ATS score?\n\n"
                    "- ✅ Who should be shortlisted?\n\n"
                    "- ❌ Which skills are missing?\n\n"
                    "- 💼 What is the experience of each candidate?\n\n"
                    "- 🐍 Who has Python and SQL?\n\n"
                    "- 📊 Who has Python, SQL and Power BI?\n\n"
                    "- 🔎 Compare the candidates."
                )

    # --------------------------------------------------------
    # SAVE ASSISTANT RESPONSE
    # --------------------------------------------------------

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    # Refresh the chatbot fragment to display both messages.
    st.rerun(scope="fragment")


# ============================================================
# RUN CHATBOT
# ============================================================

resume_chatbot()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🤖 AI Resume Screening System | "
    "RAG + ATS + Power BI Analytics + Streamlit"
)
