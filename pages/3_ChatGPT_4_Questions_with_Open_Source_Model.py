# Implement demo code by Streamlit: https://github.com/streamlit/llm-examples/tree/main


import os
import sys
import streamlit as st
import pandas as pd
import openai
import types
import inspect
import textwrap
import json
import replicate



#%%###################################################################################################################### 
# AGENT CONFIGURATION
#########################################################################################################################

functions_definitions = {
    "generic_spend_report": {
            "function": 'generic_spend_report',
            "title":  "",
            "vendor_filter": [],
            "category_filter": [],
            "hospital_filter": [],
            "department_filter": [],
            "division_filter": [],
            "gl_account_filter": [],
            "time_period_filter": [],
            "fiscal_calendar": 'True or False',
            "metrics": [],
            "dimensions": [],
            "user_request": "",
    },
    "hospital_benchmarking_spend_report": {
            "function": 'hospital_benchmarking_spend_report',
            "title":  "",
            "category_filter": [],
            "hospital_filter": [],
            "department_filter": [],
            "division_filter": [],
            "gl_account_filter": [],
            "time_period_filter": [],
            "fiscal_calendar": 'True or False',
            "user_request": "",
    },
    "market_share_report": {
            "function": 'market_share_report',
            "title":  "",
            "vendor_filter": [],
            "category_filter": [],
            "hospital_filter": [],
            "department_filter": [],
            "division_filter": [],
            "gl_account_filter": [],
            "time_period_filter": [],
            "fiscal_calendar": 'True or False',
            "user_request": "",
    },
    "vendor_market_share_map": {
            "function": 'vendor_market_share_map',
            "title":  "",
            "vendor_filter": [],
            "category_filter": [],
            "hospital_filter": [],
            "department_filter": [],
            "division_filter": [],
            "gl_account_filter": [],
            "time_period_filter": [],
            "fiscal_calendar": 'True or False',
            "user_request": "",
    },
    "generate_error_message": {
            "function": 'generate_error_message',
            "reason":  "",
    }
}


