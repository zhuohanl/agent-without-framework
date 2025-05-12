from tools import tools, query_database, search_wikipedia

from typing import List, Dict, Optional, Any
from openai import OpenAI, AzureOpenAI
import json

import os

class Agent:
    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize an AI Agent with optional system prompt.

        Args:
            system_prompt: Initial instructions for the AI
        """
        # Initialize OpenAI client - expects OPENAI_API_KEY in environment
        # self.client = OpenAI()
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # Initialize conversation history
        self.messages = []

        # Set up system prompt if provided, otherwise use default
        default_prompt = """You are a helpful AI assistant with access to a database
        and Wikipedia. Follow these rules:
        1. When asked about data, always check the database first
        2. For general knowledge questions, use Wikipedia
        3. If you're unsure about data, query the database to verify
        4. Always mention your source of information
        5. If a tool returns an error, explain the error to the user clearly
        """

        self.messages.append({
            "role": "system",
            "content": system_prompt or default_prompt
        })

    def execute_tool(self, tool_call: Any) -> str:
        """
        Execute a tool based on the LLM's decision.

        Args:
            tool_call: The function call object from OpenAI's API

        Returns:
            str: JSON-formatted result of the tool execution
        """
        try:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # Execute the appropriate tool. Add more here as needed.
            if function_name == "query_database":
                result = query_database(function_args["query"])
            elif function_name == "search_wikipedia":
                result = search_wikipedia(function_args["query"])
            else:
                result = json.dumps({
                    "error": f"Unknown tool: {function_name}"
                })

            return result

        except json.JSONDecodeError:
            return json.dumps({
                "error": "Failed to parse tool arguments"
            })
        except Exception as e:
            return json.dumps({
                "error": f"Tool execution failed: {str(e)}"
            })

    def process_query(self, user_input: str) -> str:
        """
        Process a user query through the AI agent.

        Args:
            user_input: The user's question or command

        Returns:
            str: The agent's response
        """
        # Add user input to conversation history
        self.messages.append({
            "role": "user",
            "content": user_input
        })

        try:
            max_iterations = 5
            current_iteration = 0

            while current_iteration < max_iterations:  # Limit to 5 iterations
                current_iteration += 1
                completion = self.client.chat.completions.create(
                    # model="gpt-4o",
                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                    messages=self.messages,
                    tools=tools,  # Global tools list from Step 1
                    tool_choice="auto"  # Let the model decide when to use tools
                )

                response_message = completion.choices[0].message

                # If no tool calls, we're done
                if not response_message.tool_calls:
                    self.messages.append(response_message)
                    return response_message.content

                # If tool call
                # Add the model's thinking to conversation history
                self.messages.append(response_message)

                # Process all tool calls
                for tool_call in response_message.tool_calls:
                    try:
                        print("Tool call:", tool_call)
                        result = self.execute_tool(tool_call)
                        print("Tool executed......")
                    except Exception as e:
                        print("Execution failed......")
                        result = json.dumps({
                            "error": f"Tool execution failed: {str(e)}"
                        })

                    print(f"Tool result custom: {result}")

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                    print("Messages:", self.messages)

            # If we've reached max iterations, return a message indicating this
            max_iterations_message = {
                "role": "assistant",
                "content": "I've reached the maximum number of tool calls (5) without finding a complete answer. Here's what I know so far: " + response_message.content
            }
            self.messages.append(max_iterations_message)
            return max_iterations_message["content"]

        except Exception as e:
            error_message = f"Error processing query: {str(e)}"
            self.messages.append({
                "role": "assistant",
                "content": error_message
            })
            return error_message

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.

        Returns:
            List[Dict[str, str]]: The conversation history
        """
        return self.messages