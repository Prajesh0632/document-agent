import azure.functions as func
from config import get_settings
from document_agent.agent_router import route_document_agents
from document_agent.database import init_firebase



settings = get_settings()
init_firebase()


auth_level = func.AuthLevel.FUNCTION if settings.enable_auth else func.AuthLevel.ANONYMOUS

app = func.FunctionApp()

@app.function_name("AgentOrchestrator")
@app.route(route="loan-orchestrate", auth_level=auth_level)
async def document_agent_orchestrator(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main orchestrator for loan agents - routes to other agents
    """
    doc_num = req.params.get('doc-number')
    username = req.params.get('username')
    if not doc_num and not username:
        try:
            req_body = req.get_json()
            doc_num = req_body.get('doc-number')
            username = req_body.get('username')
        except ValueError:
            pass

    if doc_num and username:
        
        response = await route_document_agents(int(doc_num), username)
        return func.HttpResponse(f"Hello, {doc_num} and {username} {response}!")
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
