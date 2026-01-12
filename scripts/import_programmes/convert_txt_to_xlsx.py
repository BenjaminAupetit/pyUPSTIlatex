from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment


def text_to_excel(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    raw_cells = content.strip().split("\n\n")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Commentaires"

    for i, cell in enumerate(raw_cells, start=1):
        c = ws.cell(row=i, column=1, value=cell)
        # Activer l'affichage multi-lignes
        c.alignment = Alignment(wrap_text=True)

    wb.save(output_path)
    print(f"Fichier Excel généré : {output_path}")


if __name__ == "__main__":
    text_to_excel("commentaires-ATS-II-2025.txt", "output-ATS-II-2025.xlsx")
