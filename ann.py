import tensorflow as tf
from tensorflow.keras import layers
import numpy as np

class ANN:
    """
    A stateful Recurrent Neural Network for controlling the Street Fighter bot.
    This class encapsulates a Keras model and provides methods for prediction
    and weight management, which are essential for a neuroevolutionary algorithm.
    """
    def __init__(self):
        """
        Initializes and builds the RNN model.
        """
        self.input_size = 15
        self.gru_units = 32
        self.dense_units = 16
        self.output_size = 10  # For 10 combat buttons: U, D, L, R, Y, B, A, X, L, R

        # The model is stateful, meaning it maintains its hidden state between predictions.
        # We use an InputLayer to explicitly define the batch_input_shape, which is
        # required for a stateful RNN. Shape is (batch_size, timesteps, features).
        self.model = tf.keras.Sequential([
            layers.InputLayer(batch_input_shape=(1, 1, self.input_size)),
            layers.GRU(self.gru_units, stateful=True, name="GRU_layer"),
            layers.Dense(self.dense_units, activation='relu', name="Dense_layer"),
            layers.Dense(self.output_size, activation='sigmoid', name="Output_layer")
        ])

    @tf.function(input_signature=[
        tf.TensorSpec(shape=(1, 1, 15), dtype=tf.float32)
    ])
    def predict(self, input_tensor):
        """
        Predicts the next action based on the input tensor.
        This method is decorated with @tf.function to compile it into a high-performance
        TensorFlow graph for repeated calls.

        Args:
            input_tensor: A 3D tf.Tensor of shape (1, 1, 15).

        Returns:
            A flat tensor of 10 probabilities, one for each button.
        """
        # By decorating, we ensure this runs as a compiled graph.
        prediction = self.model(input_tensor)
        return tf.reshape(prediction, [-1])

    def reset_hidden_state(self):
        """
        Resets the internal state of the GRU layer.
        This should be called at the beginning of each new fight or round.
        The state is stored in the layer itself, not the model.
        """
        self.model.get_layer('GRU_layer').reset_states()

    def get_weights(self):
        """
        Returns the model's weights as a list of numpy arrays.
        Essential for the genetic algorithm (selection, crossover).
        """
        return self.model.get_weights()

    def set_weights(self, weights):
        """
        Sets the model's weights from a list of numpy arrays.
        Essential for the genetic algorithm (crossover, mutation).
        """
        self.model.set_weights(weights)

    def save_weights(self, file_path):
        """
        Saves the model's current weights to a HDF5 file.
        """
        self.model.save_weights(file_path)

    def load_weights(self, file_path):
        """
        Loads weights from a HDF5 file into the model.
        """
        self.model.load_weights(file_path)
