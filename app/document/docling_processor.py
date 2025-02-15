import os
import json
import logging
import tempfile
from typing import List, Dict, Optional

import pinecone
from dotenv import load_dotenv

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

from app.document.s3_manager import S3Manager
from app.document.tokenizer import OpenAITokenizerWrapper
from langchain.embeddings import OpenAIEmbeddings

load_dotenv()
logger = logging.getLogger(__name__)

class DoclingProcessor:
    def __init__(self):
        """
        Initialize S3, Pinecone, Docling converter/chunker, and embeddings.
        """
        self.s3_manager = S3Manager()

        pinecone_api = os.getenv("PINECONE_API_KEY")
        pinecone_env = os.getenv("PINECONE_ENVIRONMENT")
        pinecone_index = os.getenv("PINECONE_INDEX_NAME")

        if not pinecone_api or not pinecone_env or not pinecone_index:
            raise ValueError("Must set PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME in .env")

        pinecone.init(api_key=pinecone_api, environment=pinecone_env)
        self.index = pinecone.Index(pinecone_index)

        self.converter = DocumentConverter()
        self.tokenizer = OpenAITokenizerWrapper(model_name="cl100k_base", max_length=8191)
        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_tokens=8191,
            merge_peers=True
        )
        self.embeddings = OpenAIEmbeddings()  # uses OPENAI_API_KEY

    def process_and_index_document(self, document_id: str, s3_key: str, metadata: Dict) -> Dict:
        """
        1) Download PDF from S3
        2) Convert & chunk with Docling
        3) Embed & upsert to Pinecone
        4) Save mapping file to S3
        """
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                local_pdf = os.path.join(tmpdir, "temp.pdf")
                downloaded = self.s3_manager.download_file(s3_key, local_pdf)
                if not downloaded:
                    raise FileNotFoundError(f"Could not download from S3: {s3_key}")

                result = self.converter.convert(local_pdf)
                if not result.document:
                    raise ValueError("Docling conversion returned empty doc.")

                docling_doc = result.document
                chunks = list(self.chunker.chunk(dl_doc=docling_doc))
                if not chunks:
                    raise ValueError("No chunks from docling chunker.")

                vectors = []
                for i, chunk in enumerate(chunks):
                    text = chunk.text
                    chunk_meta = {
                        "document_id": document_id,
                        "s3_key": s3_key,
                        "title": chunk.meta.headings[0] if chunk.meta.headings else None,
                        "page_numbers": sorted({
                            prov.page_no
                            for item in chunk.meta.doc_items
                            for prov in item.prov
                        }) if chunk.meta.doc_items else None,
                        **metadata
                    }
                    emb = self.embeddings.embed_query(text)
                    vectors.append((
                        f"{document_id}_chunk_{i}",
                        emb,
                        {
                            **chunk_meta,
                            "chunk_text": text  # If you want the chunk text in Pinecone
                        }
                    ))

                # Upsert to pinecone
                self.index.upsert(vectors=vectors)

                # Save doc structure in S3
                structure = {
                    "num_chunks": len(chunks),
                    "metadata": metadata,
                    "chunks": [
                        {
                            "chunk_id": f"{document_id}_chunk_{i}",
                            "title": chunk.meta.headings[0] if chunk.meta.headings else None,
                            "pages": chunk_meta["page_numbers"],
                            "snippet": text[:300]
                        }
                        for i, chunk in enumerate(chunks)
                    ]
                }
                map_key = f"docling_mappings/{document_id}_mapping.json"
                self.s3_manager.s3_client.put_object(
                    Bucket=self.s3_manager.bucket_name,
                    Key=map_key,
                    Body=json.dumps(structure)
                )

                return {"status": "success", "indexed_chunks": len(chunks)}

        except Exception as e:
            logger.exception(f"Error in process_and_index_document: {e}")
            return {"status": "error", "error": str(e)}

    def search_document(self, query: str, document_id: Optional[str] = None, top_k: int = 3) -> List[Dict]:
        """
        Query pinecone to retrieve top chunks. If document_id is provided,
        filter results by that doc ID. Return chunk metadata + snippet from Pinecone.
        """
        emb = self.embeddings.embed_query(query)
        flt = {}
        if document_id:
            flt = {"document_id": document_id}

        results = self.index.query(
            vector=emb,
            filter=flt,
            top_k=top_k,
            include_metadata=True
        )
        out = []
        if results and results.matches:
            for match in results.matches:
                out.append({
                    "score": match.score,
                    "metadata": match.metadata
                })
        return out

    def get_document_structure(self, document_id: str) -> Optional[Dict]:
        """
        Retrieve the doc's structure mapping from S3.
        """
        try:
            map_key = f"docling_mappings/{document_id}_mapping.json"
            obj = self.s3_manager.s3_client.get_object(
                Bucket=self.s3_manager.bucket_name,
                Key=map_key
            )
            return json.loads(obj["Body"].read())
        except Exception as e:
            logger.error(f"Could not retrieve structure for doc {document_id}: {e}")
            return None
