from google import genai

client = genai.Client(api_key="")


def call_ai(profile, candidates):
    candidate_text = "\n".join([f"- {c['title']}" for c in candidates])

    prompt = f"""
    You are a book recommendation system.

    User:
    - Viewed: {", ".join([v['title'] for v in profile['views']])}
    - Borrowed: {", ".join([b['title'] for b in profile['borrows']])}
    - Categories: {", ".join([c['name'] for c in profile['categories']])}

    Candidate books:
    {candidate_text}

    Task:
    - Recommend 3 books
    - Return STRICT JSON format like this:
    [
      {{
        "title": "...",
        "reason": "..."
      }}
    ]
    Do not add markdown, no explanation, only JSON.
    """

    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt
    )

    return response.text