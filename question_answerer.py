# Question Detection and Answer Generation System

import os
from dotenv import load_dotenv
import google.generativeai as genai
from knowledge_base import COURSE_INFO, FAQS

load_dotenv()
import translation

def call_gemini_fallback(user_text, state=None):
    """
    Call Gemini API to generate a helpful sales response in the selected language.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[Gemini] API Key missing, falling back to pre-defined responses.")
        return None
    
    lang_code = "te-IN"
    if state and "language" in state:
        lang_code = state["language"]
        
    LANG_NAME_MAP = {
        "te-IN": "Telugu",
        "en-IN": "English",
        "hi-IN": "Hindi",
        "es-ES": "Spanish"
    }
    lang_name = LANG_NAME_MAP.get(lang_code, "Telugu")
    
    # Custom instructions based on language
    if lang_code == "te-IN":
        style_rule = "You speak in a warm, welcoming, and professional Indian English mixed with polite Telugu (common words like 'సరే' (ok), 'బాగుంది' (good), 'చెప్పండి' (tell me))."
        slang_hint = "Use polite Telugu words naturally. Do NOT use slang words like 'బ్రో' or 'bro'."
    elif lang_code == "hi-IN":
        style_rule = "You speak in a warm, welcoming, and professional Hindi mixed with English terms (common words like 'sahi hai', 'bataiye')."
        slang_hint = "Use polite Hindi words naturally. Do NOT use slang words like 'bhai' or 'yaar'."
    elif lang_code == "es-ES":
        style_rule = "You speak in a warm, welcoming, and professional Spanish (common words like 'vale', 'bueno', 'cuéntame')."
        slang_hint = "Use polite Spanish words naturally. Do NOT use slang words like 'amigo' or 'brother'."
    else: # en-IN or fallback
        style_rule = "You speak in a warm, welcoming, and professional Indian English (common words like 'sure', 'tell me')."
        slang_hint = "Use friendly and professional English naturally. Do NOT use slang words like 'bro' or 'dude'."
    
    try:
        genai.configure(api_key=api_key)
        model_name = os.getenv("GENIE_MODEL_NAME", "gemini-1.5-flash").strip()
        # Build prompt using knowledge base and conversational instructions
        system_instruction = f"""
You are Rocky, an energetic, enthusiastic, and friendly 10+ years experienced AI Developer acting as a 'Job Kottu' Agency Counselor. 
Your goal is to guide the student towards booking a free demo class for our Full Stack Bootcamp programs (Python or Java).
{style_rule}

Here is the program knowledge base:
- Program Names: 
  1. Python Full Stack Development Bootcamp: 8 weeks duration, fee 12,000 INR (after 20% discount). Topics: Python, Django, React, Databases, REST APIs.
  2. Java Full Stack Development Bootcamp: 10 weeks duration, fee 14,000 INR (after 20% discount). Topics: Java, Spring Boot, React, Databases, Microservices.
- Placements: 85% placement rate, average salary 3.5 to 5.5 LPA. Top companies: TCS, Infosys, Accenture, Wipro.
- Timing: Evening batch (6-8 PM) and Weekend batch (10 AM-1 PM).
- Projects: E-commerce, Social Media App, Chat App (added to GitHub portfolio).
- Mentors: 5-10+ years industry experience with 1-on-1 doubt solving.
- Certificates: Recognized by TechIndia Council.
- Demo Class: 1 hour completely FREE hands-on coding session, no commitment.
- Refund Policy: 30-day money back guarantee if not satisfied.

