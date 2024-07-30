from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
from utils import initalize_sqlgenex, ask_sqlgenex, read_table, format_dataframe_tabulate
import os
import re

app = FastAPI()

model_name = "gpt-4o"
api_key = os.getenv("OPENAI_API_KEY")
table_info_file = "../data/db_info.txt"
db_name = "../data/example_db.db"

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    message: str

@app.post("/chat")
async def chat(message: Message):
    output_message = ""
    sql_query = ""
    regenerate_prompt = "Please recreate/adjust the SQL query by interpretating my SQL request differently. Only give me the SQL query string."

    # LLM prompting
    user_prompt = message.message
    model_setup = initalize_sqlgenex(model_name=model_name, api_key=api_key, table_info_file=table_info_file)
    model_response = ask_sqlgenex(model_setup["client"], model_setup["model_name"], user_prompt, model_setup["chat_history"])
    if re.search(r'\bSELECT\b', model_response["output_message"], re.IGNORECASE) is not None:
        sql_str = model_response["output_message"]
        df_output = read_table(sql_str, db_name)
        print(sql_str)
        sql_query = sql_str

        # When the output is empty, ask LLM to reinterperate the user request
        if df_output.shape[0] == 0:
            model_response = ask_sqlgenex(model_setup["client"], model_setup["model_name"], regenerate_prompt, model_setup["chat_history"])

            if re.search(r'\bSELECT\b', model_response["output_message"], re.IGNORECASE) is not None:
                sql_str = model_response["output_message"]
                df_output = read_table(sql_str, db_name)
                
                print(sql_str)
                sql_query = sql_str
                if df_output.shape[0] == 0:
                    output_message = "There are no results for your query. \nPlease try again with a different question."
                else:
                    output_message = format_dataframe_tabulate(df_output)
            else:
                output_message = model_response["output_message"]

        else:
            output_message = format_dataframe_tabulate(df_output)
    else:
        output_message = model_response["output_message"]

    return {"output_message": output_message, "sql_query": sql_query}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
