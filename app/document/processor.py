import fitz
from pathlib import Path
import pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
import os
from typing import List, Dict, Optional
import json
import logging
from .s3_manager import S3Manager

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Initialize Pinecone
        pinecone.init(
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT')
        )
        self.index_name = os.getenv('PINECONE_INDEX_NAME')
        if not self.index_name:
            raise ValueError("PINECONE_INDEX_NAME environment variable is not set")
            
        self.index = pinecone.Index(self.index_name)
        self.embeddings = OpenAIEmbeddings()
        self.s3_manager = S3Manager()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def process_pdf(self, file_path: str, document_id: str) -> Dict:
        """Process a PDF file and store its embeddings in Pinecone."""
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Extract text and metadata from PDF
        doc = fitz.open(file_path)
        pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages.append({
                "page_num": page_num + 1,
                "text": text,
            })

        # Split text into chunks
        all_texts = [page["text"] for page in pages]
        chunks = self.text_splitter.split_text("\n".join(all_texts))

        # Create embeddings and store in Pinecone
        vectors_to_upsert = []
        for i, chunk in enumerate(chunks):
            embedding = self.embeddings.embed_query(chunk)
            vectors_to_upsert.append({
                'id': f"{document_id}_chunk_{i}",
                'values': embedding,
                'metadata': {
                    'document_id': document_id,
                    'page': i // 2 + 1,
                    'text': chunk
                }
            })

        # Upsert to Pinecone in batches
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            self.index.upsert(vectors=batch)

        # Save page mapping to S3
        page_mapping = {
            "total_pages": len(doc),
            "pages": pages
        }
        
        mapping_key = f"{document_id}_mapping.json"
        self.s3_manager.s3_client.put_object(
            Bucket=self.s3_manager.bucket_name,
            Key=mapping_key,
            Body=json.dumps(page_mapping)
        )

        return {
            "status": "success",
            "num_pages": len(doc),
            "num_chunks": len(chunks)
        }

    def search_document(self, document_id: str, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant chunks in a document using Pinecone."""
        query_embedding = self.embeddings.embed_query(query)
        
        results = self.index.query(
            vector=query_embedding,
            filter={"document_id": document_id},
            top_k=top_k,
            include_metadata=True
        )
        
        return [{
            "text": match.metadata["text"],
            "metadata": {
                "page": match.metadata["page"],
                "score": match.score
            }
        } for match in results.matches]

    def get_page_content(self, document_id: str, page_num: int) -> Optional[str]:
        """Get the content of a specific page from S3."""
        mapping_key = f"{document_id}_mapping.json"
        try:
            response = self.s3_manager.s3_client.get_object(
                Bucket=self.s3_manager.bucket_name,
                Key=mapping_key
            )
            mapping = json.loads(response['Body'].read())
            
            for page in mapping["pages"]:
                if page["page_num"] == page_num:
                    return page["text"]
                    
            return None
        except Exception as e:
            logger.error(f"Error retrieving page content: {str(e)}")
            return None
