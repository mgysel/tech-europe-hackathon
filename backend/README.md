# AI Hackathon Backend

A FastAPI server that integrates with LangChain to process conversational ordering tasks using AI.

## Features

- **FastAPI Server**: Modern, fast web framework for building APIs
- **LangChain Integration**: AI-powered conversational ordering assistance using OpenAI
- **Smart Clarification**: Automatically asks for missing information
- **Universal Ordering**: Handles any type of ordering task (food, services, products, etc.)
- **RESTful API**: Clean, documented endpoints

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your variables:

```bash
cp env.example .env
```

Edit `.env` with your actual values:

```env
# OpenAI API Key for LangChain
OPENAI_API_KEY=your_actual_openai_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
```



### 4. Run the Server

```bash
# Development
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test Conversational Orders

```bash
# Test the conversational order processing
python test_conversation.py

# Or test manually with curl
curl -X POST http://localhost:8000/order/process \
  -H "Content-Type: application/json" \
  -d '{"order_text": "I want 30 pizzas at 4pm"}'
```

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Root Endpoint
- **GET** `/`
- **Description**: Health check and API info
- **Response**: 
```json
{
  "message": "AI Hackathon Backend API",
  "status": "running"
}
```

#### 2. Process Conversational Order
- **POST** `/order/process`
- **Description**: Process a conversational order using LangChain agent with clarification capabilities
- **Request Body**:
```json
{
  "order_text": "I want 30 pizzas at 4pm",
  "conversation_id": "optional_conversation_id"
}
```
- **Response**:
```json
{
  "response": "Great! I can help you with that order. Do you have any preference for pizza toppings?",
  "needs_clarification": true,
  "conversation_id": "conv_1234567890",
  "order_id": null
}
```



#### 3. Health Check
- **GET** `/health`
- **Description**: Detailed health status of services
- **Response**:
```json
{
  "status": "healthy",
  "firebase": "connected",
  "langchain": "available"
}
```

## How It Works

The system uses LangChain with OpenAI's GPT-3.5-turbo to:

1. **Understand Orders**: Parse natural language order requests
2. **Ask Clarifying Questions**: Identify missing information and ask relevant questions
3. **Provide Friendly Responses**: Maintain conversational tone throughout the interaction
4. **Detect Completion**: Automatically determine when enough information is gathered



## Development

### Project Structure
```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── env.example         # Environment variables template
└── README.md          # This file
```

### Customizing Responses

To customize the agent's responses, modify the prompt in the `process_order_conversation` function in `main.py`:

```python
prompt = f"""
You are a helpful ordering assistant. A customer has said: "{request.order_text}"

Your job is to:
1. Understand what they want to order or procure
2. Ask clarifying questions if needed
3. Be friendly and helpful
4. If you have enough information, search for the best options

# Add your custom instructions here
"""
```

### Error Handling

The application includes comprehensive error handling for:
- LangChain LLM creation failures
- API endpoint errors
- Missing environment variables

## Production Deployment

1. Set up proper environment variables
2. Set up proper CORS origins
3. Use a production WSGI server like Gunicorn
4. Set up monitoring and logging

## Troubleshooting

### Common Issues

1. **LangChain LLM Error**: Verify your OpenAI API key
2. **Import Errors**: Ensure all dependencies are installed

### Logs

The application logs to stdout. Check the logs for detailed error information. 