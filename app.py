import streamlit as st
import pandas as pd
import plotly.express as px
from database import load_collection, save_collection, save_record
from agents import run_candidate_assessment, generate_interview_kit, workforce_insights, hr_copilot_answer
from utils import load_demo_candidates, parse_skills, SKILL_LIBRARY, extract_uploaded_text
from ai_agents import gemini_status, ai_extract_resume

st.set_page_config(page_title="TalentOS AI", page_icon="🧭", layout="wide")

st.markdown("""
<style>
.stApp{background:#0b1020;color:#eef2ff}
[data-testid="stSidebar"]{background:#10182b;border-right:1px solid #263653}
.block-container{padding-top:1.5rem;max-width:1450px}
.hero{padding:24px 28px;border:1px solid #263653;border-radius:20px;background:linear-gradient(120deg,#162541,#111a30 60%,#241b45);margin-bottom:18px}
.eyebrow{text-transform:uppercase;letter-spacing:2px;color:#a5b4fc;font-size:11px;font-weight:800}
.hero h1{font-size:36px;line-height:1.1;margin:8px 0;color:#f8fafc}
.muted{color:#9aa9c4}
.kpi{border:1px solid #263653;background:#121c31;padding:17px;border-radius:16px;min-height:108px}
.kpi-label{font-size:12px;color:#9aa9c4}
.kpi-value{font-size:27px;font-weight:800;color:#f8fafc;margin-top:7px}
div[data-testid="stMetric"]{background:#121c31;border:1px solid #263653;padding:14px;border-radius:14px}
</style>
""", unsafe_allow_html=True)

# Restore persisted data when the Streamlit session starts.
_saved_candidates = load_collection("candidates")
_saved_assessments = load_collection("assessments")
_saved_decisions = load_collection("decisions")
_saved_kits = load_collection("interview_kits")

if "candidates" not in st.session_state:
    if _saved_candidates:
        st.session_state.candidates = pd.DataFrame(list(_saved_candidates.values())).fillna("")
    else:
        st.session_state.candidates = load_demo_candidates()
        save_collection(
            "candidates",
            {
                str(row["Candidate_ID"]): row
                for row in st.session_state.candidates.to_dict("records")
            },
        )

if "assessments" not in st.session_state:
    st.session_state.assessments = _saved_assessments
if "decisions" not in st.session_state:
    st.session_state.decisions = _saved_decisions
if "interview_kits" not in st.session_state:
    st.session_state.interview_kits = _saved_kits
if "assessments" not in st.session_state: st.session_state.assessments = {}
if "decisions" not in st.session_state: st.session_state.decisions = {}
if "interview_kits" not in st.session_state: st.session_state.interview_kits = {}

with st.sidebar:
    st.markdown("## 🧭 TalentOS **AI**")
    st.caption("Talent Intelligence Platform")
    st.divider()
    page = st.radio("WORKSPACE", ["Executive Overview", "Talent Matching", "Interview Studio", "Workforce Intelligence", "HR Copilot"])
    st.divider()
    st.caption("AI-assisted recommendations · Human-reviewed decisions")
    if gemini_status():
        st.success("Gemini API key detected")
    else:
        st.warning("Gemini not configured · Demo mode")
    st.caption("Prototype v0.2")

def hero(title, subtitle, tag="TALENT INTELLIGENCE"):
    st.markdown(f'<div class="hero"><div class="eyebrow">{tag}</div><h1>{title}</h1><div class="muted">{subtitle}</div></div>', unsafe_allow_html=True)

def kpi(label, value, note):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="muted" style="font-size:11px;margin-top:5px">{note}</div></div>', unsafe_allow_html=True)

