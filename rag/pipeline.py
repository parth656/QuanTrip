import sys
from pathlib import Path

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


        embedding = HuggingFaceEmbeddings(
            model_name=embedding_model
        )

        vectorizer = Vectorizer(
            CHROMA_DIR=chroma_dir,
            embedding=embedding,
        )

    
        if Path(chroma_dir).exists():
            print("Existing vector DB found -> loading it")
            vector_db = vectorizer.load_vector_store()
        else:
            print("No vector DB found -> building it once")

            loader = DocumentLoader(data_folder)
            documents = loader.load_documents()

            vector_db = vectorizer.build_vector(documents)


        self.vectorizer = vectorizer         
        self.vector_db = vector_db
        self.generator = Generator(model_name=gemini_model, api_key=gemini_api_key)

    

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

    def run(self, city, days, budget, travelers, travel_types):
        city = (city or "").strip().title()
        question = self.build_trip_request(city, days, budget, travelers, travel_types)


        base_retriever = self.vectorizer.create_retriever(
            self.vector_db, city=city, k=5
        )
        retriever = Retriever(base_retriever)

        rag_context = retriever.search_documents(question)   # only this city's places
        prompt = self.generator.build_prompt(question, "", rag_context)
        raw = self.generator.generate(prompt)
        data = self.generator.parse_output(raw)
        return data, raw