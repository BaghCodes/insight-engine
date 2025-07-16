    from email.mime import text
    import os
    import fitz  # PyMuPDF for PDFs
    import docx  # For .docx files
    import pandas as pd  # For .xlsx files
    import warnings
    import hashlib
    from tqdm import tqdm
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_ollama.llms import OllamaLLM
    from langchain_ollama import OllamaEmbeddings

    warnings.filterwarnings("ignore")

    class DocumentProcessor:
        """
        A class to process various document types (PDF, DOCX, XLSX),
        extract text, create vector embeddings, and handle Q&A.
        """
        def __init__(self):   
            # MODIFIED: Using relative paths for directories
            # These folders will be created inside the 'backend' directory
            # when the application starts.
            self.upload_dir = "uploads"
            self.vector_dir = "vectorstore"
            os.makedirs(self.upload_dir, exist_ok=True)
            os.makedirs(self.vector_dir, exist_ok=True)

            model_name = "llama3:8b"

            self.embeddings = OllamaEmbeddings(model=model_name)
            self.llm = OllamaLLM(model=model_name)

        def _extract_text_from_pdf(self, file_path: str) -> str:
            """Extracts text content from a PDF file."""
            text = ""
            try:
                with fitz.open(file_path) as doc:
                    for page in doc:
                        text += page.get_text()
                return text
            except Exception as e:
                print(f'Error opening or processing PDF file: {e}')
                return ""

        def _extract_text_from_docx(self, file_path: str) -> str:
            """Extracts text content from a DOCX file."""
            text = ""
            try:
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text
            except Exception as e:
                print(f'Error opening or processing DOCX file: {e}')
                return ""

        def _extract_text_from_excel(self, file_path: str) -> str:
            """Extracts text content from an Excel (XLSX) file."""
            text = ""
            try:
                xls = pd.ExcelFile(file_path)
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                    text += f"--- Sheet: {sheet_name} ---\n"
                    text += df.to_string(index=False) + "\n\n"
                return text
            except Exception as e:
                print(f'Error opening or processing Excel file: {e}')
                return ""

        def extract_text_from_file(self, file_path: str) -> str:
            """
            Extracts text from a file by detecting its extension.
            """
            _, file_extension = os.path.splitext(file_path)
            
            if file_extension.lower() == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_extension.lower() == '.docx':
                return self._extract_text_from_docx(file_path)
            elif file_extension.lower() == '.xlsx':
                return self._extract_text_from_excel(file_path)
            else:
                print(f"Unsupported file type: {file_extension}")
                return ""
        
        def _get_vectorstore_path(self, text: str) -> str:
                file_hash = hashlib.sha256(text.encode()).hexdigest()
                return os.path.join(self.vector_dir, file_hash)

        def createVectorEmbeddings(self, text: str):
            try:
                # Hash the tex  t to determine if embeddings already exist
                path = self._get_vectorstore_path(text)

                # If vectorstore already exists, load and return
                if os.path.exists(os.path.join(path, "index.faiss")):
                    print("🔁 Reusing existing vector store.")
                    return FAISS.load_local(folder_path=path, embeddings=self.embeddings)

                print("🆕 Creating new vector store.")
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                chunks = text_splitter.split_text(text=text)
                chunks = [chunk for chunk in chunks if chunk.strip()]
                if not chunks:
                    print("No chunks created from input text.")
                    return None

                embeddings = self.embeddings
                vectorStore = FAISS.from_texts([chunks[0]], embedding=embeddings)
                for chunk in tqdm(chunks[1:], desc="Embedding Chunks", unit="chunk"):
                    new_store = FAISS.from_texts([chunk], embedding=embeddings)
                    vectorStore.merge_from(new_store)
                vectorStore.save_local(path)  
                return vectorStore
            except Exception as e:
                print(f"Error creating vector store: {e}")
                return None

            
        def getConversationChainTwo(self,vectorStore):
            """Creates a conversational chain for Q&A."""
            try:
                retriever = vectorStore.as_retriever(search_kwargs={"k": 3})
                llm = self.llm
                system_prompt = (
                "Use the given context to answer the question. "
                "If you don't know the answer, say you don't know. "
                "Use three sentence maximum and keep the answer concise. "
                "Context: {context}"
                )
                prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("human", "{input}"),
                ]
                )
                question_answer_chain = create_stuff_documents_chain(llm, prompt)
                chain = create_retrieval_chain(retriever,question_answer_chain)
                return chain
            except Exception as e:
                print(f"Error Creating the chain: {e}")
                return None

        def handle_userInput(self,conversatioChain,question):
            """Processes a user's question and returns an answer."""
            try:
                qa_chain = conversatioChain
                result = qa_chain.invoke({"input":question})
                return {
                    "answer": result["answer"]
                }
            except Exception as e:
                print(f'Error answering the question:{e}')
                return {"answer":f'Error Processing your question:{str(e)}'}
