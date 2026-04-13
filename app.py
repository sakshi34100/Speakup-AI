
import base64
import os
import re
import time

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from gtts import gTTS
from PyPDF2 import PdfReader
from streamlit_mic_recorder import speech_to_text

# --- NEW: IMPORT DATABASE LOGIC ---
# This matches your Database Schema Diagram (Figure 6.4) [cite: 551]
from database import (add_score, add_user, get_leaderboard,
                      get_user_module_scores, login_user)

# --- 1. CONFIGURATION & SETUP ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("API Key not found. Please check your .env file.")

# Using Gemini  Flash as the core AI Intelligence Layer
model = genai.GenerativeModel('models/gemini-flash-latest')
st.set_page_config(page_title="SpeakUp AI | Mastery in Communication", layout="wide")

# --- INITIALIZE SESSION STATES ---
# --- INITIALIZE SESSION STATES ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "step" not in st.session_state:
    st.session_state.step = "welcome"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""
if "last_score" not in st.session_state:
    st.session_state.last_score = None
if "score_saved" not in st.session_state:
    st.session_state.score_saved = False

# Function to convert local image to base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None

def play_audio(text):
    """Generates and plays audio for AI response (TTS Module) [cite: 412, 594]"""
    clean_text = re.sub(r'[*_#]', '', text)
    tts = gTTS(text=clean_text[:300], lang='en')
    tts.save("response.mp3")
    with open("response.mp3", "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" autoplay="true"></audio>', unsafe_allow_html=True)

image_path = r"C:\Users\91956\Downloads\Gemini_Generated_Image_tg14mztg14mztg14.png"

try:
    bin_str = get_base64_image(image_path)
    if bin_str:
        background_css = f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(10, 25, 47, 0.85), rgba(10, 25, 47, 0.85)), url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #E6F1FF;
        }}
        </style>
        """
    else:
        background_css = """<style>.stApp { background-color: #0A192F; color: #E6F1FF; }</style>"""
except Exception:
    background_css = """<style>.stApp { background-color: #0A192F; color: #E6F1FF; }</style>"""

# --- 2. ENHANCED CSS (Presentation Layer) [cite: 554] ---
st.markdown(background_css, unsafe_allow_html=True)
st.markdown("""
    <style>
    .nav-bar {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 40px; background-color: rgba(2, 12, 27, 0.95);
        border-bottom: 1px solid #233554; position: fixed;
        top: 0; left: 0; right: 0; z-index: 999; height: 60px;
    }
    .hero-container { padding-top: 80px; }
    .hero-text { font-size: 65px; font-weight: 900; color: #FFFFFF; line-height: 1.1; margin-bottom: 25px; font-family: 'Helvetica Neue', sans-serif; }
    .hero-highlight { color: #2ECC71; }
    
    .hero-desc, p, label, .stMarkdown div p, .stRadio label, .stFileUploader label {
        font-size: 24px !important; 
        color: #FFFFFF !important; 
        font-weight: 800 !important; 
    }

    .stButton>button { border-radius: 8px; height: 3.5em; background-color: #2ECC71 !important; color: white !important; font-weight: 700; font-size: 18px !important; border: none; }
    .stButton>button:hover { background-color: #27ae60 !important; transform: translateY(-3px); }
    .auth-box { background-color: rgba(17, 34, 64, 0.9); padding: 30px; border-radius: 15px; border: 1px solid #233554; }
    
    .auth-title { font-size: 45px !important; font-weight: 900 !important; color: #90EE90 !important; text-align: center; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] p { font-size: 24px !important; font-weight: 800 !important; color: #90EE90 !important; }
    .stTextInput label { font-size: 22px !important; font-weight: 700 !important; color: #90EE90 !important; }

    .mode-card { background-color: rgba(17, 34, 64, 0.8); border: 2px solid #233554; padding: 40px; border-radius: 20px; text-align: left; margin-bottom: 20px; min-height: 250px; }
    .mode-card:hover { border-color: #2ECC71; background-color: rgba(29, 53, 87, 0.9); }
    .mode-card h3 { font-size: 30px !important; color: #2ECC71; }
    .chat-text { font-size: 20px !important; line-height: 1.6; color: #FFFFFF !important; font-weight: 600; }
    .back-btn button { background-color: transparent !important; border: 1px solid #8892B0 !important; color: #FFFFFF !important; font-size: 18px !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Helper function for navigation
def go_back(target_step):
    st.session_state.step = target_step
    st.session_state.messages = []
    st.session_state.voice_text = ""
    st.session_state.score_saved = False
    st.session_state.last_score = None
    st.rerun()

# --- LOGIN / SIGNUP LOGIC (User Authentication Module) [cite: 374, 397] ---
if not st.session_state.authenticated:
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        try:
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            st.markdown("<p class='auth-title'>🎙️ SpeakUp AI Access</p>", unsafe_allow_html=True)
            auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Create Account"])
            
            with auth_tab1:
                l_email = st.text_input("Username/Email", key="l_user")
                l_pass = st.text_input("Password", type="password", key="l_pass")
                if st.button("Sign In"):
                    with st.spinner("Authenticating..."):
                        # Verification against SQLite database [cite: 521, 722]
                        user = login_user(l_email, l_pass)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.username = l_email
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please try again.")
            
            with auth_tab2:
                s_email = st.text_input("Enter New Username/Email", key="s_user")
                s_pass = st.text_input("Create Password", type="password", key="s_pass")
                if st.button("Register"):
                    if add_user(s_email, s_pass):
                        st.success("Account created! Please switch to Login tab.")
                    else:
                        st.error("Username already exists.")
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"System Error: {e}")
            if st.button("🔙 Back to Login"):
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- TOP NAVIGATION (LOGGED IN) ---
st.markdown(f"""
    <div class="nav-bar">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 30px; margin-right: 15px;">🎙️</span>
            <span style="font-weight: 900; font-size: 26px; color: white;">SpeakUp AI</span>
        </div>
        <div style="color: #2ECC71; font-weight: bold; font-size: 18px;">Welcome, {st.session_state.username}</div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("Main Menu")
    if st.button("🏠 Home Dashboard"):
        go_back("welcome")
    if st.button("🏆 Leaderboard"):
        st.session_state.step = "leaderboard"
        st.rerun()
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

# --- PAGE: LEADERBOARD (Competitive Benchmarking) [cite: 381, 541] ---
# --- PAGE: LEADERBOARD (Competitive Benchmarking) [cite: 381, 541] ---
if st.session_state.step == "leaderboard":
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    st.markdown("<h1>🏆 Global Leaderboard</h1>", unsafe_allow_html=True)

    # Show current user's module-wise scores
    user_scores = get_user_module_scores(st.session_state.username)
    if user_scores:
        st.markdown("<h3 style='color:#2ECC71;'>📊 My Module Scores</h3>", unsafe_allow_html=True)
        import pandas as pd
        my_df = pd.DataFrame(user_scores, columns=["Module", "Score"])
        st.table(my_df)
    else:
        st.info("No module-wise scores found yet. Complete a session to view them.")

    st.markdown("<h3 style='color:#2ECC71;'>🌍 Overall Leaderboard</h3>", unsafe_allow_html=True)
    lb_data = get_leaderboard()
    if lb_data:
        import pandas as pd
        df = pd.DataFrame(lb_data, columns=["User", "Total Score"])
        df.index = df.index + 1
        st.table(df)
    else:
        st.info("The leaderboard is currently empty. Start practicing to rank!")

    if st.button("🔙 Back"):
        go_back("welcome")
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 1: WELCOME ---
elif st.session_state.step == "welcome":
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    col_text, col_spacer = st.columns([1.5, 1])
    with col_text:
        st.markdown('<h1 class="hero-text">Master Professional Communication with <span class="hero-highlight">SpeakUp AI</span></h1>', unsafe_allow_html=True)
        st.markdown('<p class="hero-desc">Break the barriers of hesitation. Practice interviews, boost fluency, and build unstoppable confidence.</p>', unsafe_allow_html=True)
        if st.button("Start Your Transformation 🚀"):
            st.session_state.step = "select_mode"
            st.rerun()
        if st.button("🔙 Back"):
            st.rerun()
        st.markdown('<div class="quote-box" style="color: white; font-size: 22px;">"Confidence is silent. Insecurities are loud. Master your voice to master your future."</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 2: MODE SELECTION [cite: 511] ---
elif st.session_state.step == "select_mode":
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    st.markdown('<h1 style="color: white; font-size: 45px; margin-bottom:10px;">Select Your Module</h1>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    with col1:
        st.markdown('<div class="mode-card"><h3>👔 Job Interview</h3><p>Ace technical and HR rounds with real-time feedback.</p></div>', unsafe_allow_html=True)
        if st.button("Start Interview"):
            st.session_state.mode = "Interview"
            st.session_state.step = "setup_mode"
            st.rerun()
    with col2:
        st.markdown('<div class="mode-card"><h3>🗣️ Fluency Coach</h3><p>Eliminate hesitation and boost natural English fluency.</p></div>', unsafe_allow_html=True)
        if st.button("Start Coaching"):
            st.session_state.mode = "Fluency"
            st.session_state.step = "setup_mode"
            st.rerun()
    with col3:
        st.markdown('<div class="mode-card"><h3>⚖️ Strategic Debate</h3><p>Enhance critical thinking in high-pressure debates.</p></div>', unsafe_allow_html=True)
        if st.button("Start Debate"):
            st.session_state.mode = "Debate"
            st.session_state.step = "setup_mode"
            st.rerun()
    with col4:
        st.markdown('<div class="mode-card"><h3>🏆 Leaderboard</h3><p>Check your rank and session progress metrics.</p></div>', unsafe_allow_html=True)
        if st.button("View Rankings"):
            st.session_state.step = "leaderboard"
            st.rerun()
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("🔙 Back"):
        go_back("welcome")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 3: SETUP MODE (Contextual Setup & PDF Parsing) [cite: 401, 510] ---
elif st.session_state.step == "setup_mode":
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    st.markdown(f'<h1 style="color:#2ECC71; font-size:45px;">Configure: {st.session_state.mode}</h1>', unsafe_allow_html=True)
    
    if st.session_state.mode == "Interview":
        job_role = st.text_input("Target Designation", placeholder="e.g., Data Analyst")
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        if st.button("Initialize AI Interviewer 👔"):
            if job_role and uploaded_file:
                with st.spinner("Analyzing Resume..."):
                    st.session_state.job_role = job_role
                    # Using PyPDF2 for text extraction [cite: 329, 588, 701]
                    reader = PdfReader(uploaded_file)
                    st.session_state.resume_text = "".join([page.extract_text() for page in reader.pages])
                    st.session_state.step = "main_ai"
                    st.rerun()

    elif st.session_state.mode == "Debate":
        debate_option = st.radio("Topic Selection Method:", ["Propose Custom Topic", "AI-Generated Random Topic"])
        if debate_option == "Propose Custom Topic":
            debate_topic = st.text_input("Enter Your Debate Proposition")
        else:
            if st.button("Generate Random Topic 🎲"):
                res = model.generate_content("Generate one short, controversial professional debate topic. Provide only the topic name.")
                st.session_state.generated_topic = res.text
            debate_topic = st.session_state.get("generated_topic", "Press button to generate")
            st.markdown(f"<p style='color:white; font-size:22px;'>Topic: {debate_topic}</p>", unsafe_allow_html=True)
            
        st.session_state.stance = st.radio("Define Your Perspective:", ["Affirmative (In Favour)", "Negative (Against)"])
        if st.button("Commence Strategic Debate ⚔️"):
            if debate_topic and debate_topic != "Press button to generate":
                st.session_state.topic = debate_topic
                st.session_state.step = "main_ai"
                st.rerun()

    else: # Fluency
        st.markdown("<p style='color:white; font-size:22px;'>The AI Coach will guide you through natural daily life topics.</p>", unsafe_allow_html=True)
        if st.button("Start Session 🚀"):
            st.session_state.step = "main_ai"
            st.rerun()

    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("🔙 Back"):
        go_back("select_mode")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 4: MAIN AI ENGINE (Multimodal Interaction Loop) [cite: 410, 427, 719] ---
elif st.session_state.step == "main_ai":
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    st.markdown(f'<h2 style="color:#2ECC71; font-size:35px;">{st.session_state.mode} Training Active</h2>', unsafe_allow_html=True)
    
        # Adding a visible 'Finish' button in the main area [cite: 432]
    if st.button("🏁 Finish Session & View My Score"):
     with st.spinner("Analyzing your performance..."):

        # ✅ Only user answers (important fix)
        hist = "\n".join([m['content'] for m in st.session_state.messages if m['role'] == 'user'])

        score_prompt = f"""
You are a strict evaluator.

Evaluate ONLY the USER'S performance in this {st.session_state.mode} session.

SCORING RULES:
- 90-100 = excellent, highly confident, accurate, clear, professional
- 75-89 = good, minor mistakes, mostly clear and relevant
- 60-74 = average, noticeable grammar/content/confidence problems
- 40-59 = weak, many mistakes, poor clarity, incomplete answers
- 1-39 = very poor, irrelevant, extremely weak communication/performance

IMPORTANT:
- Do not give a generic score
- Do not default to 85
- Be strict
- Base score on actual quality of user responses only
- Return ONLY ONE INTEGER between 1 and 100
- No explanation
- No extra text

SESSION:
{hist}
"""

        res = model.generate_content(score_prompt)

        try:
            score_text = res.text.strip()
            score_match = re.search(r'\b(100|[1-9]?[0-9])\b', score_text)
            if score_match:
                score = int(score_match.group(1))
            else:
                raise ValueError("No valid score found")
                add_score(st.session_state.username, st.session_state.mode, score)
                st.session_state.last_score = score
                st.session_state.score_saved = True
                st.success(f"Session Saved! Your Score: {score}")
                st.rerun()
        except:
                st.error("Could not calculate score. Please try again.")

    with st.sidebar:
     if st.button("🏁 End & Save Score"):
        with st.spinner("Analyzing performance..."):

            # ✅ Only user answers
            hist = "\n".join([m['content'] for m in st.session_state.messages if m['role'] == 'user'])

            score_prompt = f"""
You are a strict evaluator.

Evaluate ONLY the USER'S performance in this {st.session_state.mode} session.

SCORING RULES:
- 90-100 = excellent, highly confident, accurate, clear, professional
- 75-89 = good, minor mistakes, mostly clear and relevant
- 60-74 = average, noticeable grammar/content/confidence problems
- 40-59 = weak, many mistakes, poor clarity, incomplete answers
- 1-39 = very poor, irrelevant, extremely weak communication/performance

IMPORTANT:
- Do not give a generic score
- Do not default to 85
- Be strict
- Base score on actual quality of user responses only
- Return ONLY ONE INTEGER between 1 and 100
- No explanation
- No extra text

SESSION:
{hist}
"""

            res = model.generate_content(score_prompt)

            score_text = res.text.strip()
            score_match = re.search(r'\b(100|[1-9]?[0-9])\b', score_text)
            score = int(score_match.group(1))
            add_score(st.session_state.username, st.session_state.mode, score)
            go_back("leaderboard")
        if st.button("🚪 Exit Without Saving"):
            go_back("select_mode")

    if not st.session_state.messages:
        with st.spinner("AI is entering the room..."):
            if st.session_state.mode == "Interview":
                # Prompt engineering for AI persona [cite: 405, 591, 631]
                prompt = f"""Act as a Professional HR Executive interviewing for the role of {st.session_state.job_role}. 
                Resume context: {st.session_state.resume_text}.

ROLE:
You are a realistic, professional interviewer conducting a structured interview.

STRICT FLOW:
1. Greeting + ask for INTRODUCTION
2. EDUCATIONAL BACKGROUND
3. SKILLS (deep dive)
4. PROJECTS (from resume)
5. TECHNICAL QUESTIONS

STRICT RULES:
- Ask ONLY ONE question at a time
- WAIT for user response before continuing
- DO NOT generate multiple questions together
- DO NOT continue unless user answers

AFTER EVERY USER ANSWER:
1. Give SHORT REVIEW (strength + mistake)
2. Provide REFINED/IDEAL answer
3. Ask NEXT question

DEPTH REQUIREMENTS:
- Minimum 5 questions from SKILLS
- Minimum 3 questions per PROJECT

FINAL STEP:
When interview ends, generate:
- Score (1-100)
- Strengths
- Weak areas
- Improvement suggestions

START NOW:
Greet the candidate and ask for introduction."""
            elif st.session_state.mode == "Debate":
                ai_side = "Negative (Against)" if "Favour" in st.session_state.stance else "Affirmative (In Favour)"
                # Adversarial Logic Prompt [cite: 304, 314, 606]
                prompt = f"""Role: Master Debater. Topic: {st.session_state.topic}. AI Stance: {ai_side}. 
                FLOW:
1. Greet the user
2. Give a SHORT introduction about the topic
3. Decide your stance:
   - If user is "Affirmative" → you take "Negative"
   - If user is "Negative" → you take "Affirmative"

TURN RULE:
- If AI has opposite stance → AI speaks FIRST
- If user starts → WAIT for user input

DEBATE RULES:
- One argument at a time
- WAIT for user reply
- After each reply:
    1. Analyze user's argument
    2. Point out strengths + weaknesses
    3. Respond with counter argument
    4. WAIT again

STRICT:
- Do NOT send multiple arguments together
- Do NOT continue without user input

ENDING:
When user says "stop" or "end debate":
Generate:
- Debate performance review
- Strengths
- Logical gaps
- Communication feedback
- Final score (1–100)

START NOW:
Greet and introduce the topic, then begin debate based on stance.
                RULE: If AI chooses Affirmative/Favour, AI speaks first. If User chooses Affirmative/Favour, AI waits for user."""
            else: # Fluency
                # --- NEW COACHING LOGIC ---
                prompt = """You are a Professional English Fluency Coach.

GOAL:
Improve user's daily conversation fluency.

FLOW:
1. Greet the user
2. Start a natural daily-life conversation

RULES:
- Talk ONLY about real-life topics (daily routine, college, work, friends, etc.)
- Ask ONE question at a time
- WAIT for user response

AFTER EVERY USER REPLY:
1. Correct grammar mistakes
2. Improve sentence structure
3. Suggest better vocabulary
4. Then continue conversation

STOP CONDITION:
If user says:
"stop", "end", "generate report"

Then generate:
- Fluency score (1–100)
- Grammar mistakes
- Vocabulary improvement
- Confidence level
- Final suggestions

IMPORTANT:
- Do NOT ask multiple questions
- Do NOT continue without user reply

START NOW:
Greet the user and start a casual conversation."""
            
            resp_content = model.generate_content(prompt).text
            # Logic to handle who speaks first [cite: 407, 408]
            if not (st.session_state.mode == "Debate" and "Affirmative" not in prompt):
                st.session_state.messages.append({"role": "assistant", "content": resp_content})
                play_audio(resp_content)

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(f'<div class="chat-text">{m["content"]}</div>', unsafe_allow_html=True)

    # Multimodal Input Processing (STT handler) [cite: 331, 377, 411, 706]
       # Multimodal Input Processing (STT handler)
    col_v, col_t = st.columns([1, 4])
    with col_v:
        voice_input = speech_to_text(
            language='en',
            start_prompt="🎤 Speak",
            stop_prompt="📤 Transcribe",
            just_once=True,
            key='mic'
        )

    u_input = st.chat_input("Edit text or type here...")

    # Give priority to voice input if available, otherwise typed input
    if voice_input:
        u_input = voice_input

    if u_input:
        # Check for stop trigger in Fluency module
        if st.session_state.mode == "Fluency" and "stop" in u_input.lower() and "report" in u_input.lower():
            st.info("Generating Final Report card..."); time.sleep(1); st.session_state.step = "leaderboard"; st.rerun()
            
        st.session_state.messages.append({"role": "user", "content": u_input})
        with st.spinner("AI analyzing..."):
            hist_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
            
            # Use appropriate logic for response
            if st.session_state.mode == "Interview":
                final_prompt = f"History: {hist_context}. Resume: {st.session_state.resume_text}. REVIEW last answer, provide REFINED answer, then ask NEXT question in sequence (Intro->Background->Skills->Projects->Tech)."
            else: 
                final_prompt = hist_context
            
            resp = model.generate_content(final_prompt).text
            st.session_state.messages.append({"role": "assistant", "content": resp})
            play_audio(resp); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
