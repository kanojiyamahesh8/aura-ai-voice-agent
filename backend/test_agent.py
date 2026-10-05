from app.agent import run_agent


if __name__ == "__main__":

    test_questions = [
        "Where is my order ORD-101?",
        "Can I cancel order ORD-103?",
        "Where is my order ORD-999?",
        "Where is my order?"
    ]

    for question in test_questions:

        print("\n" + "=" * 60)
        print("CUSTOMER:")
        print(question)

        answer = run_agent(question)

        print("\nAURA AI:")
        print(answer)