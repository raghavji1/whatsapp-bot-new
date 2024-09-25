from langchain.prompts import PromptTemplate
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langchain.agents.agent_types import AgentType
import logging

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define the custom prompt template
custom_prompt = '''You are a job-seeking website that holds all job openings in your knowledge base, including information about job URL, position name, vessel type, salary, joining date, and country. When a user asks for specific job openings, extract and return the relevant information in the following format:

    JOB Title: "{position_name}"
    
    If no matching records are found, return: "No matching jobs found for the specified criteria."
    make sure you are return the answer as string ,
    we will provide maximum 5 entries at a time and minimum one 
    ANSWER SHOULD BE IN MAXIMUM 1400 WORDS DO NOT GIVE ANSWER'S IN MORE THAN 1400 WORDS
    Here is the query:
    {query}
    AI Answer: String(answer) 
'''

def get_answer_from_csv(query):
    prompt_template = PromptTemplate(template=custom_prompt, input_variables=["query"])

    # Create the CSV agent
    csv_agent = create_csv_agent(
        llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo", api_key=api_key),
        path="database/data.csv",  # Directly passing the path to the CSV
        prompt_template=prompt_template,
        verbose=True,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        allow_dangerous_code=True,
        handle_parsing_errors=True  # Opt-in for executing arbitrary code
    )

    # Invoke the agent with the query and return the result as a string
    final_answer = csv_agent.invoke(query)
    return str(final_answer['output'])

# Example usage
# query = '''Give me job details in this formate
#     JOB Title: "{position_name}"
#     Vessel Type: "{vessel_type}"
#     Date of Joining: "{date_of_joining}"
#     Salary: "{salary}"
#     Apply Link: "{job_url}"
#  for the position of chief engineer on a general cargo vessel with a salary of more than 4800 USD'''
# print(get_answer_from_csv(query))
