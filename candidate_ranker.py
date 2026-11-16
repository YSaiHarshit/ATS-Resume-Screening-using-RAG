from ats_scoring import calculate_ats_score

def screen_candidates( candidates , required_skills ):

    results = []

    for candidate in candidates:

        result = calculate_ats_score(candidate['text'], required_skills)

        results.append({

            "name": candidate['name'],

            "ATS Score" : result['score'],

            "Matched Skills": ",".join(result['matched_skills']),

            "Missing Skills": ",".join(result['missing_skills'])

        })

    results.sort( key = lambda x: x["ATS Score"], reverse=True)

    return results
