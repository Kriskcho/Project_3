import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, TextContentItem
from azure.core.credentials import AzureKeyCredential

client = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(os.environ["GITHUB_TOKEN"]),
    api_version="2024-08-01-preview",
)

SYSTEM_PROMPT = (
    "You are part of a fitness platform that encourages young people to get fit. "
    "You are an advisor. If someone asks something dangerous, warn them. "
    "If someone asks something unrelated, respond with "
    "'I am fitness service AI bot, I can answer only to questions related to this topic.'"
)

def ask_ai(user_text, chat_history):
    """
    user_text: the latest user message (string)
    chat_history: list of ChatMessage objects from DB
    """
    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        for msg in chat_history:
            if msg.sender == "user":
                messages.append(UserMessage(content=[TextContentItem(text=msg.message)]))
            else:
                messages.append({"role": "assistant", "content": msg.message})

        messages.append(UserMessage(content=[TextContentItem(text=user_text)]))

        response = client.complete(
            messages=messages,
            model="openai/gpt-4",
            temperature=1,
            top_p=1,
            response_format="text"
        )

        return response.choices[0].message.content
    
    except Exception as e:
        print(f"AI API Error: {e}")
        return "I'm having trouble connecting right now. Please try again later."