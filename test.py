import google.generativeai as genai

# Your Gemini API Key
genai.configure(api_key="AIzaSyBczD9mRFEO4izTFA29e-StjjIe0Z2r6vA")

# Load Gemini Model
model = genai.GenerativeModel("gemini-2.5-flash")

print("Type 'exit' to stop\n")

while True:
    question = input("Ask Question: ")

    if question.lower() == "exit":
        break

    response = model.generate_content(question)

    print("\nAI Reply:")
    print(response.text)
    print("\n")