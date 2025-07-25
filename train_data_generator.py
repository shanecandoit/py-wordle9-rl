import json
import csv
import io
import random
import os
from datetime import datetime
from typing import List, Dict, Any

from ollama import Client

# --- Configuration ---
# The model that will act as the "expert" to generate training data.
# For best results, use a powerful model (e.g., gpt-4, claude-3-opus).
ORACLE_MODEL_NAME = "gemma3:4b"  # deepseek-r1:8b
OLLAMA_HOST = 'http://localhost:11434'

MAX_GUESSES = 6
NUM_GAMES_PER_RUN = 9 # How many concurrent games to simulate for one data generation run
WORDLIST_FILE = "wordlist.txt"
ORACLE_TRAIN_FOLDER = "train/"
OUTPUT_DATASET_FILE = "wordle_training_data.jsonl"
FINAL_GUESS_MARKER = "Final Guess:"

# --- Initialize Ollama Client ---
# This client will be our "oracle"
oracle_client = Client(host=OLLAMA_HOST)

# --- Core Wordle Logic ---

def load_wordlist() -> List[str]:
    """Load words from the wordlist file."""
    with open(WORDLIST_FILE, "r") as file:
        return file.read().splitlines()

def initialize_games() -> List[Dict[str, Any]]:
    """Initialize nine Wordle games with unique target words."""
    words = load_wordlist()
    target_words = random.sample(words, NUM_GAMES_PER_RUN)
    return [{"target_word": word, "guesses": [], "feedback": []} for word in target_words]

def format_csv_guess(guess: str, feedback: List[str]) -> str:
    """Format a guess for CSV output with feedback indicators."""
    result = ''
    for letter, color in zip(guess, feedback):
        big_letter = letter.upper()
        result += "".join(
            f"={big_letter}=" if color == "green" else
            f"-{big_letter}-" if color == "yellow" else
            f"_{letter}_"
            
        )
    return result

def generate_csv_content(game_states: List[Dict[str, Any]]) -> str:
    """Generate the game progress as a CSV string."""
    headers = [f"Game{i+1}" for i in range(len(game_states))]
    max_guesses = max(len(game["guesses"]) for game in game_states) if game_states else 0
    rows = []
    for guess_index in range(max_guesses):
        row_data = []
        for game in game_states:
            if guess_index < len(game["guesses"]):
                guess = game["guesses"][guess_index]
                feedback = game["feedback"][guess_index]
                formatted_guess = format_csv_guess(guess, feedback)
                row_data.append(formatted_guess)
            else:
                row_data.append("")
        rows.append(row_data)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()

def create_wordle_prompt(game_states: List[Dict[str, Any]]) -> str:
    """Create the prompt for the LLM."""
    state_csv = generate_csv_content(game_states)
    return (
        "You are an expert Wordle player. "
        "Based on the current game states, generate a single 5-letter word guess. "
        "You are playing nine games of Wordle at the same time.\n"
        "The game state as a csv: \n"
        f"{state_csv} \n"
        "The indicators mean: _r_: r is wrong letter (grey/bad), -S-: s is right letter, wrong spot (yellow/ok), =T=: t is right spot (green/great). \n"
        "---\n"
        "First, do some reasoning about each board. "
        "Second, do some reasoning about the letters you see. "
        "Third, do some reasoning about the letters you have not seen. "
        "Fourth, do some reasoning about the grey and yellow letters specifically. "
        "Finally, make a 5-letter word guess. "
        "End your response with 'Final Guess: <your_guess>'."
    )

def generate_feedback(guess: str, target_word: str) -> List[str]:
    """Generate feedback for a guess."""
    feedback = [''] * 5
    target_list = list(target_word)
    guess_list = list(guess)

    # First pass for green letters
    for i in range(5):
        if guess_list[i] == target_list[i]:
            feedback[i] = "green"
            target_list[i] = None  # Mark as used
            guess_list[i] = None   # Mark as used

    # Second pass for yellow and grey letters
    for i in range(5):
        if guess_list[i] is not None:
            if guess_list[i] in target_list:
                feedback[i] = "yellow"
                target_list[target_list.index(guess_list[i])] = None # Mark as used
            else:
                feedback[i] = "grey"
    return feedback

def apply_guess_to_games(guess: str, game_states: List[Dict[str, Any]]):
    """Apply a guess to all games and update their state in place."""
    for game in game_states:
        if len(game["guesses"]) < MAX_GUESSES and game["guesses"] and game["guesses"][-1] != game["target_word"]:
            feedback = generate_feedback(guess, game["target_word"])
            game["guesses"].append(guess)
            game["feedback"].append(feedback)

