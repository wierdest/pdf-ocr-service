from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

doc = SimpleDocTemplate("exemplo_nota_fiscal_escaneado.pdf", pagesize=A4)
styles = getSampleStyleSheet()

story = []
story.append(Paragraph("<b>NOTA FISCAL ELETRÔNICA - ESCANEADA</b>", styles["Title"]))
story.append(Spacer(1, 12))

story.append(Paragraph("Emitente: Empresa Exemplo LTDA", styles["Normal"]))
story.append(Paragraph("CNPJ: 12.345.678/0001-99", styles["Normal"]))
story.append(Paragraph("Endereço: Rua Exemplo, 123 - São Paulo - SP", styles["Normal"]))
story.append(Spacer(1, 12))

story.append(Paragraph("Produto: Serviço de Teste de Extração de PDF", styles["Normal"]))
story.append(Paragraph("Valor Total: R$ 1.234,56", styles["Normal"]))
story.append(Paragraph("Data de Emissão: 14/12/2025", styles["Normal"]))

doc.build(story)

print("PDF gerado: exemplo_nota_fiscal_escaneado.pdf")
