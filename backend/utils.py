import sqlite3
from openai import OpenAI
from tabulate import tabulate
import pandas as pd

def initialize_dbs():
    # Create connection to the database files
    con = sqlite3.connect("data/example_db.db")

    # Create a cursor object using the connection
    cur = con.cursor()

    # Create the ref_table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ref_table (
        company_id VARCHAR(255),
        parent_company_id VARCHAR(255),
        lob_lvl_1 VARCHAR(255),
        lob_lvl_2 VARCHAR(255),
        lob_lvl_3 VARCHAR(255)
    )
    ''')

    # Insert 10 example rows into ref_table
    example_ref_data = [
        ('company1', 'parent1', 'abc', '123', 'ab1'),
        ('company2', 'parent2', 'def', '456', 'bc2'),
        ('company3', 'parent3', 'hij', '789', 'ef3'),
        ('company4', 'parent4', 'abc', '123', 'ab1'),
        ('company5', 'parent5', 'def', '456', 'bc2'),
        ('company6', 'parent6', 'hij', '789', 'ef3'),
        ('company7', 'parent7', 'abc', '123', 'ab1'),
        ('company8', 'parent8', 'def', '456', 'bc2'),
        ('company9', 'parent9', 'hij', '789', 'ef3'),
        ('company10', 'parent10', 'abc', '123', 'ab1')
    ]

    cur.executemany('''
    INSERT OR IGNORE INTO ref_table (company_id, parent_company_id, lob_lvl_1, lob_lvl_2, lob_lvl_3) 
    VALUES (?, ?, ?, ?, ?)
    ''', example_ref_data)

    # Create the payments_table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS payments_table (
        date VARCHAR(255),
        company_id VARCHAR(255),
        amount FLOAT,
        direction VARCHAR(255)
    )
    ''')

    # Insert 10 example rows into payments_table
    example_payment_data = [
        ('20230101', 'company1', 1000.50, 'inbound'),
        ('20230201', 'company2', 2000.75, 'outbound'),
        ('20230301', 'company3', 1500.20, 'inbound'),
        ('20230401', 'company4', 3000.00, 'outbound'),
        ('20230501', 'company5', 2500.65, 'inbound'),
        ('20230601', 'company6', 1750.80, 'outbound'),
        ('20230701', 'company7', 2250.40, 'inbound'),
        ('20230801', 'company8', 2750.90, 'outbound'),
        ('20230901', 'company9', 3250.30, 'inbound'),
        ('20231001', 'company10', 3500.50, 'outbound')
    ]

    cur.executemany('''
    INSERT OR IGNORE INTO payments_table (date, company_id, amount, direction) 
    VALUES (?, ?, ?, ?)
    ''', example_payment_data)

    con.commit()
    con.close()
    print("Successfully created tables and examples :)")

def read_table(sql_str, table_name):
    con = sqlite3.connect(table_name)
    cur = con.cursor()
    cur.execute(sql_str)
    headers = [description[0] for description in cur.description]
    output_rows = cur.fetchall()
    con.close()
    return pd.DataFrame(output_rows, columns=headers)

def initalize_sqlgenex(model_name: str, api_key: str, table_info_file: str):

    client = OpenAI(api_key=api_key)

    instructions = "You are a LLM that generates SQL queries based on the user's prompt/question and given database. You are given information about the tables in the database. When asked a casual/non-related question, answer with a standard chatbot response. In every other case, please create the SQL query that best align with answering the user's prompt/question. Only return the SQL query string."

    # Open the file in read mode
    with open(table_info_file, 'r') as file:
        # Read the content of the file into a string
        table_info_content = file.read()

    messages = [
        {"role": "system", "content": instructions},
        {'role': 'user', 'content': f"{table_info_content}\n\n\nGive me all the outbound transactions of the parent2\n\n\nWrite me the SQL query. Only give me the SQL query string."},
        {'role': 'assistant', 'content': "\nSELECT p.*\nFROM payments_table p\nJOIN ref_table r ON p.company_id = r.company_id\nWHERE r.parent_company_id = 'parent2' AND p.direction = 'outbound';\n"}
    ]
    
    return {"client": client, "model_name": model_name, "chat_history": messages}

def ask_sqlgenex(client, model_name, input_message, chat_history):

    input_message_raw = f"{input_message}"
    input_message = {"role": "user", "content": input_message_raw}
    chat_history.append(input_message)
    response_full = client.chat.completions.create(
        model=model_name,
        messages=chat_history
    )
    response = response_full.choices[0].message.content
    response = response.strip("```sql")
    output_message = {"role": "assistant", "content": response}
    chat_history.append(output_message)
    return {"client": client, "model_name": model_name, "chat_history": chat_history, "output_message": response}

def format_dataframe_tabulate(df):
    return tabulate(df, headers='keys', tablefmt='grid')
