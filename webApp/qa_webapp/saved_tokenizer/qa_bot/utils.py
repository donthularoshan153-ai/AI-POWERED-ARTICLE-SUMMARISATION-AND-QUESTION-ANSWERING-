from transformers import pipeline

def load_model():
    # Use a model that provides longer answers
    model = pipeline("question-answering", model="deepset/roberta-base-squad2")
    return model

def answer_question(model, context, question):
    # Increase max_answer_length to get longer answers
    result = model(question=question, context=context, max_answer_length=100)  # Adjust max_answer_length as needed
    return result['answer']