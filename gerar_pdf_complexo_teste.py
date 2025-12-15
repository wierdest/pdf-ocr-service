from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.graphics.barcode import code128

doc = SimpleDocTemplate(
    "exemplo_nota_fiscal_complexa_escaneado.pdf",
    pagesize=A4
)

styles = getSampleStyleSheet()
story = []

# Título
story.append(Paragraph("<b>NOTA FISCAL ELETRÔNICA - ESCANEADO</b>", styles["Title"]))
story.append(Spacer(1, 12))

# Logo fictício (quadrado cinza)
story.append(Paragraph("<i>[LOGO DA EMPRESA]</i>", styles["Normal"]))
story.append(Spacer(1, 12))

# Dados do emitente
story.append(Paragraph("Emitente: Empresa Exemplo LTDA", styles["Normal"]))
story.append(Paragraph("CNPJ: 12.345.678/0001-99", styles["Normal"]))
story.append(Paragraph("Endereço: Rua Exemplo, 123 - São Paulo - SP", styles["Normal"]))
story.append(Spacer(1, 12))

# Tabela de produtos
tabela_dados = [
    ["Produto", "Qtd", "Valor Unitário", "Total"],
    ["Serviço A", "1", "R$ 500,00", "R$ 500,00"],
    ["Serviço B", "2", "R$ 200,00", "R$ 400,00"],
    ["Serviço C", "1", "R$ 334,56", "R$ 334,56"],
]

tabela = Table(tabela_dados, colWidths=[200, 50, 100, 100])
tabela.setStyle(TableStyle([
    ("GRID", (0,0), (-1,-1), 1, colors.black),
    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
    ("ALIGN", (1,1), (-1,-1), "RIGHT"),
]))

story.append(tabela)
story.append(Spacer(1, 20))

# Valor total
story.append(Paragraph("<b>Valor Total: R$ 1.234,56</b>", styles["Normal"]))
story.append(Paragraph("Data de Emissão: 14/12/2025", styles["Normal"]))
story.append(Spacer(1, 20))

# Código de barras
barcode = code128.Code128("12345678901234567890", barHeight=40)
story.append(barcode)

doc.build(story)

print("PDF gerado: exemplo_nota_fiscal_complexa.pdf")
