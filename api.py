import os
from flask import Flask, request, render_template, send_file
from PIL import Image
import io
import os
import pytesseract
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

# Folder where images will be stored
UPLOAD_FOLDER = "uploads"
EXCEL_FILE = os.path.join(UPLOAD_FOLDER, "data.xlsx")

# Set the path to Tesseract-OCR (Change this if needed)
# Example for Windows: pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# For Linux/macOS, it's usually installed in the system path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ✅ Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    try:
        width = int(request.form.get('width', 800))
        height = int(request.form.get('height', 800))
        output_format = request.form.get('format', 'JPEG').upper()
        quality = int(request.form.get('quality', 100))

        image = Image.open(file).convert("RGB")
        image.thumbnail((width, height))

        img_io = io.BytesIO()
        image.save(img_io, format=output_format, quality=quality)
        img_io.seek(0)

        ext = output_format.lower()
        filename = f"compressed.{ext}"

        return send_file(img_io, mimetype=f"image/{ext}", as_attachment=True, download_name=filename)

    except Exception as e:
        return f"Error: {str(e)}", 500

# ✅ Convert a single image to PDF
@app.route('/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    try:
        image = Image.open(file).convert("RGB")
        
        pdf_io = io.BytesIO()
        image.save(pdf_io, format="PDF")
        pdf_io.seek(0)

        return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name="converted.pdf")

    except Exception as e:
        return f"Error: {str(e)}", 500

# ✅ Convert all images in the "uploads" folder into a single PDF
@app.route('/convert-folder-to-pdf', methods=['GET'])
def convert_folder_to_pdf():
    try:
        image_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not image_files:
            return "No images found in the folder", 400

        images = []
        for file_name in sorted(image_files):  # Sort to maintain order
            img_path = os.path.join(UPLOAD_FOLDER, file_name)
            image = Image.open(img_path).convert("RGB")
            images.append(image)

        if not images:
            return "No valid images found", 400

        # Save as a multi-page PDF
        pdf_io = io.BytesIO()
        images[0].save(pdf_io, format="PDF", save_all=True, append_images=images[1:])
        pdf_io.seek(0)

        return send_file(pdf_io, mimetype="application/pdf", as_attachment=True, download_name="all_images.pdf")

    except Exception as e:
        return f"Error: {str(e)}", 500
# ✅ API to update Excel file
@app.route('/update-excel', methods=['POST'])
def update_excel():
    try:
        # ✅ Get input data from the form
        date = request.form.get("date")
        remarks = request.form.get("remarks")

        if not date or not remarks:
            return "Error: Please provide both Date and Remarks.", 400

        # ✅ Load existing data or create new DataFrame
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE, engine='openpyxl')  # Use openpyxl for better handling
        else:
            df = pd.DataFrame(columns=["Date", "Remarks"])

        # ✅ Append new data
        new_data = pd.DataFrame({"Date": [date], "Remarks": [remarks]})
        df = pd.concat([df, new_data], ignore_index=True)

        # ✅ Save back to Excel with proper closing
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, index=False)

        return redirect(url_for('index'))

    except Exception as e:
        return f"Error: {str(e)}", 500

# ✅ API to Convert Image Text to .txt File
@app.route("/image-to-text", methods=["POST"])
def image_to_text():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    try:
        # Open Image
        image = Image.open(file)

        # Extract text using Tesseract OCR
        extracted_text = pytesseract.image_to_string(image)

        if not extracted_text.strip():
            return "No readable text found in the image.", 400

        # Save text to file
        txt_io = io.BytesIO()
        txt_io.write(extracted_text.encode("utf-8"))
        txt_io.seek(0)

        return send_file(txt_io, mimetype="text/plain", as_attachment=True, download_name="extracted_text.txt")

    except Exception as e:
        return f"Error: {str(e)}", 500



if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
