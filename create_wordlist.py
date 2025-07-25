# get common words from a file and create a wordlist
url = "https://raw.githubusercontent.com/kkrypt0nn/wordlists/refs/heads/main/wordlists/discovery/common.txt"
# 417 words in this file

# url = "https://raw.githubusercontent.com/kkrypt0nn/wordlists/refs/heads/main/wordlists/discovery/big.txt"
# how many words in this file? 1773
# too much junk

# just the 5 letter words, all lowercase
# no punctuation, no numbers, no special characters (like _)

import requests

# Fetch the wordlist from the URL
response = requests.get(url)
if response.status_code == 200:
    words = response.text.splitlines()

    # Filter for 5-letter words, all lowercase, no punctuation, numbers, or special characters
    wordlist = [word for word in words if len(word) == 5 and word.isalpha() and word.islower()]

    # Save the filtered wordlist to a file
    with open("wordlist.txt", "w") as file:
        file.write("\n".join(wordlist))

    print(f"Wordlist created with {len(wordlist)} words.")
else:
    print(f"Failed to fetch wordlist. HTTP status code: {response.status_code}")