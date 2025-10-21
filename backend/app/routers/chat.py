from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas import ChatMessage, ChatResponse
from app.auth import get_current_user
from app.utils.openai_tools import process_chat_message
import logging

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
        message: ChatMessage,
        current_user: dict = Depends(get_current_user)
):
    """
    AI Copilot chat endpoint

    Processes natural language commands and executes actions like:
    - "approve Ramesh" - Approves a pending visitor
    - "deny John Doe" - Denies a pending visitor
    - "check in Suresh" - Checks in an approved visitor
    - "check out Mr Verma" - Checks out a checked-in visitor
    - "show me all pending visitors" - Lists visitors by status

    The AI uses OpenAI function calling to execute these actions
    after validating user permissions and visitor state.

    **Parameters:**
    - **message**: Natural language command or question

    **Returns:**
    - **response**: AI's text response
    - **action_taken**: Name of action performed (if any)
    - **details**: Details of the action result (if any)
    """
    try:
        logger.info(f"Chat message from user {current_user['id']}: {message.message}")
        print(current_user["household_id"])
        response = await process_chat_message(message.message, current_user)
        logger.info(f"Chat response: {response.response}")
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )
