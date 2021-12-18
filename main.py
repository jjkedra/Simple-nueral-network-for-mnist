from typing import Callable, List, Tuple
from keras.datasets import mnist
from keras.utils import np_utils
import cv2
import glob
import numpy as np
from network import Network
from c_layer import CLayer
from active_layer import ActiveLayer
from activation_functions import sigmoid, sigmoid_prime
from losses import mse, mse_prime
from os import getcwd

FILES = glob.glob(getcwd()+"/samples/*.jpg")


def prep_data() -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
    # mnist data : 60000 samples
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    # reshape and normalize
    x_train = x_train.reshape(x_train.shape[0], 1, 28*28)
    x_train = x_train.astype('float32')
    x_train /= 255
    # encode output which is a number in range [0,9] into a vector of size 10
    # e.g. number 3 will become [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
    y_train = np_utils.to_categorical(y_train)

    # same for test data : 60000 samples
    x_test = x_test.reshape(x_test.shape[0], 1, 28*28)
    x_test = x_test.astype('float32')
    x_test /= 255
    y_test = np_utils.to_categorical(y_test)
    return (x_train, y_train), (x_test, y_test)


def create_network(shape:List[int], x_data:np.ndarray, y_data:np.ndarray,
                   activation:Callable[[float, float], float],
                   activation_prime:Callable[[float, float], float],
                   loss:Callable[[float], float], loss_prime:Callable[[float], float],
                   epochs: int=30, learning_rate: float=0.1,
                   test_size: int=1000) -> Network:
    net = Network()
    shape.insert(0, 28*28)
    shape.append(10)
    for previous, current in zip(shape, shape[1:]):
        net.add(CLayer(previous, current))
        net.add(ActiveLayer(activation, activation_prime))

    # set loss function
    net.use(loss, loss_prime)
    # train
    net.fit(x_data[0:test_size], y_data[0:test_size], epochs, learning_rate)
    return net


def convert(path='samples') -> List[np.ndarray]:
    test_list = list()
    for file in FILES:
        image = cv2.imread(file, cv2.IMREAD_GRAYSCALE)
        image = image.reshape(1, 28*28)
        image = image.astype('float32')
        image = (255 - image) / 255
        test_list.append(image)
    return test_list


def test_real(network: Network) -> str:
    out = network.predict(convert())
    values = list()

    for list_ in out:
        dic = dict()
        enum = 0
        for prob in np.ndenumerate(list_):
            dic[enum] = prob[1]
            enum += 1
        values.append(dic)

    output = ""
    for enum, entry in enumerate(values):
        highest_val = max(entry, key=entry.get)
        output += (f"NETWORK CLASSIFIED {enum} as {highest_val} " +
                   f"with probability of {entry[highest_val]}\n")

    return output


def test_mnist(network: Network, test_size: int, x_test: np.ndarray,
               y_test: np.ndarray) -> float:
    out = network.predict(x_test[:test_size])
    accuracy = 0
    for enum, elem in enumerate(out):
        max_index = np.argmax(elem[0])
        if y_test[enum][max_index] == 1:
            accuracy += 1
    return accuracy / test_size


def main() -> None:
    (x_train, y_train), (x_test, y_test) = prep_data()
    network = create_network([200, 100, 50, 25], x_train, y_train, sigmoid, sigmoid_prime,
                             mse, mse_prime, test_size=30000, epochs=10)
    # network = create_network([100, 25], x_train, y_train, sigmoid, sigmoid_prime,
    #                           mse, mse_prime, test_size=10000, epochs=10)

    print("Accuracy for 1000 samples is:")
    print(test_mnist(network, 1000, x_test, y_test))

    print(test_real(network))


if __name__ == '__main__':
    main()
