import re

SKILLS = [
    "Python",
    "SQL",
    "Machine Learning",
    "Deep Learning",
    "Power BI",
    "Tableau",
    "Pandas",
    "NumPy",
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",
    "Excel",
    "AWS",
    "Azure",
    "Docker",
    "Kubernetes",
    "React",
    "Angular",
    "Java",
    "Node.js"
]

def extract_skills(resume_text):

    skills_found = []

    for skill in SKILLS:

        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, resume_text, re.IGNORECASE):

            skills_found.append(skill)

    return skills_found


text = """
I am a Data Scientist with experience in Python, SQL,
Machine Learning,Deep Learning , NLP , GENAI.
"""

skills = extract_skills(text)

print("Skills found:", skills)