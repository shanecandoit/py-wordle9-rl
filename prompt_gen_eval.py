import json
import csv
import io
import random
import os
from datetime import datetime
from typing import List, Dict, Any

from ollama import Client

# --- Configuration ---
# The model you are evaluating (or your fine-tuned model)
MODEL_TO_EVALUATE = "gemma3:1b" 
OLLAMA_HOST = 'http://localhost:11434'

# Evaluation Parameters
NUM_ROLLOUTS = 10
MAX_GUESSES = 6
NUM_GAMES_PER_ROLLOUT = 9
WORDLIST_FILE = "wordlist.txt"
REPORT_DIR = "prompts"
FINAL_GUESS_MARKER = "Final Guess:"

# Score Calculation
SCORE_WIN = 100
SCORE_GREEN = 5
SCORE_YELLOW = 1

# --- Prompts to Evaluate ---
# Add or modify the prompts you want to test here.
PROMPT_SUGGESTIONS = {
    "prompt_1_baseline": (
        "You are an expert Wordle player. Based on the current game states, generate a single 5-letter word guess. "
        "You are playing nine games of Wordle at the same time.\n"
        "The game state as a csv: \n{game_state_csv}\n"
        "The indicators mean: _r_: r is wrong letter (grey/bad), -s-: s is right letter, wrong spot (yellow/ok), =t=: t is right spot (green/great).\n---\n"
        "First, do some reasoning about each board. Second, do some reasoning about the letters you see. "
        "Third, do some reasoning about the letters you have not seen. Fourth, do some reasoning about the grey and yellow letters specifically. "
        "Finally, make a 5-letter word guess. End your response with 'Final Guess: <your_guess>'."
    ),
    "prompt_1.1_baseline_more_guessing": (
        "You are an expert Wordle player. Based on the current game states, generate a single 5-letter word guess. "
        "You are playing nine games of Wordle at the same time.\n"
        "The game state as a csv: \n{game_state_csv}\n"
        "The indicators mean: _r_: r is wrong letter (grey/bad), -s-: s is right letter, wrong spot (yellow/ok), =t=: t is right spot (green/great).\n---\n"
        "First, do some reasoning about each board. "
        "Second, do some reasoning about the letters you see. "
        "Third, do some reasoning about the letters you have not seen. "
        "Fourth, generate a list of 20 possible words, each with at least 2 new letters. "
        "Finally, make a 5-letter word guess. End your response with 'Final Guess: <your_guess>'."
    ),
    "prompt_1.5_forward_backward": (
        "You are an expert Wordle player. Based on the current game states, generate a single 5-letter word guess. "
        "You are playing nine games of Wordle at the same time.\n"
        "The game state as a csv: \n{game_state_csv}\n"
        "The indicators mean: _r_: r is wrong letter (grey/bad), -s-: s is right letter, wrong spot (yellow/ok), =t=: t is right spot (green/great).\n---\n"
        "First, do some reasoning about each board. "
        "Second, do some reasoning about the letters you see and their positions. "
        "Third, do some reasoning about the letters you have not seen and new words to guess. "
        "Fourth, generate a list of 20 possible words, consider each how many new letters it reveals. "
        "Finally, make a 5-letter word guess. End your response with 'Final Guess: <your_guess>'."
    ),
    "prompt_2_concise": (
        "You are a Wordle solver. Given the CSV of 9 concurrent games, provide the best single 5-letter guess. "
        "The game state is below:\n{game_state_csv}\n"
        "Indicators: _l_ is grey, -l- is yellow, =l= is green.\n"
        "Your goal is to maximize information gain across all boards. Provide only the guess after the marker. "
        "Final Guess: <your_guess>"
    ),
    "prompt_3_persona": (
        "You are a logical deduction engine specializing in word puzzles. Analyze the board states provided in the CSV. "
        "Your sole objective is to output the most informative 5-letter word guess to solve all 9 games.\n"
        "Game State CSV:\n{game_state_csv}\n"
        "Conclude with your final guess. Final Guess: <your_guess>"
    )
}


# --- Initialize Client ---
eval_client = Client(host=OLLAMA_HOST)

# --- Core Wordle Logic (Mostly unchanged) ---
def load_wordlist() -> List[str]:
    with open(WORDLIST_FILE, "r") as file:
        return file.read().splitlines()

def initialize_games() -> List[Dict[str, Any]]:
    words = load_wordlist()
    target_words = random.sample(words, NUM_GAMES_PER_ROLLOUT)
    return [{"target_word": word, "guesses": [], "feedback": []} for word in target_words]

def generate_feedback(guess: str, target_word: str) -> List[str]:
    feedback = [''] * 5; target_list = list(target_word); guess_list = list(guess)
    for i in range(5):
        if guess_list[i] == target_list[i]:
            feedback[i] = "green"; target_list[i] = None; guess_list[i] = None
    for i in range(5):
        if guess_list[i] is not None:
            if guess_list[i] in target_list:
                feedback[i] = "yellow"; target_list[target_list.index(guess_list[i])] = None
            else:
                feedback[i] = "grey"
    return feedback

def format_csv_guess(guess: str, feedback: List[str]) -> str:
    return "".join(f"={l}=" if c=="green" else f"-{l}-" if c=="yellow" else f"_{l}_" for l, c in zip(guess, feedback))

