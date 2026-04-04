from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model = 'chatgpt-4o-latest'
)