from flask import Flask, request, render_template, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv
import os
import json
import sys

# Configure standard output/error to use UTF-8, preventing console encoding issues on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Import our custom systems
import translation
from knowledge_base import COURSE_INFO, FAQS
from question_answerer import detect_question_type, generate_answer
from sales_intelligence import (
    get_intro_message, get_interest_check, get_yes_response, get_no_response,
    get_answer_intro, get_after_answer, get_demo_message, get_close, handle_objection
)
from course_booking import (
    get_course_selection, get_course_confirmation, get_demo_booking,
    get_demo_time, get_booking_confirmation, get_closing,
    extract_course, extract_day, extract_time
)
from booking_system import create_booking

def clean_student_name(user_input):
    """Clean common conversational prefixes from spoken/typed candidate names"""
    text = str(user_input).strip()
    text_lower = text.lower()
    
    # Common prefixes in English, Telugu, Hindi, Spanish
    prefixes = [
        "my name is", "i am", "this is", "myself", "here is",
        "naa peru", "na peru", "peru",
        "mera naam", "naam", "main hoon",
        "soy", "me llamo", "mi nombre es"
    ]
    
    for prefix in prefixes:
        if text_lower.startswith(prefix):
            text = text[len(prefix):].strip()
            text_lower = text.lower()
            
    return text.strip(".,! ")

def extract_phone_number(user_input):
    """Extract numeric characters and + prefix for clean phone storage"""
    text = str(user_input).strip()
    # Retain only digits and the '+' prefix if present
    cleaned = "".join(c for c in text if c.isdigit() or c == '+')
    if any(c.isdigit() for c in cleaned):
        return cleaned
    return text

def get_twilio_voice(lang_code, gender):
    """Map language and gender to Twilio voice configurations.
    Returns (voice_name, engine)
    """
    voices = {
        "te-IN": {
            "female": ("Google.te-IN-Standard-A", "google"),
            "male": ("Google.te-IN-Standard-B", "google")
        },
        "hi-IN": {
            "female": ("Polly.Kajal", "polly"),
            "male": ("Polly.Chanakya", "polly")
        },
        "en-IN": {
            "female": ("Polly.Aditi", "polly"),
            "male": ("Google.en-IN-Standard-B", "google")
        },
        "es-ES": {
            "female": ("Polly.Lucia", "polly"),
            "male": ("Polly.Enrique", "polly")
        }
    }
    lang = str(lang_code).strip()
    if lang == "te":
        lang = "te-IN"
    elif lang == "hi":
        lang = "hi-IN"
    elif lang == "en":
        lang = "en-IN"
    elif lang == "es":
        lang = "es-ES"
        
    lang_voices = voices.get(lang, voices["te-IN"])
    return lang_voices.get(gender, lang_voices["female"])

app = Flask(__name__)
load_dotenv(override=True)

print("=" * 70)
print("[*] ADVANCED AI SALES AGENT WITH SMART BOOKING SYSTEM")
print("[+] Talks like experienced sales counselor")
print("[+] Course selection & slot booking automation")
print("=" * 70)

# =============================
# CALL STATE TRACKING
# =============================
call_state = {}
conversation_history = {}
turn_count = {}
student_interest = {}
student_phone = {}

def get_state(call_id):
    return call_state.get(call_id, {
        "stage": "intro",
        "questions_asked": 0,
        "demo_offered": False,
        "course_selected": None,
        "demo_date": None,
        "demo_time": None,
        "student_name": None,
        "student_mobile": None,
        "language": "te-IN",
        "gender": "female"
    })

def update_state(call_id, state):
    call_state[call_id] = state


def is_affirmative(text):
    text_lower = text.lower()
    return any(word in text_lower for word in ["yes", "ya", "yup", "sure", "okay", "of course", "absolutely", "want", "i do", "నేను", "అవును", "సరే", "si", "sí", "claro", "por supuesto", "haan", "haanji"])


