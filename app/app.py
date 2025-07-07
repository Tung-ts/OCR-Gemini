import os
import io
from PIL import Image
from pdf2image import convert_from_bytes
from flask import Flask, request, render_template
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Flask setup
app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    text_output = ""

    if request.method == "POST":
         #Get industry and criteria from form
        industry = request.form.get("industry", "").strip()
        criteria = request.form.get("criteria", "").strip()

        files = request.files.getlist("file")
        for file in files:
            if file:
                filename = file.filename
                file_bytes = file.read()
                file_ext = filename.rsplit(".", 1)[-1].lower()

                try:
                    #Convert PDF to images or load image directly
                    if file_ext == "pdf":
                        images = convert_from_bytes(file_bytes)
                    else:
                        image = Image.open(io.BytesIO(file_bytes))
                        images = [image]

                    full_text = ""
                    for i, image in enumerate(images):
                        response = model.generate_content([
                            "Extract the content from the image, preserve layout and Vietnamese language:",
                            image
                        ])
                        full_text += f"\n--- {filename} - Page {i+1} ---\n{response.text.strip()}"

                    #  Evaluate CV match if industry and criteria are provided
                    if industry and criteria:
                        eval_prompt = f"""
Bạn là chuyên gia tuyển dụng. CV sau đây có phù hợp với ngành "{industry}" và các tiêu chí "{criteria}" không?
- Chấm điểm từ 0 đến 100
- Giải thích ngắn gọn lý do

CV:
{full_text}
                        """
                        eval_response = model.generate_content(eval_prompt)
                        score_text = eval_response.text.strip()

                        text_output += f"\n>>> Đánh giá mức độ phù hợp cho **{filename}**:\n{score_text}\n"
                    else:
                        text_output += f"\n>>> Đã trích xuất nội dung CV từ {filename} (không đánh giá do thiếu ngành/tiêu chí)\n"

                except Exception as e:
                    text_output += f"\n--- {filename} ---\nError processing: {str(e)}\n"

        # Write results to .txt file
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#         result_file = os.path.join(RESULT_FOLDER, f"{timestamp}.txt")
#         with open(result_file, "w", encoding="utf-8") as f:
#             f.write(text_output)

    return render_template("index.html", text=text_output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999)
