import numpy as np

from .base import DifferentiableModel


class PyTorchModel(DifferentiableModel):
    """Creates a model instance from a PyTorch nn.Module.

    Parameters
    ----------
    model : `torch.nn.Module`
        The PyTorch model as an nn.Module.
    cuda : bool
        A boolean specifying whether the model uses CUDA.

    """

    def __init__(
            self,
            model,
            *args,
            num_classes,
            cuda=True,
            channel_axis=1,
            **kwargs):

        super().__init__(*args, channel_axis=channel_axis, **kwargs)

        self._num_classes = num_classes
        self._model = model
        self.cuda = cuda

    def batch_predictions(self, images):
        # lazy import
        import torch
        from torch.autograd import Variable

        n = len(images)
        images = torch.from_numpy(images)
        if self.cuda:
            images = images.cuda()
        images = Variable(images, volatile=True)
        predictions = self._model(images)
        predictions = predictions.data
        predictions = predictions.numpy()
        assert predictions.ndim == 2
        assert predictions.shape == (n, self.num_classes())
        return predictions

    def num_classes(self):
        return self._num_classes

    def predictions_and_gradient(self, image, label):
        # lazy import
        import torch
        import torch.nn as nn
        from torch.autograd import Variable

        target = np.array([label])
        target = torch.from_numpy(target)
        target = Variable(target)

        assert image.ndim == 3
        images = image[np.newaxis]
        images = torch.from_numpy(images)
        if self.cuda:
            images = images.cuda()
        images = Variable(images, requires_grad=True)
        predictions = self._model(images)
        ce = nn.CrossEntropyLoss()
        loss = ce(predictions, target)
        loss.backward()
        grad = images.grad

        predictions = predictions.data
        predictions = predictions.numpy()
        predictions = np.squeeze(predictions, axis=0)
        assert predictions.ndim == 1
        assert predictions.shape == (self.num_classes(),)

        grad = grad.data
        grad = grad.numpy()
        grad = np.squeeze(grad, axis=0)
        assert grad.shape == image.shape

        return predictions, grad