from transformers import BertTokenizer, BertForSequenceClassification
import torch
import joblib
import ollama

def get_date(text):
    prompt = f"Извлеки из текста дату и преобразуй в формат 'DD.MM.YY':  \"{text}\". В ответе должна быть только дата " \
             f"определенного формата"

    response = ollama.chat(model='mistral', messages=[
        {'role': 'user', 'content': prompt}
    ])

    return response['message']['content']

intent_model = joblib.load("intent_model.joblib")

def predict_intent(message):
    return intent_model.predict([message])[0]


checkpoint_path = "./results/checkpoint-624"
tokenizer = BertTokenizer.from_pretrained("DeepPavlov/rubert-base-cased")
model = BertForSequenceClassification.from_pretrained(checkpoint_path)
model.eval()

with open('results/label_map.txt', 'r') as f:
  label_map = {}
  for i in range(16):
    if i != 15:
      label_map[i] = f.readline()[:-1]
    else:
      label_map[i] = f.readline()

def get_doctor(symptoms):
    inputs = tokenizer(symptoms, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=1).squeeze()
    max_prob, predicted_class_id = torch.max(probabilities, dim=0)
    if max_prob.item() < 0.4:
        final_prediction = "Терапевт"
    else:
        final_prediction = label_map[predicted_class_id.item()]
    return final_prediction

