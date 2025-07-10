import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List

# --- Configuration ---

# This path points to the directory where the FAISS index will be stored.
VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'vector_store_data')
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
# --- Private Helper Functions ---

def _get_embedding_function():
    return HuggingFaceEmbeddings(
            model_name = EMBEDDING_MODEL_NAME,
            model_kwargs={"device":"cpu"}
            )

# --- Public API ---

def create_or_update_store(text_content: str):
    """
    Takes a block of text, chunkes it, creats embeddings and then creates/updates FAISS vector index.
    text_content is the cleaned text extracted from a document.
    """
    if not text_content or not text_content.strip():
        print(f"Warning: Empty text content recieved.")
        return {
            "success":False,
            "reason":"Empty text content",
            "chunks_added":0
        }

    print(f"Chunking document text.....")
    text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len,
            )
    text_chunks = text_splitter.split_text(text_content)

    if not text_chunks:
        print("Warning: Could not create any chunks from the document")
        return {
            "success": False,
            "reason": "Text splitting failed",
            "chunks_added": 0
        }

    print(f"Generating embeddings for {len(text_chunks)} chunks using '{EMBEDDING_MODEL_NAME}'...")
    embedding_function = _get_embedding_function()

    new_vector_store = FAISS.from_texts(
        texts=text_chunks,
        embedding=embedding_function
    )

    print("Saving and merging the index.....")
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    index_fp = os.path.join(VECTOR_STORE_PATH, 'index.faiss')
    meta_fp = os.path.join(VECTOR_STORE_PATH, 'index.pkl')

    if os.path.exists(index_fp) and os.path.exists(meta_fp):
        try:
            print("   - Existing index found. Merging new data...")
            og_vector_store = FAISS.load_local(
                folder_path=VECTOR_STORE_PATH,
                embeddings=embedding_function,
                allow_dangerous_deserialization=True
                )
            og_vector_store.merge_from(new_vector_store)
            og_vector_store.save_local(VECTOR_STORE_PATH)
            print("Successfully merged and saved the updated index.")
        except Exception as e:
            return {
                "success": False,
                "reason": f"Merge failed: {str(e)}",
                "chunks_added": len(text_chunks)
            }
    else:
        if os.path.exists(index_fp) and not os.path.exists(meta_fp):
            print("Warning: FAISS index file exists but metadata (.pkl) is missing.")
        print("No existing index found. Creating a new one...")
        new_vector_store.save_local(VECTOR_STORE_PATH)
        print("Successfully saved the new index.")
    return {
    "success": True,
    "chunks_added": len(text_chunks),
    "index_path": os.path.abspath(index_fp)
    }

def get_retriever(search_k_value: int = 4):
    """
     This is the core vector search function. It loads the persisted FAISS
    index and returns it as a LangChain retriever object.

    Args:
        search_k_value: The number of top relevant documents to retrieve.

    Returns:
        A LangChain retriever object ready for searching, or None if the
        index does not exist.
    """
    index_fp= os.path.join(VECTOR_STORE_PATH, 'index.faiss')
    if not os.path.exists(index_fp):
        print("Error: FAISS index not found. Please process documents first.")
        return None
    
    try:
        embedding_function = _get_embedding_function()
        vector_store = FAISS.load_local(
            folder_path=VECTOR_STORE_PATH,
            embeddings=embedding_function,
            allow_dangerous_deserialization=True
        )
        # The 'as_retriever' method prepares the vector store to perform similarity searches based on user queries.
        return vector_store.as_retriever(search_kwargs={"k": search_k_value})
    except Exception as e:
        print(f"Error: Failed to load FAISS index. Reason: {e}")
        return None
        
