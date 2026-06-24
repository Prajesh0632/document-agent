from azure.storage.blob import BlobServiceClient
from config import get_settings
from urllib.parse import urlparse


settings = get_settings()


blob_service_client = None


def get_file_from_blob(url : str):

    
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.lstrip('/').split('/', 1)

        container_name = path_parts[0]
        blob_name = path_parts[1]

        service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        
        blob_client = service_client.get_blob_client(container=container_name, blob=blob_name)      
        
        file_bytes = blob_client.download_blob().readall()
        return file_bytes
        
    except Exception as error:
        print(f"Error reading from blob: {error}")
        return error

    

# async def store_in_blob(
#                         loan_type : str,
#                         document_model : CommonLoanDocuments,
#                         documents : list[UploadFile],
#                         document_requirements : dict,
#                         document_titles : list[str],
#                         current_user : str,
#                         doc_count : int,
#                         )->list[str]:
    
#     await init_blob()
#     urls : str = []


#     try:
#         for index, document in enumerate(documents):
#             file_bytes = await document.read()
#             filename = document_titles[index]
#             container_name = settings.AZURE_BLOB_CONTAINER_NAME
#             blob_path =  f"{current_user}/doc{doc_count + 1}/{loan_type}/{filename}" 

#             azure_url =  await upload_file(file_bytes, filename, container_name, blob_path)

#             if not azure_url:
#                 return None
            
#             urls.append(azure_url)

        
    
#     except Exception as error:
#         print(error)
#         return None

#     return urls 
        


    


    



# async def upload_file(
#                       file_bytes,
#                       filename : str,
#                       container_name : str,
#                       blob_path : str,
#                                )->str:
#     global blob_service_client

#     try:
#         if not blob_service_client:
#             await init_blob()

#         blob_client = blob_service_client.get_blob_client(
#             container = container_name,
#             blob = blob_path
#         )    
#         blob_client.upload_blob(file_bytes, overwrite=True)
#         return blob_client.url


#     except Exception as err:
#         print(err)
#         return None     




# async def rollback_uploads(current_user : str, doc_count : int)->bool:
    
#     directory = f"{current_user}/doc{doc_count}"
    
#     try:
#         container_client = blob_service_client.get_container_client(settings.AZURE_BLOB_CONTAINER_NAME)
#         blobs = container_client.list_blobs(name_starts_with=directory)

#         for blob in blobs:
#             container_client.delete_blob(blob.name)

#         return True    

#     except Exception as error:
#         print(error)
#         return None        

    
    
   















