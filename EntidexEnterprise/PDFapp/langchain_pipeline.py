import os
import getpass
from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.graph import START, StateGraph
from langchain_chroma import Chroma
from langchain import hub
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing_extensions import TypedDict, List
from dotenv import load_dotenv
from langchain_core.runnables import Runnable

load_dotenv()  # Esto carga automáticamente las variables del archivo .env

# Las claves ya están disponibles en os.environ
langsmith_key = os.environ.get("LANGSMITH_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY")

if not langsmith_key or not google_key:
    raise RuntimeError("❌ Faltan claves de API en variables de entorno.")
# =====================
# Establecer claves en variables de entorno (sólo una vez)
# if not os.environ.get("LANGSMITH_API_KEY"):
#     os.environ["LANGSMITH_API_KEY"] = getpass.getpass(
#         "INGRESA LA API KEY DE LANGSMITH: "
#     )

# if not os.environ.get("GOOGLE_API_KEY"):
#     os.environ["GOOGLE_API_KEY"] = getpass.getpass(
#         "INGRESA LA API KEY DE GOOGLE GEMINI: "
#     )

# =====================
# Inicializar el modelo LLM (Google Gemini)
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

# =====================
# Inicializar embeddings livianos
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# =====================
# Inicializar vector store Chroma
# Recargar vector store desde persistencia justo antes de retrieve
global vector_store
vector_store = Chroma(
    collection_name="example_collectionV2",
    embedding_function=HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ),
    persist_directory="./chroma_langchain_db",
)

# =====================
# Definir prompt desde LangChain Hub
prompt = hub.pull("rlm/rag-prompt")


# =====================
# TypedDict para el estado
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


# =====================
# Funciones para retrieve y generate


def retrieve(state: State) -> dict:
    print(f"🔍 Buscando contexto para la pregunta: {state['question']}")
    retrieved_docs = vector_store.similarity_search(state["question"])
    print(f"✅ Documentos recuperados: {len(retrieved_docs)}")
    return {"context": retrieved_docs}


def generate(state: State) -> dict:
    print("🧠 Generando respuesta...")
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    # Añadimos instrucción en la pregunta para respuesta en español
    question_es = state["question"] + "\nPor favor responde en español."
    messages = prompt.invoke({"question": question_es, "context": docs_content})
    response = llm.invoke(messages)
    print("✅ Respuesta generada.")
    return {"answer": response.content}


# =====================
# Construcción del grafo de estados
graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()


def construir_graph_con(vector_store: Chroma) -> Runnable:
    def retrieve(state: State) -> dict:
        print(f"🔍 Buscando contexto para la pregunta: {state['question']}")
        retrieved_docs = vector_store.similarity_search(state["question"])
        print(f"✅ Documentos recuperados: {len(retrieved_docs)}")
        return {"context": retrieved_docs}

    def generate(state: State) -> dict:
        print("🧠 Generando respuesta...")
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        question_es = state["question"] + "\nPor favor responde en español."
        messages = prompt.invoke({"question": question_es, "context": docs_content})
        response = llm.invoke(messages)
        print("✅ Respuesta generada.")
        return {"answer": response.content}

    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    return graph_builder.compile()