def is_negative(text):
    text_lower = text.lower()
    return any(word in text_lower for word in ["no", "don't", "dont", "nah", "not interested", "కాదు", "లేదు", "nahi", "nahin", "tampoco"])


def add_to_history(call_id, role, text):
    if call_id not in conversation_history:
        conversation_history[call_id] = []
    conversation_history[call_id].append({"role": role, "text": text})


def get_turn(call_id):
    return turn_count.get(call_id, 0)


def increment_turn(call_id):
    turn_count[call_id] = get_turn(call_id) + 1


def get_stage_followup_prompt(state):
    stage = state.get("stage", "intro")
    lang_code = state.get("language", "te-IN")
    
    if stage == "intro":
        return translation.get_text(lang_code, "interest_check")
    elif stage == "course_selection":
        return translation.get_text(lang_code, "course_selection")
    elif stage == "demo_interest":
        return translation.get_text(lang_code, "demo_booking")
    elif stage == "demo_date_selection":
        return translation.get_text(lang_code, "demo_booking")
    elif stage == "demo_time_selection":
        return translation.get_text(lang_code, "demo_time")
    elif stage == "collect_student_details":
        if state.get("student_name") is None:
            return translation.get_text(lang_code, "ask_name")
        elif state.get("student_mobile") is None:
            return translation.get_text(lang_code, "ask_mobile_fallback")
        else:
            return translation.get_text(lang_code, "confirm_details_doubt")
    return translation.get_text(lang_code, "unclear")


def try_general_question_response(response, call_id, user_input, state):
    question_type, direct_answer = detect_question_type(user_input)
    
    # If Gemini is configured, let it handle unclear questions, otherwise return False
    has_gemini = bool(os.getenv("GEMINI_API_KEY", "").strip())
    if question_type == "unclear" and not has_gemini:
        return False

    ai_response = generate_answer(question_type, user_input, state)

    # Don't add double introduction if it is a general chat response or direct chatbot self-introduction
    if question_type not in ["who_are_you", "what_can_you_do", "google_gemini", "how_gemini_works", "what_is_ai", "what_is_llm", "what_is_training_data", "are_you_sales_agent", "how_ai_assistant_works", "general_doubt"] and not (question_type in ["unclear", "general_doubt"] and has_gemini):
        lang_code = state.get("language", "te-IN")
        if lang_code == "te-IN":
            intro = get_answer_intro(question_type)
            if intro:
                ai_response = intro + " " + ai_response
        elif lang_code == "hi-IN":
            ai_response = "बढ़िया सवाल भाई! " + ai_response
        elif lang_code == "es-ES":
            ai_response = "¡Buena pregunta, amigo! " + ai_response
        else:
            ai_response = "Good question, bro! " + ai_response

    lang_code = state.get("language", "te-IN")
    gender = state.get("gender", "female")
    voice_name, engine = get_twilio_voice(lang_code, gender)

    response.say(ai_response, voice=voice_name, language=lang_code)
    add_to_history(call_id, "Agent", ai_response)

    follow_up = get_stage_followup_prompt(state)
    gather = Gather(
        input="speech",
        action="/process",
        method="POST",
        timeout=10,
        speechTimeout="auto",
        language=lang_code
    )
    gather.say(follow_up, voice=voice_name, language=lang_code)
    response.append(gather)
    return True

# =============================
# CACHE CONTROL FOR APIS
# =============================
@app.after_request
def add_header(response):
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

# =============================
# HEALTH CHECK
# =============================
@app.route("/health", methods=["GET"])
def health():
    return "✅ Real AI Sales Agent is running with ACTUAL course knowledge!"


