from flask import Flask, request, session
from dotenv import load_dotenv
from langchain_core.prompts.prompt import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAI
import os
from backend_csv import get_answer_from_csv
from twilio_api import send_message
import logging
from concurrent.futures import ThreadPoolExecutor
import time
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')
logging.basicConfig(level=logging.INFO)

# MongoDB setup
mongo_client = MongoClient(os.getenv('MONGODB_URI'))

db = mongo_client["chat_db_my"]
chats_collection = db["chats"]

template = """The following is a friendly conversation between a human and an AI. The AI acts as a recruiter. The AI is talkative and asks the user specific details in an interactive way.

Current conversation:
{history}
Human: {input}
AI Assistant:
"""

PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)

def chat_llm(query):
    llm = OpenAI(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        temperature=0.5
    )
    conversation = ConversationChain(
        prompt=PROMPT,
        llm=llm,
        verbose=False,
        memory=ConversationBufferMemory(human_prefix="Candidate", ai_prefix="AI"),
    )
    response = conversation.invoke(query)
    return response['response']

executor = ThreadPoolExecutor()

def store_chat(sender_id, ai_message, human_message):
    chat = {
        "ai_message": ai_message,
        "human_message": human_message
    }
    chats_collection.update_one(
        {"session_id": sender_id},
        {"$push": {"chat": chat}, "$set": {"updated_at": datetime.now()}},
        upsert=True
    )
    

@app.route('/chat', methods=['POST'])
def receive_message():
    try:
        message = request.form['Body']
        sender_id = request.form['From']
        logging.info(f"Received message from {sender_id}: {message}")
        
        # Initialize or retrieve user session data
        if 'user_answers' not in session:
            session['user_answers'] = {
                "greeting": None,
                "name": None,
                "position": None,
                "vessel": None,
                "salary": None,
                "citizenship": None
            }
        
        user_answers = session['user_answers']
        ai_message = ""

        if user_answers["greeting"] is None:
            user_answers["greeting"] = message
            ai_message = 'Hello there! This is the Job Search Platform for Ships. Can I have your name, please?'
        elif user_answers["name"] is None:
            user_answers["name"] = message
            ai_message = f"Great to meet you, *{(user_answers['name'].capitalize())}*! What position are you looking for?"
        elif user_answers["position"] is None:
            user_answers["position"] = message
            ai_message = f"What type of vessel are you interested in, {(user_answers['name']).capitalize()}?"
        elif user_answers["vessel"] is None:
            user_answers["vessel"] = message
            ai_message = f"What is your desired salary for this position?"
        elif user_answers["salary"] is None:
            user_answers["salary"] = message
            ai_message = f"And your citizenship?"
        elif user_answers["citizenship"] is None:
            user_answers["citizenship"] = message
            final_prompt = f"""Give me all in 1500 words maximum job details in this format:
            *JOB Title*: position_name
            *Vessel Type*: vessel_type
            *Date of Joining*: date_of_joining
            *Salary*: salary
            Apply Link*: -one link only 'without writing [Job Link] just provide link'
            for the position of {user_answers['position']} on a {user_answers['vessel']} with a salary of more than or equal to {user_answers['salary']} USD
            """
            logging.info("Final prompt generated: " + final_prompt)
            send_message(sender_id, "Please wait while I check the available openings. Maximum waiting time is *30* seconds")
            executor.submit(process_query, sender_id, final_prompt)
            session.pop('user_answers', None)  # Clear user answers after processing
            return 'Valid response', 200

        # Store the updated answers in session
        session['user_answers'] = user_answers
        
        # Store chat in MongoDB
        store_chat(sender_id, ai_message, message)

        # Send the next question to the user
        send_message(sender_id, ai_message)
        return 'Valid response', 200
    
    except Exception as e:
        logging.error(f"Error handling the message: {e}")
        return 'Error processing request', 500

def process_query(sender_id, query):
    try:
        # Get the job openings from CSV based on the query
        relevant = get_answer_from_csv(query)
        time.sleep(15)
        # Send the results back to the user
        send_message(sender_id, relevant)
        thank_message = "Thank You For Using Our Services. To continue chatting with AI, type 'CHAT' or type 'JOB' for searching more job options."
        send_message(sender_id, thank_message)
    except Exception as e:
        logging.error(f"Error in processing query: {e}")
        send_message(sender_id, "Error processing your request. Please try again later.")


if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
