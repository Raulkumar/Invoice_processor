import google.generativeai as genai
import os
import json
import time

# 1. SETUP
# Replace with your actual key
MY_API_KEY = "your api key"
genai.configure(api_key=MY_API_KEY)

# 2. THE BRAIN (Same System Prompt)
sys_prompt = """
You are a strict data extraction engine. Analyze the input text and determine if it is a valid invoice.

Decision Logic:
1. IF Valid Invoice: Extract data into Schema A. Calculate totals internally. Normalize dates to YYYY-MM-DD.
2. IF NOT Invoice: Output Schema B (Error).

Schema A (Success):
{ "status": "success", "vendor": string, "date": "YYYY-MM-DD", "line_items": [{"item": string, "qty": int, "cost": float}], "total_amount": float }

Schema B (Error):
{ "status": "error", "reason": string }

Constraint: Output ONLY the raw JSON. No markdown formatting.
"""

model = genai.GenerativeModel('models/gemini-2.5-flash-lite', system_instruction=sys_prompt)

# 3. BATCH PROCESSING SETUP
input_folder = "invoices"
results_list = []

# Check if folder exists
if not os.path.exists(input_folder):
    print(f"Error: Folder '{input_folder}' not found. Please create it.")
    exit()

# Get all .txt files
files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
print(f"Found {len(files)} invoices to process.\n")

# 4. THE LOOP
for filename in files:
    file_path = os.path.join(input_folder, filename)
    print(f"Processing: {filename}...")

    try:
        with open(file_path, 'r') as f:
            user_text = f.read()

        # Call API
        response = model.generate_content(user_text)
        
        # Clean JSON
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        # Add filename to the data so we know which file it came from
        data['source_file'] = filename
        
        # Add to big list
        results_list.append(data)
        print(f"  -> Status: {data.get('status', 'unknown')}")

    except Exception as e:
        print(f"  -> CRASH: {str(e)}")
        results_list.append({"source_file": filename, "status": "code_crash", "error": str(e)})

    # Sleep to respect Free Tier limits (avoid 429 errors)
    time.sleep(1)

# 5. SAVE EVERYTHING
with open('all_data.json', 'w') as f:
    json.dump(results_list, f, indent=2)

print("\n" + "="*30)
print("BATCH COMPLETE. Results saved to 'all_data.json'")
print("="*30)