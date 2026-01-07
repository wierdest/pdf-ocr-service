from pydantic import BaseModel, Field
from typing import List, Optional

class OcrOptions(BaseModel):
    language: str = "por"
    deskew: bool = True
    rotate_pages: bool = True
    clean: bool = False
    clean_final: bool = False
    remove_background: bool = False
    threshold: bool = False
    optimize: int = 3
    redo_ocr: bool = False
    skip_text: bool = True  # keeps original text if searchable
    tesseract_config: Optional[str] = None  # e.g. "tessedit_char_whitelist=ABC123"

class EngineResult(BaseModel):
    engine: str            # 'pdfminer', 'pdftotext'
    texto: str

class PageResult(BaseModel):
    pagina: int
    resultados: List[EngineResult]

class ExtractionResult(BaseModel):
    idioma: str
    origem: str          # 'nativo', 'ocr'
    paginas: List[PageResult]

