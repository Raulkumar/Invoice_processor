import google.generativeai as genai
import os

# 1. SETUP: Replace 'PASTE_YOUR_KEY_HERE' with your actual key
# Keep the quotes! e.g., "AIzaSy..."
MY_API_KEY = "your api key"

genai.configure(api_key=MY_API_KEY)

# 2. SELECT THE MODEL
model = genai.GenerativeModel('models/gemini-2.5-flash-lite')

# 3. RUN A TEST
response = model.generate_content("Are you online? Answer with only 'Yes'.")

# 4. PRINT RESULT
print(f"Bot says: {response.text}")