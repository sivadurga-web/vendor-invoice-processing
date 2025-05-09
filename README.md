# Vendor Invoice Processing Application

A FastAPI-based application that integrates with WhatsApp and Cashfree MCP services to process vendor invoices and payments. The application uses AI-powered message processing and supports secure payment workflows.

## Features

- 💬 Automated responses for invoice-related queries and do invoice transfer
- 🤖 AI-powered message processing using Claude 3 Haiku
- 🔐 Secure integration with Cashfree MCP services

## Prerequisites

- Python 3.11+
- `.env` file with required environment variables
- Docker installed on your system

## Configuration

1. Set up `multi_server_config.json` with your MCP service configurations.
2. Ensure the public key for Cashfree is placed in the `public_keys/` directory.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sivadurga-web/vendor-invoice-processing.git
   cd vendor-invoice-processing
   ```

2. Install Python dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

3. Install Node.js dependencies for Cashfree MCP and vendor chat services:
   ```bash
   cd cashfree-mcp && npm install
   cd ../vendor-invoice-processor-chat && npm install
   ```

## Usage

### Run Locally

1. Start the FastAPI application:
   ```bash
   uv run main.py
   ```

2. Start the Cashfree MCP service:
   ```bash
   node ./cashfree-mcp/src/index.js
   ```

3. Start the vendor chat service:
   ```bash
   node ./vendor-invoice-processor-chat/src/index.js
   ```

The FastAPI server will start on `http://0.0.0.0:8000`.

### Run with Docker

1. Build the Docker image:
   ```bash
   docker build -t vendor-invoice .
   ```

2. Run the application using Docker:
   ```bash
   docker run -p 8085:8080 -p 8000:8000 vendor-invoice
   ```

   - The FastAPI application will be available at `http://localhost:8000`.
   - The vendor chat service will be available at `http://localhost:8085`.

## API Endpoints

### Process WhatsApp Message
- **POST** `/api/process_message`
- Handles incoming WhatsApp messages.
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
- Handles payment confirmation webhooks from Cashfree.
- Expects Cashfree webhook payload format.

## Development

The application uses:
- **FastAPI** for the web framework.
- **LangGraph** for AI agent creation.
- **Anthropic's Claude 3 Haiku** for natural language processing.
- **Node.js** for Cashfree MCP and vendor chat services.

## Environment Variables

The `.env` file should include:
- `ANTHROPIC_API_KEY`: API key for Claude 3 Haiku.

## License

This project is licensed under the terms specified in the LICENSE file.
