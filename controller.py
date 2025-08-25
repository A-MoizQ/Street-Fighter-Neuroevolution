import socket
import json
from game_state import GameState
import sys
from bot import Bot
import random
import os
import time

READY_FILE = "controller_ready.txt"

def connect(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", port))
    server_socket.listen(5)
    (client_socket, _) = server_socket.accept()
    print ("Connected to game!")
    
    return client_socket

def send(client_socket, command):
    command_dict = command.object_to_dict()
    pay_load = json.dumps(command_dict).encode()
    client_socket.sendall(pay_load)

def receive(client_socket):
    pay_load = client_socket.recv(4096)
    input_dict = json.loads(pay_load.decode())
    game_state = GameState(input_dict)
    return game_state

def main():
    start_time = time.time()
    print(f"[{time.time() - start_time:.2f}s] Controller starting...")
    print(f"[{time.time() - start_time:.2f}s] Using Python interpreter: {sys.executable}")

    if (sys.argv[1]=='1'):
        client_socket = connect(9999)
    elif (sys.argv[1]=='2'):
        client_socket = connect(10000)
    
    print(f"[{time.time() - start_time:.2f}s] Socket connected.")

    bot = Bot()
    print(f"[{time.time() - start_time:.2f}s] Bot object created.")

    bot.ann.load_weights("current_weights.weights.h5")
    print(f"[{time.time() - start_time:.2f}s] ANN weights loaded.")

    # Signal to Lua script that controller is ready after loading weights
    with open(READY_FILE, "w") as f:
        f.write("ready")
    print(f"[{time.time() - start_time:.2f}s] Controller ready signal sent after ANN loaded.")

    # Match-specific data
    fight_history = []
    damage_dealt = 0
    damage_taken = 0
    health_bonus = 0
    time_bonus = 0
    distance_values = []
    last_opponent_health = 176
    last_bot_health = 176

    # State machine states
    CHARACTER_SELECT = -1
    IDLE = 0
    FIGHTING = 1
    MATCH_OVER = 2
    current_state = CHARACTER_SELECT
    
    # Character selection variables
    char_select_frames = random.randint(5, 15)
    frames_waited = 0
    
    # Edge detection variables
    prev_round_started = False
    prev_round_over = False
    prev_timer = None
    timer_stuck_count = 0
    idle_frames = 0  # Counter to ensure we stay in idle long enough

    while current_state != MATCH_OVER:
        game_state = receive(client_socket)
        
        # Current frame flags
        curr_round_started = game_state.has_round_started
        curr_round_over = game_state.is_round_over

        # Timer stagnation detection
        if prev_timer is not None and current_state == FIGHTING:
            if game_state.timer == prev_timer:
                timer_stuck_count += 1
            else:
                timer_stuck_count = 0

        if current_state == CHARACTER_SELECT:
            if frames_waited < char_select_frames:
                # Move cursor randomly
                bot.my_command.player_buttons.up = random.choice([True, False])
                bot.my_command.player_buttons.down = random.choice([True, False])
                bot.my_command.player_buttons.left = random.choice([True, False])
                bot.my_command.player_buttons.right = random.choice([True, False])
                bot_command = bot.my_command
                frames_waited += 1
            elif frames_waited == char_select_frames:
                # Press Start to select character
                bot.my_command.player_buttons.start = True
                bot_command = bot.my_command
                frames_waited += 1
            else:
                # Release start and wait for match to begin
                bot.my_command.player_buttons.start = False
                bot_command = bot.my_command
                # Only transition when round actually starts (rising edge)
                if not prev_round_started and curr_round_started and not curr_round_over:
                    current_state = FIGHTING
                    bot.reset()
                    last_opponent_health = 176
                    last_bot_health = 176
                    print("Character selected. First round starting!")

        elif current_state == IDLE:
            idle_frames += 1
            # Only transition to FIGHTING when:
            # 1. Round has started (rising edge from previous frame)
            # 2. Round is not over
            # 3. We've been in idle for at least a few frames to avoid immediate transitions
            if (not prev_round_started and curr_round_started and 
                not curr_round_over and idle_frames > 60):
                current_state = FIGHTING
                bot.reset()
                last_opponent_health = 176
                last_bot_health = 176
                idle_frames = 0
                print("New round has started!")
            bot_command = bot.my_command

        elif current_state == FIGHTING:
            # Detect round end in multiple ways:
            # 1. Standard round over flag with rising edge
            # 2. Timer reaches 0 (timeout scenario)
            # 3. Either player's health reaches 0
            
            round_ended = False
            timeout_win = False
            
            # Standard round end detection
            if (not prev_round_over and curr_round_over and 
                game_state.fight_result != "NOT_OVER" and game_state.fight_result != "NONE"):
                round_ended = True
            
            # Timer-based round end detection
            elif timer_stuck_count > 60:
                round_ended = True
                timeout_win = True
                print("Round ended due to timer expiring!")
            
            # Health-based round end detection (backup)
            elif (game_state.player1.health == 255 or game_state.player2.health == 255):
                round_ended = True
                print("Round ended due to health reaching zero!")
            
            if round_ended:
                current_state = IDLE
                idle_frames = 0
                timer_stuck_count = 0
                print("Round is over.")
                
                # Determine win condition more robustly
                bot_won = False
                bot_health = game_state.player1.health if sys.argv[1] == '1' else game_state.player2.health
                opponent_health = game_state.player2.health if sys.argv[1] == '1' else game_state.player1.health
                
                if timeout_win:
                    # Timer ran out - winner is determined by health
                    if bot_health > opponent_health:
                        bot_won = True
                        print(f"Won by timeout! Bot health: {bot_health}, Opponent: {opponent_health}")
                    elif bot_health == opponent_health:
                        bot_won = False  # Draw goes to opponent
                        print(f"Draw by timeout. Bot health: {bot_health}, Opponent: {opponent_health}")
                    else:
                        bot_won = False
                        print(f"Lost by timeout. Bot health: {bot_health}, Opponent: {opponent_health}")
                else:
                    # Check explicit fight result first
                    if (sys.argv[1] == '1' and game_state.fight_result == "P1") or \
                       (sys.argv[1] == '2' and game_state.fight_result == "P2"):
                        bot_won = True
                    
                    # If fight result is inconclusive, check health
                    elif game_state.fight_result in ["TIME_OVER", "DRAW", ""]:
                        if bot_health > opponent_health:
                            bot_won = True
                        elif bot_health == opponent_health:
                            bot_won = False  # or True, depending on your preference
                    
                    # Health-based win detection (when someone's health hits 255 means -1)
                    elif opponent_health == 255 and bot_health != 255:
                        bot_won = True
                    elif bot_health == 255 and opponent_health != 255:
                        bot_won = False
                
                if bot_won:
                    fight_history.append(1)
                    health_bonus += bot_health
                    time_bonus += max(0, game_state.timer - 48)  # Don't add negative time
                    print("Round won!")
                else:
                    fight_history.append(0)
                    print("Round lost!")
                
                print(f"Fight History: {fight_history}")
                print(f"Final health - Bot: {bot_health}, Opponent: {opponent_health}, Timer: {game_state.timer}")
                
                # Check for match-ending conditions
                if (fight_history.count(0) >= 2) or (fight_history.count(1) >= 2):
                    current_state = MATCH_OVER

                bot_command = bot.my_command
            else:
                # Track damage during active fighting
                bot_health = game_state.player1.health if sys.argv[1] == '1' else game_state.player2.health
                opponent_health = game_state.player2.health if sys.argv[1] == '1' else game_state.player1.health
                
                # Only track damage if neither player is knocked out (255)
                if opponent_health != 255 and last_opponent_health != 255:
                    if opponent_health < last_opponent_health:
                        damage_dealt += last_opponent_health - opponent_health
                        
                if bot_health != 255 and last_bot_health != 255:
                    if bot_health < last_bot_health:
                        damage_taken += last_bot_health - bot_health

                last_bot_health = bot_health
                last_opponent_health = opponent_health

                # Track distance for aggressiveness score
                distance_values.append(abs(game_state.player1.x_coord - game_state.player2.x_coord))

                bot_command = bot.fight(game_state, sys.argv[1])

        send(client_socket, bot_command)
        
        # Update previous frame flags for edge detection
        prev_round_started = curr_round_started
        prev_round_over = curr_round_over
        prev_timer = game_state.timer

    # --- MATCH IS OVER ---
    print("Match complete. Calculating and saving fitness results...")
    
    # Determine if the bot won the match
    won_match = fight_history.count(1) >= 2

    # Calculate average distance, avoiding division by zero
    avg_distance = sum(distance_values) / len(distance_values) if distance_values else 0

    # Package results into a dictionary
    results = {
        "won_match": won_match,
        "fight_history": fight_history,
        "damage_dealt": damage_dealt,
        "damage_taken": damage_taken,
        "health_bonus": health_bonus,
        "time_bonus": time_bonus,
        "average_distance": avg_distance
    }

    # Write results to a JSON file for the evolution script to read
    with open("fitness_results.json", "w") as f:
        json.dump(results, f)

    # Clean up the ready file for the next run
    if os.path.exists(READY_FILE):
        os.remove(READY_FILE)
        print("Ready file cleaned up.")

    print("Results saved. Exiting controller.")
    client_socket.close()

if __name__ == '__main__':
   main()