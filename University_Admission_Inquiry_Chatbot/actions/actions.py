from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import os
import requests
import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionGeminiFallback(Action):
    def name(self) -> Text:
        return "action_gemini_fallback"

    def __init__(self):
        # Official university links
        self.official_links = {
            "faculty": "https://su.edu.pk/faculty/faculty-of-computing-and-information-technology",
            "university": "https://su.edu.pk/",
            "admissions": "https://admissions.su.edu.pk",
            "cs_program": "https://su.edu.pk/department/cs",
            "it_program": "https://su.edu.pk/department/it",
            "se_program": "https://su.edu.pk/department/se"
        }
        
        # Department contacts
        self.contacts = {
            "faculty": "fcit@su.edu.pk",
            "admission": "admission@su.edu.pk",
            "helpdesk": "048-9230811" # Assuming this is a general helpdesk number
        }

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message.get("text", "").strip()
        logger.info(f"Attempting Gemini fallback for user message: '{user_message}'")

        try:
            # Try Gemini API first
            gemini_raw_response_data = self.get_gemini_raw_response_data(user_message)
            processed_gemini_response = self.process_api_response(user_message, gemini_raw_response_data)
            
            # If the processed response is a special "fallback_signal", then trigger smart fallback
            if processed_gemini_response == "FALLBACK_SIGNAL":
                logger.info("Gemini response explicitly triggered smart fallback.")
                fallback = self.generate_smart_fallback(user_message)
                dispatcher.utter_message(text=fallback)
            else:
                dispatcher.utter_message(text=processed_gemini_response)
                logger.info("Gemini API call successful, dispatched response.")
        
        except Exception as e:
            logger.error(f"Gemini API failed or returned invalid format (or other error): {str(e)}")
            # If Gemini fails or returns an invalid format, use smart fallback
            fallback = self.generate_smart_fallback(user_message)
            dispatcher.utter_message(text=fallback)
            logger.info("Dispatched smart fallback message due to API failure.")
            
        return []

    def get_gemini_raw_response_data(self, query: str) -> Dict[Text, Any]:
        """Get raw JSON response from Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set.")
            raise ValueError("Gemini API key not configured")
        
        prompt = self.create_contextual_prompt(query)
        logger.debug(f"Gemini prompt: {prompt}")

        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                json={
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.2, # Slightly lower to encourage less creativity
                        "topP": 0.7,      # Slightly lower to focus on more probable tokens
                        "maxOutputTokens": 350
                    }
                },
                timeout=8
            )
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request failed: {str(e)}")
            raise # Re-raise the exception to be caught by the run method's try-except
        except Exception as e:
            logger.error(f"An unexpected error occurred during Gemini API call: {str(e)}")
            raise

    def create_contextual_prompt(self, query: str) -> str:
        """Create optimized prompt with university context and strong fallback instruction."""
        return f"""
        Role: Official University of Sargodha Faculty of Computing and IT Admission and Information Assistant.
        You are a highly professional, concise, and accurate chatbot.

        Current Official Links (USE THESE IF APPLICABLE, DO NOT INVENT):
        - Faculty: {self.official_links['faculty']}
        - University: {self.official_links['university']}
        - Admissions: {self.official_links['admissions']}
        - CS Program: {self.official_links['cs_program']}
        - IT Program: {self.official_links['it_program']}
        - SE Program: {self.official_links['se_program']}

        Query: "{query}"

        Response Guidelines:
        1.  **Direct and Concise:** Respond in 1-3 sentences.
        2.  **Accuracy First:** Prioritize absolute accuracy. Do not generate speculative or incorrect information.
        3.  **Strictly University of Sargodha FCIT Context:** Only provide information relevant to the University of Sargodha's Faculty of Computing and IT, or general admissions.
        4.  **Use Official Links:** If a query relates to academic programs, faculty, or admissions, *you MUST include the most relevant official link from the provided list in your answer.*
        5.  **Professional Tone:** Always maintain a polite and professional tone.
        6.  **Explicit "Cannot Answer" Rule (CRITICAL):**
            * **IF** you cannot confidently provide an accurate answer directly from the provided context or general public knowledge about University of Sargodha.
            * **OR IF** the query is outside the scope of university admissions/information (e.g., personal details, current events, jokes, non-academic topics).
            * **THEN** you MUST respond with *only one of the following exact phrases*:
                * "I don't have enough information."
                * "This specific detail is not available."
                * "I cannot provide that specific information."
                * "My knowledge is limited on this topic."
            * **DO NOT** try to guess, generate irrelevant information, or provide a generic "I'm a language model..." response. Just use one of these specific phrases.
        7.  **No Hallucinations:** Do not invent facts, names, or policies.
        """

    def process_api_response(self, query: str, data: dict) -> str:
        """Validate and enhance the API response, handling explicit 'no answer' phrases and detecting irrelevant answers."""
        try:
            gemini_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            logger.debug(f"Raw Gemini response text: {gemini_text}")
            
            # --- Check for explicit "no answer" phrases from Gemini's response ---
            no_answer_phrases = [
                "i don't have enough information", 
                "this specific detail is not available", 
                "i cannot provide that specific information",
                "my knowledge is limited on this topic"
            ]
            
            gemini_text_lower = gemini_text.lower()
            if any(phrase in gemini_text_lower for phrase in no_answer_phrases):
                logger.warning(f"Gemini explicitly indicated 'no answer' for query: '{query}'.")
                return "FALLBACK_SIGNAL" # Signal to trigger smart fallback in run method

            # --- Additional Check: Does Gemini's response seem relevant and contain a link if expected? ---
            # This is a heuristic to catch irrelevant answers like the VC example
            # If the query implies needing official info/link (e.g., programs, admissions, faculty)
            query_lower = query.lower()
            requires_link_keywords = ["program", "admission", "faculty", "cs", "it", "se", "fee", "criteria", "apply", "course", "department"]
            
            if any(k in query_lower for k in requires_link_keywords):
                has_relevant_link = False
                for link in self.official_links.values():
                    if link in gemini_text:
                        has_relevant_link = True
                        break
                
                # If Gemini should have given a link but didn't, trigger fallback
                if not has_relevant_link:
                    logger.warning(f"Gemini response for query '{query}' did not contain an expected official link. Triggering smart fallback.")
                    return "FALLBACK_SIGNAL"
            
            # --- If Gemini provided an answer and it seems relevant, ensure a link is added if missing ---
            # This is only for valid answers that Gemini actually tried to give
            if not any(link in gemini_text for link in self.official_links.values()):
                relevant_link = self.determine_relevant_link(query)
                gemini_text += f"\n\nFor official information, please visit: {relevant_link}"
                logger.debug(f"Added relevant link: {relevant_link}")
                
            return gemini_text
            
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Invalid response format from Gemini API: {e}. Data: {data}")
            raise ValueError("Invalid response format from Gemini API") # Re-raise to trigger fallback

    def determine_relevant_link(self, query: str) -> str:
        """Select the most appropriate official link based on query"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["faculty", "staff", "teacher", "lecturer"]):
            return self.official_links["faculty"]
        elif any(term in query_lower for term in ["cs", "computer science", "bs-cs", "bs cs"]):
            return self.official_links["cs_program"]
        elif any(term in query_lower for term in ["it", "information technology", "bs-it", "bs it"]):
            return self.official_links["it_program"]
        elif any(term in query_lower for term in ["se", "software engineering", "bs-se", "bs se"]):
            return self.official_links["se_program"]
        elif any(term in query_lower for term in ["admission", "admissions", "apply", "داخلہ", "fee", "fees", "criteria", "eligibility"]):
            return self.official_links["admissions"]
        else:
            return self.official_links["university"]

    def generate_smart_fallback(self, query: str) -> str:
        """Generate context-aware fallback message"""
        relevant_link = self.determine_relevant_link(query)
        
        # Check for Urdu Unicode range to detect Urdu characters
        if any('\u0600' <= char <= '\u06FF' for char in query):
            return (f"معذرت، میں آپ کے سوال کا صحیح جواب نہیں دے پا رہا۔ برائے مہربانی مزید وضاحت فرمائیں۔\n\n"
                    f"سرکاری معلومات کے لیے یہاں تشریف لائیں: {relevant_link}\n"
                    f"یا مزید معلومات کے لیے اس نمبر پر رابطہ کریں: {self.contacts['helpdesk']}\n\n"
                    f"کیا میں آپ کی کسی اور چیز میں مدد کر سکتا ہوں؟")
            
        # English response
        return (f"I couldn't retrieve the requested information or provide a confident answer. Please visit our official page:\n"
                f"{relevant_link}\n\n"
                f"For direct assistance, you can contact us at: {self.contacts['helpdesk']}\n\n"
                f"How else may I help you today?")