# =============================
# SIMPLE WEB DASHBOARD
# =============================
@app.route("/", methods=["GET"])
@app.route("/simulator", methods=["GET"])
def simulator():
    SIMULATE_MODE = os.getenv("SIMULATE_MODE", "").strip().lower() in ("1", "true", "yes")
    STUDENT_PHONE_NUMBER = os.getenv("STUDENT_PHONE_NUMBER", "").strip()
    GEMINI_CONFIGURED = bool(os.getenv("GEMINI_API_KEY", "").strip())
    return render_template(
        "simulator.html",
        active_page="simulator",
        simulate=SIMULATE_MODE,
        student_number=STUDENT_PHONE_NUMBER,
        gemini=GEMINI_CONFIGURED
    )

@app.route("/bookings", methods=["GET"])
def bookings():
    SIMULATE_MODE = os.getenv("SIMULATE_MODE", "").strip().lower() in ("1", "true", "yes")
    GEMINI_CONFIGURED = bool(os.getenv("GEMINI_API_KEY", "").strip())
    return render_template(
        "bookings.html",
        active_page="bookings",
        simulate=SIMULATE_MODE,
        gemini=GEMINI_CONFIGURED
    )

@app.route("/settings", methods=["GET"])
def settings():
    from booking_system import COURSES
    from knowledge_base import FAQS
    
    SIMULATE_MODE = os.getenv("SIMULATE_MODE", "").strip().lower() in ("1", "true", "yes")
    GEMINI_CONFIGURED = bool(os.getenv("GEMINI_API_KEY", "").strip())
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    VOICE_WEBHOOK_URL = os.getenv("VOICE_WEBHOOK_URL", "").strip()
    GEMINI_MODEL = os.getenv("GENIE_MODEL_NAME", "gemini-1.5-flash").strip()
    
    env_status = {
        "twilio_configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER),
        "gemini_configured": GEMINI_CONFIGURED,
        "gemini_model": GEMINI_MODEL,
        "simulate_mode": SIMULATE_MODE,
        "voice_webhook": VOICE_WEBHOOK_URL
    }
    
    return render_template(
        "settings.html",
        active_page="settings",
        simulate=SIMULATE_MODE,
        gemini=GEMINI_CONFIGURED,
        courses=COURSES,
        faqs=FAQS,
        env_status=env_status
    )


@app.route("/trigger_call", methods=["POST"])
def trigger_call():
    """Trigger an outbound call via Twilio (uses same env vars as call.py).
    Expects JSON: { "phone": "+123...", "language": "en-IN", "gender": "male" }
    """
    from twilio.rest import Client
    phone = request.json.get("phone") if request.is_json else request.form.get("phone")
    if not phone:
        return jsonify({"error": "Phone number required"}), 400

    lang_code = (request.json.get("language") if request.is_json else request.form.get("language")) or "te-IN"
    gender = (request.json.get("gender") if request.is_json else request.form.get("gender")) or "female"

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    VOICE_WEBHOOK_URL = os.getenv("VOICE_WEBHOOK_URL", "").strip()
    SIMULATE_MODE = os.getenv("SIMULATE_MODE", "").strip().lower() in ("1", "true", "yes")

    print(f"[trigger_call] SIMULATE_MODE={SIMULATE_MODE}, VOICE_WEBHOOK_URL='{VOICE_WEBHOOK_URL}', TWILIO_FROM_NUMBER='{TWILIO_FROM_NUMBER}'")

    if SIMULATE_MODE:
        return jsonify({"status": "simulated", "webhook_response": "simulate mode active"})

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, VOICE_WEBHOOK_URL]):
        missing = [
            name
            for name, value in [
                ("TWILIO_ACCOUNT_SID", TWILIO_ACCOUNT_SID),
                ("TWILIO_AUTH_TOKEN", TWILIO_AUTH_TOKEN),
                ("TWILIO_FROM_NUMBER", TWILIO_FROM_NUMBER),
                ("VOICE_WEBHOOK_URL", VOICE_WEBHOOK_URL),
            ]
            if not value
        ]
        return jsonify({"error": f"Missing Twilio configuration: {', '.join(missing)}. Please set them in your .env file."}), 400

    # Real call via Twilio - propagate language and gender in query parameters
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Append settings as query parameters
        webhook_url = VOICE_WEBHOOK_URL
        separator = "&" if "?" in webhook_url else "?"
        webhook_url += f"{separator}Language={lang_code}&Gender={gender}"
        
        call = client.calls.create(to=phone, from_=TWILIO_FROM_NUMBER, url=webhook_url)
        return jsonify({"status": "started", "call_sid": call.sid})
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500

