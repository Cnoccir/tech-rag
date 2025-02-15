# app/chat/chat_manager.py
from typing import List, Dict, Optional
from langchain_community.chat_models import ChatOpenAI  # Updated import
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import logging

from app.document.docling_processor import DoclingProcessor

logger = logging.getLogger("app")

class ChatManager:
    def __init__(self):
        """Initialize chat manager with document processor and language model."""
        self.document_processor = DoclingProcessor()
        self.llm = ChatOpenAI(temperature=0.7)
        self.system_prompt = """You are a helpful technical assistant with access to various technical documents.
        When answering questions:
        1. Always cite your sources with page numbers, section titles, and relevant quotes
        2. If you're referencing multiple documents, clearly indicate which document you're citing
        3. If you're not sure about something, say so rather than making assumptions
        4. If the context contains technical information, explain it clearly and accurately
        5. When discussing code or technical concepts, provide practical examples if relevant"""

    def generate_response(
        self,
        query: str,
        document_ids: List[str],
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """Generate a response using RAG with Docling's advanced document understanding."""
        try:
            logger.debug(f"Generating response for query: {query}")

            # Search across all documents
            all_results = []
            for doc_id in document_ids:
                results = self.document_processor.search_document(query, doc_id)
                all_results.extend(results)

            # Sort results by score
            all_results.sort(key=lambda x: x["metadata"]["score"], reverse=True)
            logger.debug(f"Found {len(all_results)} relevant chunks")

            # Build context with structured information
            contexts = []
            for result in all_results:
                metadata = result["metadata"]
                context_entry = f"\nSection: {metadata.get('title', 'Untitled')}"
                if metadata.get('page_numbers'):
                    context_entry += f"\nPage(s): {', '.join(map(str, metadata['page_numbers']))}"
                context_entry += f"\nContent: {result['text']}"
                contexts.append(context_entry)

            context = "\n\n".join(contexts)

            # Build conversation history
            messages = [SystemMessage(content=self.system_prompt)]

            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))

            # Add current query with context
            current_prompt = f"""Context from documents:
            {context}

            User question: {query}

            Please provide a response based on the context above. Include specific citations with section titles and page numbers where available."""

            messages.append(HumanMessage(content=current_prompt))

            # Generate response
            logger.debug("Generating LLM response")
            response = self.llm.generate([messages])
            ai_message = response.generations[0][0].text

            # Extract citations and structure them
            citations = []
            for result in all_results:
                if result["text"].lower() in ai_message.lower():
                    citations.append({
                        "section": result["metadata"].get("title", "Untitled"),
                        "page_numbers": result["metadata"].get("page_numbers", []),
                        "text": result["text"][:200] + "..."  # Truncate long citations
                    })

            logger.info(f"Generated response with {len(citations)} citations")
            return {
                "response": ai_message,
                "citations": citations
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            raise

    def get_document_structure(self, document_id: str) -> Optional[Dict]:
        """Get the hierarchical structure of a document."""
        try:
            return self.document_processor.get_document_structure(document_id)
        except Exception as e:
            logger.error(f"Error getting document structure: {str(e)}", exc_info=True)
            return None
