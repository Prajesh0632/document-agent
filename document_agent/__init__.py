"""
document_agent
--------------
Nepal National Identity (NIN) document extraction package.

Main entry point:
    from document_agent.pipeline import run_pipeline
    result = run_pipeline("NIN", file_bytes=b"...", file_type="pdf")
    print(result["report"])
"""
