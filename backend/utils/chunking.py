from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.default_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def split_text(self, text: str) -> List[str]:
        """Splits text into chunks using recursive character splitting."""
        return self.default_splitter.split_text(text)

    def split_code(self, code: str, language: str) -> List[str]:
        """Specialized splitting for code files."""
        # Note: LangChain has specific splitters for many languages
        try:
            from langchain_text_splitters import Language
            lang_map = {
                "py": Language.PYTHON,
                "js": Language.JS,
                "ts": Language.TS,
                "go": Language.GO,
                "java": Language.JAVA,
            }
            if language in lang_map:
                parser = RecursiveCharacterTextSplitter.from_language(
                    language=lang_map[language],
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
                return parser.split_text(code)
        except ImportError:
            pass
        return self.split_text(code)
