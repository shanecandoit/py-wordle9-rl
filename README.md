
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

## Goal

### Fine Tune with Unsloth

To train a model with Unsloth, you need to generate a dataset of high-quality examples. The goal is to create pairs of (prompt, ideal_response). This process is Supervised Fine-Tuning (SFT). SFT teaches the model by showing it correct input-output pairs.

The standard format for Unsloth is a JSONL file where each line is a JSON object. The ChatML/ShareGPT format is recommended.

ChatML Format Example:

```JSON

{"messages": [{"role": "user", "content": "The Wordle game state prompt..."}, {"role": "assistant", "content": "The ideal reasoning and final guess..."}]}
{"messages": [{"role": "user", "content": "Another Wordle game state prompt..."}, {"role": "assistant", "content": "Another ideal reasoning and final guess..."}]}
```

- user content: The prompt (create_wordle_prompt).
- assistant content: A high-quality, "expert" response that you want the model to learn to emulate.

### Details

The primary challenge is generating the assistant content. Your current code uses the gemma3:1b model to generate a guess. For training, you want a response that is better than what your base model can produce. This is achieved using an oracle. The oracle is a source of high-quality data.

There are two primary methods for generating this oracle data:

1. Use a Stronger LLM: Use a more capable model (e.g., GPT-4, Claude 3 Opus) as the oracle. You would send it the same prompt and save its superior response as the target assistant content for training your smaller model.

2. Use an Algorithm: Develop a deterministic Wordle-solving algorithm to find the optimal guess. You would then use an LLM to generate plausible human-like reasoning that leads to that optimal guess.

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
