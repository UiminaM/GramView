import ollama

prompt = "Мы задавали вопрос 'как ваще имя' и получили ответ \"мои родители Ваня и Лариса назвали меня Машей\". Извлеки имя человека отвечавшего на вопрос.В ответе должна быть только одно имя"

response = ollama.chat(model='mistral', messages=[
    {'role': 'user', 'content': prompt}
])

print(response['message']['content'])
