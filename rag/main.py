import os

from dotenv import load_dotenv

from pipeline import RAGPipeline

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def main():
    pipeline = RAGPipeline(
        data_folder="data",
        chroma_dir="chroma_db",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        gemini_model="gemini-3.1-flash-lite",
        gemini_api_key=GEMINI_API_KEY,
    )

    data, raw = pipeline.run(
        city="Amritsar",
        days=2,
        budget="moderate",
        travelers=2,
        travel_types=[
            "religious",
            "historical",
            "food",
        ],
    )

    print("\n===== STRUCTURED DICT =====\n")
    print(data)

    print("\n===== RAW LLM OUTPUT =====\n")
    print(raw)


if __name__ == "__main__":
    main()