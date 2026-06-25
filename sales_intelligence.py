# Advanced Sales Intelligence for 10+ Years Experience Sales Person
# This module handles conversations like a seasoned institute sales person

from knowledge_base import COURSE_INFO, FAQS

class SalesIntelligence:
    """
    10+ years experienced institute sales person intelligence
    """
    
    def __init__(self):
        self.experience_level = "10+ years"
        self.style = "friendly_mentor"
    
    def get_introduction(self):
        """
        Warm introduction like experienced sales person
        """
        return (
            "హలో! నేను రాకీ. 'Job Kottu' Agency నుండి call చేస్తున్నాను."
            "నాకు soft skills and technical training లో 10 years experience ఉంది."
            "ఇక్కడ మేము engineering students ని software engineers గా మార్చేస్తాము."
            "ఇంటర్ నుండి ఉద్యోగం వరకు - మేము ఉన్నాము."
            "Technical course లో interest ఉంటే, నేను useful information ఇస్తాను."
            "Software engineer కాదా లేదా technical skills learn చేయాలనుకుంటున్నావా?"
        )
    
    def get_interest_question(self):
        """
        Simple interest check in Telugu slang
        """
        return "Engineering student ఆవా లేదా technical skills learn చేయాలనుకుంటున్నావా? Yes లేదా no చెప్పు."
    
    def get_encouragement_response(self):
        """
        Response when student shows interest in Telugu slang
        """
        return (
            "బాగుంది! నీ interest చూసి నాకు చాలా సంతోషం."
            "నేను నీకు ఏమైనా చెప్తాను."
            "ఈ course లో నీరు actual industry practices, real projects, job-ready skills నేర్చుకుంటావు."
            "మన 85% students ని నేను personally చూసాను - top companies లో placed అవ్వటం."
            "ఇప్పుడు నీకు specifically ఏమైనా తెలుసుకోవాలనుకుంటున్నావా?"
        )
    
    def get_rejection_response(self):
        """
        Respectful exit when student says no in Telugu slang
        """
        return (
            "సరే, ఏ problem లేదు. తర్వాత నీకు interest వచ్చే తర్వాత call చేస్తూ ఉంటాను."
            "All the best నీ studies కి. నీ bright future కి ఎలాంటి సమస్య ఉండదు. Thank you!"
        )
    
    def get_mid_flow_answer_intro(self, question_type):
        """
        Introduction before answering mid-flow questions in Telugu slang
        """
        responses = {
            "fees_and_discounts": "నీకు సరైన question బ్రో! ఈ investment గురించి honest explain చేస్తాను బ్రో. ",
            "placement_guarantee": "చాలా important question బ్రో! నేను నా 10 years experience నుండి చెప్తాను బ్రో. ",
            "course_timing": "Schedule ఖచ్చితంగా flexible బ్రో! నీ convenience చూసి చెప్తా బ్రో. ",
            "projects_real": "ఇది చాలా practical question బ్రో! నేను students నిర్మిన real projects చూపిస్తాను బ్రో. ",
            "prerequisite_skills": "నీకు confusion ఉందా బ్రో? అందుకే నేను ఉన్నాను బ్రో. Clear చేస్తాను బ్రో. ",
            "what_is_full_stack": "బాగుందా బ్రో! నీకు simple example ఇస్తా బ్రో - నీరు understand చేసుకుంటారు బ్రో. ",
            "salary_expectations": "Salary గురించి నేను honest explain చేస్తాను బ్రో - realistic figures బ్రో. ",
            "placement": "Placements గురించి నేను నా students నుండి నేరుగా stories చెప్తాను బ్రో. "
        }
        return responses.get(question_type, "ఈ question గురించి నీకు clear చేస్తాను:")
    
    def get_after_answer_continuation(self):
        """
        Smart follow-up after answering questions
        """
        continuations = [
            "ఇక్కడ చెప్పిన విషయాలు clear అయ్యాయా? నీకు ఇంకా doubt ఉందా?",
            "ఈ answer సరిపోతుందా? నీకు మరో angle నుండి విచారించాలనుకుంటున్నావా?",
            "ఇది account చేసుకో - నీకు ఇదే answer చాలా సాధారణమైనది. More detail కావాలా?",
            "నీ concern clear అయ్యాలని నేను నిశ్చితం. ఇంకా question ఉందా?",
            "ఇక్కడ చెప్పిన విషయం నీకు convincing అయ్యాయా? మీకు నా numbers trust చేయవచ్చు.",
            "నీకు ఇంకా ఏమైనా doubt ఉందా? నేను clear చేస్తాను - ఏమైనా అడుగు.",
            "ఈ explanation సరిపోతుందా? నీకు practical example కావాలా?",
            "మీరు ఇంకా ఏమైనా తెలుసుకోవాలనుకుంటున్నారా? నేను ఉన్నాను."
        ]
        return continuations[0]  # Can rotate these
    
    def get_demo_push_message(self, turn_number):
        """
        Smart demo push after multiple conversations
        """
        if turn_number >= 4:
            return (
                "తర్వాత నేను నీకు suggest చేస్తాను - free demo class కి వెళ్లు."
                "అక్కడ నీరు live coding చూస్తాయ, actual mentors తో కలిసేటాయ, మరియు నీ doubts clear చేస్తాయ."
                "1 hour, completely free, no pressure. మీకు ఆసక్తి ఉందా?"
            )
        return None
    
    def get_closing_message(self):
        """
        Professional closing if call ends in Telugu slang
        """
        return (
            "ఇది చాలా nice conversation. నీతో మాట్లాడటం చాలా బాగా ఉంది."
            "ఇక్కడ చెప్పిన విషయాలు consider చేసుకో."
            "తర్వాత నీకు questions ఉంటే, నా contact number వాడు."
            "నీ brilliant future కి all the best! Thank you!"
        )
    
    def get_objection_handler(self, objection_type):
        """
        Handle common objections like experienced sales person
        """
        handlers = {
            "expensive": (
                "నీకు fee చాలా ఎక్కువ అనిపిస్తుందా? నేను చెప్తాను -"
                "ఇది investment, expense కాదు. నీరు 6 months లో ఈ fee కు doubly earn చేస్తాయ."
                "ఇలాంటి training లేకుండా, నీరు 2-3 years waste చేస్తాయ. Investment చెసుకో!"
            ),
            "time": (
                "Time manage చేయాలనుకుంటున్నావా? పీర్ బోధ!"
                "మన course పూర్తిగా మీ schedule నుండి flexible."
                "పూర్తి-time job చేస్తూ కూడా, evening batches లో చేయవచ్చు."
            ),
            "doubt": (
                "Doubt ఉందా? అందుకే నేను ఉన్నాను!"
                "చెల్లు, నీరు try చేసుకో. 30-day money back guarantee ఉంది."
                "ఉండకపోతే, complete refund. Risk లేదు!"
            ),
            "job_guarantee": (
                "నీరు placement guarantee అన్నారా? నేను guarantee ఇవ్వను -"
                "కానీ నీరు काम చేస్తే, 90% సంభావ్యత ఉంది।"
                "మన 85% students ని personally నేను place చేసాను."
                "నీరు serious ఉండాలి."
            )
        }
        return handlers.get(objection_type, "ఈ doubt గురించి మీరు చింతపడకండి. నీరు sure చేసుకోవచ్చు.")

# Create global instance
sales_person = SalesIntelligence()

def get_intro_message():
    return sales_person.get_introduction()

def get_interest_check():
    return sales_person.get_interest_question()

def get_yes_response():
    return sales_person.get_encouragement_response()

def get_no_response():
    return sales_person.get_rejection_response()

def get_answer_intro(q_type):
    return sales_person.get_mid_flow_answer_intro(q_type)

def get_after_answer():
    return sales_person.get_after_answer_continuation()

def get_demo_message(turn):
    return sales_person.get_demo_push_message(turn)

def get_close():
    return sales_person.get_closing_message()

def handle_objection(obj_type):
    return sales_person.get_objection_handler(obj_type)
