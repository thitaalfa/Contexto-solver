import aiohttp
import asyncio
import urllib.parse

async def test_word(session, word: str):
    encoded_word = urllib.parse.quote(word)
    #adjust the url /878/ is today's date! check the today's request number and replace 
    url = f"https://api.contexto.me/machado/en/game/878/{encoded_word}"
    headers = {'User-Agent': 'Python Contexto Solver/1.0'}
    
    retries = 3  # Set max retries to 3
    attempt = 0
    while attempt < retries:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        distance = data.get('distance')
                        word_response = data.get('word')

                        print(f"Distance: {distance}, Word: {word_response}")  # Fixed indentation here
                        
                        if isinstance(distance, int):
                            return word_response, distance
                        return None, None  # Invalid distance format

                    except Exception as e:
                        print(f"JSON Error for {word}: {e}")
                        return None, None  # Return None on JSON parsing errors

                elif response.status == 404:
                    print(f"Word not found: {word}")
                    return None, None  # Word not found in the API

                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    attempt += 1
                    continue  # Retry the request after waiting

                else:
                    print(f"HTTP Error {response.status} for {word}")
                    return None, None  # Return None for other errors

        except Exception as e:
            print(f"Request Error for {word}: {e}")
            attempt += 1
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

    print(f"Failed after {retries} attempts: {word}")
    return None, None

async def find_correct_word(dictionary_file):
    try:
        with open(dictionary_file, "r") as file:
            words = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: File {dictionary_file} not found")
        return

    async with aiohttp.ClientSession() as session:
        BATCH_SIZE = 10000  # Adjust batch size to prevent rate-limiting
        for i in range(0, len(words), BATCH_SIZE):
            batch = words[i:i + BATCH_SIZE]
            tasks = [test_word(session, word) for word in batch]
            results = await asyncio.gather(*tasks)
            
            for word, distance in results:
                if distance == 0:
                    print(f"\nSUCCESS! Correct word: {word}")
                    return  # Exit after finding the correct word
            
            print(f"Processed {i + BATCH_SIZE} words...", end='\r')
            await asyncio.sleep(2)  # Slight delay between batches

    print("\nNo correct word found in dictionary.")

if __name__ == "__main__":
    dictionary_file = "dict.txt"
    asyncio.run(find_correct_word(dictionary_file))
