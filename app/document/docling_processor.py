# app/document/docling_processor.py
import os
import json
import logging
import tempfile
from typing import List, Dict, Optional

from pinecone import Pinecone
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from langchain_community.embeddings import OpenAIEmbeddings

from app.document.s3_manager import S3Manager
from app.document.tokenizer import OpenAITokenizerWrapper

load_dotenv()
logger = logging.getLogger(__name__)

class DoclingProcessor:
    def __init__(self):
        """Initialize processors and services."""
        self.s3_manager = S3Manager()
        self.initialize_pinecone()

        self.converter = DocumentConverter()
        self.tokenizer = OpenAITokenizerWrapper(model_name="cl100k_base", max_length=8191)
        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_tokens=8191,
            merge_peers=True
        )
        self.embeddings = OpenAIEmbeddings()

    def initialize_pinecone(self):
        """Initialize Pinecone client and index."""
        try:
            api_key = os.getenv("PINECONE_API_KEY")
            index_name = os.getenv("PINECONE_INDEX_NAME")

            if not api_key or not index_name:
                raise ValueError("Missing required Pinecone configuration: PINECONE_API_KEY or PINECONE_INDEX_NAME")

            pc = Pinecone(api_key=api_key)
            self.index = pc.Index(index_name)
            logger.info(f"Successfully initialized Pinecone index: {index_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            raise RuntimeError(f"Pinecone initialization failed: {str(e)}")

    def process_and_index_document(self, document_id: str, s3_key: str, metadata: Dict) -> Dict:
        """Process and index a document."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                local_pdf = os.path.join(tmpdir, "temp.pdf")
                if not self.s3_manager.download_file(s3_key, local_pdf):
                    raise FileNotFoundError(f"Could not download from S3: {s3_key}")

                result = self.converter.convert(local_pdf)
                if not result.document:
                    raise ValueError("Docling conversion returned empty document")

                chunks = list(self.chunker.chunk(dl_doc=result.document))
                if not chunks:
                    raise ValueError("No chunks generated from document")

                vectors = []
                for i, chunk in enumerate(chunks):
                    chunk_meta = {
                        "document_id": document_id,
                        "s3_key": s3_key,
                        "title": chunk.meta.headings[0] if chunk.meta.headings else None,
                        "page_numbers": sorted({
                            prov.page_no
                            for item in chunk.meta.doc_items
                            for prov in item.prov
                        }) if chunk.meta.doc_items else None,
                        "chunk_text": chunk.text,
                        **metadata
                    }

                    emb = self.embeddings.embed_query(chunk.text)
                    vectors.append({
                        'id': f"{document_id}_chunk_{i}",
                        'values': emb,
                        'metadata': chunk_meta
                    })

                # Batch upsert to Pinecone
                batch_size = 100
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    self.index.upsert(vectors=batch)

                # Save document structure
                structure = {
                    "num_chunks": len(chunks),
                    "metadata": metadata,
                    "chunks": [
                        {
                            "chunk_id": f"{document_id}_chunk_{i}",
                            "title": v["metadata"].get("title"),
                            "pages": v["metadata"].get("page_numbers"),
                            "snippet": v["metadata"]["chunk_text"][:300]
                        }
                        for i, v in enumerate(vectors)
                    ]
                }

                map_key = f"docling_mappings/{document_id}_mapping.json"
                self.s3_manager.s3_client.put_object(
                    Bucket=self.s3_manager.bucket_name,
                    Key=map_key,
                    Body=json.dumps(structure)
                )

                logger.info(f"Successfully processed and indexed document {document_id} with {len(chunks)} chunks")
                return {"status": "success", "indexed_chunks": len(chunks)}

        except Exception as e:
            logger.exception(f"Error processing document {document_id}: {str(e)}")
            return {"status": "error", "error": str(e)}

    def search_document(self, query: str, document_id: Optional[str] = None, top_k: int = 3) -> List[Dict]:
        """Search for relevant document chunks."""
        try:
            embedding = self.embeddings.embed_query(query)
            filter_dict = {"document_id": document_id} if document_id else {}

            results = self.index.query(
                vector=embedding,
                filter=filter_dict,
                top_k=top_k,
                include_metadata=True
            )

            return [
                {
                    "score": match.score,
                    "metadata": match.metadata
                }
                for match in results.matches
            ] if hasattr(results, 'matches') else []

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

    def get_document_structure(self, document_id: str) -> Optional[Dict]:
        """Get document structure from S3."""
        try:
            map_key = f"docling_mappings/{document_id}_mapping.json"
            obj = self.s3_manager.s3_client.get_object(
                Bucket=self.s3_manager.bucket_name,
                Key=map_key
            )
            return json.loads(obj["Body"].read())

        except Exception as e:
            logger.error(f"Could not retrieve structure for document {document_id}: {str(e)}")
            return None
