

import subprocess
import json
import os
import numpy as np
from ann import ANN
import time

# --- Configuration ---
POPULATION_SIZE = 20
NUM_GENERATIONS = 500
BIZHAWK_PATH = "D:/pythonProjs/Street-Fighter-neuroevolution/AI Project/gamebot-competition-master/single-player/EmuHawk.exe"
ROM_PATH = "D:/pythonProjs/Street-Fighter-neuroevolution/AI Project/gamebot-competition-master/single-player/Street Fighter II Turbo (U).smc"
SAVE_SLOT_TO_LOAD = 1
WEIGHTS_FILE = "current_weights.weights.h5"
RESULTS_FILE = "fitness_results.json"
BEST_MODELS_DIR = "best_models"
OVERALL_BEST_MODELS_DIR = "best_model_over_all_generations"
CONTROLLER_PORT = 9999

# --- Main Neuroevolution Functions ---

def create_initial_population():
    """Creates a list of 50 brand new, randomly initialized ANNs."""
    population = []
    for _ in range(POPULATION_SIZE):
        population.append(ANN())
    print(f"Created initial population of {POPULATION_SIZE} individuals.")
    return population

def evaluate_fitness(individual, individual_id):
    """
    Evaluates a single ANN's fitness by launching the emulator and controller,
    waiting for the match to complete, and reading the results.
    """
    print(f"\n--- Evaluating Individual {individual_id} ---")
    
    # 1. Save the individual's weights to a file for the controller to load
    individual.save_weights(WEIGHTS_FILE)

    # 2. Launch the emulator, loading from our character-select save state
    script_dir = os.path.dirname(os.path.abspath(__file__))
    emulator_command = [
        BIZHAWK_PATH,
        f"--load-slot={SAVE_SLOT_TO_LOAD}",
        f"--socket_ip=127.0.0.1",
        f"--socket_port={CONTROLLER_PORT}",
        f"--lua={os.path.join(script_dir, 'auto_tool.lua')}",
        ROM_PATH
    ]
    print(f"Starting emulator...")
    emulator_process = subprocess.Popen(emulator_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3) 
    # --- LAUNCH auto_gui.py AND controller.py IN PARALLEL ---    
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    python_executable = os.path.join(project_root, "venv", "Scripts", "python.exe")
    auto_gui_path = os.path.join(script_dir, "auto_gui.py")
    controller_path = os.path.join(script_dir, "controller.py")

    auto_gui_command = [python_executable, auto_gui_path]
    controller_command = [python_executable, controller_path, "1"]

    controller_process = None
    auto_gui_process = None

    try:
        print(f"Starting controller with interpreter: {python_executable}")
        controller_process = subprocess.Popen(controller_command)
        time.sleep(5)
        print("Starting auto_gui.py for mouse automation...")
        auto_gui_process = subprocess.Popen(auto_gui_command)

        # Wait for both processes with timeout protection
        print("Waiting for controller to finish...")
        try:
            controller_process.wait(timeout=480)  # 8 minute timeout
            print("Controller finished successfully.")
        except subprocess.TimeoutExpired:
            print("Controller timeout - force terminating...")
            controller_process.terminate()
            time.sleep(2)
            if controller_process.poll() is None:
                controller_process.kill()
            print("Controller force terminated.")

        print("Waiting for auto_gui to finish...")
        try:
            auto_gui_process.wait(timeout=120)  # 2 minute timeout
            print("Auto GUI finished successfully.")
        except subprocess.TimeoutExpired:
            print("Auto GUI timeout - force terminating...")
            auto_gui_process.terminate()
            time.sleep(2)
            if auto_gui_process.poll() is None:
                auto_gui_process.kill()
            print("Auto GUI force terminated.")

        print("Controller and auto_gui.py have finished.")

    finally:
        # CRITICAL: Always clean up processes in finally block
        print("Cleaning up all processes...")
        
        # Clean up controller process
        if controller_process and controller_process.poll() is None:
            try:
                print("Force terminating controller...")
                controller_process.terminate()
                time.sleep(1)
                if controller_process.poll() is None:
                    controller_process.kill()
                    time.sleep(1)
            except Exception as e:
                print(f"Error terminating controller: {e}")

        # Clean up auto_gui process  
        if auto_gui_process and auto_gui_process.poll() is None:
            try:
                print("Force terminating auto_gui...")
                auto_gui_process.terminate()
                time.sleep(1)
                if auto_gui_process.poll() is None:
                    auto_gui_process.kill()
                    time.sleep(1)
            except Exception as e:
                print(f"Error terminating auto_gui: {e}")

        # Clean up emulator process
        if emulator_process and emulator_process.poll() is None:
            try:
                print("Force terminating emulator...")
                emulator_process.terminate()
                time.sleep(2)
                if emulator_process.poll() is None:
                    emulator_process.kill()
                    time.sleep(1)
            except Exception as e:
                print(f"Error terminating emulator: {e}")

        print("Process cleanup complete.")

    # 6. Read the fitness results from the file the controller created
    try:
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)
        
        # --- Fitness Calculation based on Policies ---
        fitness = 0
        
        # Policy 1: Match Outcome (heavily weighted)
        if results["won_match"]:
            fitness += 1000
        else:
            fitness -= 1000
            
        # Policy 2: Damage Differential
        damage_dealt = results.get("damage_dealt", 0)
        damage_taken = results.get("damage_taken", 0)
        fitness += (damage_dealt * 1.5) # Reward dealing damage
        fitness -= (damage_taken * 2.0) # Penalize taking damage more heavily
        
        # Policy 3: Health & Time Efficiency
        health_bonus = results.get("health_bonus", 0)
        time_bonus = results.get("time_bonus", 0)
        fitness += health_bonus
        fitness += time_bonus

        # Policy 4: Aggressiveness (lower average distance is better)
        avg_distance = results.get("average_distance", 255) # Default to a high distance if not found
        fitness += (255 - avg_distance) * 0.5 # Reward for staying close

        # Policy 5: Perfect Win Bonus
        if results["fight_history"] == [1, 1]:
            fitness += 500 # Add a significant bonus for a flawless 2-round victory

        print(f"Individual {individual_id} Fitness Score: {fitness}")
        return fitness

    except FileNotFoundError:
        print(f"Error: Results file '{RESULTS_FILE}' not found. Controller may have failed.")
        return -9999 # Return a very low fitness score on error
    except Exception as e:
        print(f"An error occurred during fitness calculation: {e}")
        return -9999


