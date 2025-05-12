from memory_agent import MemoryAgent, MemoryConfig  # assuming we saved our code in your_agent.py
import os
from dotenv import load_dotenv

load_dotenv()

# Create an agent
agent = MemoryAgent(
    memory_config=MemoryConfig(
        max_messages=10,  # summarize after 10 messages
        db_connection=os.getenv("DB_CONNECTION")
    )
)

# Simple question-answer interaction
def chat_with_agent(question: str):
    print(f"\nUser: {question}")
    print(f"Assistant: {agent.process_query(question)}")

if __name__ == "__main__":
    chat_with_agent("How many employees do we have in our database?")
    chat_with_agent("What's the average age of employees?")
    chat_with_agent("Find the top 5 departments with the highest average salary")
    chat_with_agent("What were the numbers you just mentioned?")
    chat_with_agent("What are the most interesting trends you can find in our employee data?")