# TalentOS AI — AI-powered Talent Intelligence Platform

A Streamlit prototype for an individual assignment on domain-expert AI agents for HR and workforce management.

## What's included
- Executive overview and candidate pipeline
- Candidate CSV import
- Deterministic skills-overlap assessment with transparent supporting evidence
- Optional Gemini-enhanced narrative resume review
- Interview Studio with Gemini-generated structured interview questions and evaluation rubrics (template fallback available)
- Workforce capacity / skill-gap analytics with CSV upload
- HR Copilot with optional live Gemini responses and built-in guidance fallback
- Human review decisions saved for the current session
- CSV exports and responsible-use safeguards

## Run locally on macOS
1. Extract the project ZIP and open the `TalentOS-AI` folder in VS Code.
2. In the VS Code terminal, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

3. Open `.env` in VS Code and replace `PASTE_YOUR_GEMINI_API_KEY_HERE` with your key. Do not add quotes or share the key. Save the file.
4. Start the app:

```bash
streamlit run app.py
```

If Streamlit is already running, stop it with `Control + C` in its terminal and run the command again after adding the key.

## CSV formats
Candidate CSV requires `Name` and `Resume_Text`. Optional columns: `Candidate_ID`, `Current_Role`, `Experience_Years`, `Stage`, `Location`.

Workforce CSV requires `Department`, `Headcount`, `Open_Roles`, `Critical_Skill_Gaps`, `Training_Hours_Avg`.

## Gemini features
The sidebar indicates whether a key was detected. When configured, toggle Gemini on in Talent Matching, Interview Studio, or HR Copilot. The app uses the `google-genai` SDK. The default model is `gemini-2.5-flash`; change `GEMINI_MODEL` in `.env` if your account uses another available model. API access, quota, billing and model availability depend on your Google AI Studio account.

## Important responsible-use limitations
- The skills-overlap percentage is literal text overlap, not a validated prediction of performance or a hiring probability.
- Missing resume keywords do not prove a person lacks a skill.
- Demo workforce data is illustrative.
- Do not use the app to infer protected characteristics or make automated employment decisions. Human review is required.
- Avoid uploading unnecessary personal or sensitive data. Use synthetic/anonymized profiles for demonstrations.
- Keep `.env` private; never commit the real API key to GitHub.
