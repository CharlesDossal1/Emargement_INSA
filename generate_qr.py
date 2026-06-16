#!/usr/bin/env python3
"""
Génère un PDF imprimable avec les QR codes de tous les étudiants.
Utilisation : BASE_URL=https://... python generate_qr.py
"""

import csv
import os
import io
import sqlite3
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
DB_PATH = os.path.join(os.path.dirname(__file__), "presence.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "etudiants_5A.csv")
OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "qrcodes_5A.pdf")

COLS = 6
QR_SIZE = 2.8 * cm
LABEL_HEIGHT = 0.6 * cm
CELL_W = QR_SIZE + 0.4 * cm
CELL_H = QR_SIZE + LABEL_HEIGHT + 0.4 * cm
MARGIN_X = 1.2 * cm
MARGIN_Y = 1.5 * cm


def charger_etudiants():
    """Lit les étudiants depuis la base avec leurs IDs."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, nom, prenom FROM etudiants ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def generer_qr_image(url):
    """Génère un QR code et retourne un objet ImageReader pour ReportLab."""
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def generer_pdf(etudiants):
    page_w, page_h = A4
    rows_per_page = int((page_h - 2 * MARGIN_Y) / CELL_H)
    cells_per_page = COLS * rows_per_page

    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    x0 = MARGIN_X
    y_top = page_h - MARGIN_Y - CELL_H

    for i, etu in enumerate(etudiants):
        if i > 0 and i % cells_per_page == 0:
            c.showPage()

        idx = i % cells_per_page
        col_pos = idx % COLS
        row_pos = idx // COLS

        x = x0 + col_pos * CELL_W
        y = y_top - row_pos * CELL_H

        url = f"{BASE_URL}/scan/{etu['id']}"
        qr_img = generer_qr_image(url)

        c.drawImage(qr_img, x, y + LABEL_HEIGHT, width=QR_SIZE, height=QR_SIZE)

        label = f"{etu['nom']} {etu['prenom']}"
        c.setFont("Helvetica", 6.5)
        text_w = c.stringWidth(label, "Helvetica", 6.5)
        c.drawString(x + (QR_SIZE - text_w) / 2, y + 2, label)

    c.save()
    print(f"PDF généré : {OUTPUT_PDF}")


if __name__ == "__main__":
    etudiants = charger_etudiants()
    if not etudiants:
        print("Base vide. Lance d'abord : python init_db.py")
    else:
        generer_pdf(etudiants)
        print(f"{len(etudiants)} QR codes générés.")
