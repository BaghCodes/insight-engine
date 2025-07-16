from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os


# Use the class from our document processor script
from document_processor import DocumentProcessor

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the processor and global state variables
doc_processor = DocumentProcessor()
conversation_chain = None
UPLOAD_DIR = doc_processor.upload_dir

# Pydantic model for the question payload
class QuestionRequest(BaseModel):
    question: str

@app.post("/process")
async def process_document(file: UploadFile = File(...)):
    global conversation_chain 
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        # Save the uploaded file to the 'uploads' directory
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Call the correct, generalized text extraction method
        text = doc_processor.extract_text_from_file(file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from the document. The file might be empty or unsupported.")

        # Create vector embeddings from the extracted text
        vector_store = doc_processor.createVectorEmbeddings(text)
        if not vector_store:
            raise HTTPException(status_code=500, detail="Failed to create vector embeddings.")
        
        # Create the conversation chain
        conversation_chain = doc_processor.getConversationChainTwo(vector_store)
        if not conversation_chain:
            raise HTTPException(status_code=500, detail="Failed to create the conversation chain.")

        return {"status": "success", "message": f"Successfully processed {file.filename}."}

    except Exception as e:
        # Catch any other errors and return a server error
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # --- IMPROVEMENT ---
        # Clean up by deleting the uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/ask")
async def ask_question(payload: QuestionRequest):
    global conversation_chain

    if not conversation_chain:
        raise HTTPException(status_code=400, detail="Document not processed yet. Please upload a document first.")

    try:
        # Get the answer from the document processor
        response = doc_processor.handle_userInput(conversation_chain, payload.question)
        if not response or "answer" not in response:
            raise HTTPException(status_code=500, detail="Failed to generate a response.")
        
        # --- IMPROVEMENT ---
        # Return the answer with a consistent key
        return {"answer": response['answer']}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
