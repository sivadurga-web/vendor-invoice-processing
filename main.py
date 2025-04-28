
"""
This script implements a FastAPI application for handling WhatsApp-based cake orders
and payment processing for a homebaker. It integrates with external tools and services
to process customer messages, generate payment links, and send WhatsApp messages.

Modules:
- `logging`: For logging application events.
- `os`: For accessing environment variables.
- `typing`: For type annotations.
- `fastapi`: For building the web application.
- `uvicorn`: For running the FastAPI application.
- `dotenv`: For loading environment variables from a `.env` file.
- `langchain_mcp_adapters.client`: For interacting with the MultiServer MCP client.
- `langgraph.prebuilt`: For creating a React agent.
- `langchain_anthropic`: For using the ChatAnthropic model.
- `json`: For handling JSON data.
- `utils`: For utility functions like loading configuration files and pretty-printing responses.
- `termcolor`: For colored terminal output.

Functions:
- `handle_cake_order_lead(phone_number: str, name: str, message: str) -> Dict[str, str]`:
    Processes a customer message to identify cake order intent and sends flavor options via WhatsApp.

- `handle_confirm_order(phone_number: str, name: str, message: str) -> Dict[str, str]`:
    Handles a confirmed cake order by identifying the flavor and generating a payment link.

- `handle_webhook(payload: str) -> Dict[str, str]`:
    Processes webhook payloads to confirm payment status and notify the customer via WhatsApp.

FastAPI Endpoints:
- `@app.post("/api/process_message")`:
    Processes incoming WhatsApp messages for cake orders and determines the appropriate action.

- `@app.post("/api/webhook")`:
    Handles incoming webhook requests from Cashfree Payments to confirm payment status.

Lifecycle Events:
- `@app.on_event("startup")`:
    Initializes the agent, client, and other resources on application startup.

- `@app.on_event("shutdown")`:
    Cleans up resources on application shutdown.

Main Execution:
- Runs the FastAPI application using Uvicorn on `host="0.0.0.0"` and `port=8000`.

Environment Variables:
- `SUPABASE_PROJECT_ID`: The Supabase project ID, loaded from the `.env` file.

Configuration:
- `multi_server_config.json`: A configuration file for the MultiServer MCP client.

Global Variables:
- `agent`: The React agent for processing customer messages.
- `client`: The MultiServer MCP client for interacting with external tools.
"""


import logging
import os
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
import json

from utils import load_config_file, pretty_print_response
from termcolor import colored

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load server configuration
SERVER_CONFIG = load_config_file("multi_server_config.json")

# FastAPI app
app = FastAPI()

# Global variables to store agent, client, and ngrok tunnel
agent = None
client = None

async def handle_cake_order_lead(phone_number: str, name: str, message: str) -> Dict[str, str]:
    """Handle a cake order: identify intent, send cake options via WhatsApp."""
    order_prompt = (
        f"You are an intelligent assistant for a homebaker, delighting customers with friendly responses. Process a customer message to identify a cake order intent and send flavor options.\n"
        f"Inputs:\n"
        f"- Phone number: '{phone_number}'\n"
        f"- Name: '{name}'\n"
        f"- Message: '{message}'\n"
        "Follow these steps exactly, using appropriate spacing and emojis:\n"
        "1. Identify cake order intent:\n"
        "   - A cake order intent is defined as a message containing any of the keywords (case-insensitive): 'cake', 'order', 'buy', 'purchase', 'want'.\n"
        "   - If no intent is identified, return: {'status': 'Message ignored'}\n"
        "2. Offer 3 cake options for different prices chocolate 500, vanilla 300, butterscotch 700:\n"
        "   - A confirmed flavor from the customer is a happy path. Customer needs to confirm one of the flavors. Wait for customer to confirm the flavor.\n"
        "   - If no confirmation is identified, ask the customer to choose a correct option.\n"
        "5. Evaluate the outcome:\n"
        "   - If the flavors options are sent successfully, return: {'status': 'Order processed, payment link sent'}\n"
        "   - If any tool fails (e.g., message sending failure), return: {'status': 'ERROR: Order processing failed'}\n"
        "Return the output as a JSON object with a 'status' field."
    )
    response = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": order_prompt
        }]
    })
    pretty_print_response(response, "Handle Cake Order Lead")
    response_text = response["messages"][-1].content.lower()

    if "message ignored" in response_text:
        return {"status": "Message ignored"}
    elif "error" in response_text:
        return {"status": response_text.split("error:")[1].strip() if "error:" in response_text else "ERROR: Unknown error"}
    return {"status": "Order identified, flavor options sent"}

