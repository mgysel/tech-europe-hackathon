# AI Hackathon Backend

A FastAPI server that integrates with LangChain and Firebase to process orders using AI agents.

## Features

- **FastAPI Server**: Modern, fast web framework for building APIs
- **LangChain Integration**: AI-powered order processing using OpenAI
- **Firebase Integration**: Real-time database for order management
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

# Firebase Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/serviceAccountKey.json
FIREBASE_PROJECT_ID=your_firebase_project_id

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### 3. Firebase Setup

#### Option A: Using Service Account Key (Recommended for Production)

1. Go to Firebase Console → Project Settings → Service Accounts
2. Generate a new private key
3. Download the JSON file
4. Set the path in `GOOGLE_APPLICATION_CREDENTIALS`

#### Option B: Using Firebase Emulator (Development)

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize Firebase emulator
firebase init emulators

# Start emulator
firebase emulators:start
```

### 4. Run the Server

```bash
# Development
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
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

#### 2. Process Order
- **GET** `/order/{order_id}`
- **Description**: Process an order using LangChain agent
- **Parameters**: 
  - `order_id` (path): The ID of the order to process
- **Response**:
```json
{
  "order_id": "order123",
  "status": "success",
  "result": "Order processing result from LangChain agent",
  "message": "Order order123 processed successfully"
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

## LangChain Agent Tools

The LangChain agent has access to the following tools:

1. **get_order_details**: Retrieves order information from Firebase
2. **update_order_status**: Updates order status in Firebase
3. **process_order**: Processes an order and returns details

## Firebase Collections

The application expects a `orders` collection in Firebase with documents containing:

```json
{
  "order_id": "string",
  "customer_id": "string",
  "items": ["array"],
  "total": "number",
  "status": "string",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

## Development

### Project Structure
```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── env.example         # Environment variables template
└── README.md          # This file
```

### Adding New Tools

To add new tools to the LangChain agent, modify the `create_langchain_agent()` function in `main.py`:

```python
tools = [
    # ... existing tools ...
    Tool(
        name="your_new_tool",
        func=your_new_function,
        description="Description of what your tool does"
    )
]
```

### Error Handling

The application includes comprehensive error handling for:
- Firebase connection issues
- LangChain agent creation failures
- API endpoint errors
- Missing environment variables

## Production Deployment

1. Set up proper environment variables
2. Configure Firebase production credentials
3. Set up proper CORS origins
4. Use a production WSGI server like Gunicorn
5. Set up monitoring and logging

## Troubleshooting

### Common Issues

1. **Firebase Connection Error**: Check your service account credentials
2. **LangChain Agent Error**: Verify your OpenAI API key
3. **Import Errors**: Ensure all dependencies are installed

### Logs

The application logs to stdout. Check the logs for detailed error information. 