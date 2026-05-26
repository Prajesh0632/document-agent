import azure.functions as func
import os
from config import get_settings

settings = get_settings()

auth_level = func.AuthLevel.FUNCTION if settings.enable_auth else func.AuthLevel.ANONYMOUS

app = func.FunctionApp()

@app.function_name("DocumentAgentOrchestrator")
@app.route(route="document-orchestrate", auth_level=auth_level)
def document_agent_orchestrator(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main orchestrator for document agent - routes to other agents
    """
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
            name = req_body.get('name')
        except ValueError:
            pass

    if name:
        return func.HttpResponse(f"Hello, {name}!")
    else:
        return func.HttpResponse(
            "Please pass a name on the query string or in the request body",
            status_code=400
        )

@app.function_name("Health")
@app.route(route="health")
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint
    """
    return func.HttpResponse(
        f"OK - Environment: {settings.environment}",
        status_code=200
    )
