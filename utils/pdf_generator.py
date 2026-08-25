from fpdf import FPDF
from database import SessionLocal
from models.material import Material
from models.requirement import Requirement
from models.warehouse import Warehouse
import os


def generate_dispatch_pdf(dispatch):
    db = SessionLocal()

    pdf = FPDF()
    pdf.add_page()

    # TITULO
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "GUIA DE REMISION", ln=True, align="C")

    pdf.ln(10)

    # DATOS
    pdf.set_font("Arial", "", 12)

    pdf.cell(100, 10, f"Guia: {dispatch.guia_number}", ln=True)

    pdf.cell(
        100,
        10,
        f"Fecha: {dispatch.dispatch_date.strftime('%Y-%m-%d %H:%M')}",
        ln=True
    )

    pdf.cell(
        100,
        10,
        f"Requerimiento ID: {dispatch.requirement_id}",
        ln=True
    )
     # Obtener requerimiento
    requirement = db.query(Requirement).filter(
        Requirement.id == dispatch.requirement_id
    ).first()
     # Almacén destino
    destination_name = "Desconocido"
    destination_location = "Desconocida"
        
    if requirement:
            
            destination_warehouse = db.query(Warehouse).filter(
                 Warehouse.id == requirement.warehouse_id_obra
            ).first()
            
            if destination_warehouse:
                destination_name = destination_warehouse.name
                destination_location = destination_warehouse.location
                
     # Almacén origen
    origin_name = "Principal"
    pdf.cell(
            100,
            10,
            f"Almacén origen: {origin_name}",
            ln=True
        )
    
    pdf.cell(
            100,
            10,
            f"Almacén destino: {destination_name}",
            ln=True
    )
    pdf.cell(
         100,
         10,
         f"Descripcion destino: {destination_location}",
         ln=True
        )
    

    pdf.ln(10)

    # TABLA
    pdf.set_font("Arial", "B", 12)

    pdf.cell(100, 10, "Material", border=1)
    pdf.cell(40, 10, "Cantidad", border=1)

    pdf.ln()

    pdf.set_font("Arial", "", 12)

    for item in dispatch.items:

        material = db.query(Material).filter(
             Material.id == item.material_id
            ).first()
        material_name = material.name if material else "Material"
        pdf.cell(100, 10, material_name, border=1)

        pdf.cell(
            40,
            10,
            str(item.dispatched_qty),
            border=1
        )

        pdf.ln()

    pdf.ln(20)

    pdf.cell(
        100,
        10,
        "Firma Responsable: __________________"
    )
    pdf.ln(20)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(
    200,
    10,
    "Documento generado automaticamente por el sistema MRP",
    ln=True,
    align="C"
    )

    # CREAR CARPETA
    os.makedirs("storage/guides", exist_ok=True)

    filename = f"storage/guides/{dispatch.guia_number}.pdf"

    pdf.output(filename)
    db.close()

    return filename