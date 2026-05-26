# Azure Serverless Function Setup

## Local Development

1. Install Azure Functions Core Tools
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run locally: `func start`

## Testing Endpoints

### Document Agent Orchestrator
```
GET http://localhost:7071/api/document-orchestrate?name=YourName
```

### Health Check
```
GET http://localhost:7071/api/health
```

### POST Request Example
```bash
curl -X POST http://localhost:7071/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"name": "DocumentProcessor"}'
```

## Deploy to Azure

1. Create Azure storage account and function app
2. Publish: `func azure functionapp publish <FunctionAppName>`

## Function Structure

- `document_orchestrator.py` - Main orchestrator function code
- `config.py` - Environment configuration (local vs production)
- `.env.local` - Local environment variables (don't commit)
- `local.settings.json` - Local configuration (don't commit)
- `requirements.txt` - Python dependencies