if page == "Executive Overview":
    hero("Make talent decisions with more context.", "A multi-agent workspace for skills-based hiring, interview planning and workforce insights.")
    df = st.session_state.candidates
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("CANDIDATE PROFILES", len(df), "In the current workspace")
    with c2: kpi("ASSESSED", len(st.session_state.assessments), "Profiles assessed against a role")
    with c3: kpi("INTERVIEW KITS", len(st.session_state.interview_kits), "Generated this session")
    with c4: kpi("HUMAN REVIEWS", len(st.session_state.decisions), "Review actions recorded")
    # Recruiter decision analytics
    decisions = st.session_state.get("decisions", {})
    decision_rows = []

    for candidate_name, decision_info in decisions.items():
        decision_rows.append({
            "Candidate": candidate_name,
            "Role": decision_info.get("role", ""),
            "Recruiter decision": decision_info.get("decision", "Not reviewed"),
            "Recruiter notes": decision_info.get("note", ""),
        })

    decision_df = pd.DataFrame(decision_rows)

    st.subheader("Recruiter decision analytics")
    reviewed = len(decision_df)
    invited = (
        int((decision_df["Recruiter decision"] == "Invite to interview").sum())
        if not decision_df.empty else 0
    )
    more_info = (
        int((decision_df["Recruiter decision"] == "Request more information").sum())
        if not decision_df.empty else 0
    )
    not_progressing = (
        int((decision_df["Recruiter decision"] == "Do not progress").sum())
        if not decision_df.empty else 0
    )
    awaiting = max(len(st.session_state.get("last_results", [])) - reviewed, 0)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        kpi("INVITED TO INTERVIEW", invited, "Recruiter-recorded decisions")
    with d2:
        kpi("MORE INFORMATION", more_info, "Additional evidence requested")
    with d3:
        kpi("NOT PROGRESSING", not_progressing, "Recruiter-recorded decisions")
    with d4:
        kpi("AWAITING REVIEW", awaiting, "From the latest assessment results")

    if not decision_df.empty:
        chart_counts = (
            decision_df["Recruiter decision"]
            .value_counts()
            .rename_axis("Decision")
            .reset_index(name="Candidates")
        )
        decision_fig = px.bar(
            chart_counts,
            x="Decision",
            y="Candidates",
            color="Decision",
            template="plotly_dark",
        )
        decision_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=10, r=10, t=20, b=10),
            height=280,
        )
        st.plotly_chart(decision_fig, use_container_width=True)
        st.dataframe(decision_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recruiter decisions recorded yet. Run an assessment in Talent Matching and save a review to populate this section.")

    # Export available assessment and decision data
    assessments = st.session_state.get("assessments", {})
    export_rows = []
    for candidate_name, result in assessments.items():
        decision_info = decisions.get(candidate_name, {})
        export_rows.append({
            "Candidate": candidate_name,
            "Role": result.get("role", decision_info.get("role", "")),
            "Skills overlap (%)": result.get("fit_score", ""),
            "Evidence strength": result.get("evidence_strength", ""),
            "Matched skills": ", ".join(result.get("matched_skills", [])),
            "Skills to verify": ", ".join(result.get("missing_skills", [])),
            "Recruiter decision": decision_info.get("decision", "Not reviewed"),
            "Recruiter notes": decision_info.get("note", ""),
        })

    if export_rows:
        export_df = pd.DataFrame(export_rows)
        st.download_button(
            "Download assessment and review report (CSV)",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="talentosai_assessment_report.csv",
            mime="text/csv",
        )
        st.caption("The report combines recorded assessment evidence with human review decisions. Skill overlap is not a prediction of job performance.")

    left,right = st.columns([1.4,1])
    with left:
        st.subheader("Talent pipeline")
        counts = df["Stage"].value_counts().rename_axis("Stage").reset_index(name="Candidates")
        fig = px.bar(counts, x="Stage", y="Candidates", color="Stage", template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",showlegend=False,margin=dict(l=10,r=10,t=20,b=10),height=300)
        st.plotly_chart(fig,use_container_width=True)
    with right:
        st.subheader("Your AI workspace")
        st.markdown("**Talent Matching** — skills evidence and gaps\n\n**Interview Studio** — structured questions and rubrics\n\n**Workforce Intelligence** — capacity and capability signals\n\n**HR Copilot** — explainable workflow guidance")
        st.info("Start with Talent Matching to run the assessment workflow.")
    st.subheader("Candidate workspace")
    st.dataframe(df[["Candidate_ID","Name","Current_Role","Experience_Years","Stage","Location"]],use_container_width=True,hide_index=True)
    with st.expander("Import candidate profiles from CSV"):
        st.caption("Required columns: Name and Resume_Text. Other fields are optional.")
        uploaded=st.file_uploader("Candidate CSV",type=["csv"],key="candidate_csv")
        if uploaded:
            new_df=pd.read_csv(uploaded)
            if not {"Name","Resume_Text"}.issubset(new_df.columns):
                st.error("CSV must include Name and Resume_Text.")
            else:
                if "Candidate_ID" not in new_df: new_df["Candidate_ID"]=[f"USR-{i+1:03d}" for i in range(len(new_df))]
                for col,default in [("Current_Role","Candidate"),("Experience_Years",0),("Stage","New"),("Location","Not specified")]:
                    if col not in new_df: new_df[col]=default
                st.session_state.candidates=new_df.fillna("")
                st.success(f"Loaded {len(new_df)} profiles. Reopen this page to refresh the overview.")

elif page == "Talent Matching":
    hero("Talent matching, with evidence.", "Specialist agents identify job-related skills, compare role requirements, and surface areas for human verification.", "RECRUITMENT WORKFLOW")
    df=st.session_state.candidates
    role=st.text_input("Role title","Business Analyst")

    st.markdown("### Upload job description")
    jd_file = st.file_uploader(
        "Job description (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        key="jd_upload"
    )
    if jd_file is not None:
        try:
            st.session_state["uploaded_jd_text"] = extract_uploaded_text(jd_file)
            st.success(f"Loaded job description: {jd_file.name}")
        except Exception as e:
            st.error(f"Could not read job description: {e}")

    st.markdown("### Upload candidate resumes")
    resume_files = st.file_uploader(
        "Upload resumes (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="resume_uploads"
    )

    if "processed_resume_names" not in st.session_state:
        st.session_state.processed_resume_names = set()

    if "resume_extraction_done" not in st.session_state:
        st.session_state.resume_extraction_done = set()

    for resume_file in resume_files or []:
        resume_key = f"{resume_file.name}:{resume_file.size}"
        if resume_key in st.session_state.resume_extraction_done:
            continue
        try:
            resume_text = extract_uploaded_text(resume_file)
            filename_name = resume_file.name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip()
            details = {}
            if gemini_status():
                with st.spinner(f"Extracting resume details: {resume_file.name}"):
                    try:
                        details = ai_extract_resume(resume_text)
                    except Exception as exc:
                        st.warning(f"AI extraction failed; retaining resume text. Details: {exc}")
            name = str(details.get("name") or filename_name).strip()
            if not name or name.lower() == "unknown":
                name = filename_name
            existing = st.session_state.candidates
            if name in existing["Name"].astype(str).tolist():
                name = f"{name} (Uploaded)"
            try:
                experience = max(0, float(details.get("experience_years", 0) or 0))
            except (ValueError, TypeError):
                experience = 0
            skills = details.get("skills", [])
            education = details.get("education", [])
            if isinstance(skills, list):
                skills = ", ".join(str(x) for x in skills)
            if isinstance(education, list):
                education = ", ".join(str(x) for x in education)
            candidate = {
                "Candidate_ID": f"UP-{len(existing) + 1:03d}",
                "Name": name,
                "Current_Role": str(details.get("current_role") or "Not specified"),
                "Experience_Years": experience,
                "Stage": "New",
                "Location": "Not specified",
                "Resume_Text": resume_text,
                "Skills": skills,
                "Education": education,
                "Summary": str(details.get("summary") or ""),
            }
            st.session_state.candidates = pd.concat(
                [existing, pd.DataFrame([candidate])], ignore_index=True
            ).fillna("")
            save_collection(
                "candidates",
                {
                    str(row["Candidate_ID"]): row
                    for row in st.session_state.candidates.to_dict("records")
                },
            )
            st.session_state.resume_extraction_done.add(resume_key)
            st.success(f"Added {name} with " + ("AI-extracted details." if details else "resume text retained; AI extraction unavailable."))
        except Exception as exc:
            st.error(f"Could not process {resume_file.name}: {exc}")


    df = st.session_state.candidates

    jd=st.text_area(
        "Job description / required skills",
        value=st.session_state.get(
            "uploaded_jd_text",
            "Required: SQL, Excel, Power BI, stakeholder communication, problem solving. Preferred: Python, dashboarding, business analysis."
        ),
        height=150,
        key="talentos_jd"
    )
    required=parse_skills(jd)
    st.caption("Skills detected: "+(", ".join(required) if required else "Add specific skills such as SQL, Excel, Python or Power BI."))
    selected=st.multiselect("Candidates to assess",df["Name"].tolist(),default=df["Name"].tolist()[:min(5,len(df))])
    use_gemini = st.toggle("Enhance candidate evidence summaries with Gemini", value=gemini_status(), disabled=not gemini_status(), help="Deterministic skill matching remains visible; Gemini adds a narrative review.")
    if st.button("Run talent assessment",type="primary",use_container_width=True):
        if not required: st.error("Add recognizable, job-related skills to the job description.")
        elif not selected: st.warning("Select at least one candidate.")
        else:
            results=[]
            progress=st.progress(0)
            for i,name in enumerate(selected):
                row=df[df["Name"]==name].iloc[0]
                result=run_candidate_assessment(row.to_dict(),role,jd,required,use_ai=use_gemini)
                st.session_state.assessments[name]=result
                save_record("assessments", name, result)
                results.append(result)
                progress.progress((i+1)/len(selected))
            st.session_state.last_results=results
            st.session_state.last_role=role
            st.success(f"Assessment completed for {len(results)} candidate(s).")
    results=st.session_state.get("last_results",[])
    if results:
        ranked = sorted(results, key=lambda r: r["fit_score"], reverse=True)
        table = pd.DataFrame([
            {
                "Rank": i,
                "Candidate": r["name"],
                "Job-related text coverage": f'{r["fit_score"]}%',
                "Evidence strength": r["evidence_strength"],
                "Matched skills": ", ".join(r["matched_skills"]),
                "Skills to verify": ", ".join(r["missing_skills"]),
            }
            for i, r in enumerate(ranked, start=1)
        ])
        st.subheader("Ranked assessment results")
        st.dataframe(table, width="stretch", hide_index=True)
        st.download_button(
            "Download ranked assessments (CSV)",
            data=table.to_csv(index=False).encode("utf-8"),
            file_name="talentosai_ranked_assessments.csv",
            mime="text/csv",
        )
        st.caption("Skills overlap is a text-based indicator, not a probability of job performance or an automated hiring decision.")
        for r in sorted(results,key=lambda x:x["fit_score"],reverse=True):
            with st.expander(f'{r["name"]} · {r["fit_score"]}% skills overlap'):
                a,b=st.columns([1,2])
                with a:
                    st.metric("Skills overlap",f'{r["fit_score"]}%')
                    st.progress(r["fit_score"]/100)
                    st.write("**Detected:**",", ".join(r["matched_skills"]) or "None detected")
                    st.write("**To verify:**",", ".join(r["missing_skills"]) or "No missing listed skills")
                with b:
                    st.write("**Evidence summary**")
                    st.write(r["evidence_summary"])
                    st.write("**Suggested follow-up**")
                    st.write(r["follow_up"])
                    if r.get("ai_enhanced"):
                        st.divider()
                        st.write("**Gemini Resume Intelligence review**")
                        st.markdown(r.get("ai_review", ""))
                    elif r.get("ai_error"):
                        st.warning("Gemini enhancement failed: " + r["ai_error"])
                decision=st.selectbox("Human review",["Not reviewed","Invite to interview","Request more information","Do not progress"],key=f"decision_{r['name']}")
                note=st.text_input("Review note (optional)",key=f"note_{r['name']}")
                if st.button("Save review",key=f"save_{r['name']}"):
                    st.session_state.decisions[r["name"]]={"decision":decision,"note":note,"role":r["role"]}
                    save_record("decisions", r["name"], st.session_state.decisions[r["name"]])
                    st.success("Review decision saved for this session.")

elif page == "Interview Studio":
    hero("Build structured, consistent interviews.", "Generate competency-linked questions, strong-answer indicators and follow-up probes.", "INTERVIEW DESIGN")
    role=st.text_input("Role","Marketing Analyst")
    skills=st.text_input("Competencies (comma-separated)","data analysis, communication, problem solving, stakeholder management")
    level=st.selectbox("Seniority",["Entry level","Mid-level","Senior"])
    use_gemini = st.toggle("Generate questions with Gemini", value=gemini_status(), disabled=not gemini_status())
    if st.button("Generate interview kit",type="primary"):

        kit=generate_interview_kit(role,skills,level,use_ai=use_gemini)
        st.session_state.interview_kits[f"{role} · {level}"]=kit
        save_record("interview_kits", f"{role} · {level}", kit)
        st.session_state.current_kit=kit
    kit=st.session_state.get("current_kit")
    if kit:
        for i,q in enumerate(kit,1):
            with st.container(border=True):
                st.markdown(f"**{i}. {q['question']}**")
                st.caption("Competency: "+q["competency"])
                st.write("**Strong answer indicators:** "+q["strong_answer"])
                st.write("**Follow-up probe:** "+q["probe"])
                st.slider("Score (1 = weak, 5 = strong)",1,5,3,key=f"score_{i}")
        st.download_button("Download interview kit (CSV)",pd.DataFrame(kit).to_csv(index=False).encode(),file_name="talentosai_interview_kit.csv",mime="text/csv")

elif page == "Workforce Intelligence":
    hero("Plan capability, not just headcount.", "Explore illustrative workforce data or upload a CSV. Signals support HR review; they are not employee judgments.", "WORKFORCE ANALYTICS")
    sample=pd.DataFrame({"Department":["Sales","Marketing","Technology","Operations","HR","Finance"],"Headcount":[42,24,61,33,12,18],"Open_Roles":[7,4,9,3,1,2],"Critical_Skill_Gaps":[4,3,8,3,1,2],"Training_Hours_Avg":[8,10,12,7,11,8]})
    upload=st.file_uploader("Upload workforce CSV (optional)",type=["csv"],key="workforce_upload")
    wdf=pd.read_csv(upload) if upload else sample
    required_cols={"Department","Headcount","Open_Roles","Critical_Skill_Gaps","Training_Hours_Avg"}
    if required_cols.issubset(wdf.columns):
        a,b,c=st.columns(3)
        a.metric("Total headcount",int(wdf["Headcount"].sum()))
        b.metric("Open roles",int(wdf["Open_Roles"].sum()))
        c.metric("Critical skill gaps",int(wdf["Critical_Skill_Gaps"].sum()))
        fig=px.bar(wdf,x="Department",y=["Open_Roles","Critical_Skill_Gaps"],barmode="group",template="plotly_dark",title="Open roles vs skill gaps")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=360)
        st.plotly_chart(fig,use_container_width=True)
        st.subheader("Workforce Planning Agent")
        for insight in workforce_insights(wdf): st.markdown("- "+insight)
        st.download_button("Download workforce insights (CSV)",pd.DataFrame({"Insight":workforce_insights(wdf)}).to_csv(index=False).encode(),file_name="workforce_insights.csv",mime="text/csv")
    else: st.error("CSV must contain: "+", ".join(sorted(required_cols)))

elif page == "HR Copilot":
    hero("Your HR workflow copilot.", "Ask for guidance on role fit, structured interviews, workforce capability and responsible use.", "HR INTELLIGENCE")
    suggestions=["Explain how the skills-overlap indicator works","What should an interviewer verify before shortlisting?","How can we prioritize workforce skill gaps?","What are the limitations and fairness safeguards?"]
    question=st.selectbox("Suggested question",suggestions)
    custom=st.text_area("Ask a question",question,height=90)
    use_gemini = st.toggle("Use Gemini for a dynamic answer", value=gemini_status(), disabled=not gemini_status())
    if st.button("Ask TalentOS",type="primary"):
        st.markdown(hr_copilot_answer(custom,st.session_state.candidates,st.session_state.assessments,use_ai=use_gemini))
    st.divider()
    st.subheader("Multi-agent architecture")
    st.markdown("""
    - **Resume Intelligence Agent:** detects job-related skill mentions and supporting text.
    - **Role Fit Agent:** compares detected skills with the role requirements.
    - **Interview Design Agent:** generates consistent questions and evaluation anchors.
    - **Workforce Planning Agent:** summarizes capacity and skill-gap signals.
    - **Orchestrator:** routes work and consolidates structured outputs for human review.

    Deterministic Python logic provides reproducible skill evidence and workforce calculations. Gemini can enhance narrative reviews, interview design and HR guidance. Final employment decisions remain with human reviewers.
    """)
