from src.agent import ask_agent

question = input("Ask BuisnessAgent: ")

answer = ask_agent(question)

print("\nBuisnessAgent:")
print(answer)