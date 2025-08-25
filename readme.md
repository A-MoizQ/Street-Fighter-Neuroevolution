# Street Fighter Neuroevolution Bot

An automated neuroevolution system that trains AI bots to play Street Fighter II using genetic algorithms and recurrent neural networks. The entire training process runs with zero human interaction, automatically managing emulator instances, game states, and evolutionary processes.

## System Overview

This project implements a complete neuroevolution pipeline that:
- Automatically launches and controls BizHawk emulator instances
- Manages Street Fighter II game sessions through socket communication
- Evolves recurrent neural networks using genetic algorithms
- Evaluates fitness through actual gameplay performance
- Saves and loads the best performing models across generations

## Environment Setup

### Prerequisites
- Python 3.8 or higher
- BizHawk emulator (version 2.3.1 or later)
- Street Fighter II ROM file
- Windows operating system (required for GUI automation)

### Setting Up Python Environment with venv

1. **Navigate to the project directory**:
   ```bash
   cd your_project_directory\Street-Fighter-Neuroevolution\gamebot-competition-master\PythonAPI
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   
   **On Windows:**
   ```bash
   venv\Scripts\activate
   ```
   
   **On macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

### Manual Package Installation (Alternative)

If you don't have a requirements.txt file, install packages manually:
```bash
pip install tensorflow
pip install numpy
pip install pyautogui
pip install pygetwindow
pip install keyboard
```

### Requirements.txt Dependencies
The project requires the following packages:
- `tensorflow>=2.8.0` - Neural network implementation
- `numpy>=1.21.0` - Numerical computations
- `pyautogui>=0.9.54` - GUI automation for emulator control
- `pygetwindow>=0.0.9` - Window management
- `keyboard>=1.13.0` - Keyboard input handling

## Architecture Components

### Core AI Components

#### `ann.py` - Artificial Neural Network
- **Stateful RNN**: Uses TensorFlow/Keras GRU (Gated Recurrent Unit) for temporal decision making
- **Input**: 15-dimensional normalized game state vector
- **Output**: 10 sigmoid activations for combat buttons (U, D, L, R, Y, B, A, X, L, R)
- **Architecture**: Input(15) → GRU(32) → Dense(16) → Output(10)
- **Key Features**:
  - Stateful processing maintains memory between frames
  - Compiled with `@tf.function` for performance
  - Weight management for genetic operations

#### `bot.py` - Game Controller Interface
- **State Translation**: Converts complex game states to normalized ANN inputs
- **Action Translation**: Converts ANN outputs to game button presses
- **Normalization Constants**: Scales all inputs to [0,1] range using observed game data
- **Feature Engineering**: Creates 15 features including:
  - Player health, position, state (jumping/crouching)
  - Opponent health, position, state, move data
  - Relative positioning and health differences
  - Game timer information

### Game Interface Components

#### `controller.py` - Match Management
- **Socket Communication**: Handles TCP communication with emulator on ports 9999/10000
- **State Machine**: Manages character selection, fighting, and match transitions
- **Fitness Tracking**: Records damage dealt/taken, health bonuses, time efficiency
- **Robust Match Detection**: Multiple fallback mechanisms for round/match end detection
- **Automated Character Selection**: Random movement followed by selection

#### `game_state.py` & `player.py` - Data Models
- **JSON Deserialization**: Converts emulator data to Python objects
- **Game State Representation**: Complete game state including both players, timer, match status
- **Player State**: Health, position, movement state, button presses, move data

#### `buttons.py` & `command.py` - Input Management
- **Button Abstraction**: Maps Street Fighter controls to boolean flags
- **Command Serialization**: Converts button states to JSON for emulator communication
- **Multi-player Support**: Handles both P1 and P2 input simultaneously

### Automation Components

#### `auto_gui.py` - GUI Automation
- **Window Management**: Automatically focuses BizHawk emulator window
- **Mouse Control**: Clicks "Gyroscope Bot" to enable network communication
- **Synchronization**: Waits for controller readiness before proceeding
- **Cleanup**: Removes synchronization files after completion

#### `auto_tool.lua` - Emulator Control
- **Emulator Integration**: Lua script runs inside BizHawk emulator
- **Pause Management**: Controls emulator pause/unpause states
- **Toolbox Control**: Automatically opens required emulator tools
- **File Synchronization**: Monitors readiness files for coordination

## Neuroevolution Pipeline

### `evolution.py` - Genetic Algorithm Engine

#### Population Management
- **Initial Population**: Creates 20 randomly initialized RNNs
- **Generational Evolution**: Runs for 500 generations by default
- **Population Size**: Configurable (default: 20 individuals)

#### Fitness Evaluation Process
1. **Individual Testing**: Each RNN plays a complete Street Fighter match
2. **Emulator Launch**: Automatically starts BizHawk with proper configuration
3. **Parallel Processes**: Runs controller and GUI automation simultaneously
4. **Results Collection**: Reads match results from JSON files
5. **Cleanup**: Terminates all processes and cleans up files

#### Fitness Function (Multi-objective)
- **Match Outcome**: ±1000 points for win/loss (primary factor)
- **Damage Efficiency**: +1.5x damage dealt, -2.0x damage taken
- **Health Preservation**: Bonus points for remaining health
- **Time Efficiency**: Bonus for quick victories
- **Aggressiveness**: Rewards staying close to opponent
- **Perfect Victory**: +500 bonus for 2-0 wins

#### Genetic Operations
- **Selection**: Top 20% (4/20) individuals become parents
- **Crossover**: Single-point crossover on flattened weight vectors
- **Mutation**: Gaussian noise (5% rate, 10% strength) applied to weights
- **Elitism**: Best individual always survives to next generation

#### Model Management
- **Generation Best**: Saves best model from each generation
- **Overall Best**: Tracks and saves the best model across all generations
- **Weight Persistence**: Models saved in HDF5 format for reliability

## Automated Workflow

### Zero-Human-Interaction Process

1. **Initialization**
   - Evolution script creates initial population of 20 random RNNs
   - Creates necessary directories for model storage
   - Loads any existing best models from previous runs

2. **Individual Evaluation Loop** (for each of 20 individuals per generation)
   - Saves current individual's weights to `current_weights.weights.h5`
   - Launches BizHawk emulator with specific ROM and save state
   - Starts controller process with socket communication
   - Starts GUI automation for emulator interaction
   - Controller loads ANN weights and signals readiness
   - GUI automation clicks necessary buttons to start match
   - Controller manages character selection and gameplay
   - Match proceeds with RNN making real-time decisions
   - Results automatically saved to `fitness_results.json`
   - All processes terminated and cleaned up

3. **Genetic Evolution**
   - Fitness scores calculated for all 20 individuals
   - Top 4 individuals selected as parents
   - New population created through crossover and mutation
   - Best models saved automatically

4. **Generational Progress**
   - Process repeats for 500 generations
   - Each generation produces improved individuals
   - Best models tracked and saved throughout training

### Synchronization Mechanisms

- **Ready Files**: `controller_ready.txt` coordinates process timing
- **JSON Communication**: Results passed through `fitness_results.json`
- **Socket Protocol**: Real-time game state exchange via TCP
- **Process Management**: Timeout protection and forced cleanup prevent hanging

## File Structure and Data Flow

```
PythonAPI/
├── evolution.py          # Main evolution loop
├── controller.py         # Game session manager
├── bot.py               # AI decision maker
├── ann.py               # Neural network implementation
├── auto_gui.py          # GUI automation
├── auto_tool.lua        # Emulator control script
├── game_state.py        # Game state data model
├── player.py            # Player data model
├── buttons.py           # Input abstraction
├── command.py           # Command serialization
├── current_weights.weights.h5    # Active model weights
├── fitness_results.json          # Match results
├── controller_ready.txt          # Synchronization file
├── best_models/                  # Generation winners
└── best_model_over_all_generations/  # Overall champions
```

## Running the System

### Initial Setup

1. **Configure BizHawk Emulator**:
   - Install BizHawk emulator
   - Place Street Fighter II ROM in accessible location
   - Create a save state at character selection screen (save slot 1)

2. **Update File Paths**:
   Edit `evolution.py` to match your system paths:
   ```python
   bizhawk_path = r"C:\Your\Path\To\BizHawk\EmuHawk.exe"
   rom_path = r"C:\Your\Path\To\StreetFighterII.rom"
   lua = r"C:\Your\Path\To\auto_tool.lua"
   ```
3. **File Path Configuration**:
   - The `auto_tool.lua` script should be placed in the same directory as `evolution.py`
   - By default, the code expects the virtual environment (`venv`) to be located two levels above the `evolution.py` directory
   - If you want to change the virtual environment path to the current directory, you can modify the path in the code or consult with AI assistants for guidance

### Running the Training

1. **Ensure Virtual Environment is Active**:
   ```bash
   # If not already activated
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # macOS/Linux
   ```

2. **Start Evolution Process**:
   ```bash
   python evolution.py
   ```

### What to Expect During Execution

#### Phase 1: Initialization (First 30 seconds)
```
Generation 1/500
Evaluating individual 1/20...
Launching BizHawk emulator...
Starting controller process...
Starting GUI automation...
```

#### Phase 2: Individual Evaluation (2-3 minutes per individual)
```
Controller ready, starting match...
Character selection in progress...
Round 1 starting...
Match completed - Results: Win/Loss, Damage: X/Y, Health: Z
Cleaning up processes...
Individual 1 fitness: 850.5
```

#### Phase 3: Generation Summary (After all 20 individuals)
```
Generation 1 Results:
Best Fitness: 1250.8
Average Fitness: 324.6
Worst Fitness: -890.2
Best model saved to: best_models/generation_1.weights.h5
```

#### Phase 4: Genetic Operations
```
Performing selection and crossover...
Applying mutations...
Creating next generation...
```

### Expected Training Timeline

- **Per Individual**: 2-3 minutes (including emulator startup/shutdown)
- **Per Generation**: 40-60 minutes (20 individuals)
- **Full Training**: 2-4 days (500 generations)

### Monitoring Progress

#### Console Output Indicators
- ✅ **Normal**: Steady progression through individuals and generations
- ⚠️ **Warning**: Occasional emulator crashes (automatically retried)
- ❌ **Error**: Persistent failures may indicate configuration issues

#### Generated Files During Training
```
PythonAPI/
├── current_weights.weights.h5    # Currently evaluating model
├── fitness_results.json          # Latest match results
├── controller_ready.txt          # Process synchronization
├── best_models/
│   ├── generation_1.weights.h5   # Best from each generation
│   ├── generation_2.weights.h5
│   └── ...
└── best_model_over_all_generations/
    └── best_model.weights.h5     # Overall champion
