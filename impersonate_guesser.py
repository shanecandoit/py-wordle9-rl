import random
from typing import List, Dict, Any, Tuple

# --- Constants ---
WORDLIST_FILE = "wordlist.txt"
NUM_CANDIDATES = 100

def load_wordlist() -> List[str]:
    """Loads the 5-letter wordlist from a file."""
    try:
        with open(WORDLIST_FILE, "r") as f:
            # Filter for 5-letter words just in case the list is mixed
            return [line.strip().lower() for line in f if len(line.strip()) == 5]
    except FileNotFoundError:
        print(f"Error: '{WORDLIST_FILE}' not found. Please create it.")
        return []

def extract_game_knowledge(game: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts all known letter information from a single game's state.
    
    Returns a dictionary with:
    - 'grey_letters': set of letters known to be incorrect.
    - 'yellow_letters': set of letters known to be in the word but in the wrong position.
    - 'green_letters': dict mapping correct letters to a set of their known positions.
    - 'all_known_letters': a combined set of all letters seen so far.
    """
    knowledge = {
        "grey_letters": set(),
        "yellow_letters": set(),
        "green_letters": {},  # e.g., {'a': {0}, 'e': {3}}
    }
    
    guesses = game.get("guesses", [])
    feedback_history = game.get("feedback", [])

    for i, guess in enumerate(guesses):
        feedback = feedback_history[i]
        for j, letter in enumerate(guess):
            if feedback[j] == 'green':
                if letter not in knowledge["green_letters"]:
                    knowledge["green_letters"][letter] = set()
                knowledge["green_letters"][letter].add(j)
            elif feedback[j] == 'yellow':
                knowledge["yellow_letters"].add(letter)
            elif feedback[j] == 'grey':
                knowledge["grey_letters"].add(letter)

    # A letter can be yellow/green and also grey if duplicated (e.g., guess 'apple', target 'paper')
    # True grey letters cannot be in the word at all.
    knowledge["grey_letters"] -= knowledge["yellow_letters"]
    knowledge["grey_letters"] -= set(knowledge["green_letters"].keys())

    knowledge["all_known_letters"] = knowledge["grey_letters"] | knowledge["yellow_letters"] | set(knowledge["green_letters"].keys())

    return knowledge

def is_word_valid_for_game(word: str, knowledge: Dict[str, Any]) -> bool:
    """Checks if a word violates the hard constraints of a single game."""
    # 1. Must not contain any known grey letters.
    if not knowledge["grey_letters"].isdisjoint(word):
        return False
        
    # 2. Must contain all yellow letters.
    if not knowledge["yellow_letters"].issubset(word):
        return False
        
    # 3. Must have all green letters in their correct positions.
    for letter, positions in knowledge["green_letters"].items():
        for pos in positions:
            if word[pos] != letter:
                return False
                
    return True

def build_reasoning_report(analysis_results: List[Dict[str, Any]]) -> str:
    """   Builds a stream-of-consciousness report based on the analysis results.
    
    Returns a string containing the reasoning report.
    """

        # Separate words into categories
    great_guesses = []
    good_guesses = []
    bad_guesses = []

    # Define thresholds. These might need tuning based on actual scores.
    # For this example, let's use relative thresholds.
    if analysis_results:
        max_score = analysis_results[0]["score"]
        min_score = analysis_results[-1]["score"]
        score_range = max_score - min_score if max_score != min_score else 1 # Avoid division by zero

        for result in analysis_results:
            # Normalize score to a 0-1 range
            normalized_score = (result["score"] - min_score) / score_range

            if normalized_score >= 0.8: # Top 20%
                great_guesses.append(result)
            elif normalized_score >= 0.5: # Next 30%
                good_guesses.append(result)
            else: # Bottom 50%
                bad_guesses.append(result)

    print(f"Great Guesses count: {len(great_guesses)}")
    print(f"Good Guesses count: {len(good_guesses)}")
    print(f"Bad Guesses count: {len(bad_guesses)}")

    # Build the stream-of-consciousness report
    report_parts = [
        "Okay, let's think this through like we're playing a game, and we need to pick the best word.",
        "We're looking at what each word tells us and how much it helps us solve the puzzle."
    ]

    report_parts.append("\n---\n## Reasoning Report\n")

    # Reasoning for Great Guesses
    if great_guesses:
        report_parts.append("### Great Guesses\n")
        report_parts.append("These words are excellent for gathering new information and are strong contenders.")
        for result in great_guesses:
            word = result["word"]
            score = result["score"]
            details = result["details"]
            valid_for_n_games = details["valid_for_n_games"]
            total_new_letters = details["total_new_letters"]
            total_reused_grey = details["total_reused_grey"]
            total_reused_yellow = details["total_reused_yellow"]
            total_reused_green = details["total_reused_green"]

            report_parts.append(f"\n**Word: {word}**")
            report_parts.append(f"This word got a **score of {score:.2f}**.")
            
            if valid_for_n_games > 0:
                report_parts.append(f"It's currently valid for **{valid_for_n_games} game(s)**, which is a big plus because it can actually be used right now.")
            else:
                report_parts.append("It's not valid for any specific games right now, but that's okay because we're thinking about general strategy.")
            
            report_parts.append(f"The big win here is it brings in **{total_new_letters} new letters**. That's a lot of fresh information, which is usually a good thing.")
            
            if total_reused_yellow > 0:
                report_parts.append(f"It also smartly reuses **{total_reused_yellow} yellow letters**, meaning we're trying to figure out where some of these known letters finally fit.")
            if total_reused_green > 0:
                report_parts.append(f"And it uses **{total_reused_green} green letters**, meaning it's building on what we already know for sure.")
            if total_reused_grey > 0:
                report_parts.append(f"Crucially, it reused **{total_reused_grey} grey letters**, which is generally bad. We want to avoid using letters we know are wrong.")
            
            report_parts.append("So, this is a very strong choice for moving forward.")

    # Reasoning for Good Guesses
    if good_guesses:
        report_parts.append("\n---\n### Good Guesses\n")
        report_parts.append("These words are decent choices, but they might not give us as much new information or might have a slight drawback.")
        for result in good_guesses:
            word = result["word"]
            score = result["score"]
            details = result["details"]
            valid_for_n_games = details["valid_for_n_games"]
            total_new_letters = details["total_new_letters"]
            total_reused_grey = details["total_reused_grey"]
            total_reused_yellow = details["total_reused_yellow"]
            total_reused_green = details["total_reused_green"]

            report_parts.append(f"\n**Word: {word}**")
            report_parts.append(f"This word scored **{score:.2f}**.")
            
            if valid_for_n_games > 0:
                report_parts.append(f"It's valid for **{valid_for_n_games} game(s)**, so it's a usable word.")
            else:
                report_parts.append("It's not valid for any current games.")

            report_parts.append(f"It introduces **{total_new_letters} new letters**, which is helpful, but maybe not as many as we'd ideally like.")
            
            if total_reused_yellow > 0:
                report_parts.append(f"It incorporates **{total_reused_yellow} yellow letters**, trying to place them correctly.")
            if total_reused_green > 0:
                report_parts.append(f"And it used **{total_reused_green} green letters**. While that helps confirm what we know, it doesn't expand our knowledge as much.")
            if total_reused_grey > 0:
                report_parts.append(f"It reused **{total_reused_grey} grey letters**, which is a bit of a negative. We're spending a guess on letters we know aren't there.")
            
            report_parts.append("Overall, it's a fine choice, just not a top-tier one for exploration.")

    # Reasoning for Bad Guesses
    if bad_guesses:
        report_parts.append("\n---\n### Bad Guesses\n")
        report_parts.append("These words are less ideal choices. They might not give us enough new information, or they might reuse too many letters we already know are wrong.")
        for result in bad_guesses:
            word = result["word"]
            score = result["score"]
            details = result["details"]
            valid_for_n_games = details["valid_for_n_games"]
            total_new_letters = details["total_new_letters"]
            total_reused_grey = details["total_reused_grey"]
            total_reused_yellow = details["total_reused_yellow"]
            total_reused_green = details["total_reused_green"]

            report_parts.append(f"\n**Word: {word}**")
            report_parts.append(f"This word only scored **{score:.2f}**.")
            
            if valid_for_n_games > 0:
                report_parts.append(f"It's valid for **{valid_for_n_games} game(s)**, so we could use it, but there are better options.")
            else:
                report_parts.append("It's not valid for any current games, and it's not bringing enough new to the table.")

            report_parts.append(f"It only introduces **{total_new_letters} new letters**. That's not much bang for our buck in terms of new information.")
            
            if total_reused_yellow > 0:
                report_parts.append(f"It reused **{total_reused_yellow} yellow letters**, but that's not enough to make up for other issues.")
            if total_reused_green > 0:
                report_parts.append(f"And it used **{total_reused_green} green letters**. While confirming, it doesn't help us discover much new.")
            if total_reused_grey > 0:
                report_parts.append(f"The biggest problem: it reused **{total_reused_grey} grey letters**. We know these letters are wrong, so using them again is a wasted guess.")
            
            report_parts.append("This word isn't very efficient for solving our puzzles.")

    report_parts.append("\n---\n### Conclusion\n")
    report_parts.append("Here's a breakdown of the words we considered:")

    report_parts.append("\n#### Great Guesses")
    # for result in great_guesses:
    #     report_parts.append(f"- {result['word']} (Score: {result['score']:.2f})")
    greats = ', '.join([result['word'] for result in great_guesses])
    report_parts.append(f"[{greats}]")

    report_parts.append("\n#### Good Guesses")
    # for result in good_guesses:
    #     report_parts.append(f"- {result['word']} (Score: {result['score']:.2f})")
    goods = ', '.join([result['word'] for result in good_guesses])
    report_parts.append(f"[{goods}]")

    report_parts.append("\n#### Bad Guesses")
        # for result in bad_guesses:
        #     report_parts.append(f"- {result['word']} (Score: {result['score']:.2f})")
    bads = ', '.join([result['word'] for result in bad_guesses])
    report_parts.append(f"[{bads}]")

    reasoning_report = "\n".join(report_parts)
    return reasoning_report


def impersonate_guesser(game_states: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Analyzes 100 candidate words against the current game states to find the best guess.

    Args:
        game_states: A list of dictionaries, each representing one of the 9 Wordle games.

    Returns:
        A sorted list of dictionaries, each containing a candidate word and its analysis,
        and a string representing the reasoning report.
    """
    wordlist = load_wordlist()
    if not wordlist:
        return [], "No wordlist loaded."

    candidate_words = random.sample(wordlist, min(NUM_CANDIDATES, len(wordlist)))

    # Flatten list of all previous guesses for quick lookups
    previously_guessed = {guess for game in game_states for guess in game.get("guesses", [])}

    analysis_results = []

    for word in candidate_words:
        if word in previously_guessed:
            continue

        total_new = 0
        total_reused_grey = 0
        total_reused_yellow = 0
        total_reused_green = 0
        valid_for_games = 0

        word_letters = set(word)

        for game in game_states:
            # Skip scoring for games that are already won
            if game.get("guesses") and game["guesses"][-1] == game["target_word"]:
                continue

            knowledge = extract_game_knowledge(game)

            if is_word_valid_for_game(word, knowledge):
                valid_for_games += 1

            # --- Score the word based on exploration and exploitation ---
            # New letters (Exploration)
            new_letters = word_letters - knowledge["all_known_letters"]
            total_new += len(new_letters)

            # Reused letters (Exploitation / Redundancy)
            total_reused_grey += len(word_letters.intersection(knowledge["grey_letters"]))
            total_reused_yellow += len(word_letters.intersection(knowledge["yellow_letters"]))
            total_reused_green += len(word_letters.intersection(knowledge["green_letters"].keys()))

        # Heuristic score to rank guesses.
        # Higher is better.
        # - Prioritize validity across all games.
        # - Encourage new letters (exploration).
        # - Penalize reusing grey letters heavily.
        score = (valid_for_games * 10) + (total_new * 1.5) - (total_reused_grey * 5)

        analysis_results.append({
            "word": word,
            "score": score,
            "details": {
                "valid_for_n_games": valid_for_games,
                "total_new_letters": total_new,
                "total_reused_grey": total_reused_grey,
                "total_reused_yellow": total_reused_yellow,
                "total_reused_green": total_reused_green,
            }
        })

    # Sort results from best score to worst
    analysis_results.sort(key=lambda x: x["score"], reverse=True)

    # Build a reasoning report based on the analysis results
    reasoning_report = build_reasoning_report(analysis_results)

    return analysis_results, reasoning_report

# Example Usage:
if __name__ == '__main__':
    # Create a mock game state for demonstration
    # This state simulates 2 guesses ('audio', 'trice') across 9 boards.
    # In a real scenario, this would come from the main simulation loop.
    mock_game_states = []
    for i in range(9):
         # Create slightly different target words to get varied feedback
        target = random.choice(['slate', 'crane', 'brick', 'power', 'hasty', 'flame', 'ghost', 'quirk', 'jumbo'])
        
        game = {"target_word": target, "guesses": [], "feedback": []}
        
        # Simulate first guess 'audio'
        guess1 = 'audio'
        feedback1 = ['yellow', 'grey', 'grey', 'grey', 'grey'] # Simplified feedback for demo
        game["guesses"].append(guess1)
        game["feedback"].append(feedback1)

        # Simulate second guess 'trice'
        guess2 = 'trice'
        feedback2 = ['grey', 'yellow', 'yellow', 'green', 'green'] # Simplified feedback for demo
        game["guesses"].append(guess2)
        game["feedback"].append(feedback2)

        mock_game_states.append(game)

    print("--- Running Impersonated Guesser on Mock Game State ---")
    
    # This is the interesting part where we analyze the mock game states
    # Get the list of analyzed potential guesses
    analyzed_guesses, report = impersonate_guesser(mock_game_states)
    
    # Print the top 5 best guesses based on the heuristic score
    print("\nTop 5 Potential Guesses:")
    for result in analyzed_guesses[:5]:
        print(
            f"Word: {result['word']}, "
            f"Score: {result['score']:.2f}, "
            f"Details: {result['details']}"
        )

    print("\nBottom 5 Potential Guesses:")
    for result in analyzed_guesses[-5:]:
        print(
            f"Word: {result['word']}, "
            f"Score: {result['score']:.2f}, "
            f"Details: {result['details']}"
        )
    print("\n--- Reasoning Report ---")
    print(report)
    print("\n--- End of Analysis ---")
