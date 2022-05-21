from PIL import Image
from cv2 import COLOR_BGR2GRAY, cvtColor, imread
from skimage.metrics import structural_similarity as compare_ssim


def calculate_ssim(file_name: str) -> float:
    img = Image.open(file_name)
    img.resize(Image.open("res/profile_example.png").size).save(file_name)

    imageA = imread("res/profile_example.png")
    imageB = imread(file_name)

    imageA = cvtColor(imageA, COLOR_BGR2GRAY)
    imageB = cvtColor(imageB, COLOR_BGR2GRAY)

    score, _ = compare_ssim(imageA, imageB, full=True)
    return round(score, 2)
