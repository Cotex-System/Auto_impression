from http.client import HTTPException
import win32print
import win32api
import win32ui
import subprocess
import time
from PIL import Image, ImageWin
import fitz  # PyMuPDF
from win32con import HORZRES, VERTRES, PHYSICALWIDTH, PHYSICALHEIGHT
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware 
import tempfile
import os

ACROBAT_PATH = r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe"
PRINTER_NAME = "ZDesigner TLP 2844"
API_TOKEN = os.environ.get("PRINT_API_TOKEN")

if not API_TOKEN:
    raise RuntimeError("PRINT_API_TOKEN non défini")
    
def check_token(authorization: str | None):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Token manquant")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Format du token invalide")

    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalide")
        
def print_epl(epl: bytes):
    # Protection: vérifier que les données reçues semblent bien être du EPL
    if isinstance(epl, (bytes, bytearray)) and epl.startswith(b"%PDF"):
        raise ValueError("Les données reçues semblent être un PDF — impossible d'imprimer en RAW EPL.")

    hPrinter = win32print.OpenPrinter(PRINTER_NAME)
    print(f"Imprimante ouverte: {hPrinter}")
    print(f"Contenu EPL à imprimer: {epl[:100]}...")  # Affiche les 100 premiers caractères pour vérification
    try:
        hJob = win32print.StartDocPrinter(
            hPrinter, 1, ("EPL", None, "RAW")
        )
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, epl)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)


def pdf_to_images(pdf_path, dpi=300, oversample=2, to_mode="RGB"):
    """Render PDF pages to PIL Images.

    - dpi: target DPI for the final image (typ. printer DPI e.g. 203)
    - oversample: render at dpi * oversample, then downscale with Lanczos
    - to_mode: final PIL mode ("RGB" or "L")
    """
    doc = fitz.open(pdf_path)
    images = []

    render_dpi = int(dpi * oversample)
    mat = fitz.Matrix(render_dpi / 72, render_dpi / 72)
    for page in doc:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Downscale to target DPI size
        if oversample > 1:
            target_w = int(img.width / oversample)
            target_h = int(img.height / oversample)
            img = img.resize((target_w, target_h), resample=Image.LANCZOS)

        if to_mode and img.mode != to_mode:
            img = img.convert(to_mode)

        images.append(img)

    return images


def print_image_via_gdi(image: Image.Image):
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(PRINTER_NAME)

    printable_area = (hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES))
    printer_size = (hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT))

    # Scale image to fit printable area while preserving aspect
    img_width, img_height = image.size
    ratio = min(printable_area[0] / img_width, printable_area[1] / img_height)
    target_width = int(img_width * ratio)
    target_height = int(img_height * ratio)

    hDC.StartDoc("AutoImpression")
    hDC.StartPage()

    dib = ImageWin.Dib(image)
    x1 = 0
    y1 = 0
    x2 = target_width
    y2 = target_height
    dib.draw(hDC.GetHandleOutput(), (x1, y1, x2, y2))

    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()


def print_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} introuvable")

    # 0) Tentative: rasteriser et imprimer via GDI (utilise le pilote Windows)
    try:
        print("Tentative d'impression via GDI (rasterisation PDF)")
        images = pdf_to_images(pdf_path)
        for img in images:
            print_image_via_gdi(img)
        return
    except Exception as e:
        print("Impression via GDI a échoué:", e)

    # 1) Tentative avec ShellExecute 'printto'
    try:
        print(f"Tentative ShellExecute printto vers '{PRINTER_NAME}'")
        win32api.ShellExecute(0, "printto", pdf_path, PRINTER_NAME, ".", 0)
        time.sleep(5)
        return
    except Exception as e:
        print("ShellExecute printto a échoué:", e)

    # 2) Si Acrobat est installé, essayer la commande /t qui demande l'impression silencieuse
    if os.path.exists(ACROBAT_PATH):
        try:
            print("Tentative d'impression via Acrobat Reader (/t)")
            subprocess.run([ACROBAT_PATH, '/t', pdf_path, PRINTER_NAME], check=True)
            return
        except Exception as e:
            print("Acrobat /t a échoué:", e)

    # 3) Dernier recours: utiliser l'association Windows via os.startfile('print')
    try:
        print("Tentative d'impression via os.startfile('print')")
        os.startfile(pdf_path, 'print')
        return
    except Exception as e:
        print("os.startfile('print') a échoué:", e)
        # Remonter l'erreur pour que l'appelant sache que l'impression a échoué
        raise RuntimeError("Impossible d'imprimer le PDF avec les méthodes disponibles") from e

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou domaine précis
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/print")
async def print_label(
    carrier: str = Form(...),
    file: UploadFile = File(...)
):
    data = await file.read()

    if carrier == "tnt":
        print_epl(data)
    elif carrier == "poste":
        print_epl(data)
    elif carrier == "chronopost":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(data)
            pdf_path = f.name
        print_pdf(pdf_path)
        os.remove(pdf_path)

    else:
        return {"error": "Transporteur inconnu"}

    return {"status": "printed"}