# =============================
# INITIAL VOICE CALL ENDPOINT
# =============================
@app.route("/voice", methods=["POST"])
def voice():
    """
    When student receives the call, this is what they hear first
    """
    call_id = request.form.get("CallSid", "default")
    phone = request.form.get("From", "unknown")
    
    # Read language and gender configuration (can be form parameters or query params in webhook URL)
    lang_code = request.values.get("Language", "te-IN").strip()
    gender = request.values.get("Gender", "female").strip()
    
    # Store student phone number for booking
    student_phone[call_id] = phone
    
    call_state[call_id] = {
        "stage": "intro",
        "questions_asked": 0,
        "demo_offered": False,
        "course_selected": None,
        "demo_date": None,
        "demo_time": None,
        "student_name": None,
        "student_mobile": None,
        "language": lang_code,
        "gender": gender
    }
    
    response = VoiceResponse()
    voice_name, engine = get_twilio_voice(lang_code, gender)
    
    gather = Gather(
        input="speech",
        action="/process",
        method="POST",
        timeout=10,
        speechTimeout="auto",
        language=lang_code
    )
    
    opening = translation.get_text(lang_code, "intro")
    interest_q = translation.get_text(lang_code, "interest_check")
    full_message = opening + " " + interest_q
    
    gather.say(full_message, voice=voice_name, language=lang_code)
    response.append(gather)
    
    return str(response)

