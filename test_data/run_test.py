import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from document_agent.pipeline.document_pipeline import run_pipeline

# ── Point to your PDF ──────────────────────────────────────────────────────
PDF_PATH = os.path.join(os.path.dirname(__file__), "NIN1.pdf")

with open(PDF_PATH, "rb") as f:
    file_bytes = f.read()

print(f"Running pipeline on: {PDF_PATH} ({len(file_bytes)} bytes)")
result = run_pipeline("NIN" ,file_bytes, file_type="pdf")
report = result["report"]

print("\n" + "="*50)
print("STATUS :", report.get("status"))
print("VERDICT:", report.get("verdict"))
print("SCORE  :", report.get("blur_score"))
print("="*50)

if report.get("status") == "success":
    fields = report.get("extracted_fields", {})
    print("\nExtracted Fields:")
    for k, v in fields.items():
        print(f"  {k:<22} : {v}")
else:
    print("\nRejected:")
    print(report.get("reupload_message"))