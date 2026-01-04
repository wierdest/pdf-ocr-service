from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from extractor import extrair_texto_com_ocr_fallback
from schemas import ExtractionResult, PageResult
import tempfile
import os

MAX_FILE_SIZE_MB = 20

app = FastAPI(
    title="PDF OCR Service",
    version="1.0.0",
    description="Pdf text extraction with OCR fallback",
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/v1/extract", response_class=JSONResponse)
async def extract_text_endpoint(
    file: UploadFile = File(...),
    idioma: str = Query("por", min_length=2, max_length=5),
):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser um PDF",
        )
    
    filename = os.path.basename(file.filename or "input.pdf")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, filename)

        # Copy with size guard
        size = 0
        with open(pdf_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    raise HTTPException(
                        status_code=413,
                        detail="Arquivo maior que o limite permitido",
                    )
                f.write(chunk)

        try:
            origem, resultados_por_pagina = extrair_texto_com_ocr_fallback(
                caminho_pdf=pdf_path,
                idioma=idioma,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Erro interno ao processar o PDF",
            )
        finally:
            await file.close()
    
        paginas = [
            PageResult(
                pagina=pagina,
                resultados=resultados_engine
            )
            for pagina, resultados_engine in resultados_por_pagina.items()
        ]

    return ExtractionResult(
        idioma=idioma,
        origem=origem,
        paginas=paginas,
    )
