import os
import subprocess
import tempfile
import fitz # PyMuPDF

def extrair_texto_nativo(caminho_pdf: str) -> dict[int, str]:
    """
    Extrai texto nativo de um PDF digital usando PyMuPDF.
    Retorna um dicionário: {numero_da_pagina: texto}
    """
    resultado: dict[int, str] = {}

    with fitz.Document(caminho_pdf) as documento:
        for i in range(documento.page_count):
            pagina = documento.load_page(i)
            texto = pagina.get_text()
            resultado[i] = texto or ""

    return resultado

def texto_nativo_e_suficiente(paginas: dict[int, str], minimo_caracteres: int = 100) -> bool:
    """
    Decide se o texto extraído nativamente é suficiente.
    Heurística simples baseada na quantidade total de caracteres.
    """
    total = sum(len(texto.strip()) for texto in paginas.values())
    return total >= minimo_caracteres

def executar_ocr(
    caminho_pdf_entrada: str,
    caminho_pdf_saida: str,
    idioma: str = "por"
) -> None:
    """
    Executa OCR usando OCRmyPDF via subprocess.
    """
    comando = [
         "ocrmypdf",
        "--skip-text",
        "--optimize", "3",
        "-l", idioma,
        caminho_pdf_entrada,
        caminho_pdf_saida,
    ]

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



def extrair_texto_com_fallback(
    caminho_pdf: str,
    idioma: str = "por"
) -> dict[int, str]:
    """
    Tenta extrair texto nativo.
    Se o texto for insuficiente, aplica OCR e extrai novamente.
    """
    # 1. Tentativa nativa
    texto_nativo = extrair_texto_nativo(caminho_pdf)

    if texto_nativo_e_suficiente(texto_nativo):
        return texto_nativo

    # 2. OCR como fallback
    with tempfile.TemporaryDirectory() as tmpdir:
        caminho_pdf_ocr = os.path.join(tmpdir, "ocr.pdf")

        executar_ocr(
            caminho_pdf_entrada=caminho_pdf,
            caminho_pdf_saida=caminho_pdf_ocr,
            idioma=idioma,
        )

        return extrair_texto_nativo(caminho_pdf_ocr)