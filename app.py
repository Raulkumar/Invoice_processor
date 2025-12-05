import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import os
from dotenv import load_dotenv
from PIL import Image
import docx
from pypdf import PdfReader

# 1. SETUP

# Load the hidden .env file
load_dotenv()

# Replace with your actual key
# Get the key safely
MY_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=MY_API_KEY)

# DB FILE NAME
DB_FILE = "invoice_history.csv"

# 2. SYSTEM PROMPT
sys_prompt = """
You are a strict data extraction engine.
1. UNIVERSAL INPUT: The input can be in ANY human language.
2. TRANSLATION: Detect language and translate relevant details to ENGLISH.
3. EXTRACTION: Extract data into Schema A.

Schema A (Success):
{ 
  "status": "success", 
  "vendor": string, 
  "date": "YYYY-MM-DD", 
  "line_items": [{"item": string, "qty": int, "cost": float}], 
  "total_amount": float, 
  "original_language": string 
}

Schema B (Error):
{ "status": "error", "reason": string }

Constraint: Output ONLY the raw JSON. No markdown.
"""

# 3. HELPER FUNCTIONS
def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.type
    if "pdf" in file_type:
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except: return "Error reading PDF"
    elif "word" in file_type or "docx" in uploaded_file.name:
        try:
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except: return "Error reading Word"
    elif "excel" in file_type or "spreadsheet" in file_type:
        try:
            df = pd.read_excel(uploaded_file)
            return df.to_string()
        except: return "Error reading Excel"
    elif "text" in file_type:
        return str(uploaded_file.read(), "utf-8")
    return None

def save_to_history(data):
    # Flatten the data for CSV (we join items into a single string for summary)
    items_summary = "; ".join([f"{i['qty']}x {i['item']}" for i in data.get('line_items', [])])
    
    new_row = {
        "date": data.get("date"),
        "vendor": data.get("vendor"),
        "total": data.get("total_amount"),
        "language": data.get("original_language"),
        "items": items_summary
    }
    
    df = pd.DataFrame([new_row])
    
    # Append to CSV (create if doesn't exist)
    if not os.path.exists(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode='a', header=False, index=False)

# 4. UI LAYOUT
st.set_page_config(page_title="Universal Invoice AI", layout="wide")
st.title("📂 Universal Invoice Extractor + Database")

# Sidebar for Analytics & History
with st.sidebar:
    st.header("📊 Dashboard")
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        st.metric("Total Invoices", len(df))
        st.metric("Total Spend", f"${df['total'].sum():.2f}")
        
        st.divider()
        
        # Download Button
        st.download_button(
            label="Download Report",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="finance_report.csv",
            mime="text/csv"
        )
        
        st.write("") # Spacer
        
        # CLEAR HISTORY BUTTON (New Feature)
        if st.button("🗑️ Clear All History", type="primary"):
            try:
                os.remove(DB_FILE)
                st.success("History deleted!")
                st.rerun() # Refreshes the app immediately
            except Exception as e:
                st.error(f"Error: {e}")
                
    else:
        st.write("No history yet.")
        
# ... (Rest of main input area remains the same)

# Main Input Area
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("New Invoice")
    input_method = st.radio("Input Type:", ["File Upload", "Paste Text"], horizontal=True)

    final_payload = None 

    if input_method == "File Upload":
        uploaded_file = st.file_uploader("Upload File", type=["png", "jpg", "pdf", "docx", "xlsx", "txt"])
        if uploaded_file:
            if "image" in uploaded_file.type:
                image = Image.open(uploaded_file)
                st.image(image, width=300)
                if st.button("Process Image"):
                    final_payload = image
            else:
                if st.button("Process Document"):
                    with st.spinner("Reading file..."):
                        final_payload = extract_text_from_file(uploaded_file)

    elif input_method == "Paste Text":
        text_input = st.text_area("Paste text:", height=150)
        if st.button("Process Text"):
            final_payload = text_input

# Results Area
with c2:
    if final_payload:
        with st.spinner("AI Analyzing & Saving..."):
            try:
                model = genai.GenerativeModel('models/gemini-2.5-flash-lite', system_instruction=sys_prompt)
                response = model.generate_content(final_payload)
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                
                if data.get("status") == "success":
                    st.success("✅ Saved to Database!")
                    
                    # SAVE TO DB
                    save_to_history(data)
                    
                    # Display
                    st.metric("Vendor", data.get("vendor"))
                    st.metric("Total", f"${data.get('total_amount')}")
                    st.json(data)
                    
                    # Force reload to update sidebar stats
                    st.rerun()
                    
                else:
                    st.error(f"AI Error: {data.get('reason')}")
            except Exception as e:
                st.error(f"System Error: {e}")