def chat_gpt_basic_BI_agent (sentence):

    # Configure
    system_message = f"""        
        You are a Business Intelligence (BI) agent that produces reports to answer business questions and meet information requests from "business users". You respond only in JSON format. 
        
        Your job is to: 
            1. interpret a business question or information request from a "business user".
            2. choose the correct type of report and identify the dimensions, filters, and metrics to be used in that report. Then respond providing that information in a JSON structure that will be used by a function to create and send the report to the business user.
            3. if not possible to meet the requirements with the data and reports that you have available, then respond to the user with a JSON structure named "generate_error_message".

        No other response to the user is acceptable: you must either respond as indicated in item 2 or item 3. 

        The type of reports that you have available are:
            a) Generic Spend Report: Flexible report that you can use to answer many user questions about historical transaction volumes and spend. You can specify various filters, dimensions, and metrics for this report using the 'generic_spend_report' JSON structure.
            b) Hospital Benchmarking Spend Report: Answers questions for a single specific hospital such as: Are we spending more on a given category than other hospitals? Use this report to compare all the cost and performance metrics of one hospital or facility against similar hospitals. Dimensions and metrics are fixed, but you may specify filters using the 'hospital_benchmarking_spend_report'.
            c) Market Share Report: Answers questions such as: what are the top N vendors in a given category? Use this report to show the largest vendors available in the market and their share. Dimensions and metrics are fixed. You may specify a vendor count limit (top N) and filters using the 'market_share_report' stucture.
            d) Vendor Market Share Map: It displays a map to answer questions such as: what markets does a given vendor serve and what share does it have? who is the market leader for a given category? and where does that market leader offer services? Dimensions and metrics are fixed, but you may specify filters using the 'vendor_market_share_map' structure.

        The data that these reports can access is a table of hospital expenditures in a PostgreSQL database. The table has records for every purchase or service transaction and contains the following fields:
            - 'transaction_datetime' : the date and time of the purchase or service (type: timestamp)
            - 'spend_amount'         : the cost of the purchase or service in US$ (type: numeric)
            - 'vendor_name'          : the name of the vendor company (a.k.a. service provider, manufacturer, distributor, contractor) that provided the product or service (type: char)
            - 'category_name'        : the category of the expense according to a standard classification system (type: char)
            - 'hospital_name'        : the name of the hospital (also refered to as "facility") that incurred the expense (type: char)
            - 'division_name'        : the name of the division of the hopital or hospital group that incurred the expense (type: char)
            - 'department_name'      : the name of the department of the hopital that incurred the expense (type: char)
            - 'gl_account_name'      : the General Ledger account of the expenditure in the accouting system of the hospital or hospital group (type: char)
            - 'geographic_market'    : the name of the geographical region where the hospital facility is located under a standard classification system (imagine MSAs, CBSAs, CSAs, DMAs, or similar systems.) (type: char)

        All reports have the following "filters" available, which you can use to control what expenditures are included: 
            - 'vendor_filter'      (type list of strings): List of vendor company names that the report should include. This parameter is optional. If not provided, all vendors will be used.
            - 'category_filter'    (type list of strings): List of spend categoriy names that the report should include. This parameter is optional. If not provided, all categories will be used.
            - 'hospital_filter'    (type list of strings): List of hospital or facility names that the report should include. This parameter is optional. If not provided, all hospitals will be used.
            - 'department_filter'  (type list of strings): List of department names that the report should include. This parameter is optional. If not provided, all departments will be used.
            - 'division_filter'    (type list of strings): List of division names that the report should include. This parameter is optional. If not provided, all divisions will be used.
            - 'gl_account_filter'  (type list of strings): List of GL account that the report should include. This parameter is optional. If not provided, all GL Accounts will be used.
            - 'time_period_filter' (type list of strings): List of time period names that the report should include. The list of acceptable period names is specified below. This parameter is optional. If not provided, the report will either apply a default period or include all time.
            - 'fiscal_calendar'    (type boolean) : If True, the time periods in the filters and dimensions will be calculated using fiscal years and fiscal quarters. If False, they will be calculated using normal calendar years and quarters. This parameter is optional. If not provided, normal calendar periods will be used as default.
        
        For the time_period_filter, the following is the list of "period names" that you can use. The start/end dates of each period will be calculated by the report based on transaction_date and the current date:  
                'LAST YEAR', 'LAST QUARTER', 'LAST MONTH', 'LAST WEEK';
                'LAST N YEARS', 'LAST N QUARTERS', 'LAST N MONTHS', 'LAST N WEEKS', 'LAST N DAYS' (where N = integer you must specify);
                'YEAR TO DATE', 'QUARTER TO DATE', 'MONTH TO DATE'; 
                'YEAR yyyy', 'QUARTER yyyy-q', 'MONTH yyyy-mm' (where you can specify an exact year "yyyy", quarter number "q", and month number "mm"); 
                'FROM yyyy-mm-dd TO yyy-mm-dd' (where you can specify the start and end-date of an ad-hoc period in YYYY-MM-DD format);
                'STLY' (means "same time last year" and its calculated taking the previous period in the list and shifting it 1 year back in time);
                and 'ALL TIME' (if the report must include all transaction dates, e.g. not have any time filter).

        Some reports allow you to specify dimensions. If the report accepts dimensions, they are an optional parameter. Valid dimension names are: 
            'vendor_name', 'category_name', 'hospital_name', 'division_name', 'department_name', 'gl_account_name';
            'transaction_year', 'transaction_quarter', 'transaction_month', 'transaction_day', and 'transaction_week' (which come from grouping transaction_datetime). 

        Some reports allow you to specify metrics. If the report accepts metrics, they are an optional parameter. Valid metrics name and their definitions are:
            'num_vendors'  = count of unique vendor companies,
            'num_p80_vendors'  = count of unique vendor companies within the top 80 percent of spend,
            'total_volume' = count of unique transactions,
            'total_amount' = sum(spend_amount),
            'min_amount'   = min(spend_amount),
            'max_amount'   = max(spend_amount),
            'avg_amount'   = total_amount / total_volume,
            'pXX_amount'   = percentile of spend_amount (where XX = integer you specify, for example 'p50_amount' is the median),
            'spend_share'  = total_amount of a vendor as a percent of the grand total amount in the "market" (defined as the geographic_market and the category filters in the report).                

        Finally, the JSON structures may ask you to provide the following data elemements:
        - 'function'     : Please specify the name of the JSON structure. This parameter is always mandatory.",
        - 'title'        : Please write a name or title for the report to be displayed to the business user. This parameter is mandatory for all the reports but should not be included in error messages.",
        - 'reason'       : Please provide a brief explanation why it is not possible to produce the report. This parameter is mandatory for error messages and should not be included in reports.  
        - 'user_request' : Please copy the text of the business user request or question that you are seeking to answer with this report. It will not be used in producing the report (it's passed only for documentation purposes.) This parameter is for all report mandatory.",

        Here is the technical definition of the JSON structures for each report. Your response must pack the information using one of these structures:
        {json.dumps(functions_definitions)}

        Additional instructions:
        - You must strictly adhere to the specifications of each JSON structure. Use only the field names provided above. Do not change or add new fields.  Respect the data types indicated for each field.  
        - Do NOT include any additional explanation of your thought process, analytics methodology, or how-to steps to generate the report. Respond only with one of the available JSON structures. 
        - Do NOT include any other technical details aside from the JSON structure. Do NOT include python code, javascript code, or SQL queries in your response.  
        - Keep each report as simple as possible: Do not add any filters, dimensions, or metrics that are not essential to answer the business question.  
        """
    
    # Please answer the following question or information request from a business user:
    prompt = f"""Look at the examples above and answer me in the same format. [SENTENCE]"""

    prompt = """\
        [INST] Show for this year spend per ledger and per service provider for Flooring Repairs and New Flooring Installation. [/INST]
        {
            "report": "generic_spend_report",
            "title": "Spend per ledger and service provider for New Flooring and Flooring Repairs",
            "category_filter": ["Flooring Repairs", "New Flooring Installation"],
            "time_period_filter": ['YEAR TO DATE'],
            "dimensions": ['gl_account_name', 'vendor_name'],
            "metrics": ['total_amount'],
            "user_request": "Show for this year spend per ledger and per service provider for Flooring Repairs and New Flooring Installation."
        }
        [INST] Provide a visualization of the market presence of mallory safety & supply in various geographies over the last six fiscal quarters. [/INST]
        {
            "report": "vendor_market_share_map",
            "title": "Mallory Safety & Supply Market Presence",
            "vendor_filter": ['mallory safety & supply'],
            "time_period_filter": ['LAST 6 QUARTERS'],
            "fiscal_calendar": True,
            "user_request": "Provide a visualization of the market presence of mallory safety & supply in various geographies over the last six fiscal quarters."
        }
        [INST] What is the fastest train in the world? [/INST]
        {
            "report": "generate_error_message",
            "reason": "I\'m not able to provide an answer to that question as it is not related to any report that has been defined. The reports available are focused on analyzing expenses and costs, not providing real-time information about trains speed."
        }
        [INST] """ + prompt + " [/INST]"
    
    # Cleanup
    prompt = textwrap.dedent(prompt).strip()
    prompt = prompt.replace('[SENTENCE]', sentence)
    if system_message:
        system_message = textwrap.dedent(system_message).strip()

    # Return
    return prompt, system_message



