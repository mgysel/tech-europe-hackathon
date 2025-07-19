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


class AgentService:
    """Service for managing LangChain agents, conversation sessions, and order processing."""
    
    def __init__(self):
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
        # Create a new session ID if needed
        session_id = req.session_id or self.create_session_id()
        memory, agent = self.get_agent(session_id)

        try:
            # Clear existing memory for this session
            memory.clear()
            
            # Process conversation history
            for i, msg in enumerate(req.messages):
                if msg.user:
                    # Add user message to memory
                    memory.chat_memory.add_user_message(msg.user)
                    
                    # If this is the last message, invoke the agent
                    if i == len(req.messages) - 1:
                        result = agent.invoke({"input": msg.user})
                        return OrderResponse(
                            session_id=session_id, 
                            response=str(result["output"])
                        )
                
                if msg.ai:
                    # Add AI response to memory
                    memory.chat_memory.add_ai_message(msg.ai)
            
            # If no user message in the last item, return an error
            raise HTTPException(
                status_code=400, 
                detail="Last message must be from user"
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            # Wrap other exceptions as HTTP 500 errors
            raise HTTPException(status_code=500, detail=str(exc)) from exc


# Global instance
agent_service = AgentService() 