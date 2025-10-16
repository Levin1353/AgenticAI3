import os
from typing import Annotated, TypedDict
from langchain_groq import ChatGroq
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
llm = ChatGroq(groq_api_key=groq_api_key, model="llama-3.3-70b-versatile")
llm_with_tools = llm.bind_tools(tools)

# -------------------- State Definition --------------------

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Create a state graph for the conversation flow
graph_builder = StateGraph(State)

# Node: Chatbot LLM invocation
def chatbot(state: State):
    # Pass conversation messages to the LLM and get the response
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

# Node: Tool execution
tool_node = ToolNode(tools)
graph_builder.add_node("tools", tool_node)

# Conditional edge: If tool is needed, go to tool node
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)

# After tool execution, return to chatbot
graph_builder.add_edge("tools", "chatbot")
# Start the graph at the chatbot node
graph_builder.add_edge(START, "chatbot")

# Compile the graph
graph = graph_builder.compile()

# -------------------- Chat Loop --------------------
def invoke_chat_loop():
    print("You can chat with the LLM. It will decide when to use tools (weather, add, subtract). Type 'exit' to quit.")
    conversation = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break
        # Add user message to conversation
        conversation.append(HumanMessage(content=user_input))
        state = {"messages": conversation}
        # Invoke the graph with the current state
        result = graph.invoke(state)
        # Update conversation with new messages
        conversation = result["messages"]
        print("AI:", conversation[-1].content)
    