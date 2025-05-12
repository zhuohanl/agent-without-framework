from datetime import datetime
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import Json, UUID_adapter
from agent import Agent

from openai import OpenAI, AzureOpenAI

import os

DB_CONNECTION = os.getenv("DB_CONNECTION")

@dataclass
class MemoryConfig:
    """Configuration for memory management"""
    max_messages: int = 20  # When to summarize
    summary_length: int = 2000  # Max summary length in words
    db_connection: str = DB_CONNECTION

class AgentMemory:
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.session_id = str(uuid.uuid4())
        self.setup_database()

    def setup_database(self):
        """Create necessary database tables if they don't exist"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id UUID NOT NULL,
                user_input TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                tool_calls JSONB,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id SERIAL PRIMARY KEY,
                session_id UUID NOT NULL,
                summary TEXT NOT NULL,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ NOT NULL,
                message_count INTEGER NOT NULL
            );
            """
        ]

        with psycopg2.connect(self.config.db_connection) as conn:
            with conn.cursor() as cur:
                for query in queries:
                    cur.execute(query)

    def store_interaction(self,
                         user_input: str,
                         agent_response: str,
                         tool_calls: Optional[List[Dict]] = None):
        """Store a single interaction in the database"""
        query = """
        INSERT INTO conversations
            (session_id, user_input, agent_response, tool_calls)
        VALUES (%s, %s, %s, %s)
        """

        with psycopg2.connect(self.config.db_connection) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    self.session_id,
                    user_input,
                    agent_response,
                    Json(tool_calls) if tool_calls else None
                ))

    def create_summary(self, messages: List[Dict]) -> str:
        """Create a summary of messages using the LLM"""
        # client = OpenAI()
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # Prepare messages for summarization
        summary_prompt = f"""
        Summarize the following conversation in less than {self.config.summary_length} words.
        Focus on key points, decisions, and important information discovered through tool usage.

        Conversation:
        {messages}
        """

        response = client.chat.completions.create(
            # model="gpt-4o",
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": summary_prompt}]
        )

        return response.choices[0].message.content

    def store_summary(self, summary: str, start_time: datetime, end_time: datetime, message_count: int):
        """Store a conversation summary"""
        query = """
        INSERT INTO conversation_summaries
            (session_id, summary, start_time, end_time, message_count)
        VALUES (%s, %s, %s, %s, %s)
        """

        with psycopg2.connect(self.config.db_connection) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    self.session_id,
                    summary,
                    start_time,
                    end_time,
                    message_count
                ))

    def get_recent_context(self) -> str:
        """Get recent conversations and summaries for context"""
        # First, get the most recent summary
        summary_query = """
        SELECT summary, end_time
        FROM conversation_summaries
        WHERE session_id = %s
        ORDER BY end_time DESC
        LIMIT 1
        """

        # Then get conversations after the summary
        conversations_query = """
        SELECT user_input, agent_response, tool_calls, timestamp
        FROM conversations
        WHERE session_id = %s
        AND timestamp > %s
        ORDER BY timestamp ASC
        """

        with psycopg2.connect(self.config.db_connection) as conn:
            with conn.cursor() as cur:
                # Get latest summary
                cur.execute(summary_query, (self.session_id,))
                summary_row = cur.fetchone()

                if summary_row:
                    summary, last_summary_time = summary_row
                    # Get conversations after the summary
                    cur.execute(conversations_query, (self.session_id, last_summary_time))
                else:
                    # If no summary exists, get recent conversations
                    cur.execute("""
                        SELECT user_input, agent_response, tool_calls, timestamp
                        FROM conversations
                        WHERE session_id = %s
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (self.session_id, self.config.max_messages))

                conversations = cur.fetchall()

        # Format context
        context = []
        if summary_row:
            context.append(f"Previous conversation summary: {summary}")

        for conv in conversations:
            user_input, agent_response, tool_calls, _ = conv
            context.append(f"User: {user_input}")
            if tool_calls:
                context.append(f"Tool Usage: {tool_calls}")
            context.append(f"Assistant: {agent_response}")

        return "\n".join(context)

    def check_and_summarize(self):
        """Check if we need to summarize and do it if necessary"""
        query = """
        SELECT COUNT(*)
        FROM conversations
        WHERE session_id = %s
        AND timestamp > (
            SELECT COALESCE(MAX(end_time), '1970-01-01'::timestamptz)
            FROM conversation_summaries
            WHERE session_id = %s
        )
        """

        with psycopg2.connect(self.config.db_connection) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (self.session_id, self.session_id))
                count = cur.fetchone()[0]

                if count >= self.config.max_messages:
                    # Get messages to summarize
                    cur.execute("""
                        SELECT user_input, agent_response, tool_calls, timestamp
                        FROM conversations
                        WHERE session_id = %s
                        ORDER BY timestamp ASC
                        LIMIT %s
                    """, (self.session_id, count))

                    messages = cur.fetchall()
                    if messages:
                        # Create and store summary
                        summary = self.create_summary(messages)
                        self.store_summary(
                            summary,
                            messages[0][3],  # start_time
                            messages[-1][3],  # end_time
                            len(messages)
                        )

# Update Agent class to use memory.
class MemoryAgent(Agent):
    def __init__(self, memory_config: Optional[MemoryConfig] = None):
        # self.client = OpenAI()
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.memory = AgentMemory(memory_config)
        self.messages = []

        # Initialize with system prompt
        self.messages.append({
            "role": "system",
            "content": "You are a helpful AI assistant..."
        })

    def process_query(self, user_input: str) -> str:
        try:
            # Check if we need to summarize before adding new messages
            self.memory.check_and_summarize()

            # Get context (including summaries) from memory
            context = self.memory.get_recent_context()

            # Add context to messages if it exists
            if context:
                self.messages = [
                    self.messages[0],  # Keep system prompt
                    {
                        "role": "system",
                        "content": f"Previous conversation context:\n{context}"
                    }
                ]

            # Process the query as before...
            response = super().process_query(user_input)

            # Store the interaction in memory
            tool_calls = None
            if hasattr(self, 'last_tool_calls'):
                tool_calls = self.last_tool_calls

            self.memory.store_interaction(
                user_input=user_input,
                agent_response=response,
                tool_calls=tool_calls
            )

            return response

        except Exception as e:
            error_message = f"Error processing query: {str(e)}"
            self.memory.store_interaction(
                user_input=user_input,
                agent_response=error_message
            )
            return error_message

    def execute_tool(self, tool_call: Any) -> str:
        # Store tool calls for memory
        if not hasattr(self, 'last_tool_calls'):
            self.last_tool_calls = []

        result = super().execute_tool(tool_call)

        # Store tool call information
        self.last_tool_calls.append({
            'tool': tool_call.function.name,
            'arguments': tool_call.function.arguments,
            'result': result
        })

        return result