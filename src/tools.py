import json
import psycopg2
import wikipedia
from typing import Dict, List, Any

import os
from dotenv import load_dotenv

load_dotenv()

DB_CONNECTION = os.getenv("DB_CONNECTION")

def get_database_schema(schema_name: str) -> str:
    """Retrieve the database schema information"""
    schema_query = f"""
    SELECT
        t.table_name,
        array_agg(
            c.column_name || ' ' ||
            c.data_type ||
            CASE
                WHEN c.is_nullable = 'NO' THEN ' NOT NULL'
                ELSE ''
            END
        ) as columns
    FROM information_schema.tables t
    JOIN information_schema.columns c
        ON c.table_name = t.table_name
    WHERE t.table_schema = '{schema_name}'
        AND t.table_type = 'BASE TABLE'
    GROUP BY t.table_name;
    """

    try:
        with psycopg2.connect(DB_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_query)
                schema = cur.fetchall()

                # Format schema information
                schema_str = "Database Schema:\n"
                for table_name, columns in schema:
                    schema_str += f"\n{table_name}\n"
                    for col in columns:
                        schema_str += f"  - {col}\n"

                return schema_str
    except Exception as e:
        return f"Error fetching schema: {str(e)}"

# First, we define how the LLM should understand our tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": """Execute a PostgreSQL SELECT query and return the results.
                            Only SELECT queries are allowed for security reasons.
                            Returns data in JSON format.
                            Available tables and their schemas:
                            
                            department
                            - dept_name character varying NOT NULL
                            - id character NOT NULL

                            department_employee
                            - department_id character NOT NULL
                            - from_date date NOT NULL
                            - to_date date NOT NULL
                            - employee_id bigint NOT NULL

                            department_manager
                            - employee_id bigint NOT NULL
                            - department_id character NOT NULL
                            - from_date date NOT NULL
                            - to_date date NOT NULL

                            employee
                            - id bigint NOT NULL
                            - birth_date date NOT NULL
                            - first_name character varying NOT NULL
                            - last_name character varying NOT NULL
                            - gender USER-DEFINED NOT NULL
                            - hire_date date NOT NULL

                            salary
                            - amount bigint NOT NULL
                            - from_date date NOT NULL
                            - to_date date NOT NULL
                            - employee_id bigint NOT NULL

                            title
                            - title character varying NOT NULL
                            - from_date date NOT NULL
                            - to_date date
                            - employee_id bigint NOT NULL
                            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": """The SQL SELECT query to execute.
                                        Must start with SELECT and should not
                                        contain any data modification commands.
                                        All tables sit under database named employees and schema named employees.
                                        Make sure you fully qualify the table name with the schema name.
                                        For example, use employees.employee instead of just employee.
                                        Example: SELECT * FROM employees.employee WHERE age > 30"""
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": """Search Wikipedia and return a concise summary.
                            Returns the first three sentences of the most
                            relevant article.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to search for on Wikipedia"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

# Now implement the actual tool functions
# Updated database query function
def query_database(query: str) -> str:
    """
    Execute a PostgreSQL query with schema awareness
    """
    if not query.lower().strip().startswith('select'):
        return json.dumps({
            "error": "Only SELECT queries are allowed for security reasons.",
            "schema": get_database_schema()  # Return schema for reference
        })

    try:
        with psycopg2.connect(DB_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute(query)

                # Get column names from cursor description
                columns = [desc[0] for desc in cur.description]

                # Fetch results and convert to list of dictionaries
                results = []
                for row in cur.fetchall():
                    results.append(dict(zip(columns, row)))

                return json.dumps({
                    "success": True,
                    "data": str(results),
                    "row_count": len(results),
                    "columns": columns
                })

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "schema": get_database_schema()  # Return schema on error for help
        })


def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia and return a concise summary.
    Handles disambiguation and missing pages gracefully.
    """
    try:
        # Try to get the most relevant page summary
        summary = wikipedia.summary(
            query,
            sentences=3,
            auto_suggest=True,
            redirect=True
        )

        return json.dumps({
            "success": True,
            "summary": summary,
            "url": wikipedia.page(query).url
        })

    except wikipedia.DisambiguationError as e:
        # Handle multiple matching pages
        return json.dumps({
            "error": "Disambiguation error",
            "options": e.options[:5],  # List first 5 options
            "message": "Topic is ambiguous. Please be more specific."
        })
    except wikipedia.PageError:
        return json.dumps({
            "error": "Page not found",
            "message": f"No Wikipedia article found for: {query}"
        })
    except Exception as e:
        return json.dumps({
            "error": "Unexpected error",
            "message": str(e)
        })