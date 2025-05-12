This is a repo to re-construct the tutorial [How to Build AI Agents Without Frameworks: A Step-by-Step Guide](https://www.pondhouse-data.com/blog/ai-agents-from-scratch).

In case of change of the webpage, the tutorial is also available in [PDF](tutorial/how_to_build_ai_agents_without_frameworks_tutorial.pdf).

# How to run

## Step 1:
Set up the database and load data by referring to this [README.md](data/README.md).

## Step 2:
Install `uv`. See [installation methods](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)

## Step 3:
```
uv run python src/main.py
```
For the first run, `uv` will set up `.venv` for you

## Example output
```
User: How many employees do we have in our database?
Tool call: ChatCompletionMessageToolCall(id='call_xdECyFJQTGlr1OJKSx44Ut11', function=Function(arguments='{"query":"SELECT COUNT(*) AS employee_count FROM employees.employee"}', name='query_database'), type='function')
Tool executed......
Tool result custom: {"success": true, "data": "[{'employee_count': 300024}]", "row_count": 1, "columns": ["employee_count"]}
Messages: [{'role': 'system', 'content': 'You are a helpful AI assistant...'}, {'role': 'user', 'content': 'How many employees do we have in our database?'}, ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_xdECyFJQTGlr1OJKSx44Ut11', function=Function(arguments='{"query":"SELECT COUNT(*) AS employee_count FROM employees.employee"}', name='query_database'), type='function')]), {'role': 'tool', 'tool_call_id': 'call_xdECyFJQTGlr1OJKSx44Ut11', 'content': '{"success": true, "data": "[{\'employee_count\': 300024}]", "row_count": 1, "columns": ["employee_count"]}'}]
Assistant: There are 300,024 employees in the database.

User: What's the average age of employees?
Tool call: ChatCompletionMessageToolCall(id='call_oKiq9iXexHoPgQt7ZbepePem', function=Function(arguments='{"query":"SELECT AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))) AS average_age FROM employees.employee"}', name='query_database'), type='function')
Tool executed......
Tool result custom: {"success": true, "data": "[{'average_age': Decimal('66.2806975441964643')}]", "row_count": 1, "columns": ["average_age"]}
Messages: [{'role': 'system', 'content': 'You are a helpful AI assistant...'}, {'role': 'system', 'content': 'Previous conversation context:\nUser: How many employees do we have in our database?\nTool Usage: [{\'tool\': \'query_database\', \'result\': \'{"success": true, "data": "[{\\\'employee_count\\\': 300024}]", "row_count": 1, "columns": ["employee_count"]}\', \'arguments\': \'{"query":"SELECT COUNT(*) AS employee_count FROM employees.employee"}\'}]\nAssistant: There are 300,024 employees in the database.'}, {'role': 'user', 'content': "What's the average age of employees?"}, ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_oKiq9iXexHoPgQt7ZbepePem', function=Function(arguments='{"query":"SELECT AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))) AS average_age FROM employees.employee"}', name='query_database'), type='function')]), {'role': 'tool', 'tool_call_id': 'call_oKiq9iXexHoPgQt7ZbepePem', 'content': '{"success": true, "data": "[{\'average_age\': Decimal(\'66.2806975441964643\')}]", "row_count": 1, "columns": ["average_age"]}'}]
Assistant: The average age of employees in the database is approximately 66.3 years old.

User: Find the top 5 departments with the highest average salary
Tool call: ChatCompletionMessageToolCall(id='call_TjrzzOlDcryF6PVF3TiQ4wy8', function=Function(arguments='{"query":"SELECT d.dept_name, AVG(s.amount) AS avg_salary\\nFROM employees.department AS d\\nJOIN employees.department_employee AS de ON d.id = de.department_id\\nJOIN employees.salary AS s ON de.employee_id = s.employee_id\\nGROUP BY d.dept_name\\nORDER BY avg_salary DESC\\nLIMIT 5"}', name='query_database'), type='function')
Tool executed......
Tool result custom: {"success": true, "data": "[{'dept_name': 'Sales', 'avg_salary': Decimal('80667.605755337693')}, {'dept_name': 'Marketing', 'avg_salary': Decimal('71913.200004191532')}, {'dept_name': 'Finance', 'avg_salary': Decimal('70489.364896996098')}, {'dept_name': 'Research', 'avg_salary': Decimal('59665.181701268599')}, {'dept_name': 'Production', 'avg_salary': Decimal('59605.482461651448')}]", "row_count": 5, "columns": ["dept_name", "avg_salary"]}
Messages: [{'role': 'system', 'content': 'You are a helpful AI assistant...'}, {'role': 'system', 'content': 'Previous conversation context:\nUser: What\'s the average age of employees?\nTool Usage: [{\'tool\': \'query_database\', \'result\': \'{"success": true, "data": "[{\\\'employee_count\\\': 300024}]", "row_count": 1, "columns": ["employee_count"]}\', \'arguments\': \'{"query":"SELECT COUNT(*) AS employee_count FROM employees.employee"}\'}, {\'tool\': \'query_database\', \'result\': \'{"success": true, "data": "[{\\\'average_age\\\': Decimal(\\\'66.2806975441964643\\\')}]", "row_count": 1, "columns": ["average_age"]}\', \'arguments\': \'{"query":"SELECT AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))) AS average_age FROM employees.employee"}\'}]\nAssistant: The average age of employees in the database is approximately 66.3 years old.\nUser: How many employees do we have in our database?\nTool Usage: [{\'tool\': \'query_database\', \'result\': \'{"success": true, "data": "[{\\\'employee_count\\\': 300024}]", "row_count": 1, "columns": ["employee_count"]}\', \'arguments\': \'{"query":"SELECT COUNT(*) AS employee_count FROM employees.employee"}\'}]\nAssistant: There are 300,024 employees in the database.'}, {'role': 'user', 'content': 'Find the top 5 departments with the highest average salary'}, ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_TjrzzOlDcryF6PVF3TiQ4wy8', function=Function(arguments='{"query":"SELECT d.dept_name, AVG(s.amount) AS avg_salary\\nFROM employees.department AS d\\nJOIN employees.department_employee AS de ON d.id = de.department_id\\nJOIN employees.salary AS s ON de.employee_id = s.employee_id\\nGROUP BY d.dept_name\\nORDER BY avg_salary DESC\\nLIMIT 5"}', name='query_database'), type='function')]), {'role': 'tool', 'tool_call_id': 'call_TjrzzOlDcryF6PVF3TiQ4wy8', 'content': '{"success": true, "data": "[{\'dept_name\': \'Sales\', \'avg_salary\': Decimal(\'80667.605755337693\')}, {\'dept_name\': \'Marketing\', \'avg_salary\': Decimal(\'71913.200004191532\')}, {\'dept_name\': \'Finance\', \'avg_salary\': Decimal(\'70489.364896996098\')}, {\'dept_name\': \'Research\', \'avg_salary\': Decimal(\'59665.181701268599\')}, {\'dept_name\': \'Production\', \'avg_salary\': Decimal(\'59605.482461651448\')}]", "row_count": 5, "columns": ["dept_name", "avg_salary"]}'}]
Assistant: The top 5 departments with the highest average salary are:

1. Sales: $80,668
2. Marketing: $71,913
3. Finance: $70,489
4. Research: $59,665
5. Production: $59,605

These departments offer the highest average salaries among all departments in the database.

User: What were the numbers you just mentioned?
Assistant: Here are the numbers I just mentioned:

- Total number of employees in the database: **300,024**
- Average age of employees: **66.3 years old**
- Top 5 departments with the highest average salary:
  1. Sales: **$80,668**
  2. Marketing: **$71,913**
  3. Finance: **$70,489**
  4. Research: **$59,665**
  5. Production: **$59,605**

Let me know if you need more details on any of these!

User: What are the most interesting trends you can find in our employee data?
Assistant: Based on the employee data and the queries we've run so far, here are some interesting trends and observations:

1. **Aging Workforce**:  
   - The average age of employees is approximately **66.3 years old**, which is considerably higher than typical averages in many industries. This could imply a workforce with significant experience, but it may also suggest upcoming retirements and a potential need for succession planning.

2. **Large Organization**:  
   - With **300,024 employees**, the company is exceptionally large, likely indicating a multinational or highly diversified organization with many departments.

3. **Departments with Highest Compensation**:  
   - The top five departments by average salary are:
     1. Sales: **$80,668**
     2. Marketing: **$71,913**
     3. Finance: **$70,489**
     4. Research: **$59,665**
     5. Production: **$59,605**
   - Sales dominates as the highest paid department, suggesting that either commission-based or performance-based incentives significantly boost average pay in that field.

4. **Department Salary Gap**:  
   - There is a notable gap between the top three (Sales, Marketing, Finance) and the next group (Research, Production), indicating differences in perceived value, skill requirement, or performance incentives.

5. **Potential for Talent Bottlenecks**:  
   - With a high average employee age, critical departments like Sales and Finance (which command the highest salaries) may face challenges in recruitment and knowledge transfer if a significant proportion retire.

**Additional trends I could explore with further data:**
- Gender distribution by department and seniority.
- Average tenure or years of service.
- Trends in hiring (annual new hire rates, diversity metrics).
- Breakdown of titles and management layers.
- Regional differences, if location data is available.

If there’s a specific trend or metric you’re interested in—such as diversity, tenure, promotion rates, or department growth—let me know! I can run targeted analyses for deeper insights.
```

