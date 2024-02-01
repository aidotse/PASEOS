import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from sklearn.datasets import make_circles
from sklearn.model_selection import train_test_split


class SimpleNeuralNetwork(torch.nn.Module):
    """Neural network to perform binary classification on 2D points"""

    def __init__(self, node_id):
        super(SimpleNeuralNetwork, self).__init__()

        input_dim = 2
        hidden_dim = 10
        output_dim = 1
        self.layer_1 = torch.nn.Linear(input_dim, hidden_dim)
        torch.nn.init.kaiming_uniform_(self.layer_1.weight, nonlinearity="relu")
        self.layer_2 = torch.nn.Linear(hidden_dim, output_dim)
        self.num_epochs = 1

        self.optimizer = None
        self.loss_fn = None
        self.node_id = node_id
        self.load_data()

    def set_optimizer(self, optimizer, scheduler=None):
        """Attach an optimizer to the model

        Args:
            optimizer (_type_): optimization method
            scheduler (_type_, optional): schedule method. Defaults to None.
        """
        self.optimizer = optimizer
        self.scheduler = scheduler

    def set_loss_fn(self, loss_fn):
        """Attach a loss function for the training"""
        self.loss_fn = loss_fn

    def load_data(self):
        """Create dataloaders based on points belonging to two circles"""

        class Data(Dataset):
            """Custom dataset to read out 2D points and labels"""

            def __init__(self, X, y):
                self.X = torch.from_numpy(X.astype(np.float32))
                self.y = torch.from_numpy(y.astype(np.float32))
                self.len = self.X.shape[0]

            def __getitem__(self, index):
                return self.X[index], self.y[index]

            def __len__(self):
                return self.len

        # Instantiate training and test data
        X, y = make_circles(n_samples=10000, noise=0.05, random_state=26)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=26)

        # divide the training set so none of the peers have the same data
        if self.node_id == 1:
            train_mask = X_train[:, 0] < 0
        elif self.node_id == 2:
            train_mask = X_train[:, 0] > -0

        X_train = np.ma.compress_rows(
            np.ma.masked_array(X_train, mask=np.transpose(np.tile(train_mask, (2, 1))))
        )
        y_train = np.ma.masked_array(y_train, mask=train_mask).compressed()

        # Create dataloaders
        train_data = Data(X_train, y_train)
        test_data = Data(X_test, y_test)
        self.train_dataloader = DataLoader(dataset=train_data, batch_size=64, shuffle=True)
        self.test_dataloader = DataLoader(dataset=test_data, batch_size=64, shuffle=True)

    def forward(self, x):
        """Do inference on model

        Args:
            x (_type_): 2D input

        Returns:
            _type_: prediction
        """
        x = torch.nn.functional.relu(self.layer_1(x))
        x = torch.sigmoid(self.layer_2(x))
        return x

    def train(self):
        """Train model using the training data

        Returns:
            _type_: loss values for each datapoint
        """
        loss_values = []
        for epoch in range(self.num_epochs):
            for X, y in self.train_dataloader:
                # zero the parameter gradients
                self.optimizer.zero_grad()

                # forward + backward + optimize
                pred = self.forward(X)
                loss = self.loss_fn(pred, y.unsqueeze(-1))
                loss_values.append(loss.item())
                loss.backward()
                self.optimizer.step()
        return loss_values

    def eval(self):
        """Evaluate the model on the test set

        Returns:
            _type_: accuracy
        """
        total = 0
        correct = 0
        with torch.no_grad():
            for X, y in self.test_dataloader:
                outputs = self.forward(X)
                predicted = np.where(outputs < 0.5, 0, 1)
                predicted = [item for sublist in predicted for item in sublist]
                total += y.size(0)
                correct += (predicted == y.numpy()).sum().item()
        acc = correct / total

        return acc
