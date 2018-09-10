from PIL import Image
import numpy as np


def handle(image):
    mapping_before_exchange = {
        0: 39, 1: 38, 2: 48, 3: 49, 4: 41, 5: 40, 6: 46, 7: 47, 8: 35, 9: 34, 10: 50, 11: 51, 12: 33, 13: 32, 14: 28,
        15: 29, 16: 27, 17: 26, 18: 36, 19: 37, 20: 31, 21: 30, 22: 44, 23: 45, 24: 43, 25: 42, 26: 12, 27: 13, 28: 23,
        29: 22, 30: 14, 31: 15, 32: 21, 33: 20, 34: 8, 35: 9, 36: 25, 37: 24, 38: 6, 39: 7, 40: 3, 41: 2, 42: 0, 43: 1,
        44: 11, 45: 10, 46: 4, 47: 5, 48: 19, 49: 18, 50: 16, 51: 17,
    }
    mapping = {value: key for key, value in mapping_before_exchange.items()}

    matrix = np.array(image)
    m1 = matrix[0: 80]
    m2 = matrix[80: 160]
    s1 = [np.array([i[j: j + 12] for i in m1]) for j in range(0, 312, 12)]
    s2 = [np.array([i[j: j + 12] for i in m2]) for j in range(0, 312, 12)]
    s = s1 + s2

    dic = {key: value for key, value in enumerate(s)}
    dic_exchange = {mapping[i]: dic[i] for i in range(52)}

    lis = [i[1] for i in sorted(dic_exchange.items(), key=lambda x: x[0])]

    n = []
    for i in range(80):
        n1 = []
        for j in lis[0: 26]:
            n1.extend(list(j[i]))
        n.append(n1)

    for i in range(80):
        n2 = []
        for j in lis[26: 52]:
            n2.extend(list(j[i]))
        n.append(n2)

    image = Image.fromarray(np.array(n))
    return image


def calculate_x(image):
    for i in range(0, image.width):
        count = 0
        for j in range(0, image.height):
            pixel = image.getpixel((i, j))
            if pixel != (0, 0, 0):
                count += 1

        if count >= 5:
            x = i + 23 - 30
            return x