```

### Troubleshooting Common Issues

#### Emulator Won't Start
- Verify BizHawk path in `evolution.py`
- Check ROM file location and format
- Ensure save state exists in slot 1

#### Socket Connection Errors
```
Error: Connection refused on port 9999
```
- Close any running BizHawk instances
- Check Windows firewall settings
- Verify `auto_tool.lua` is properly installed

#### GUI Automation Failures
```
Error: Could not find BizHawk window
```
- Ensure Windows display scaling is 100%
- Run as administrator if needed
- Check pyautogui compatibility with your Windows version

### Early Stopping and Resuming

- **Manual Stop**: Press `Ctrl+C` to gracefully stop after current individual
- **Resume Training**: Best models are automatically saved, but evolution restarts from generation 1
- **Load Specific Model**: Manually copy desired weights file to `current_weights.weights.h5`

### Performance Optimization Tips

1. **Close Unnecessary Programs**: Free up CPU/RAM for faster emulation
2. **Disable Windows Animations**: Improves GUI automation reliability
3. **Use SSD Storage**: Faster emulator loading times
4. **Monitor RAM Usage**: Each emulator instance uses ~200MB

The system is designed to run autonomously, but monitoring the first few individuals ensures proper configuration before leaving it unattended for the full training duration.

## Configuration

### Key Parameters
- `POPULATION_SIZE = 20`: Number of individuals per generation
- `NUM_GENERATIONS = 500`: Total evolution cycles
- `CONTROLLER_PORT = 9999`: Socket communication port
- `SAVE_SLOT_TO_LOAD = 1`: Emulator save state for character selection

### Hardware Requirements
- BizHawk emulator installation
- Street Fighter II ROM file
- Python 3.x with TensorFlow, pyautogui, pygetwindow
- Windows environment (for GUI automation)

## Advanced Features

- **Robust Error Handling**: Multiple fallback mechanisms for match detection
- **Process Cleanup**: Automatic termination prevents resource leaks  
- **Model Persistence**: Reliable saving/loading of neural network weights
- **Performance Optimization**: Compiled TensorFlow graphs for fast inference
- **Parallel Processing**: Simultaneous emulator and automation processes
- **Timeout Protection**: Prevents infinite loops in match scenarios

This system represents a complete automated machine learning pipeline, from raw game interaction to evolved artificial intelligence, requiring zero human supervision during operation.
