# WhatsApp Cake Order MCP

A FastAPI application that handles WhatsApp-based cake orders and payment processing for homebakers. The application integrates WhatsApp messaging, cake order processing, and payment link generation using Model Context Protocol (MCP) services.

## Features

- 🎂 Process cake order inquiries via WhatsApp
- 💬 Automated responses with cake flavor options
- 💰 Generate payment links for confirmed orders
- ✅ Handle payment confirmation webhooks
- 🤖 AI-powered message processing using Claude 3 Haiku

## Prerequisites

- Python 3.11+
- `.env` file with required environment variables
- Access to MCP services (WhatsApp and Cashfree)
- Supabase project setup

## Configuration

1. Set up `multi_server_config.json` with your MCP service configurations


## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

## Usage

Run the FastAPI application:
```bash
uv run main.py
```

The server will start on `http://0.0.0.0:8000`

## API Endpoints

### Process WhatsApp Message
- **POST** `/api/process_message`
- Handles incoming WhatsApp messages
- Payload:
  ```json
  {
    "phone_number": "string",
    "name": "string",
    "message": "string"
  }
  ```

### Payment Webhook
- **POST** `/api/webhook`
- Handles payment confirmation webhooks from Cashfree
- Expects Cashfree webhook payload format

## Order Flow

1. Customer sends a message indicating interest in ordering a cake
2. System responds with available cake flavors and prices:
   - Chocolate (₹500)
   - Vanilla (₹300)
   - Butterscotch (₹700)
3. Customer confirms flavor choice
4. System generates payment link and sends via WhatsApp
5. Payment confirmation triggers webhook
6. System sends order confirmation message

## Development

The application uses:
- FastAPI for the web framework
- LangGraph for AI agent creation
- Anthropic's Claude 3 Haiku for natural language processing
- MCP adapters for service integration

## License

This project is licensed under the terms specified in the LICENSE file.