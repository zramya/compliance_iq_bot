# Lod the pdf file from data folder
# extract the content of the file
# arrive at the chunking stategy
# chunk_overlap and size
# Load the embedding model
# embed the chunk

import tempfile

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.db import get_vector_store
import os

# load env variables
load_dotenv()


def ingest_pdf(pdf_filepath):
    print("Ingestion_started")

    # Load the PDF into LangChain Documents
    loader = PyPDFLoader(pdf_filepath)
    docs = loader.load()
    # 2 Metadata enrichment
    for doc in docs:
        doc.metadata.update(
            {
                "source": str(pdf_filepath),
                "document_extension": "pdf",
                "page": doc.metadata.get("page"),
                "last_updated": os.path.getmtime(pdf_filepath),
            }
        )

    print(docs)
    print("before chunking")

    # 3 chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # upto 1000 characters
        chunk_overlap=200,  # upto 200 characters
    )
    chunks = splitter.split_documents(docs)
    print("total chunks")
    print(len(chunks))
    print(f"Chunks metadata : {chunks[0].metadata}")

    # 4 load the embedding model & 5 generate the embeddings
    # 6. save it in vector db
    vector_store = get_vector_store(collection_name="reg_compliance_iq_bot")
    vector_store.add_documents(chunks)

    print("Ingestion Completed")


# uv run app/ingestion/ingestion.py
