from openai import OpenAI

# Replace with your actual API key
client = OpenAI(api_key="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")

def evaluate_answers(qa_pairs):
    prompt = """
You are an AI interviewer evaluating a candidate's answers to multiple questions.

For each question-answer pair:
- Mention the question number and the question.
- Give a score out of 10.
- List strengths of the answer.
- List weaknesses or areas for improvement.

After all evaluations:
- Give an overall feedback.
- Provide an overall accuracy percentage.

Respond in the following format:

Question 1:
Q: <question>
A: <answer>
Score: X/10
Strengths: ...
Weaknesses: ...
---
Question 2:
Q: <question>
A: <answer>
Score: X/10
Strengths: ...
Weaknesses: ...
---
...
Overall Feedback: ...
Accuracy: XX%
"""

    # Append all question-answer pairs
    for i, (question, answer) in enumerate(qa_pairs, start=1):
        prompt += f"\nQuestion {i}:\nQ: {question}\nA: {answer}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful interviewer AI."},
                {"role": "user", "content": prompt}
            ]
        )
        evaluation = response.choices[0].message.content
        return evaluation
    except Exception as e:
        return f"Error during evaluation: {e}"