# =============================
# MAIN PROCESSING ENDPOINT
# =============================
@app.route("/process", methods=["POST"])
def process():
    """
    MAIN ENGINE: Listens to student, detects question, gives REAL answer
    """
    user_input = request.form.get("SpeechResult", "").strip()
    call_id = request.form.get("CallSid", "default")
    
    response = VoiceResponse()
    state = get_state(call_id)
    current_turn = get_turn(call_id)

    lang_code = state.get("language", "te-IN")
    gender = state.get("gender", "female")
    voice_name, engine = get_twilio_voice(lang_code, gender)

    gather = Gather(
        input="speech",
        action="/process",
        method="POST",
        timeout=10,
        speechTimeout="auto",
        language=lang_code
    )
    
    # =============================
    # HANDLE NO SPEECH
    # =============================
    if not user_input:
        no_speech_msg = translation.get_text(lang_code, "no_speech")
        response.say(
            no_speech_msg,
            voice=voice_name,
            language=lang_code
        )
        response.append(gather)
        return str(response)
    
    # =============================
    # HANDLE HARD EXIT
    # =============================
    exit_phrases = ["stop calling", "don't call", "remove me", "not interested at all", "oddu", "vaddhu", "mat karo", "no me llames"]
    if any(word in user_input.lower() for word in exit_phrases):
        exit_msg = translation.get_text(lang_code, "hard_exit")
        response.say(exit_msg, voice=voice_name, language=lang_code)
        response.hangup()
        return str(response)
    
    # =============================
    # TRACK THE CONVERSATION
    # =============================
    add_to_history(call_id, "Student", user_input)
    increment_turn(call_id)
    current_turn = get_turn(call_id)
    
    print(f"\n[Turn {current_turn}] Student ({call_id}): {user_input}")
    
    # =============================
    # INITIAL STAGE: YES/NO TO BECOME SOFTWARE ENGINEER
    # =============================
    if state["stage"] == "intro":
        if is_affirmative(user_input):
            ai_response = translation.get_text(lang_code, "yes_response")
            state["stage"] = "course_selection"
            update_state(call_id, state)
        elif is_negative(user_input):
            closing_msg = translation.get_text(lang_code, "no_response")
            response.say(closing_msg, voice=voice_name, language=lang_code)
            response.hangup()
            return str(response)
        else:
            if try_general_question_response(response, call_id, user_input, state):
                return str(response)
            
            fallback_prompt = translation.get_text(lang_code, "interest_check")
            if lang_code == "te-IN":
                ai_response = fallback_prompt + " దయచేసి yes లేదా no చెప్పండి బ్రో."
            elif lang_code == "hi-IN":
                ai_response = fallback_prompt + " कृपया yes या no बोलें भाई।"
            elif lang_code == "es-ES":
                ai_response = fallback_prompt + " Por favor di sí o no, amigo."
            else:
                ai_response = fallback_prompt + " Please say yes or no, bro."
                
            response.say(ai_response, voice=voice_name, language=lang_code)
            response.append(gather)
            return str(response)
    
    # =============================
    # STAGE: COURSE SELECTION
    # =============================
    elif state["stage"] == "course_selection":
        course = extract_course(user_input)
        if course:
            if course.lower() == "python":
                ai_response = translation.get_text(lang_code, "course_confirmation_python")
            else:
                ai_response = translation.get_text(lang_code, "course_confirmation_java")
            state["course_selected"] = course
            state["stage"] = "demo_interest"
            update_state(call_id, state)
        else:
            if try_general_question_response(response, call_id, user_input, state):
                return str(response)
            ai_response = translation.get_text(lang_code, "course_selection")
            response.say(ai_response, voice=voice_name, language=lang_code)
            response.append(gather)
            return str(response)
    
    # =============================
    # STAGE: DEMO INTEREST
    # =============================
    elif state["stage"] == "demo_interest":
        course_name = state.get("course_selected")
        if is_affirmative(user_input):
            ai_response = translation.get_text(lang_code, "demo_booking")
            state["stage"] = "demo_date_selection"
            update_state(call_id, state)
        elif is_negative(user_input):
            ai_response = translation.get_text(lang_code, "demo_negative")
            response.say(ai_response, voice=voice_name, language=lang_code)
            response.hangup()
            return str(response)
        else:
            if try_general_question_response(response, call_id, user_input, state):
                return str(response)
            ai_response = translation.get_text(lang_code, "demo_booking")
            response.say(ai_response, voice=voice_name, language=lang_code)
            response.append(gather)
            return str(response)
    
    # =============================
    # STAGE: DEMO DATE SELECTION
    # =============================
    elif state["stage"] == "demo_date_selection":
        demo_day = extract_day(user_input)
        if demo_day:
            ai_response = translation.get_text(lang_code, "demo_time")
            state["demo_date"] = demo_day
            state["stage"] = "demo_time_selection"
            update_state(call_id, state)
        else:
            if try_general_question_response(response, call_id, user_input, state):
                return str(response)
            ai_response = translation.get_text(lang_code, "demo_booking")
            response.say(ai_response, voice=voice_name, language=lang_code)
            response.append(gather)
            return str(response)
    
    # =============================
    # STAGE: DEMO TIME SELECTION
    # =============================
    elif state["stage"] == "demo_time_selection":
        demo_time = extract_time(user_input)
        if demo_time:
            ai_response = translation.get_text(lang_code, "time_selected", demo_time=demo_time)
            state["demo_time"] = demo_time
            state["stage"] = "collect_student_details"
            update_state(call_id, state)
        else:
            if try_general_question_response(response, call_id, user_input, state):
                return str(response)
            ai_response = translation.get_text(lang_code, "demo_time")
            response.say(ai_response, voice=voice_name, language=lang_code)
            response.append(gather)
            return str(response)
    
    # =============================
    # STAGE: COLLECT STUDENT DETAILS
    # =============================
    elif state["stage"] == "collect_student_details":
        if state["student_name"] is None:
            question_type, _ = detect_question_type(user_input)
            if question_type != "unclear":
                if try_general_question_response(response, call_id, user_input, state):
                    return str(response)
            # First time - asking for name
            state["student_name"] = clean_student_name(user_input)
            ai_response = translation.get_text(lang_code, "ask_mobile", name=state["student_name"])
            update_state(call_id, state)
            
            response.say(ai_response, voice=voice_name, language=lang_code)
            response.append(gather)
            add_to_history(call_id, "Agent", ai_response)
            return str(response)
        elif state["student_mobile"] is None:
            question_type, _ = detect_question_type(user_input)
            if question_type != "unclear":
                if try_general_question_response(response, call_id, user_input, state):
                    return str(response)
            # Got name, now asking for mobile
            state["student_mobile"] = extract_phone_number(user_input)
            course_name = state["course_selected"]
            from booking_system import get_course_info
            course_info = get_course_info(course_name)
            course_display = course_info["name"] if course_info else course_name
            ai_response = translation.get_text(lang_code, "confirm_details", name=state["student_name"], mobile=state["student_mobile"], course=course_display)
            update_state(call_id, state)
            
            response.say(ai_response, voice=voice_name, language=lang_code)
            response.append(gather)
            add_to_history(call_id, "Agent", ai_response)
            return str(response)
        else:
            # Confirming course selection
            if is_affirmative(user_input):
                # Create booking with all details
                course_name = state["course_selected"]
                from booking_system import get_course_info
                course_info = get_course_info(course_name)
                
                booking = create_booking(
                    phone_number=state["student_mobile"],
                    course_name=course_info["name"] if course_info else "Unknown",
                    demo_date=state["demo_date"],
                    demo_time=state["demo_time"],
                    student_name=state["student_name"]
                )
                
                ai_response = translation.get_text(lang_code, "booking_confirmed", name=state["student_name"], course=course_info["name"] if course_info else course_name, date=state["demo_date"], time=state["demo_time"])
                state["stage"] = "booking_complete"
                update_state(call_id, state)
                
                response.say(ai_response, voice=voice_name, language=lang_code)
                response.hangup()
                add_to_history(call_id, "Agent", ai_response)
                return str(response)
            elif is_negative(user_input):
                ai_response = translation.get_text(lang_code, "course_selection")
                state["stage"] = "course_selection"
                state["student_name"] = None
                state["student_mobile"] = None
                update_state(call_id, state)
            else:
                if try_general_question_response(response, call_id, user_input, state):
                    return str(response)
                ai_response = translation.get_text(lang_code, "confirm_details_doubt")
        
        response.say(ai_response, voice=voice_name, language=lang_code)
        response.append(gather)
        add_to_history(call_id, "Agent", ai_response)
        return str(response)
    
    # =============================
    # STAGE: BOOKING COMPLETE
    # =============================
    elif state["stage"] == "booking_complete":
        course_name = state["course_selected"]
        from booking_system import get_course_info, get_student_booking
        course_info = get_course_info(course_name)
        booking = get_student_booking(student_phone.get(call_id, "unknown"))
        
        if booking:
            closing_msg = translation.get_text(lang_code, "closing", course=booking['course_name'], date=booking['demo_date'], time=booking['demo_time'])
        else:
            closing_msg = translation.get_text(lang_code, "closing_fallback")
            
        response.say(closing_msg, voice=voice_name, language=lang_code)
        response.hangup()
        return str(response)
    
    # =============================
    # STAGE: ACTIVE (QUESTIONS) - FALLBACK / UNREACHABLE
    # =============================
    else:
        question_type, direct_answer = detect_question_type(user_input)
        ai_response = generate_answer(question_type, user_input, state)

    # =============================
    # SPEAK THE RESPONSE
    # =============================
    response.say(ai_response, voice=voice_name, language=lang_code)
    add_to_history(call_id, "Agent", ai_response)
    
    # =============================
    # DECIDE NEXT STEP - INTELLIGENT FOLLOW UP
    # =============================
    gather = Gather(
        input="speech",
        action="/process",
        method="POST",
        timeout=10,
        speechTimeout="auto",
        language=lang_code
    )
    
    # Only speak course selection follow-up prompt if we transitioned to course selection stage.
    # Other stages have their next questions directly built into the main ai_response.
    if state.get("stage") == "course_selection":
        follow_up = translation.get_text(lang_code, "course_selection")
        gather.say(follow_up, voice=voice_name, language=lang_code)
        print(f"[Follow-up] {follow_up}\n")
    
    response.append(gather)
    
    return str(response)

