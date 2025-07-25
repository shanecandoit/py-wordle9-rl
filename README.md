
# py-wordle9-rl

py-wordle9-rl is a reinforcement learning project that extends the popular word-guessing game, Wordle. This project challenges an AI agent to play nine Wordle games concurrently, providing a single guess across all active boards.

-----

## Features

  - **Nine Simultaneous Games**: Generates and manages nine independent Wordle games at once.
  - **Unified Guessing**: An integrated agent observes all nine game boards but is limited to proposing one word guess applicable to all games. Learn 9x faster?
  - **Standard Wordle Mechanics**: Implements typical Wordle feedback (green for correct letter and position, yellow for correct letter wrong position, grey for incorrect letter).
  - **LLM Integration**: Utilizes **Ollama** for large language model (LLM) reasoning to inform the agent's guessing strategy.
  - **Game Generation**: Randomly selects nine distinct 5-letter words from a standard Wordle wordlist for each game instance.
  - **Automated Scoring**: Scores all nine boards after each guess.
  - **JSONL Reporting**: Outputs detailed game reports in **JSONL** (JSON Lines) format for data analysis.

-----

## Technology Stack

  - **Python**: Core programming language for game logic, agent implementation, and data processing.
  - **Rich TUI**: Provides a rich terminal user interface for displaying game boards and feedback.
  - **Ollama**: Facilitates local large language model inference for the agent's decision-making process.

-----

## How it Works

The project operates in rounds. In each round:

1.  Nine Wordle games are initialized with unique target words.
2.  The agent receives the current state of all nine game boards (guesses made, and tile colors).
3.  The **Ollama**-powered LLM processes this information and generates a single 5-letter word guess.
4.  This guess is applied to all nine active Wordle boards.
5.  Tile feedback (green, yellow, grey) is generated for each of the nine boards based on the single guess.
6.  The game continues for a set number of guesses (typically six, as in standard Wordle).
7.  Upon completion of all games (or max guesses), a comprehensive report is compiled into a JSONL file, detailing the state of each board, guesses made, and final scores.

-----

## Installation

```bash
# Clone the repository
git clone https://github.com/shanecandoit/py-wordle9-rl.git
cd py-wordle9-rl

# Install Python dependencies
pip install -r requirements.txt

# Set up Ollama (ensure Ollama is running and desired models are pulled)
# Refer to Ollama documentation for installation and model setup: https://ollama.ai/
```

-----

## Usage

```bash
# Run the py-wordle9-rl simulation
python main.py
```

-----

## Output

Game results are saved in a `reports/game_<date>_<timestamp>.jsonl` file. Each line in the file represents a single game instance and includes details such as:

  - Game ID
  - Target word
  - Guesses made
  - Tile feedback for each guess
  - Final score
  - Whether the game was won or lost
