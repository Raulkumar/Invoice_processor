import google.generativeai as genai
import os

# Paste your API Key here again
MY_API_KEY = "your api key"
genai.configure(api_key=MY_API_KEY)

print("Listing available models...")
for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)