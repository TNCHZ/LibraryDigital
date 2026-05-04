import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


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

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content


def semantic_search_books(query, books):
    """
    Tìm kiếm sách dựa trên ngữ cảnh/ý nghĩa ngữ nghĩa.
    Ví dụ: query "trí tuệ nhân tạo" sẽ tìm các sách về AI, Machine Learning, Deep Learning...
    """
    if not books:
        return []
    
    # Prepare book list for AI
    book_text = "\n".join([
        f"ID: {b['id']} | Title: {b['title']} | Author: {b.get('author', 'N/A')} | Category: {b.get('category', 'N/A')} | Desc: {b.get('description', 'N/A')[:100]}..."
        for b in books
    ])
    
    prompt = f"""
Bạn là hệ thống tìm kiếm sách thông minh. Hãy tìm các sách LIÊN QUAN đến truy vấn của người dùng.

Truy vấn: "{query}"

Danh sách sách trong thư viện:
{book_text}

Nhiệm vụ:
1. Phân tích ý nghĩa ngữ nghĩa của truy vấn (không chỉ tìm từ khóa)
2. Ví dụ: "trí tuệ nhân tạo" → tìm sách về AI, Machine Learning, Deep Learning, Neural Networks...
3. Ví dụ: "kinh tế" → tìm sách về economics, finance, business, investment...
4. Ví dụ: "tâm lý học" → tìm sách về psychology, mental health, self-help...
5. Chọn TỐI ĐA 8 sách LIÊN QUAN NHẤT
6. Trả về JSON format:
[
  {{
    "id": <book_id>,
    "relevance_score": <0.0-1.0>,
    "reason": "giải thích ngắn gọn tại sao sách này liên quan"
  }}
]

Chỉ trả về JSON, không giải thích thêm. Nếu không có sách liên quan, trả về []"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia thư viện, hiểu biết sâu rộng về nhiều lĩnh vực. Hãy tìm sách dựa trên ý nghĩa ngữ nghĩa, không chỉ keyword matching."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        # Clean up markdown code blocks if present
        if ai_response.startswith('```json'):
            ai_response = ai_response[7:]
        if ai_response.startswith('```'):
            ai_response = ai_response[3:]
        if ai_response.endswith('```'):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()
        
        results = json.loads(ai_response)
        if isinstance(results, list):
            return results
        return []
    except Exception as e:
        print(f"Semantic search error: {e}")
        return []
