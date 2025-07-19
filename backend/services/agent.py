"""Agent service for managing LangChain agents, conversation sessions, and order processing."""

from typing import Tuple
import uuid

from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_openai_functions_agent
from langchain.agents.agent import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import LLM_MODEL, TEMPERATURE, SYSTEM_TEMPLATE
from tools.restaurant_tools import search_restaurants_tool
from schemas.schemas import OrderRequest, OrderResponse
from services.firestore_service import firestore_service


class AgentService:
    """Service for managing LangChain agents, conversation sessions, and order processing."""
    
    def __init__(self):
        # For o3 and similar models that don't support custom temperature, don't set it
        if LLM_MODEL in ["o3", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4.1"]:
            self.llm = ChatOpenAI(model_name=LLM_MODEL)
        else:
            self.llm = ChatOpenAI(model_name=LLM_MODEL, temperature=TEMPERATURE)
        self.tools = [search_restaurants_tool]
        # In-memory session storage: session_id -> ConversationBufferMemory
        self._session_store: dict[str, ConversationBufferMemory] = {}
    
    def get_agent(self, session_id: str) -> Tuple[ConversationBufferMemory, AgentExecutor]:
        """Return (memory, agent) for a given session, creating them on first use."""
        if session_id not in self._session_store:
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            self._session_store[session_id] = memory
        
        memory = self._session_store[session_id]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_TEMPLATE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory,
            verbose=False,
        )
        
        return memory, agent_executor
    
    def create_session_id(self) -> str:
        """Generate a new session ID."""
        return str(uuid.uuid4())
    
    def clear_session(self, session_id: str) -> None:
        """Clear memory for a specific session."""
        if session_id in self._session_store:
            self._session_store[session_id].clear()
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session completely."""
        if session_id in self._session_store:
            del self._session_store[session_id]
    
    async def process_order(self, req: OrderRequest) -> OrderResponse:
        """Process an order request and return the response."""
        # Create a new session ID for each request
        session_id = self.create_session_id()
        memory, agent = self.get_agent(session_id)

        try:
            # Clear existing memory for this session
            memory.clear()
            
            # Print what user sent
            print(f"[ORDER ENDPOINT] User request: task_id={req.task_id}")
            
            # Fetch messages from Firestore
            firestore_messages = firestore_service.get_task_messages(req.task_id)
            
            # Print response from Firebase when requesting messages from the task id
            print(f"[ORDER ENDPOINT] Firebase response for task_id={req.task_id}:")
            print(f"[ORDER ENDPOINT] Number of messages retrieved: {len(firestore_messages)}")
            for i, msg in enumerate(firestore_messages):
                print(f"[ORDER ENDPOINT] Message {i+1}: {msg}")
            
            if not firestore_messages:
                raise HTTPException(
                    status_code=404,
                    detail=f"No messages found for task_id: {req.task_id}"
                )
            
            # Process messages from Firestore (they come in descending order, so reverse)
            firestore_messages.reverse()
            
            last_user_message = None
            for msg in firestore_messages:
                # Handle the actual Firestore message format: sender/text
                if 'sender' in msg and 'text' in msg:
                    if msg['sender'] == 'me' or msg['sender'] == 'user':
                        last_user_message = msg['text']
                        memory.chat_memory.add_user_message(msg['text'])
                    elif msg['sender'] == 'ai' or msg['sender'] == 'assistant':
                        memory.chat_memory.add_ai_message(msg['text'])
                # Fallback to other formats if they exist
                elif 'user' in msg and msg['user']:
                    last_user_message = msg['user']
                    memory.chat_memory.add_user_message(msg['user'])
                elif 'ai' in msg and msg['ai']:
                    memory.chat_memory.add_ai_message(msg['ai'])
                elif 'message' in msg:
                    # If it's a generic message, assume it's from user
                    last_user_message = msg['message']
                    memory.chat_memory.add_user_message(msg['message'])
            
            if not last_user_message:
                raise HTTPException(
                    status_code=400,
                    detail="No user messages found in task"
                )
            
            # Process the last user message with the agent
            result = agent.invoke({"input": last_user_message})
            ai_response = str(result["output"])
            
            # Write the AI response back to Firestore
            firestore_service.write_task_message(
                task_id=req.task_id,
                sender="ai",
                text=ai_response
            )
            
            return OrderResponse(
                session_id=session_id, 
                response=ai_response
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            # Wrap other exceptions as HTTP 500 errors
            raise HTTPException(status_code=500, detail=str(exc)) from exc


# Global instance
agent_service = AgentService() 