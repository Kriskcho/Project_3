import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, TextContentItem, AssistantMessage
import traceback
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
    " Keep your answers concise and to the point."
    " Always answer in 1-2 sentences. They do not need to be complicated answers."
)

def ask_ai(user_text, chat_history):
    """
    user_text: the latest user message (string)
    chat_history: list of ChatMessage objects from DB
    """
    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history

        for msg in recent_history:
            if msg.sender == "user":
                messages.append(UserMessage(content=[TextContentItem(text=msg.message)]))
            elif msg.sender == "bot":
                messages.append(AssistantMessage(content=msg.message))

        messages.append(UserMessage(content=[TextContentItem(text=user_text)]))

        response = client.complete(
            messages=messages,
            model="openai/gpt-4.1",
            temperature=1,
            top_p=1,
            response_format="text"
        )

        if response and response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            print("AI returned empty response")
            return "I'm having trouble connecting right now. Please try again later."
    
    except TimeoutError:
        print("AI API Timeout")
        return "My response is taking longer than expected. Please try again."
    except Exception as e:
        print(f"AI API Error: {e}")
        traceback.print_exc()
        return "I'm having trouble connecting right now. Please try again later."