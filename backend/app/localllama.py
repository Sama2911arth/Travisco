from langchain import ChatPromptTemplate, OllamaLLM, StrOutputParser

# Define ChatPromptTemplate with answer pattern
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Just answer about the place asked. Provide the answer in the following pattern: \n name \n1. Brief Description\n2. Key Attractions\n3. Best Time to Visit\n4. Additional Information"),
        ("user", "Question: {question}")
    ]
)

# Initialize the Ollama LLM (make sure you have the model downloaded and available)
llm = OllamaLLM(model="llama3.1")

# Define the output parser
output_parser = StrOutputParser()

# Define the chain (using LangChain's pipeline functionality)
chain = prompt | llm | output_parser

# Function to get response from the chain
def get_response(input_text):
    if input_text:
        response = chain.invoke({"question": input_text})
        return response
    return None

# Example usage
if __name__ == "__main__":
    input_text = "Tell me about Paris."
    response = get_response(input_text)
    if response:
        print(response)