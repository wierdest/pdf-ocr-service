import sys
import json
from extractor import extrair_texto_com_ocr_fallback
from schemas import OcrOptions


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python entrypoint.py <arquivo.pdf> [idioma]")
        sys.exit(1)

    caminho_pdf = sys.argv[1]
    idioma = sys.argv[2] if len(sys.argv) > 2 else "por"

    resultado = extrair_texto_com_ocr_fallback(
        caminho_pdf=caminho_pdf,
        options=OcrOptions(language=idioma)
    )

    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