def selection(population, fitness_scores):
    """Selects the top 20% of the population to be parents for the next generation."""
    sorted_indices = np.argsort(fitness_scores)[::-1] # Sort from highest to lowest
    num_parents = POPULATION_SIZE // 5
    parents = [population[i] for i in sorted_indices[:num_parents]]
    print(f"Selected top {len(parents)} individuals as parents.")
    return parents

def crossover(parents):
    """Creates a new population by breeding the selected parents."""
    offspring_population = []
    
    # Keep the best individual (elitism)
    offspring_population.append(parents[0]) 
    
    while len(offspring_population) < POPULATION_SIZE:
        p1, p2 = np.random.choice(parents, 2, replace=False)
        
        child1_ann, child2_ann = ANN(), ANN()
        child1_weights, child2_weights = [], []

        # Get weights from parents
        p1_weights = p1.get_weights()
        p2_weights = p2.get_weights()

        # Perform crossover for each layer's weights
        for p1_layer, p2_layer in zip(p1_weights, p2_weights):
            split_point = np.random.randint(0, p1_layer.flatten().shape[0])
            
            c1_flat = np.concatenate((p1_layer.flatten()[:split_point], p2_layer.flatten()[split_point:]))
            c2_flat = np.concatenate((p2_layer.flatten()[:split_point], p1_layer.flatten()[split_point:]))
            
            child1_weights.append(c1_flat.reshape(p1_layer.shape))
            child2_weights.append(c2_flat.reshape(p2_layer.shape))

        child1_ann.set_weights(child1_weights)
        child2_ann.set_weights(child2_weights)
        
        offspring_population.append(child1_ann)
        if len(offspring_population) < POPULATION_SIZE:
            offspring_population.append(child2_ann)
            
    print(f"Created {len(offspring_population)} offspring via crossover.")
    return offspring_population

