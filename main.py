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
from fastapi import FastAPI, Request, HTTPException, File, UploadFile
import uvicorn
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import json
import base64
import httpx

from utils import load_config_file, pretty_print_response
from termcolor import colored
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load server configuration
SERVER_CONFIG = load_config_file("multi_server_config.json")

# FastAPI app
app = FastAPI()

# set no CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
# Global variables to store agent, client, and ngrok tunnel
agent = None
client = None

# Global variable to store conversation history
conversation_history = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the agent, client, and ngrok tunnel on startup."""
    global agent, client, ngrok_tunnel
    try:
        # Initialize MCP client and agent
        model = ChatAnthropic(model="claude-3-7-sonnet-20250219", temperature=0.6)
        client = MultiServerMCPClient(SERVER_CONFIG)
        await client.__aenter__()  # Enter the async context
        agent = create_react_agent(model, client.get_tools())
        logger.info("MCP_tools ", client.get_tools())
        logger.info("Agent initialized successfully.")
        response = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": "hi"
            }]
        })
        logger.info(f"Response from agent: {response}")
        

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


prevmessages = ""
@app.post("/api/process_invoice")
async def process_invoice(request: Request, document: UploadFile = File(None)):
    """Process invoice data sent from the frontend using Claude client."""
    try:
        logger.info("Starting process_invoice endpoint...")

        # Parse the text from the request
        form_data = await request.form()
        text = form_data.get("text", "")
        user_id = form_data.get("user_id", "default_user")  # Use a unique identifier for the user
        logger.info(f"Extracted text from request: {text}")

        if not text and not document:
            logger.warning("No text or file provided in the request.")
            return {"error": "Missing text or file"}

        if document:
            logger.info(f"Received file: {document.filename}")
            file_content = await document.read()
            logger.info(f"File content size: {len(file_content)} bytes")

        # Initialize or update conversation history for the user
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        if text.strip():  # Ensure text is not empty
            conversation_history[user_id].append({"role": "user", "content": text})

        # Prepare the initial Claude agent prompt
        initial_prompt = (
            "You are an intelligent assistant specialized in analyzing invoices and processing transfers. "
            "Your task is to process the provided text and/or document to extract meaningful insights and assist with transfer operations. "
            "If a document is provided, analyze its content and summarize key details such as invoice number, date, amount, vendor, and bank details"
            "The beneficiary id is not required, pass the beneficiary details correctly. "
            "If only text is provided, analyze and respond appropriately. Do not use search tool for this task. "
            "If the user requests a transfer, intiate the transfer the following details with the user before proceeding: "
            "Once confirmed, provide a response with all transfer details, including the transfer ID, amount, beneficiary details, and current status. "
            "Always provide clear and concise responses, clearly formatted in plain text."
        )
        logger.debug(f"Initial prompt for Claude agent: {initial_prompt}")

        # Prepare the input data for the Claude agent
        input_data = [{"role": "system", "content": initial_prompt}]
        input_data.extend(conversation_history[user_id])  # Add conversation history
        content = []
        if text.strip():  # Ensure text is not empty
            content.append({"type": "text", "text": text})
            logger.info("Text content added to input data for Claude agent.")
        if document:
            pdf_data = base64.standard_b64encode(file_content).decode("utf-8")
            content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data,
                }
            })
            logger.info("File content encoded to base64 for Claude agent.")

        if content:  # Ensure content is not empty
            input_data.append({"role": "user", "content": content})
        else:
            logger.warning("No valid content to send to Claude agent.")
            return {"error": "No valid content to process."}

        # Call the Claude agent
        logger.info("Calling Claude agent...")
        response = await agent.ainvoke({"messages": input_data})

        # Extract and log the Claude agent's response
        pretty_print_response(response, "Process Invoice")
        response_text = response["messages"][-1].content
        logger.info(f"Claude agent response: {response_text}")

        # Add the agent's response to the conversation history
        conversation_history[user_id].append({"role": "assistant", "content": response_text})

        # Return the response from the Claude agent
        return {"message": response_text}
    except Exception as e:
        logger.error(f"Error in process_invoice: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    # Run the Uvicorn server without TLS
    logger.info("Starting Uvicorn server without TLS...")
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_certfile=None, ssl_keyfile=None)
