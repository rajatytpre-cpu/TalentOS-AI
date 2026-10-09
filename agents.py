import re
"""Specialist agents for TalentOS AI, with deterministic fallbacks and optional Gemini support."""
try:
    from ai_agents import ai_candidate_summary, ai_interview_kit, ai_hr_answer, gemini_status
except Exception:
    ai_candidate_summary = ai_interview_kit = ai_hr_answer = None
    def gemini_status(): return False

def run_candidate_assessment(candidate, role, jd, required_skills, use_ai=False):
    """Assess job-related skill coverage with evidence and optional Gemini review."""
    resume = str(candidate.get("Resume_Text", ""))
    profile_fields = [
        resume,
        str(candidate.get("Current_Role", "")),
        str(candidate.get("Skills", "")),
        str(candidate.get("Summary", "")),
        str(candidate.get("Education", "")),
    ]
    text = " ".join(profile_fields).lower()

    # Normalize whitespace and compare whole phrases to reduce accidental matches.
    normalized_text = re.sub(r"\\s+", " ", text)
    found = []
    missing = []
    evidence_by_skill = {}

    for skill in required_skills:
        skill_text = str(skill).strip()
        if not skill_text:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(skill_text.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, normalized_text):
            found.append(skill_text)
            idx = normalized_text.find(skill_text.lower())
            evidence_by_skill[skill_text] = normalized_text[max(0, idx - 60):idx + len(skill_text) + 100].strip()
        else:
            missing.append(skill_text)

    total = len(found) + len(missing)
    score = round(100 * len(found) / total) if total else 0
    evidence = (
        "Strong text coverage" if total and score >= 70
        else "Partial text coverage" if found
        else "Limited text evidence"
    )

    snippets = [
        f"{skill}: \"{evidence_by_skill[skill]}\""
        for skill in found[:5]
    ]
    summary = (
        f"Explicit text match for {len(found)} of {total} listed requirements. "
        + ("Evidence snippets: " + " | ".join(snippets)
           if snippets else
           "No listed requirements were directly detected in the supplied profile.")
    )

    result = {
        "name": str(candidate.get("Name", "Candidate")),
        "role": role,
        "fit_score": score,
        "matched_skills": found,
        "missing_skills": missing,
        "evidence_strength": evidence,
        "evidence_summary": summary,
        "evidence_by_skill": evidence_by_skill,
        "follow_up": (
            "Verify depth of experience with a consistent, job-related interview question or work sample."
            if found else
            "Review the original resume and allow the candidate to clarify relevant transferable skills."
        ),
        "ai_enhanced": False,
        "score_label": "Job-description text coverage (not a hiring recommendation)",
    }

    if use_ai and ai_candidate_summary and gemini_status():
        try:
            result["ai_review"] = ai_candidate_summary(
                candidate, role, jd, found, missing
            )
            result["ai_enhanced"] = True
        except Exception as exc:
            result["ai_error"] = str(exc)

    return result

def generate_interview_kit(role, skills, level, use_ai=False):
    if use_ai and ai_interview_kit and gemini_status():
        try:
            return ai_interview_kit(role, skills, level)
        except Exception as exc:
            # The UI can still use the reliable template-based kit.
            ai_error = str(exc)
    else:
        ai_error = None
    items=[s.strip() for s in skills.split(",") if s.strip()] or ["problem solving","communication"]
    templates=[
      "Tell me about a time you used {skill} to solve a real problem.",
      "Imagine you join as a {role}. How would you use {skill} when information is incomplete?",
      "Describe a challenge while using {skill}. What did you change afterwards?"
    ]
    out=[]
    for i,skill in enumerate(items[:8]):
        out.append({"competency":skill.title(),"question":templates[i%len(templates)].format(skill=skill,role=role),
        "strong_answer":f"A specific example, clear individual contribution, sound reasoning, verifiable outcome and reflection on {skill}.",
        "probe":"Ask about context, the candidate's own actions, evidence of impact, and lessons learned.","rubric":"Score observable evidence from 1 (no relevant example) to 5 (specific example, clear reasoning and verifiable impact)."})
    if ai_error:
        out[0]["ai_error"] = ai_error
    return out

def workforce_insights(df):
    out=[f"There are {int(df['Open_Roles'].sum())} open roles in this illustrative dataset. Validate counts against the current HR system before decisions."]
    if int(df["Critical_Skill_Gaps"].sum()):
        row=df.sort_values("Critical_Skill_Gaps",ascending=False).iloc[0]
        out.append(f"{row['Department']} has the highest recorded skill-gap count ({int(row['Critical_Skill_Gaps'])}). Review criticality, internal mobility and training options before defaulting to external hiring.")
    for _,row in df.iterrows():
        headcount=max(1,int(row["Headcount"]))
        if int(row["Open_Roles"])/headcount>=0.15:
            out.append(f"{row['Department']} has open roles equal to at least 15% of listed headcount; check workload, vacancy age and hiring-plan assumptions.")
    out.append("Suggested next step: combine role criticality, vacancy age, internal mobility and training capacity before allocating budget.")
    return out

def hr_copilot_answer(question, candidates, assessments, use_ai=False):
    if use_ai and ai_hr_answer and gemini_status():
        try:
            return ai_hr_answer(question, candidates, assessments)
        except Exception as exc:
            return "Gemini request failed: " + str(exc) + "\n\nYou can retry, or turn off AI mode to use the built-in guidance."
    q=question.lower()
    if any(word in q for word in ["score","fit","shortlist"]):
        return """### How the skills-overlap indicator works
It measures the proportion of listed job-description skills explicitly detected in the profile text. It is **not** a probability of job performance and does not measure overall merit. Resume wording can hide real capability, so validate through a structured interview or work sample.

**Safeguards:** use the same job-related criteria for everyone, review supporting evidence, allow human override, and never score protected characteristics or sensitive traits."""
    if any(word in q for word in ["workforce","skill gap","training"]):
        return """### Workforce planning approach
1. Confirm business-critical skills and the planning horizon.
2. Compare gaps with verified internal skills.
3. Evaluate training and internal mobility alongside external hiring.
4. Prioritize using role criticality, urgency and cost—not headcount alone.
5. Review with department leaders and measure progress monthly."""
    if any(word in q for word in ["fair","limitation","safeguard"]):
        return """### Limitations and safeguards
- Text matching can miss synonyms and transferable skills.
- Sample workforce data is illustrative, not evidence about a real workforce.
- A fit score is not a hiring decision or validated prediction.
- Do not infer sensitive traits or use protected characteristics.
- Apply consistent criteria, human review, documentation and data minimization."""
    if "interview" in q:
        return """### Structured interview checklist
- Map each question to an essential job competency.
- Ask the same core questions across candidates for the role.
- Use behaviorally anchored scoring criteria.
- Record evidence, not impressions.
- Allow candidates to clarify relevant experience.
- Keep final decisions with trained human reviewers."""
    return "I can help explain skills evidence, design structured interviews, suggest workforce planning steps, and discuss limitations. This starter version uses predefined HR guidance rather than a live LLM; a Gemini integration can be added after the core workflow is tested."
