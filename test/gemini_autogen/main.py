from autogen import AssistantAgent, UserProxyAgent
import google.generativeai as genai
import os


os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"
os.environ["HTTP_PROXYS"] = "http://127.0.0.1:10809"
Gemini_API_KEY = os.environ.get('Gemini_API_KEY')
Gemini_model = 'gemini-1.5-flash'


genai.configure(api_key=Gemini_API_KEY)
for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)

my_llm_config = {"model": Gemini_model,
                 "api_key": Gemini_API_KEY,
                 "api_type": "google"}


assistant = AssistantAgent(
    "assistant", llm_config=my_llm_config, max_consecutive_auto_reply=3
)

user_proxy = UserProxyAgent("user_proxy", code_execution_config=False)

result = user_proxy.initiate_chat(
    assistant, message="Tell me a joke about Trump")