# =============================
# ADDITIONAL DASHBOARD APIS
# =============================
@app.route("/api/bookings", methods=["GET"])
def get_all_bookings():
    """API endpoint to get list of bookings"""
    from booking_system import load_bookings
    bookings = load_bookings()
    return jsonify(bookings)

@app.route("/api/bookings/<phone_or_id>", methods=["DELETE"])
def delete_booking(phone_or_id):
    """API endpoint to delete a specific booking by ID or phone"""
    from booking_system import load_bookings, BOOKINGS_FILE
    bookings = load_bookings()
    
    # Normalize helper to compare phone numbers robustly
    def normalize(p):
        return "".join(c for c in str(p) if c.isdigit() or c == '+')
        
    target = phone_or_id.strip()
    normalized_target = normalize(target)
    
    # Try deleting by booking_id first
    filtered_bookings = []
    deleted_by_id = False
    
    for b in bookings:
        if str(b.get("booking_id", "")).strip() == target:
            deleted_by_id = True
        else:
            filtered_bookings.append(b)
            
    # If no bookings deleted by ID, fallback to phone-based deletion
    if not deleted_by_id:
        filtered_bookings = [
            b for b in bookings 
            if normalize(b.get("student_phone", "")) != normalized_target
        ]
        
    with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered_bookings, f, ensure_ascii=False, indent=2)
        
    return jsonify({"status": "success", "message": f"Booking {phone_or_id} deleted"})

