# PDF OCR Service

Serviço de extração de texto de PDFs com fallback automático para OCR, exposto via FastAPI e pronto para rodar localmente ou em contêiner. O pipeline combina extração nativa (`pdfminer.six` e `pdftotext`) e aplica OCR (`ocrmypdf`/Tesseract) apenas quando o conteúdo textual não é suficiente.

## Tecnologias
- Python 3.11
- FastAPI + Uvicorn
- pdfminer.six e `pdftotext` (Poppler)
- OCRmyPDF + Tesseract (inclui idioma português `tesseract-ocr-por`)
- Docker (imagem multi-stage em `Dockerfile`)

## Como funciona
- Extratores nativos (`pdfminer` e `pdftotext`) rodam sempre.
- Uma heurística simples verifica se o texto extraído possui caracteres suficientes; se não, um OCR é executado e os extratores são reaplicados sobre o PDF processado.
- Cada página pode conter múltiplos resultados, um por engine, sempre mantendo o texto mais longo encontrado para aquela combinação de página + engine.

## Requisitos de sistema
- Dependências nativas para OCR: Ghostscript, QPDF, Poppler (`pdftotext`), Tesseract + dados de idioma (`tesseract-ocr-por` por padrão).
- Verifique se o binário `pdftotext` e `ocrmypdf` estão disponíveis no `PATH` quando executar fora do Docker.

## Configuração
### Rodar com Docker
```bash
docker build -t pdf-ocr-service .
docker run --rm -p 8000:8000 pdf-ocr-service
```

### Rodar localmente
1) Crie um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate
```
2) Instale bibliotecas Python:
```bash
pip install -r requirements.txt
```
3) Certifique-se de que as dependências nativas (Ghostscript, QPDF, Poppler, Tesseract + idioma) estão instaladas.
4) Inicie a API:
```bash
uvicorn app.api:app --reload --port 8000
```

## API HTTP
- **Base URL:** `http://localhost:8000`
- **Tamanho máximo:** 20 MB por arquivo.
- **Formato:** multipart/form-data com um campo `file` (PDF).

### `GET /health`
- Retorna status simples para checar disponibilidade.
- Resposta: `{"status": "ok"}`

### `POST /v1/extract`
- Faz upload de um PDF e retorna o texto por página e engine.
- Corpo multipart:
  - `file`: PDF (`content-type: application/pdf`).
  - `options` (JSON como string): opções de OCR para o `ocrmypdf` (veja abaixo).
    - Exemplo: `-F 'options={"language":"por",...}'`
- Respostas comuns:
  - `200 OK`: corpo `ExtractionResult`.
  - `400 Bad Request`: arquivo não é PDF.
  - `413 Payload Too Large`: PDF excede 20 MB.
  - `422 Unprocessable Entity`: falha controlada do OCR.
  - `500 Internal Server Error`: erro inesperado.
- Exemplo de requisição:
```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@/caminho/para/documento.pdf" \
  -F 'options={"language":"por","deskew":true,"rotate_pages":true,"clean":false,"clean_final":false,"remove_background":false,"threshold":false,"optimize":3,"redo_ocr":false,"skip_text":true,"tesseract_config":null}' \
  -H "Accept: application/json"
```

#### Opções de OCR (`OcrOptions`)
- `language` (string, padrão `por`): idioma do Tesseract.
- `deskew` (bool): corrige inclinação.
- `rotate_pages` (bool): tenta rotacionar páginas.
- `clean` (bool): limpeza básica.
- `clean_final` (bool): limpeza final após OCR.
- `remove_background` (bool): remove fundo.
- `threshold` (bool): binarização.
- `optimize` (int 0-3): nível de otimização do OCRmyPDF.
- `redo_ocr` (bool): força OCR mesmo se já houver texto.
- `skip_text` (bool): mantém texto existente.
- `tesseract_config` (string|null): configurações avançadas do Tesseract.

#### Schemas de resposta
- `EngineResult`
  - `engine` (string): `pdfminer` ou `pdftotext`.
  - `texto` (string): conteúdo extraído para aquele engine.
- `PageResult`
  - `pagina` (int): índice zero-based da página.
  - `resultados` (array[`EngineResult`]): lista de resultados por engine para a página.
- `ExtractionResult`
  - `idioma` (string): idioma usado para OCR.
  - `origem` (string): `nativo` (sem OCR) ou `ocr`.
  - `paginas` (array[`PageResult`]): resultados por página.

Exemplo de resposta:
```json
{
  "idioma": "por",
  "origem": "ocr",
  "paginas": [
    {
      "pagina": 0,
      "resultados": [
        {
          "engine": "pdfminer",
          "texto": "Conteúdo extraído..."
        },
        {
          "engine": "pdftotext",
          "texto": "Conteúdo extraído..."
        }
      ]
    }
  ]
}
```

## Linha de comando
Para processar um PDF localmente sem subir a API:
```bash
python app/entrypoint.py caminho/arquivo.pdf [idioma]
```
Imprime o resultado JSON no stdout.
O parâmetro opcional `idioma` alimenta `options.language` internamente.

## Estrutura do projeto
- `app/api.py`: definições de rotas FastAPI.
- `app/extractor.py`: pipeline de extração e OCR.
- `app/schemas.py`: modelos Pydantic usados na API.
- `app/entrypoint.py`: utilitário CLI.
- `Dockerfile`: build multi-stage com dependências nativas de OCR.

## Testes rápidos
- `GET /health` deve retornar status `ok`.
- Submeta um PDF pesquisável e verifique `origem: "nativo"`.
- Submeta um PDF imagem/escaneado e verifique `origem: "ocr"` e presença de texto nas páginas.
