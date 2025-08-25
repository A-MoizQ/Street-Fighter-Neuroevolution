import tensorflow as tf
from command import Command
from buttons import Buttons
from ann import ANN
import numpy as np

# Normalization constants from observed game data
MAX_HEALTH = 176.0
MAX_X_COORD = 393.0
MAX_Y_COORD = 192.0
MAX_TIMER = 153.0
MAX_MOVE_ID = 33686533.0

def get_input_vector(game_state, player_number):
    """
    Flattens the complex game_state object into a simple, normalized
    15-feature vector for the ANN.
    """
    if player_number == "1":
        me = game_state.player1
        opponent = game_state.player2
    else:
        me = game_state.player2
        opponent = game_state.player1

    # Self features
    my_health = me.health / MAX_HEALTH
    my_x = me.x_coord / MAX_X_COORD
    my_y = me.y_coord / MAX_Y_COORD
    my_is_jumping = 1.0 if me.is_jumping else 0.0
    my_is_crouching = 1.0 if me.is_crouching else 0.0

    # Opponent features
    opp_health = opponent.health / MAX_HEALTH
    opp_x = opponent.x_coord / MAX_X_COORD
    opp_y = opponent.y_coord / MAX_Y_COORD
    opp_is_jumping = 1.0 if opponent.is_jumping else 0.0
    opp_is_crouching = 1.0 if opponent.is_crouching else 0.0
    opp_is_in_move = 1.0 if opponent.is_player_in_move else 0.0
    opp_move_id = opponent.move_id / MAX_MOVE_ID

    # Relational features
    relative_x = (me.x_coord - opponent.x_coord) / MAX_X_COORD
    relative_health = (me.health - opponent.health) / MAX_HEALTH
    timer = game_state.timer / MAX_TIMER

    return np.array([
        my_health, my_x, my_y, my_is_jumping, my_is_crouching,
        opp_health, opp_x, opp_y, opp_is_jumping, opp_is_crouching,
        opp_is_in_move, opp_move_id,
        relative_x, relative_health, timer
    ])

class Bot:
    """
    The Bot class now acts as a wrapper for the ANN.
    It translates game state for the ANN and ANN output into commands.
    """
    def __init__(self):
        self.ann = ANN()
        self.my_command = Command()
        self.buttn = Buttons()

    def reset(self):
        """
        Resets the bot's state for a new round. Critically, this also
        resets the hidden state of the recurrent neural network.
        """
        self.ann.reset_hidden_state()
        self.buttn = Buttons()
        self.my_command = Command()

    def fight(self, current_game_state, player):
        """
        The main decision-making function, now driven entirely by the ANN.
        """
        # 1. Convert game state to a feature vector and then to a Tensor
        input_vector = get_input_vector(current_game_state, player)
        input_tensor = tf.constant(input_vector.reshape(1, 1, -1), dtype=tf.float32)

        # 2. Get the ANN's prediction using the compiled graph
        prediction = self.ann.predict(input_tensor)

        # 3. Translate the prediction into button presses
        # The ANN outputs 10 values, we map them to the 10 combat buttons.
        # We must explicitly cast the numpy.bool_ to a standard Python bool
        # for the value to be JSON serializable.
        self.buttn.up = bool(prediction[0] > 0.5)
        self.buttn.down = bool(prediction[1] > 0.5)
        self.buttn.left = bool(prediction[2] > 0.5)
        self.buttn.right = bool(prediction[3] > 0.5)
        self.buttn.Y = bool(prediction[4] > 0.5)
        self.buttn.B = bool(prediction[5] > 0.5)
        self.buttn.A = bool(prediction[6] > 0.5)
        self.buttn.X = bool(prediction[7] > 0.5)
        self.buttn.L = bool(prediction[8] > 0.5)
        self.buttn.R = bool(prediction[9] > 0.5)
        
        # Select and Start are always False
        self.buttn.select = False
        self.buttn.start = False

        # 4. Assign the buttons to the correct player and return the command
        if player == "1":
            self.my_command.player_buttons = self.buttn
        elif player == "2":
            self.my_command.player2_buttons = self.buttn
            
        return self.my_command