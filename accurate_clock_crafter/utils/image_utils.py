from PIL import Image


def mask_subtract(image_1: Image.Image, image_2: Image.Image) -> Image.Image:
    alpha_1 = list(image_1.split()[-1].getdata())
    alpha_2 = list(image_2.split()[-1].getdata())

    result_alpha = []
    for pixel_1, pixel_2 in zip(alpha_1, alpha_2):
        result_alpha.append(max(pixel_1 - pixel_2, 0))

    result_mask = Image.new("L", image_1.size)
    result_mask.putdata(result_alpha)
    return result_mask
