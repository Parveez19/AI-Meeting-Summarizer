import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

SUMMARY_PROMPT = (
    "You are an expert business assistant. Given the following meeting notes, "
    "generate a concise summary (3-5 sentences), and then extract action items as a bullet list with responsible persons if mentioned. "
    "If there were any key decisions, list them as a short section after action items.\n\n"
    "Meeting Notes:\n{meeting_text}\n\n"
    "Output:\n"
    "Summary:\n[Your summary here]\n\n"
    "Action Items:\n[Bullet points here]\n\n"
    "Key Decisions:\n[Decisions if any, or 'None stated']\n"
)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        input_text = request.form.get("meeting_notes", "")
        orig_wc = len(input_text.split())
        error = None

        if not input_text.strip():
            error = "Please enter some meeting notes."
            return render_template("index.html", error=error, input_text=input_text)

        prompt = SUMMARY_PROMPT.format(meeting_text=input_text)
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            output = response.text.strip()

            sections = {"summary": "", "action_items": "", "key_decisions": ""}
            # Simple parsing
            if "Summary:" in output:
                split_sum = output.split("Summary:")[1]
                if "Action Items:" in split_sum:
                    sections["summary"], rest = split_sum.split("Action Items:", 1)
                    if "Key Decisions:" in rest:
                        sections["action_items"], sections["key_decisions"] = rest.split("Key Decisions:", 1)
                    else:
                        sections["action_items"] = rest
                else:
                    sections["summary"] = split_sum
            else:
                sections["summary"] = output

            # Word counts and compression
            summary_wc = len(sections["summary"].split())
            compression = f"{(summary_wc/orig_wc*100):.1f}%" if orig_wc > 0 else "--"

            return render_template(
                "results.html",
                summary=sections["summary"].strip(),
                action_items=sections["action_items"].strip(),
                key_decisions=sections["key_decisions"].strip(),
                input_text=input_text,
                orig_wc=orig_wc,
                summary_wc=summary_wc,
                compression=compression,
                error=error
            )
        except Exception as e:
            error = f"Error: {e}"
            return render_template("index.html", error=error, input_text=input_text)

    # GET request
    return render_template("index.html", error=None, input_text="")

if __name__ == "__main__":
    app.run(debug=True)
