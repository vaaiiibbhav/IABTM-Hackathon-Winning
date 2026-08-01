"""PRAXIS Onboarding Agent CLI — Phase 1 CLI.

Allows local testing of the onboarding interview and intake synthesis.
"""

import sys
import json
from api.agents.interviewer import get_onboarding_question, get_total_steps
from api.agents.intake import create_initial_spec


def main():
    print("====================================================")
    print("  PRAXIS Onboarding Interview CLI Simulator")
    print("====================================================")
    
    answers = []
    total_steps = get_total_steps()

    for step in range(1, total_steps + 1):
        q = get_onboarding_question(step)
        if not q:
            print(f"Error: Question for step {step} not found.")
            sys.exit(1)

        print(f"\n[Step {step}/{total_steps}] {q.question}")
        if q.options:
            print("Options:")
            for i, opt in enumerate(q.options, 1):
                print(f"  {i}. {opt}")
            
            while True:
                choice = input("Select an option (number): ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(q.options):
                        answers.append(q.options[idx])
                        break
                except ValueError:
                    pass
                print("Invalid choice, please select a valid option number.")
        else:
            # Free-text input
            while True:
                ans = input("Your answer: ").strip()
                if ans:
                    answers.append(ans)
                    break
                print("Answer cannot be empty.")

    print("\n----------------------------------------------------")
    print("Processing interview answers with intake agent...")
    print("----------------------------------------------------")

    try:
        user_id = "usr_cli_test"
        self_spec, aspiration, themes = create_initial_spec(user_id, answers)
        
        print("\n--- SYNTHESIS COMPLETE ---")
        print(f"User ID: {user_id}")
        print("\n[SelfSpec]")
        print(json.dumps(self_spec.model_dump(), indent=2, default=str))
        print("\n[Aspiration]")
        print(json.dumps(aspiration.model_dump(), indent=2, default=str))
        print("\n[Themes]")
        for theme in themes:
            print(json.dumps(theme.model_dump(), indent=2, default=str))
            
    except Exception as e:
        print(f"\nIntake synthesis failed: {e}")
        print("Please check your GEMINI_API_KEY / Ollama connection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
