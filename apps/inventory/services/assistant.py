import json
from openai import OpenAI
from apps.customers.models import Customer

# Initialize the OpenAI client (It will look for your API key automatically)

client = OpenAI()

def process_voice_onboarding(spoken_hindi_text, session_data=None):
    if session_data is None:
        session_data = {
            "store_name": None,
            "owner_name": None,
            "phone_number": None,
            "state_region": None,
            "gstin": None,
        }

        # System prompt directing the AI to behave like a sharp Indian wholesale clerk

        system_instruction = (
        "You are an AI assistant for a traditional Indian fishing net wholesaler. "
        "Your job is to extract customer profile details from text and return them strictly in valid JSON format. "
        "Map values to these keys: 'store_name', 'owner_name', 'phone_number', 'state_region', 'gstin'. "
        "If a piece of information is not present in the text, leave its value as null. Do not guess fields."
    )

    # Call OpenAI to extract structural data from the messy spoken Hindi text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"}, # Forces JSON response
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Extract details from this spoken text: {spoken_hindi_text}"}
        ]
    )

    # Parse the incoming JSON data from the AI
    extracted_data = json.loads(response.choices[0].message.content)

    # Merge newly extracted details into our active session tracking dictionary
    for key in session_data.keys():
        if extracted_data.get(key):
            session_data[key] = extracted_data[key]

    # DEFINE REQUIRED VALIDATION FIELDS
    required_fields = ["store_name", "owner_name", "phone_number", "state_region"]
    missing_fields = [field for field in required_fields if not session_data[field]]

    # CHECK FOR MISSING FIELDS AND PROMPT IN HINDI
    if missing_fields:
        first_missing = missing_fields[0]

        # Custom Hindi voice prompts depending on what field is missing
        prompts = {
            "store_name": "Dukan ka naam kya hai?",
            "owner_name": "Dukan ke malik (owner) ka naam kya hai?",
            "phone_number": "Unka phone number kya hai?",
            "state_region": "Woh customer kis state ya region se hain (Bihar, UP, WB)?"
        }

        return {
            "status": "incomplete",
            "message": prompts[first_missing],
            "current_session": session_data
        }

    # ALL FIELDS ARE PRESENT -> SAVE INDEPENDENT CLIENT DIRECTLY TO DJANGO DB
    new_client = Customer.objects.create(
        store_name=session_data["store_name"],
        owner_name=session_data["owner_name"],
        phone_number=session_data["phone_number"],
        state_region=session_data["state_region"],
        gstin=session_data.get("gstin")
    )

    return {
        "status": "success",
        "message": f"Naya customer '{new_client.store_name}' safaltapoorvak save kar liya gaya hai!",
        "current_session": session_data
    }
