from io import BytesIO
from flask import Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

def export_pdf_data(sim_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Title
    story.append(Paragraph("🔒 Deadlock Simulator Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata
    meta_text = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>" \
                f"<b>Mode:</b> {sim_data.get('mode', 'N/A').capitalize()}<br/>" \
                f"<b>Processes:</b> {sim_data.get('processes', 0)} | " \
                f"<b>Resources:</b> {sim_data.get('resources', 0)}"
    story.append(Paragraph(meta_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Available Resources
    story.append(Paragraph("Initial Available Resources", heading_style))
    available = sim_data.get('available', [])
    avail_data = [['Resource ID', 'Count']]
    for i, val in enumerate(available):
        avail_data.append([f'R{i}', str(val)])
    
    avail_table = Table(avail_data, colWidths=[2*inch, 2*inch])
    avail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(avail_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Allocation Matrix
    story.append(Paragraph("Allocation Matrix", heading_style))
    allocation = sim_data.get('allocation', [])
    alloc_data = [['Process'] + [f'R{i}' for i in range(len(allocation[0]) if allocation else 0)]]
    for i, row in enumerate(allocation):
        alloc_data.append([f'P{i}'] + [str(x) for x in row])
    
    alloc_table = Table(alloc_data)
    alloc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(alloc_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Request/Demand Matrix
    demand = sim_data.get('demand', [])
    if demand:
        story.append(Paragraph("Request/Demand Matrix", heading_style))
        demand_data = [['Process'] + [f'R{i}' for i in range(len(demand[0]) if demand else 0)]]
        for i, row in enumerate(demand):
            demand_data.append([f'P{i}'] + [str(x) for x in row])
        
        demand_table = Table(demand_data)
        demand_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(demand_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Simulation Results
    story.append(Paragraph("Simulation Results", heading_style))
    result = sim_data.get('result', {})
    
    if 'isSafe' in result:
        status = f"<b>Status:</b> {'✓ SAFE' if result['isSafe'] else '✗ UNSAFE'}"
        story.append(Paragraph(status, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        if result['isSafe'] and result.get('safeSequence'):
            seq = " → ".join([f'P{n}' for n in result['safeSequence']])
            story.append(Paragraph(f"<b>Safe Sequence:</b> {seq}", styles['Normal']))
    else:
        status = f"<b>Deadlock Status:</b> {'✗ DEADLOCK DETECTED' if result.get('hasDeadlock') else '✓ No Deadlock'}"
        story.append(Paragraph(status, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        if result.get('hasDeadlock') and result.get('deadlockedProcesses'):
            deadlocked = ", ".join([f'P{x}' for x in result.get('deadlockedProcesses', [])])
            story.append(Paragraph(f"<b>Deadlocked Processes:</b> {deadlocked}", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("<i>Report generated by DeadlockSim</i>", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    pdf_out = buffer.getvalue()
    buffer.close()
    
    return Response(
        pdf_out,
        mimetype="application/pdf",
        headers={"Content-disposition": "attachment; filename=deadlock_report.pdf"}
    )
