import os
from typing import Annotated, TypedDict
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, END, START

# Read GROQ_API_KEY from environment
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set.")

# -------------------- Tool Definitions --------------------

@tool
def get_credly_data(username: str) -> str:
    """Fetch a user's public badges from Credly."""
    data = {
        "name": "Cladius Fernando",
        "badges": [
            "AWS Certified AI Practitioner", 
            "AWS Certified AI Practitioner Early Adopter", 
            "Cloud Digital Leader Certification", 
            "Microsoft Certified: Azure Fundamentals", 
            "AWS Certified Data Analytics Specialty", 
            "HashiCorp Certified: Terraform Associate (002)", 
            "AWS Certified Solutions Architect Professional", 
            "AWS Certified Solutions Architect Associate", 
            "AWS Certified Cloud Practitioner"
        ],
        "badge issued date": [
            "26/09/2024", "26/09/2024", "02/11/2022", "04/07/2022", 
            "15/12/2020", "09/01/2021", "05/08/2020", "14/11/2019", "29/03/2019"
        ],
        "badge expiration date": [
            "26/09/2027", "no expiration date", "02/11/2025", "no expiration date", 
            "15/12/2023", "09/01/2023", "05/08/2023", "14/11/2023", "29/03/2023"
        ],
        "credit points": [2, 2, 3, 3, 2, 5, 2, 2, 2]
    }
    
    badge_info = "\n".join(
        [f"- {badge}\n  Issued: {issued}\n  Expires: {expires}\n  Credit Points: {points}"
         for badge, issued, expires, points in zip(data["badges"], data["badge issued date"], data["badge expiration date"], data["credit points"])]
    )
    
    return f"User: {data['name']}\nBadges Earned:\n{badge_info}"



@tool
def get_weather(location: str) -> str:
    """Call to get the current weather."""
    print(f"[TOOL CALL] get_weather called with: location={location}")
    if location.lower() in ["sf", "san francisco"]:
        result = "It's 60 degrees and foggy."
    else:
        result = "It's 90 degrees and sunny."
    print("[TOOL RESULT] get_weather returned:", result)
    return result

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    print(f"[TOOL CALL] add called with: a={a}, b={b}")
    result = a + b
    print("[TOOL RESULT] add returned: ", result)
    return result

@tool
def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    print(f"[TOOL CALL] subtract called with: a={a}, b={b}")
    result = a - b
    print("[TOOL RESULT] subtract returned:", result)
    return result

# List of available tools
tools = [get_credly_data,get_weather, add, subtract]

# -------------------- LLM Setup --------------------

# Initialize the LLM with Groq API key and model
llm = ChatGroq(groq_api_key=groq_api_key, model="openai/gpt-oss-20b")


# -------------------- State Definition --------------------

# Create the agent using the built-in create_react_agent
graph = create_react_agent(llm, tools)