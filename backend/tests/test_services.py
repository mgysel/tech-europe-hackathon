"""Tests for service modules."""

import pytest
from unittest.mock import Mock, patch

from services.agent import AgentService
from schemas.schemas import OrderRequest, Message


class TestAgentService:
    """Tests for AgentService."""
    
    def test_create_session_id(self):
        """Test session ID creation."""
        service = AgentService()
        session_id = service.create_session_id()
        assert isinstance(session_id, str)
        assert len(session_id) > 0
    
    def test_get_agent_creates_new_session(self):
        """Test that get_agent creates new sessions correctly."""
        service = AgentService()
        session_id = "test-session"
        
        memory, agent = service.get_agent(session_id)
        assert memory is not None
        assert agent is not None
        assert session_id in service._session_store
    
    @pytest.mark.asyncio
    async def test_process_order_with_session_id(self):
        """Test order processing with existing session ID."""
        service = AgentService()
        
        # Mock the get_agent method
        with patch.object(service, 'get_agent') as mock_get_agent:
            mock_memory = Mock()
            mock_agent = Mock()
            mock_agent.invoke.return_value = {"output": "Test response"}
            mock_get_agent.return_value = (mock_memory, mock_agent)
            
            request = OrderRequest(
                session_id="test-session",
                messages=[Message(user="I want pizza")]
            )
            
            response = await service.process_order(request)
            
            assert response.session_id == "test-session"
            assert response.response == "Test response"
            mock_memory.clear.assert_called_once()
            mock_agent.invoke.assert_called_once() 