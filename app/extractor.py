"""
Camada de extração de texto de PDFs.

Pipeline:
1. pdfminer
2. pdftotext
3. OCRmyPDF
"""

import os
import subprocess
import tempfile

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

from schemas import EngineResult, OcrOptions

def extrair_texto_com_pdftotext(caminho_pdf: str) -> dict[int, str]:
    result = subprocess.run(
        ["pdftotext", "-layout", caminho_pdf, "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    paginas: dict[int, str] = {}
    texto_atual = []
    pagina = 0

    for line in result.stdout.splitlines():
        if "\f" in line:
            paginas[pagina] = "\n".join(texto_atual).strip()
            texto_atual = []
            pagina += 1
        else:
            texto_atual.append(line)

    paginas[pagina] = "\n".join(texto_atual).strip()
    return paginas

def extrair_texto_com_pdfminer(caminho_pdf: str) -> dict[int, str]:
    resultado: dict[int, str] = {}

    for page_number, page_layout in enumerate(extract_pages(caminho_pdf)):
        textos = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                textos.append(element.get_text())

        resultado[page_number] = "".join(textos).strip()

    return resultado

def adicionar_resultado(
    resultados: dict[int, list[EngineResult]],
    pagina: int,
    engine: str,
    texto: str
):
    if not texto.strip():
        return

    lista = resultados.setdefault(pagina, [])

    existente = next(
        (r for r in lista if r.engine == engine),
        None
    )

    if existente is None or len(texto) > len(existente.texto):
        if existente:
            lista.remove(existente)
        lista.append(EngineResult(engine=engine, texto=texto))

def texto_e_suficiente(paginas: dict[int, str], minimo_caracteres: int = 100) -> bool:
    """
    Decide se o texto extraído nativamente é suficiente.
    Heurística simples baseada na quantidade total de caracteres.
    """
    total = sum(len(texto.strip()) for texto in paginas.values())
    return total >= minimo_caracteres

def executar_ocr(
    caminho_pdf_entrada: str,
    caminho_pdf_saida: str,
    options: OcrOptions = OcrOptions()
) -> None:
    """
    Executa OCR usando OCRmyPDF via subprocess.
    """
    comando = ["ocrmypdf"]
    if options.deskew:
        comando.append("--deskew")
    if options.rotate_pages:
        comando.append("--rotate-pages")
    if options.clean:
        comando.append("--clean")
    if options.clean_final:
        comando.append("--clean-final")
    if options.remove_background:
        comando.append("--remove-background")
    if options.threshold:
        comando.append("--threshold")
    if options.redo_ocr:
        comando.append("--redo-ocr")
    if options.skip_text:
        comando.append("--skip-text")
    comando.extend(["--optimize", str(options.optimize)])
    if options.tesseract_config:
        comando.extend(["--tesseract-config", options.tesseract_config])
    comando.extend([
        "-l", options.language,
        caminho_pdf_entrada,
        caminho_pdf_saida,
    ])

    try:
        subprocess.run(
            comando,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print("OCRmyPDF falhou")
        print("STDOUT:")
        print(e.stdout)
        print("STDERR:")
        print(e.stderr)
        raise

def extrair_texto_com_ocr_fallback(
    caminho_pdf: str,
    options: OcrOptions = OcrOptions()
) -> tuple[str, dict[int, list[EngineResult]]]:
    """
    Pipeline:
    1. pdfminer
    2. pdftotext
    3. OCR + ambos novamente
    """

    resultados_por_pagina: dict[int, list[EngineResult]] = {}

    # 1. pdfminer (sempre)
    pdfminer_texto = extrair_texto_com_pdfminer(caminho_pdf)
    for pagina, texto in pdfminer_texto.items():
        adicionar_resultado(resultados_por_pagina, pagina, "pdfminer", texto)

    # 2. pdftotext (também sempre no caminho nativo)
    try:
        pdftotext_texto = extrair_texto_com_pdftotext(caminho_pdf)
        for pagina, texto in pdftotext_texto.items():
            adicionar_resultado(resultados_por_pagina, pagina, "pdftotext", texto)
    except Exception:
        pdftotext_texto = {}

    # Decide se OCR é necessário
    if (
        texto_e_suficiente(pdfminer_texto)
        or texto_e_suficiente(pdftotext_texto)
    ):
        return "nativo", resultados_por_pagina

    # 3. OCR
    with tempfile.TemporaryDirectory() as tmpdir:
        caminho_pdf_ocr = os.path.join(tmpdir, "ocr.pdf")

        executar_ocr(
            caminho_pdf_entrada=caminho_pdf,
            caminho_pdf_saida=caminho_pdf_ocr,
            options=options
        )

        # Após OCR, roda ambos novamente
        for engine, extractor in [
            ("pdfminer", extrair_texto_com_pdfminer),
            ("pdftotext", extrair_texto_com_pdftotext),
        ]:
            try:
                texto = extractor(caminho_pdf_ocr)
                for pagina, conteudo in texto.items():
                    adicionar_resultado(resultados_por_pagina, pagina, engine, conteudo)
            except Exception:
                continue

    return "ocr", resultados_por_pagina
