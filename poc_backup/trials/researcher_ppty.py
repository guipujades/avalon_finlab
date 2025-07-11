import requests
import json

class PerplexityAgent:
    """
    A simple AI agent that queries the Perplexity API to
    retrieve concise answers for general questions.
    """

    def __init__(self, api_key: str):
        """
        Initialize the PerplexityAgent with an API key.
        :param api_key: Your Perplexity API key.
        """
        self.api_key = api_key
        # Placeholder endpoint (Please replace with a valid Perplexity endpoint)
        self.endpoint = "https://api.perplexity.ai/placeholder-endpoint"

    def ask_question(self, question: str) -> str:
        """
        Send a question to the Perplexity API and return a concise answer.
        :param question: The question to be answered.
        :return: A concise answer if available, otherwise an error message.
        """
        try:
            # Prepare headers with authentication.
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            # Request payload structure is a placeholder; adjust according to the API.
            payload = {
                "question": question,
                "numResults": 1
            }

            response = requests.post(
                self.endpoint,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.status_code != 200:
                return f"Error: Received status code {response.status_code} from Perplexity API."

            data = response.json()
            # Extracting a concise answer from the response. The actual data structure
            # may differ depending on the Perplexity API.
            answer = data.get("answer", "No answer found.")
            if not answer:
                return "No answer found."

            # Return the answer as a string.
            return answer.strip()
        except requests.exceptions.RequestException as e:
            # Handle request errors (e.g., timeouts, sever errors, etc.)
            return f"An error occurred while contacting the Perplexity API: {e}"