from answer_engine import AnswerEngine

engine = AnswerEngine()

question = """
What does dopamine primarily drive?
A. Pleasure and happiness
B. Motivation and craving
C. Memory
D. Sleep
"""

answer = engine.get_answer(question)

print(answer)