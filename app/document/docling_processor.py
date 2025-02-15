from typing import List, Dict, Optional
import os
from pathlib import Path
import tempfile
import json
import logging
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from langchain_community.embeddings import OpenAIEmbeddings
import pinecone
from .tokenizer import OpenAITokenizerWrapper
from .s3_manager import S3Manager

logger = logging.getLogger(__name__)

class DoclingProcessor:
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
        
        # Initialize Docling components
        self.converter = DocumentConverter()
        self.tokenizer = OpenAITokenizerWrapper()
        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_tokens=8191,  # text-embedding-3-large's maximum context length
            merge_peers=True,
        )

    def process_document(self, file_path: str, document_id: str, metadata: Dict) -> Dict:
        """Process a document using Docling's advanced processing pipeline."""
        try:
            # Convert document using Docling
            result = self.converter.convert(file_path)
            if not result.document:
                raise ValueError(f"Failed to convert document: {file_path}")

            # Apply hybrid chunking
            chunks = list(self.chunker.chunk(dl_doc=result.document))
            
            # Create embeddings and store in Pinecone
            vectors_to_upsert = []
            for i, chunk in enumerate(chunks):
                # Extract metadata from chunk
                chunk_metadata = {
                    'document_id': document_id,
                    'page_numbers': sorted(set(
                        prov.page_no
                        for item in chunk.meta.doc_items
                        for prov in item.prov
                    )) if chunk.meta.doc_items else None,
                    'title': chunk.meta.headings[0] if chunk.meta.headings else None,
                    'section': chunk.meta.section if hasattr(chunk.meta, 'section') else None,
                    **metadata
                }

                # Create embedding
                embedding = self.embeddings.embed_query(chunk.text)
                
                vectors_to_upsert.append({
                    'id': f"{document_id}_chunk_{i}",
                    'values': embedding,
                    'metadata': {
                        **chunk_metadata,
                        'text': chunk.text[:1000]  # Store truncated text for preview
                    }
                })

            # Upsert to Pinecone in batches
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)

            # Store document mapping in S3
            mapping = {
                "total_chunks": len(chunks),
                "metadata": metadata,
                "structure": {
                    "sections": [
                        {
                            "title": chunk.meta.headings[0] if chunk.meta.headings else None,
                            "chunk_id": f"{document_id}_chunk_{i}"
                        }
                        for i, chunk in enumerate(chunks)
                    ]
                }
            }
            
            mapping_key = f"{document_id}_mapping.json"
            self.s3_manager.s3_client.put_object(
                Bucket=self.s3_manager.bucket_name,
                Key=mapping_key,
                Body=json.dumps(mapping)
            )

            return {
                "status": "success",
                "num_chunks": len(chunks),
                "document_id": document_id
            }

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    def search_document(self, query: str, document_id: Optional[str] = None, top_k: int = 3) -> List[Dict]:
        """Search for relevant chunks using Pinecone."""
        query_embedding = self.embeddings.embed_query(query)
        
        # Prepare filter
        filter_dict = {"document_id": document_id} if document_id else {}
        
        results = self.index.query(
            vector=query_embedding,
            filter=filter_dict,
            top_k=top_k,
            include_metadata=True
        )
        
        return [{
            "text": match.metadata["text"],
            "metadata": {
                "page_numbers": match.metadata.get("page_numbers"),
                "title": match.metadata.get("title"),
                "section": match.metadata.get("section"),
                "score": match.score
            }
        } for match in results.matches]

    def get_document_structure(self, document_id: str) -> Optional[Dict]:
        """Get the document's structure from S3."""
        mapping_key = f"{document_id}_mapping.json"
        try:
            response = self.s3_manager.s3_client.get_object(
                Bucket=self.s3_manager.bucket_name,
                Key=mapping_key
            )
            return json.loads(response['Body'].read())
        except Exception as e:
            logger.error(f"Error retrieving document structure: {str(e)}")
            return None
