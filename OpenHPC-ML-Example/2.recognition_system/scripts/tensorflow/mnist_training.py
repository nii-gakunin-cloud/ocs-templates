import os
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # ignore TensofFlow warnings

# MNIST データセットのダウンロードと正規化
mnist = tf.keras.datasets.mnist

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0

# モデルの作成
model = tf.keras.models.Sequential([
    tf.keras.layers.Flatten(input_shape=(28, 28)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10)
])

# モデルのコンパイル
model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
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
if os.path.isfile('saved_model/cnn'):
    os.remove('saved_model/cnn')

# アーカイブと圧縮
import tarfile

with tarfile.open('saved_model.tgz', 'w:gz') as t:
    t.add('saved_model')