def generate_csv_content(game_states: List[Dict[str, Any]]) -> str:
    headers = [f"Game{i+1}" for i in range(len(game_states))]
    max_guesses = max(len(g["guesses"]) for g in game_states) if game_states else 0
    rows = []
    for i in range(max_guesses):
        row = [format_csv_guess(g["guesses"][i], g["feedback"][i]) if i < len(g["guesses"]) else "" for g in game_states]
        rows.append(row)
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(headers); writer.writerows(rows)
    return output.getvalue()

def is_game_over(game: Dict[str, Any]) -> bool:
    if game["guesses"] and game["guesses"][-1] == game["target_word"]:
        return True
    if len(game["guesses"]) >= MAX_GUESSES:
        return True
    return False

def compile_report(game_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compiles a report of the game states, counting wins, losses, and calculating scores.
    """
    games_won = 0
    games_lost = 0
    total_score = 0

    for game in game_states:
        if game["guesses"] and game["guesses"][-1] == game["target_word"]:
            games_won += 1
            total_score += SCORE_WIN
        else:
            games_lost += 1

        # Calculate scores for green and yellow tiles
        for feedback in game["feedback"]:
            total_score += feedback.count("green") * SCORE_GREEN
            total_score += feedback.count("yellow") * SCORE_YELLOW

    # return
    return {
        "games_won": games_won,
        "games_lost": games_lost,
        "total_score": total_score
    }       

def is_valid_guess(guess: str) -> bool:
    return len(guess) == 5 and guess.isalpha()

# --- Evaluation-Specific Functions ---
def get_agent_guess(prompt: str) -> str:
    """Gets a guess from the model being evaluated."""
    response = eval_client.chat(
        model=MODEL_TO_EVALUATE,
        messages=[{'role': 'user', 'content': prompt}]
    )
    llm_response = response.get("message", {}).get("content", "").strip()
    
    # Extract guess logic
    response_lower = llm_response.lower()
    start_index = response_lower.find(FINAL_GUESS_MARKER.lower())
    if start_index != -1:
        potential_guess = response_lower[start_index + len(FINAL_GUESS_MARKER):].strip()
        for word in potential_guess.split():
            cleaned_word = ''.join(filter(str.isalpha, word))
            if is_valid_guess(cleaned_word):
                return cleaned_word
    
    words = ''.join(c if c.isalpha() else ' ' for c in response_lower).split()
    valid_guesses = [word for word in words if is_valid_guess(word)]
    if valid_guesses:
        return valid_guesses[-1]
        
    return "audio" # Fallback

def run_single_rollout(prompt_template: str) -> (int, List[Dict[str, Any]]):
    """Plays one full 9-board game session and returns the score and final board state."""
    game_states = initialize_games()
    
    for turn in range(MAX_GUESSES):
        if all(is_game_over(g) for g in game_states):
            break
        
        # Create the specific prompt for this turn
        csv_state = generate_csv_content(game_states)
        prompt = prompt_template.format(game_state_csv=csv_state)
        
        guess = get_agent_guess(prompt)
        
        # Apply guess to all non-completed games
        for game in game_states:
            if not is_game_over(game):
                feedback = generate_feedback(guess, game["target_word"])
                game["guesses"].append(guess)
                game["feedback"].append(feedback)
                
    report = compile_report(game_states)
    score = report["games_won"] # Score is the number of games won
    score = report["total_score"]  # Total score based on green and yellow tiles
    return score, game_states

def save_evaluation_report(results: List[Dict]):
    """Saves the complete evaluation results to a single CSV file."""
    if not results:
        print("No results to save.")
        return
        
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = os.path.join(REPORT_DIR, f"evaluation_{timestamp}.csv")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Evaluation report saved to {filename}")

def evaluate_prompts():
    """Main function to orchestrate the prompt evaluation process."""
    all_results = []
    
    for prompt_id, prompt_template in PROMPT_SUGGESTIONS.items():
        print(f"\n--- Evaluating: {prompt_id} ---")
        rollout_scores = []
        rollout_boards = []
        
        for i in range(NUM_ROLLOUTS):
            print(f"Running Rollout {i+1}/{NUM_ROLLOUTS} for {prompt_id}...")
            score, final_boards = run_single_rollout(prompt_template)
            rollout_scores.append(score)
            rollout_boards.append(final_boards)
            print(f"Rollout {i+1} Score (Games Won): {score}/{NUM_GAMES_PER_ROLLOUT}")
            
        average_score = sum(rollout_scores) / len(rollout_scores) if rollout_scores else 0
        
        # Sanitize boards for CSV by converting to JSON string
        boards_json = json.dumps(rollout_boards)
        
        result_data = {
            "timestamp": datetime.now().isoformat(),
            "prompt_id": prompt_id,
            "prompt_text": prompt_template,
            "average_score": f"{average_score:.2f}",
            "individual_scores": str(rollout_scores),
            "rollout_boards_json": boards_json
        }
        all_results.append(result_data)
        
        print(f"--- Results for {prompt_id} ---")
        print(f"Individual Scores: {rollout_scores}")
        print(f"Average Score: {average_score:.2f}")

    save_evaluation_report(all_results)

if __name__ == "__main__":
    evaluate_prompts()