def call_llama2_on_replicate(user_question):
  
    prompt_final, system_message = chat_gpt_basic_BI_agent(user_question)

    output_gen = replicate.run(
        "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
        input = {
            "prompt": prompt_final,
            "system_prompt": system_message,
            "max_new_tokens": 1024,
            "temperature": 0.01,
            "top_p": 0,
            "top_k": 0
        }
    )

    output = ''
    for item in output_gen:
        output += item
    output += '\n'

    return output


#%%###################################################################################################################### 
# ACTUAL APPLICATION
#########################################################################################################################

# Load settings
api_token = st.secrets["replicate"]["key"]
_, system_message = chat_gpt_basic_BI_agent('no prompt yet')


# Display app basic information
st.title("ChatGPT 4.0 Questions with Open Source Model")
st.caption("Report generation with Llama2 70B model. Ask a business question about hospital expenditures. LLM should interpret it and call the right reporting function.")

# Initialize the web session
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": system_message}]

# Execute
for msg in st.session_state.messages:
    if msg["role"] != 'system':
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not api_token:
        st.info("Please add your Replicate API token to continue.")
        st.stop()
    # if not bi_analyst_pwd or bi_analyst_pwd != 'Valify2024':
    #     st.info("Please add your OpenAI API key to continue.")
    #     st.stop()

    os.environ["REPLICATE_API_TOKEN"] = api_token

    # Prepare the message
    # prompt, _ = chat_gpt_basic_BI_agent(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Call the API
    response_content = call_llama2_on_replicate(prompt)    
    st.chat_message("assistant").write(response_content)

