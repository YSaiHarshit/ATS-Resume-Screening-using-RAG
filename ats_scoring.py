def calculate_ats_score(resume_text, required_skills):

    resume_text = resume_text.lower()

    matched_skills = []
    missing_skills = []

    for skill in required_skills:

        if skill.lower() in resume_text:

            matched_skills.append(skill)

        else:

            missing_skills.append(skill)

    if len(required_skills) == 0:

        score = 0

    else:

        score = (len(matched_skills) / len(required_skills)) * 100

    return {

        "score": round(score, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills

    }

