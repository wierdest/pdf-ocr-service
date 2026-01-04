from pydantic import BaseModel
from typing import List

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

