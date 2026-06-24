import httpx
import json
from config import get_settings

settings = get_settings()


async def verify_document(document_type: str, document_info: dict):
  
    try:
        # Build query parameters
        params = {
            "document_type": document_type,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.DOCUMENT_VERIFICATION_API, 
                params=params,
                json=document_info
            )
            response.raise_for_status()
            
            return response.text
            
    except httpx.HTTPError as error:
        return {"error": str(error), "status": "failed"}
    except Exception as error:
        return {"error": str(error), "status": "failed"}