def mutation(population, mutation_rate=0.05, mutation_strength=0.1):
    """Applies small random changes to the weights of the new population."""
    # Don't mutate the best individual from the previous generation
    for individual in population[1:]: 
        weights = individual.get_weights()
        new_weights = []
        for layer_weights in weights:
            if np.random.rand() < mutation_rate:
                noise = np.random.normal(0, mutation_strength, layer_weights.shape)
                new_weights.append(layer_weights + noise)
            else:
                new_weights.append(layer_weights)
        individual.set_weights(new_weights)
    print("Applied mutation to the new population.")
    return population

# --- Main Training Loop ---
def main():
    if not os.path.exists(BEST_MODELS_DIR):
        os.makedirs(BEST_MODELS_DIR)
    if not os.path.exists(OVERALL_BEST_MODELS_DIR):
        os.makedirs(OVERALL_BEST_MODELS_DIR)
        
    population = create_initial_population()

    overall_best_fitness = -np.inf # Initialize with negative infinity
    overall_best_individual = None

    # Check for previous overall best model
    if os.path.exists(OVERALL_BEST_MODELS_DIR):
        existing_best_models = [f for f in os.listdir(OVERALL_BEST_MODELS_DIR) if f.endswith(".weights.h5")]
        if existing_best_models:
            # Find the model with the highest fitness in its filename
            for model_file in existing_best_models:
                try:
                    # Extract fitness from filename (e.g., overall_best_model_fitness_123.45.weights.h5)
                    fitness_str = model_file.split("fitness_")[1].split(".weights.h5")[0]
                    current_loaded_fitness = float(fitness_str)
                    if current_loaded_fitness > overall_best_fitness:
                        overall_best_fitness = current_loaded_fitness
                        overall_best_individual = ANN() # Create a new ANN object
                        overall_best_individual.load_weights(os.path.join(OVERALL_BEST_MODELS_DIR, model_file))
                        print(f"Loaded previous overall best model with fitness: {overall_best_fitness}")
                except Exception as e:
                    print(f"Warning: Could not parse fitness from filename {model_file}: {e}")

    for gen in range(NUM_GENERATIONS):
        print(f"\n{'='*20} GENERATION {gen + 1}/{NUM_GENERATIONS} {'='*20}")
        
        fitness_scores = []
        for i, individual in enumerate(population):
            fitness = evaluate_fitness(individual, i + 1)
            fitness_scores.append(fitness)
            
        # Find the best individual of the generation
        best_fitness_idx = np.argmax(fitness_scores)
        best_fitness = fitness_scores[best_fitness_idx]
        best_individual = population[best_fitness_idx]
        
        print(f"\nGeneration {gen + 1} Summary:")
        print(f"  - Best Fitness: {best_fitness}")
        print(f"  - Average Fitness: {np.mean(fitness_scores)}")
        
        # Save the best model of the generation
        best_model_path = os.path.join(BEST_MODELS_DIR, f"gen_{gen+1}_best_model.weights.h5")
        best_individual.save_weights(best_model_path)
        print(f"Saved best model of generation to {best_model_path}")

        # Compare with overall best and save if better
        if best_fitness > overall_best_fitness:
            overall_best_fitness = best_fitness
            overall_best_individual = best_individual
            overall_best_model_path = os.path.join(OVERALL_BEST_MODELS_DIR, f"overall_best_model_fitness_{overall_best_fitness:.2f}.weights.h5")
            overall_best_individual.save_weights(overall_best_model_path)
            print(f"New overall best model saved to {overall_best_model_path}")

        # Evolve the next generation
        parents = selection(population, fitness_scores)
        offspring = crossover(parents)
        population = mutation(offspring)

    print("\nTraining complete.")

if __name__ == '__main__':
    main()