@app.route("/api/bookings", methods=["DELETE"])
def clear_all_bookings():
    """API endpoint to clear all bookings"""
    from booking_system import BOOKINGS_FILE
    with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    return jsonify({"status": "success", "message": "All bookings cleared"})

@app.route("/api/state/<call_id>", methods=["GET"])
def get_call_state_api(call_id):
    """API endpoint to get the state for a calling session"""
    state = get_state(call_id)
    return jsonify(state)

@app.route("/api/tts", methods=["GET"])
def get_tts():
    """Proxy API to fetch high-quality TTS audio from Google Translate"""
    text = request.args.get("text", "").strip()
    lang = request.args.get("lang", "te").strip()
    
    if not text:
        return jsonify({"error": "Text parameter is required"}), 400
        
    import urllib.request
    import urllib.parse
    import ssl
    
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q={urllib.parse.quote(text)}"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context) as response:
            audio_data = response.read()
            
        from flask import make_response
        flask_response = make_response(audio_data)
        flask_response.headers.set('Content-Type', 'audio/mpeg')
        return flask_response
    except Exception as e:
        print(f"[TTS Proxy] Error fetching TTS from Google: {e}")
        return jsonify({"error": str(e)}), 500

# =============================
# RUN THE APP
# =============================
if __name__ == "__main__":
    print("\n[*] Starting ADVANCED AI Sales Agent (10+ Years Experience)...")
    print("[*] Webhook endpoint: POST /voice")
    print("[+] Talks like experienced institute sales counselor")
    print("[+] Human-like responses with intelligence")
    print("[+] Uses real knowledge base for answers\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