async def handle_confirm_order(phone_number: str, name: str, message: str) -> Dict[str, str]:
    """Handle a order with flavor present and send payment link against the selected order."""
    order_prompt = (
        f"You are an intelligent assistant for a homebaker, delighting customers with friendly responses. Process a customer message to identify a cake flavor in the message and generate a payment link.\n"
        f"Inputs:\n"
        f"- Phone number: '{phone_number}'\n"
        f"- Name: '{name}'\n"
        f"- Message: '{message}'\n"
        "Follow these steps exactly, using appropriate spacing and emojis:\n"
        "1. Identify cake order flavor:\n"
        "   - A cake order intent is defined as a message containing any of the keywords (case-insensitive): 'chocolate', 'vanilla', 'butterscotch'.\n"
        "   - If no flavor is identified, return: {'status': 'Message ignored'}\n"
        "2. Generate a payment link:\n"
        f"   - Generate a payment link for the identified cake order with Cashfree MCP. Reason with yourself in case of any errors while creating the link. \n"
        "3. Send the payment link:\n"
        f"   - use whatsapp mcp tool to send a WhatsApp message to '{phone_number}' sharing the payment link url. Add new lines & keep it professional yet cheerful. Dont try to use hyperlink - directly plug in the payment link url. Use emojis conservatively.\n"
        "4. Evaluate the outcome:\n"
        "   - If the payment link is generated and the message is sent successfully, return: {'status': 'Order processed, payment link sent'}\n"
        "   - If any tool fails (e.g., payment link generation or message sending failure), return: {'status': 'ERROR: Order processing failed'}\n"
        "Return the output as a JSON object with a 'status' field."
    )
    response = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": order_prompt
        }]
    })
    pretty_print_response(response, "Handle Cake Order Lead")
    response_text = response["messages"][-1].content.lower()

    if "message ignored" in response_text:
        return {"status": "Message ignored"}
    elif "error" in response_text:
        return {"status": response_text.split("error:")[1].strip() if "error:" in response_text else "ERROR: Unknown error"}
    return {"status": "Order identified, flavor options sent"}


async def handle_webhook(payload: str) -> Dict[str, str]:
    """Handle a payload passed and message confirmation to the user on successful payment."""
    order_prompt = (
        f"You are an intelligent assistant for a homebaker, delighting customers with friendly responses. Process a customer message to identify a cake order intent and generate a payment link.\n"
        f"Inputs:\n"
        f"- Payload'{payload}'\n"
        "Follow these steps exactly, using appropriate spacing and emojis:\n"
        "1. Identify the customer phone and the status of the payment in the webhook and send the confirmation to the customer via whatsapp\n"
        "Return the output as a JSON object with a 'status' field."
    )
    response = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": order_prompt
        }]
    })

    pretty_print_response(response, "Handle Cake Order")
    response_text = response["messages"][-1].content.lower()

    if "message ignored" in response_text:
        return {"status": "Message ignored"}
    elif "error" in response_text:
        return {"status": response_text.split("error:")[1].strip() if "error:" in response_text else "ERROR: Unknown error"}
    return {"status": "Order processed, payment link sent"}


@app.on_event("startup")
async def startup_event():
    """Initialize the agent, client, and ngrok tunnel on startup."""
    global agent, client, ngrok_tunnel
    try:
        # Initialize MCP client and agent
        model = ChatAnthropic(model="claude-3-5-haiku-20241022", temperature=0.7)
        client = MultiServerMCPClient(SERVER_CONFIG)
        await client.__aenter__()  # Enter the async context
        agent = create_react_agent(model, client.get_tools())
        logger.info("Agent initialized successfully.")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    global client, ngrok_tunnel
    try:
        if client:
            await client.__aexit__(None, None, None)
            logger.info("Client shutdown successfully.")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

@app.post("/api/process_message")
async def process_message(request: Request):
    """Process incoming WhatsApp messages for cake orders."""
    data = await request.json()
    phone_number = data.get("phone_number")
    message = data.get("message")
    name = data.get("name")

    if not phone_number or not message or not name:
        return {"error": "Missing phone_number, message, or name"}

    if "chocolate" in message.lower() or "vanilla" in message.lower() or "butterscotch" in message.lower():
        return await handle_confirm_order(phone_number, name, message)
    else:
        return await handle_cake_order_lead(phone_number, name, message)

@app.post("/api/webhook")
async def webhook(request: Request):
    """Handle incoming webhook requests from Cashfree Payments."""
    try:
        # Get raw payload and signature
        payload = await request.body()
        # Parse payload
        webhook_data = json.loads(payload.decode('utf-8'))
        logger.info(f"Received webhook: {json.dumps(webhook_data, indent=2)}")

        return await handle_webhook(webhook_data)
    except json.JSONDecodeError:
        logger.error("Invalid webhook payload format")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)