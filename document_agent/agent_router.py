from .database import read_from_firebase, init_firebase, get_file_from_blob, document_name_dict
from .pipeline import run_pipeline
from .tools import verify_document

async def route_document_agents(doc_count : int, username : str):



    documents_url_required, documents_url_optional = await read_from_firebase(username, doc_count)
    
    for key in documents_url_required.keys():
        document = get_file_from_blob(documents_url_required[key])
        document_type = document_name_dict[key]
        response = run_pipeline(document_type, document, "pdf")
        report = response["report"]
        if report.get("status") == "success":
            fields = report.get("extracted_fields", {})   
            return await verify_document(document_type, fields)
            
        
        else: return None
           


