import os
import pathlib
import tensorflow as tf

from tensorflow.keras.layers import Dense, Flatten, Conv2D
from tensorflow.keras import Model

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # ignore TensofFlow warnings

# MNIST データセットのダウンロードと正規化
mnist = tf.keras.datasets.mnist

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0

# チャネルの次元の追加
x_train = x_train[..., tf.newaxis]
x_test = x_test[..., tf.newaxis]


# モデルの作成
model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(64, (5,5), activation='relu', input_shape=(28, 28, 1)),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(32, (5,5), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')
])


# モデルのコンパイル
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])


# 学習
model.fit(x_train, y_train, epochs=5)


# 学習の評価
test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
print('\nTest accuracy:', test_acc)


# モデルと重みの保存
import shutil

path = 'saved_model'
if os.path.isdir(path):
    shutil.rmtree(path)
    
os.mkdir(path)
model.save('saved_model/my_model')

# cnnモデルで学習したことを示すフラグファイル
cnn_flag = pathlib.Path('saved_model/cnn') 
cnn_flag.touch()

# アーカイブと圧縮
import tarfile

with tarfile.open('saved_model.tgz', 'w:gz') as t:
    t.add('saved_model')
