import google.generativeai as genai
import os
import json

# 1. SETUP
MY_API_KEY = "your api key"
genai.configure(api_key=MY_API_KEY)

# 2. THE BRAIN (Your System Prompt from Phase 3)
sys_prompt = """
You are a strict data extraction engine. Analyze the input text and determine if it is a valid invoice.

Decision Logic:
1. IF Valid Invoice: Extract data into Schema A. Calculate totals internally. Normalize dates to YYYY-MM-DD.
2. IF NOT Invoice: Output Schema B (Error).

Schema A (Success):
{ "status": "success", "vendor": string, "date": "YYYY-MM-DD", "line_items": [{"item": string, "qty": int, "cost": float}], "total_amount": float }

Schema B (Error):
{ "status": "error", "reason": string }

Constraint: Output ONLY the raw JSON. No markdown formatting. No conversational text.
"""

# 3. CONFIGURE MODEL WITH SYSTEM PROMPT
# We use 'system_instruction' to lock in your rules
model = genai.GenerativeModel(
    'models/gemini-2.5-flash-lite',
    system_instruction=sys_prompt
)

# 4. READ THE FILE
try:
    with open('invoice.txt', 'r') as f:
        user_text = f.read()
except FileNotFoundError:
    print("Error: Could not find invoice.txt")
    exit()

print("Analyzing invoice...")

# 5. RUN THE MODEL
# We only send the user text now, because the rules are already loaded
response = model.generate_content(user_text)

# 6. CLEAN & PRINT
try:
    # Sometimes AI adds ```json at the start. We remove it just in case.
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean_json)
    
    print("-" * 30)
    print("SUCCESS! DATA EXTRACTED:")
    print(json.dumps(data, indent=2))
    print("-" * 30)
    
except json.JSONDecodeError:
    print("FAILED. The AI did not output valid JSON.")
    print("Raw Output:", response.text)