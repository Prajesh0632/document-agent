from .firebase_db import get_db
from .documents_list import documents







async def read_from_firebase(username : str, doc_count : int):

    try:
        db = get_db()
        user_document = db.collection("form-data").document(username).collection(f"doc{doc_count}")
        documemt_data = user_document.document("documents").get()
        document_data_dict : dict = documemt_data.to_dict()
        
        documents_url_required : dict = {}
        documents_url_optional : dict = {}
        for document_type in documents:
            document = document_data_dict[document_type]
            if(document["required"]):
              documents_url_required[document_type] = document["url"]
            else:
              documents_url_optional[document_type] = document["url"]

        return documents_url_required, documents_url_optional       

        

    except Exception as err:
        return err, err


# async def store_in_firebase(
#                              application_model : BaseLoanApplication, 
#                              application_requirements : dict,
#                              document_model : CommonLoanDocuments,
#                              document_requirements : dict,
#                              document_titles : list[str],
#                              urls,
#                              current_user : str):
#     db = get_db()
    




#     try:
#         application_data = application_model.model_dump()

        
#         doc = db.collection("form-data").document(current_user)
#         doc_details = doc.get()
        
#         doc_count = 0
#         if doc_details.exists:
#             doc_data = doc_details.to_dict() or {}
#             doc_count = doc_data.get("count", 0)


#         doc.set({
#             "count" : doc_count + 1,
            
#         })

        
#         loan_doc = doc.collection(f"doc{doc_count + 1}")


#         loan_doc.document("info").set(
#             {
#             "loan_type": application_data["loan_type"],
#             "status": "pending",   
#             }
#         )
       


       
#         loan_doc.document("loan_request").set(application_data["loan_request"])
#         loan_doc.document("applicant_details").set(application_data["applicant_details"])
#         loan_doc.document("employment").set(application_data["employment"])
#         loan_doc.document("security").set(application_data["security"])
#         loan_doc.document("financial_position").set(application_data["financial_position"])
#         loan_doc.document("declarations").set(application_data["declarations"])


#         loan_doc.document("application_requirements").set(application_requirements)


#         document_data = document_model.model_dump()
        
#         for index, title in enumerate(document_titles):
#             document = document_data[title]
#             document['url'] = urls[index]
#             document['required'] = document_requirements[title]
           

#         loan_doc.document("documents").set(document_data)   


        


        
#     except Exception as error:
#         print(error)
#         return None    
    
#     return True



# async def rollback_writes(current_user : str, doc_count : int)->bool:

#     db = get_db()

#     try:
        
#         document = db.collection('form-data').document(current_user)
#         loan_collection = document.collection(f"doc{doc_count}")

#         docs = loan_collection.stream()

#         for doc in docs:
#             doc.reference.delete()

#         doc_data = document.get().to_dict() or {}
#         current_count = doc_data.get("count", 0)

#         document.update({
#             "count" : max(0, current_count - 1)
#         })    
        
#         print(f"Rolled Back doc{doc_count}")
#         return True


#     except:
#         print(f"Rollback failed")
#         return False

