import sys
from pathlib import Path

# Add THIS file's folder (rag/) to Python's search path,
# so "from src.loader import ..." can be found no matter how it's launched.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from langchain_huggingface import HuggingFaceEmbeddings

from src.loader import DocumentLoader
from src.vectorizer import Vectorizer
from src.retriever import Retriever
from src.generator import Generator


class RAGPipeline:

    def __init__(
        self,
        data_folder,
        chroma_dir,
        embedding_model,
        gemini_model,
        gemini_api_key,
    ):
        if not gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Check your .env file."
            )

        # 1. Embeddings
        embedding = HuggingFaceEmbeddings(
            model_name=embedding_model
        )

        # 2. Vectorizer
        vectorizer = Vectorizer(
            CHROMA_DIR=chroma_dir,
            embedding=embedding,
        )

        # 3. Build once, load on later runs
        if Path(chroma_dir).exists():
            print("Existing vector DB found -> loading it")
            vector_db = vectorizer.load_vector_store()
        else:
            print("No vector DB found -> building it once")

            loader = DocumentLoader(data_folder)
            documents = loader.load_documents()

            vector_db = vectorizer.build_vector(documents)

        # 4. Retriever + 5. Generator (kept ready in memory)
        base_retriever = vectorizer.create_retriever(
            vector_db,
            k=5,
        )

        self.retriever = Retriever(base_retriever)

        self.generator = Generator(
            model_name=gemini_model,
            api_key=gemini_api_key,
        )

    @staticmethod
    def build_trip_request(
        city,
        days,
        budget,
        travelers,
        travel_types,
    ):
        types = ", ".join(travel_types)

        return (
            f"Destination: {city} | "
            f"Duration: {days} days | "
            f"Budget: {budget} | "
            f"Travelers: {travelers} | "
            f"Travel types: {types}"
        )

    # This runs on EVERY API request
    def run(
        self,
        city,
        days,
        budget,
        travelers,
        travel_types,
    ):
        question = self.build_trip_request(
            city,
            days,
            budget,
            travelers,
            travel_types,
        )

        # Retrieve relevant documents
        rag_context = self.retriever.search_documents(question)

        # Build prompt
        prompt = self.generator.build_prompt(
            question,
            "",
            rag_context,
        )

        # Generate response from LLM
        raw = self.generator.generate(prompt)

        # Parse JSON response
        data = self.generator.parse_output(raw)

        return data, raw