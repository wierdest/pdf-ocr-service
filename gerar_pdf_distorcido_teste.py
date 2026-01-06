"""
Gera um PDF "escaneado" com imagens distorcidas para exercitar o OCR.
- Gera PNGs com texto renderizado em múltiplas fontes/tamanhos.
- Aplica ruído, distorção leve, blur e rotação para simular digitalização ruim.
- Converte as imagens em páginas de um PDF via reportlab (texto vira raster).

Dependências recomendadas para rodar este script:
    pip install pillow reportlab numpy
"""

import math
import random
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

try:  # Pillow >= 10
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC  # type: ignore[attr-defined]
except AttributeError:  # Pillow < 10 fallback
    RESAMPLE_BICUBIC = Image.BICUBIC  # type: ignore[attr-defined]
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image as RLImage
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def _load_fonts() -> list[ImageFont.FreeTypeFont]:
    """Carrega um conjunto pequeno de fontes TrueType se disponíveis; cai no default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    fonts = []
    for path in font_paths:
        if Path(path).exists():
            for size in (18, 22, 28, 32):
                fonts.append(ImageFont.truetype(path, size=size))
    if not fonts:
        fonts.append(ImageFont.load_default())
    return fonts


def _add_noise(img: Image.Image, speckle_pct: float = 0.01) -> None:
    """Adiciona ruído aleatório (pontinhos pretos/cinza)."""
    width, height = img.size
    num_pixels = int(width * height * speckle_pct)
    draw = ImageDraw.Draw(img)
    for _ in range(num_pixels):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        shade = random.randint(0, 80)
        draw.point((x, y), fill=(shade, shade, shade))


def _add_scan_lines(img: Image.Image, lines: int = 8) -> None:
    """Desenha linhas horizontais suaves simulando passagem do scanner."""
    draw = ImageDraw.Draw(img)
    width, height = img.size
    for _ in range(lines):
        y = random.randint(0, height - 1)
        alpha = random.randint(8, 24)
        color = (alpha, alpha, alpha)
        draw.line([(0, y), (width, y)], fill=color, width=random.randint(1, 2))


def _render_text_image(text_lines: list[str], seed: int) -> Image.Image:
    random.seed(seed)
    fonts = _load_fonts()
    width, height = 1800, 2400
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    y = 120
    for line in text_lines:
        font = random.choice(fonts)
        angle = random.uniform(-2.5, 2.5)
        jitter_x = random.randint(-8, 8)
        jitter_y = random.randint(-4, 6)

        # Renderiza linha numa máscara para rotacionar separadamente.
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_w = int(text_bbox[2] - text_bbox[0])
        text_h = int(text_bbox[3] - text_bbox[1])
        text_img = Image.new("L", (text_w + 20, text_h + 10), color=255)
        text_draw = ImageDraw.Draw(text_img)
        text_draw.text((10, 5), line, font=font, fill=0)
        text_img = text_img.rotate(angle, resample=RESAMPLE_BICUBIC, expand=1, fillcolor=255)

        img.paste(ImageOps.colorize(text_img, black="black", white="white"), (100 + jitter_x, y + jitter_y))
        y += text_img.size[1] + random.randint(22, 38)

    _add_noise(img, speckle_pct=0.0035)
    _add_scan_lines(img, lines=random.randint(5, 12))

    # Pequena distorção radial simulando vidro do scanner.
    arr = np.array(img)
    center_x, center_y = arr.shape[1] / 2, arr.shape[0] / 2
    dist_coeff = 1e-7
    coords_y, coords_x = np.indices((arr.shape[0], arr.shape[1]))
    x = coords_x - center_x
    y_ = coords_y - center_y
    r2 = x * x + y_ * y_
    factor = 1 + dist_coeff * r2
    map_x = (x * factor + center_x).astype(np.float32)
    map_y = (y_ * factor + center_y).astype(np.float32)
    map_x = np.clip(map_x, 0, arr.shape[1] - 1).astype(np.int32)
    map_y = np.clip(map_y, 0, arr.shape[0] - 1).astype(np.int32)
    distorted = arr[map_y, map_x]
    img = Image.fromarray(distorted)

    # Blur leve e ajuste de contraste.
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    return img


def gerar_pdf_distorcido(destino: Path | str = "exemplo_nota_fiscal_distorcido.pdf") -> Path:
    text_lines = [
        "NOTA FISCAL ELETRÔNICA - VIA CONSUMIDOR",
        "Emitente: Empresa Exemplo LTDA",
        "CNPJ: 12.345.678/0001-99",
        "Endereço: Rua Exemplo, 123 - São Paulo - SP",
        "Itens:",
        "  1x Serviço A .................... R$ 500,00",
        "  2x Serviço B .................... R$ 400,00",
        "  1x Serviço C .................... R$ 334,56",
        "Valor Total: R$ 1.234,56",
        "Data de Emissão: 14/12/2025",
        "Autorização: 20251214-XYZ-ABCD-9999",
        "Observações: Documento gerado para testes de OCR.",
    ]

    destino = Path(destino)
    styles = getSampleStyleSheet()

    with tempfile.TemporaryDirectory() as tmpdir:
        doc = SimpleDocTemplate(str(destino), pagesize=A4)
        max_width = doc.width
        max_height = doc.height * 0.85

        image_paths = []
        page_seed = 426 # testar essa seed
        img = _render_text_image(text_lines, seed=page_seed)
        img_path = Path(tmpdir) / f"pagina_{page_seed}.png"
        img.save(img_path, format="PNG", compress_level=9)
        image_paths.append(img_path)

        story = []
        for img_path in image_paths:
            with Image.open(img_path) as pil_img:
                w, h = pil_img.size
            scale = min(max_width / w, max_height / h)
            story.append(RLImage(str(img_path), width=w * scale, height=h * scale))
            story.append(Spacer(1, 20))

        doc.build(story)

    print(f"PDF gerado com distorções: {destino}")
    return destino


if __name__ == "__main__":
    gerar_pdf_distorcido()
