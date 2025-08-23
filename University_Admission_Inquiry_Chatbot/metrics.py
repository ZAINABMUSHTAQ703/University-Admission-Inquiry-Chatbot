import json
import os
from pathlib import Path

def analyze_results():
    print("🔍 Starting analysis...")

    try:
        results_dir = Path("results")
        print(f"📂 Checking directory: {results_dir.absolute()}")

        print("\n📄 Directory contents:")
        for f in results_dir.iterdir():
            print(f" - {f.name}")

        evaluation_report = results_dir / "story_report.json"
        print(f"\n🔎 Looking for evaluation report: {evaluation_report}")

        if not evaluation_report.exists():
            raise FileNotFoundError(f"Missing file: {evaluation_report}")

        print("📖 Found evaluation report, loading...")
        with open(evaluation_report) as f:
            data = json.load(f)

        print("\n" + "="*50)
        print("🤖 Rasa Chatbot Performance Summary")
        print("="*50)

        # Overall Accuracy
        accuracy = data.get('accuracy', 0)
        print(f"\n✅ Overall Accuracy: {accuracy*100:.1f}%")

        # Failed Conversations
        if 'conversation_accuracy' in data:
            errors = len(data['conversation_accuracy'].get('error_indices', []))
            print(f"❌ Failed Conversations: {errors}")
        else:
            print("⚠️ No conversation-level data available.")

        # NLU Evaluation
        nlu_path = results_dir / "intent_report.json"
        if nlu_path.exists():
            with open(nlu_path) as f:
                nlu_data = json.load(f)
                f1_score = nlu_data['weighted avg'].get('f1-score', 0)
                print(f"🧠 NLU F1-Score: {f1_score*100:.1f}%")
        else:
            print("⚠️ No NLU report found.")

        print("\n" + "="*50)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting metrics analysis...")
    analyze_results()
    print("✅ Analysis complete")
