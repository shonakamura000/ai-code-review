from pathlib import Path
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
import os


# パスの定義
PROJECT_ROOT = Path(__file__).resolve().parent.parent
print(f"PROJECT_ROOT:{PROJECT_ROOT}")
GUIDELINES_PATH = PROJECT_ROOT / "doc/code-guidelines.md"
INDEX_PATH = PROJECT_ROOT / "indexes"

def build_index():
    # コード規約を読み込む
    documents = SimpleDirectoryReader(input_files=[str(GUIDELINES_PATH)]).load_data()
    
    # インデックスの初期化
    index = VectorStoreIndex.from_documents(documents)
    
    # インデックスをディスクに保存
    index.storage_context.persist(persist_dir=str(INDEX_PATH))
    print(f"インデックスを保存しました: {INDEX_PATH}")



if __name__ == "__main__":
    build_index()