def is_valid_guess(guess: str) -> bool:
    """Check if a guess is a 5-letter alphabetic word."""
    return len(guess) == 5 and guess.isalpha()

# --- Data Generation Logic ---

def get_oracle_response(prompt: str) -> str:
    """
    Gets a high-quality response from the oracle model.
    *** FOR UNSLOTH TRAINING ***
    Replace this with a call to a more capable model for better results?
    """
    print(f"Querying oracle model: {ORACLE_MODEL_NAME}...")
    response = oracle_client.chat(
        model=ORACLE_MODEL_NAME,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.get("message", {}).get("content", "").strip()

def extract_final_guess(llm_response: str) -> str:
    """Extracts the 5-letter guess from the oracle's full response."""
    response_lower = llm_response.lower().strip()
    start_index = response_lower.find(FINAL_GUESS_MARKER.lower())
    guess_text = response_lower[start_index + len(FINAL_GUESS_MARKER):].strip()
    guess_text = ''.join([ch for ch in guess_text if ch.isalpha() or ch.isspace()])

    if start_index != -1:
        # Extract the word immediately following the marker
        potential_guess = guess_text.strip()
        # Find the first 5-letter word in the remaining string
        for word in potential_guess.split():
            cleaned_word = ''.join([ch for ch in word if ch.isalpha()])
            if is_valid_guess(cleaned_word):
                return cleaned_word
    
    # Fallback: find the last valid 5-letter word in the entire response
    response_no_punctuation_spaces_ok = ''.join([c for c in llm_response if c.isalpha() or c.isspace()]).lower()
    all_words = [''.join(filter(str.isalpha, word)) for word in response_no_punctuation_spaces_ok.split()]
    all_words = [word for word in all_words if len(word) == 5]
    valid_guesses = [word for word in all_words if is_valid_guess(word)]
    if valid_guesses:
        return valid_guesses[-1]
        
    # Final fallback if no valid guess is found
    print("Warning: Oracle did not produce a valid 5-letter guess. Returning 'audio'.")
    common_guesses = ["crane", "slate", "trace", "crate",
                    "stare", "adieu", "audio",
                    "arise", "roast", "raise"]
    return random.choice(common_guesses)

def generate_training_data(num_simulations: int):
    """
    Main function to run simulations and generate training data.
    `num_simulations` is the total number of 9-game sets to run.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # OUTPUT_DATASET_FILE = "wordle_training_data.jsonl"
    timestamp_ext = f"_{timestamp}.jsonl"
    filename = ORACLE_TRAIN_FOLDER + OUTPUT_DATASET_FILE.replace('.jsonl', timestamp_ext )

    # make the "train" dir
    os.makedirs(ORACLE_TRAIN_FOLDER, exist_ok=True)

    # Ensure the output directory exists
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            pass # Create the file if it doesn't exist

    total_examples = 0
    for i in range(num_simulations):
        print(f"\n--- Running Simulation {i+1}/{num_simulations} ---")
        game_states = initialize_games()
        
        # We need a starting guess. Use a common one.
        current_guess = "audio" 
        
        # The game loop now generates data at each step
        for turn in range(MAX_GUESSES):
            print(f"Turn {turn + 1}: Guessing '{current_guess}'")
            
            # Apply the guess to all non-completed games
            for game in game_states:
                 if not (game["guesses"] and game["guesses"][-1] == game["target_word"]):
                    feedback = generate_feedback(current_guess, game["target_word"])
                    game["guesses"].append(current_guess)
                    game["feedback"].append(feedback)

            # 1. Create the prompt based on the new game state
            prompt = create_wordle_prompt(game_states)
            
            # 2. Get the ideal response from the "oracle"
            oracle_full_response = get_oracle_response(prompt)
            
            # 3. Create the training example in ChatML format
            training_example = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": oracle_full_response}
                ]
            }
            
            # 4. Save the example to the JSONL file
            with open(filename, 'a') as f:
                f.write(json.dumps(training_example) + '\n')
            total_examples += 1
            
            # 5. Extract the next guess from the oracle's response to continue the simulation
            current_guess = extract_final_guess(oracle_full_response)
            
            # Check if all games are won
            if all(g["guesses"] and g["guesses"][-1] == g["target_word"] for g in game_states):
                print("All games won. Ending simulation early.")
                break

    print(f"\n--- Data Generation Complete ---")
    print(f"Generated {total_examples} training examples in '{filename}'.")


if __name__ == "__main__":
    # Set how many sets of 9 games you want to simulate to generate data.
    # For example, 100 simulations will play 900 games total.
    # Each turn of each simulation creates one training data point.
    NUMBER_OF_SIMULATIONS = 10
    generate_training_data(NUMBER_OF_SIMULATIONS)
