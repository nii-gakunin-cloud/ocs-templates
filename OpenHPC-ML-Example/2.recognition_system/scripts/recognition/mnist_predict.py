import os
import pathlib
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from PIL import ImageOps
import tensorflow as tf

model_data = 'saved_model/my_model'
img_file = 'base64_img.b64'

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # ignore TensofFlow warnings

def CnvImage(image):
    cnvimg = np.zeros(28*28).reshape((1,28,28,1))
    w, h = image.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = image.getpixel((x, y))
            if a :
                cnvimg[0][y][x][0] = a / 255.0
                
    return cnvimg

model = tf.keras.models.load_model(model_data)

with open(img_file, 'r') as f1:
    base64_img = f1.read()

img = Image.open(BytesIO(base64.b64decode(base64_img.split(",")[-1]))).resize((28,28)) # ヘッダーの削除はデコードエラー対策

input_img = CnvImage(img)
if os.path.isfile('saved_model/cnn'):
    print("Model: CNN")
    input_img = input_img[..., tf.newaxis]
else:
    print("Model: Flat")

output_unit = model.predict(input_img, batch_size=1) 
print("output unit:", output_unit)

result = np.argmax(output_unit)

print("")
print("Recognised: ", result)
