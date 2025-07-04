# ocr_impreso.py
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch

# Cargar modelo entrenado para texto impreso en español
processor = TrOCRProcessor.from_pretrained("qantev/trocr-base-spanish")
model = VisionEncoderDecoderModel.from_pretrained("qantev/trocr-base-spanish")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


def ocr_impreso(image: Image.Image) -> str:
    """OCR para texto impreso en español usando TrOCR fine-tuned por Qantev."""
    pixel_values = processor(
        images=image.convert("RGB"), return_tensors="pt"
    ).pixel_values.to(device)
    generated_ids = model.generate(pixel_values)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return transcription.strip()
