"""Run with uvicorn manufacturing_app:app; import never constructs runtime."""
from rag_qa.api.app import create_manufacturing_app

app = create_manufacturing_app()
