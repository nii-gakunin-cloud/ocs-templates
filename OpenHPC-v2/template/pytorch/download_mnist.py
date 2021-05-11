import torchvision
import warnings
from six.moves import urllib
warnings.filterwarnings("ignore")


opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
urllib.request.install_opener(opener)


_ = torchvision.datasets.MNIST(
        '../data', train=True, transform=None, target_transform=None,
        download=True)