Conversational Style Rules:
1. Speak directly to the student in a helpful, persuasive counselor voice.
2. {slang_hint}
3. Do NOT output markdown, lists, or bullet points since your response will be spoken by Text-to-Speech.
4. Keep your answer brief and conversational (1-3 sentences maximum).
5. If the student has doubts or asks generic questions, answer them using the knowledge base and then politely nudge them towards booking the free demo.
"""
        
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        
        prompt = f"Student says: '{user_text}'\nCall State: {state}\nAnswer in Rocky style in the selected language {lang_name}:"
        
        response = model.generate_content(
            contents=prompt,
            generation_config={"temperature": 0.7, "max_output_tokens": 150}
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini] Error calling API: {e}")
        return None

def detect_question_type(user_text):
    """
    Detect what type of question the student is asking
    Returns the answer from knowledge base
    """
    text_lower = user_text.lower()
    
    # Check for self-introduction or assistant capabilities
    if any(word in text_lower for word in ["who are you", "who r you", "what is your name", "introduce yourself", "tell me about yourself", "who is speaking", "who is this"]):
        return "who_are_you", None
    if any(word in text_lower for word in ["what can you do", "what do you do", "your purpose", "how can you help", "help me", "what are you"]):
        return "what_can_you_do", None
    if "gemini" in text_lower:
        if any(word in text_lower for word in ["how", "work", "works", "what is", "explain", "how does", "does it"]):
            return "how_gemini_works", None
        return "google_gemini", None
    if any(word in text_lower for word in ["what is ai", "ai how", "how does ai work", "artificial intelligence", "large language model", "llm", "chatgpt", "chat gpt"]):
        return "what_is_ai", None
    if any(word in text_lower for word in ["transformer", "attention mechanism", "attention model", "large language model", "llm", "language model"]):
        return "what_is_llm", None
    if any(word in text_lower for word in ["training data", "trained on", "training process", "train the model", "fine tune", "fine-tune", "fine tuning"]):
        return "what_is_training_data", None
    if any(word in text_lower for word in ["are you a sales", "sales agent", "salesperson", "sales person", "sales person or ai", "sales and ai", "are you both", "agent or ai"]):
        return "are_you_sales_agent", None
    if any(word in text_lower for word in ["how do you work", "how do you answer", "how are you responding", "how do you know", "how do you do this", "how does this work", "what is your process"]):
        return "how_ai_assistant_works", None
    
    # Smart Course Check (Python vs Java vs generic Course Details)
    if any(word in text_lower for word in ["python full stack", "full stack python", "python full stock", "python full star", "python course", "python programming"]):
        return "python_course_details", None
    if any(word in text_lower for word in ["java full stack", "java course", "java programming"]):
        return "java_course_details", None
    if any(word in text_lower for word in ["course details", "course detail", "full stack course", "full stack programme", "course explain", "tell me about course", "course content"]):
        return "course_details", None
    if any(word in text_lower for word in ["book slot", "demo slot", "demo booking", "free demo", "demo class", "free class", "book demo", "slot on python", "slot on java"]):
        return "demo_class_detail", None
    if any(word in text_lower for word in ["certificate", "certification", "certified", "certificate after", "course complete certificate"]):
        return "certificate_value", None

    # Check for doubt/confusion words first
    doubt_words = ["doubt", "confused", "clear", "understand", "not clear", "confusing", "doubtful", "unclear", "not sure", "don't know"]
    if any(word in text_lower for word in doubt_words):
        return "general_doubt", None
    
    # Check for each FAQ
    if any(word in text_lower for word in ["what", "full stack", "full-stack", "what is"]):
        if any(word in text_lower for word in ["full stack", "full-stack", "web development"]):
            return "what_is_full_stack", None
    
    if any(word in text_lower for word in ["why python", "why use python", "why learn python"]):
        return "why_python", None
    
    if any(word in text_lower for word in ["placement", "job", "placement rate", "salary"]):
        if any(word in text_lower for word in ["guarantee", "guaranteed", "sure", "100%"]):
            return "placement_guarantee", None
        if any(word in text_lower for word in ["salary", "pay", "earning", "money", "how much salary"]):
            return "salary_expectations", None
        else:
            return "placement", None
    
    if any(word in text_lower for word in ["when", "start date", "batch", "timing", "schedule", "start"]):
        if any(word in text_lower for word in ["flexible", "flexible schedule", "working", "job"]):
            return "schedule_flexible", None
        else:
            return "course_timing", None
    
    if any(word in text_lower for word in ["fees", "fee", "cost", "price", "how much", "discount", "affordable", "money"]):
        return "fees_and_discounts", None
    
    if any(word in text_lower for word in ["python", "prerequisite", "prior", "experience", "knowledge", "beginner", "basic", "zero"]):
        return "prerequisite_skills", None
    
    if any(word in text_lower for word in ["batch size", "students per batch", "how many students", "class size", "batch"]):
        return "batch_size", None
    
    if any(word in text_lower for word in ["after", "after course", "after completion", "job assistance", "support", "help"]):
        return "after_course", None
    
    if any(word in text_lower for word in ["project", "practical", "real project", "what will i build", "build", "create"]):
        return "projects_real", None
    
    if any(word in text_lower for word in ["internship", "intern", "paid internship", "internship opportunity"]):
        return "internship", None
    
    if any(word in text_lower for word in ["refund", "money back", "guarantee", "not satisfied", "not happy", "back"]):
        return "refund_policy", None
    
    if any(word in text_lower for word in ["certificate", "certified", "recognized", "value", "worth"]):
        return "certificate_value", None
    
    if any(word in text_lower for word in ["weeks", "how long", "duration", "learning pace", "time", "8 weeks"]):
        return "learning_pace", None
    
    if any(word in text_lower for word in ["demo", "free", "free class", "demo class", "trial"]):
        return "demo_class_detail", None
    
    # Check for common doubts and concerns
    if any(word in text_lower for word in ["difficult", "hard", "tough", "challenging", "easy"]):
        return "difficulty_level", None
    
    if any(word in text_lower for word in ["time", "busy", "work", "job", "college", "studies"]):
        return "time_commitment", None
    
    if any(word in text_lower for word in ["worth", "value", "benefit", "advantage", "good"]):
        return "course_worth", None
    
    if any(word in text_lower for word in ["mentor", "teacher", "instructor", "support", "help"]):
        return "mentor_support", None
    
    # If no specific question detected, ask for clarification
    return "unclear", None

def generate_answer(question_type, user_text, state=None):
    """
    Generate a salesperson-like response. If the query is unclear/general doubt and Gemini is configured, it will use Gemini.
    """
    # Check Gemini fallback first for unclear or general doubt questions
    if question_type in ["unclear", "general_doubt"]:
        gemini_response = call_gemini_fallback(user_text, state)
        if gemini_response:
            return gemini_response

    lang_code = "te-IN"
    if state and "language" in state:
        lang_code = state["language"]

    # Retrieve response from translation module
    answer = translation.get_text(lang_code, question_type)
    if answer:
        # Check formatting if any variables (e.g. demo_time) are present in the response
        if "{demo_time}" in answer and state:
            answer = answer.format(demo_time=state.get("demo_time", "10:00 AM"))
        return answer

    # Fallback to general unclear response
    return translation.get_text(lang_code, "unclear")


def should_push_demo(conversation_turn, interest_level):
    """
    Decide if it's time to push for demo booking
    """
    if interest_level >= 2 and conversation_turn >= 3:
        return True
    if conversation_turn >= 5:
        return True
    return False

def get_demo_booking_response():
    """
    Response when pushing for demo booking
    """
    responses = [
        "నీకు free demo class book చేస్తానా? అందులో live coding చేస్తాం. 1 hour, completely free, no commitment.",
        "ఇక్కడ చెప్పిన అన్నీ demo లో see చేయవచ్చు. నీ convenient time లో. సరిపోతుందా?",
        "నీ doubt clear చేయడానికి free demo best! Actual mentors తో code చేస్తాం. నీ time ఎంటా?",
        "అన్నీ clear అయ్యే పటికి demo attend చేయనా? 0 investment, 100% practical learning!"
    ]
    return responses[0]

def get_sales_pitch_response(turn_number):
    """
    Smart intro pitch based on turn number
    """
    if turn_number == 0:
        return """
హలో! నేను రాకీ. 'Job Kottu' Agency నుండి call చేస్తున్నాను. 

మీరు engineering student? ఇంటర్ లేదా B.Tech చేస్తున్నారా? 

నిజమైన talk చేస్తాను - చాలా students coding లో struggle చేస్తారు. కానీ సరైన గైడెన్స్ తో చాలా better పడుతుంది.

हम Eight Week Full Stack Python Program conduct చేస్తున్నాం. Real Python, Real Projects, Real Placements. 

నీకు interest ఉందా? నేను details చెప్తాను.
"""
    else:
        return "ఇక్కడ చెప్పిన విషయాల గురించి మీకు ఏమైనా specific question ఉందా?"
