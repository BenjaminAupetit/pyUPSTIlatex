from pathlib import Path

import fitz  # PyMuPDF


def extract_comments(pdf_path: str, output_path: str):
    doc = fitz.open(pdf_path)
    comments = []

    for page in doc:
        # Récupère les blocs de texte de la page
        for block in page.get_text("blocks"):
            text = block[4].strip()
            if text.lower().startswith("commentaire"):
                # Supprime le mot "Commentaire" au début
                cleaned = text[len("Commentaires") :].strip()
                comments.append(cleaned)

    # Écrit les commentaires dans un fichier texte
    with open(output_path, "w", encoding="utf-8") as f:
        for c in comments:
            f.write(c + "\n")
            f.write("-" * 40 + "\n")

    print(f"Extraction terminée : {len(comments)} commentaires trouvés.")
    print(f"Fichier généré : {output_path}")


if __name__ == "__main__":
    fichier = "C:\\OD-EN\\OneDrive - ac-clermont.fr\\Pédagogie\\Compétences et programmes\\2013\\BO-2013-SII-TSI.pdf"
    extract_comments(
        fichier,
        "commentaires-TSI-2013.txt",
    )
