import os, pandas as pd, streamlit as st
from extract import extract_contact
from openai import OpenAI

# ------------------------------------------------------------------
# Hidden instructions that are ALWAYS sent to GPT‑4o
# ------------------------------------------------------------------
BASE_SYS_PROMPT = (
    "Compose a concise, friendly and professional email to follow-up on a business card exchange. Do not mention the business card or anything extraneous unless otherwise prompted. By default, simply say something like 'Great to meet you. Let's stay in touch.' filling in any personal details included by the user in the appended prompt."
    "• Always greet the recipient by their first name."
    "• Keep emails under 50 words unless instructed otherwise. "
    "• Do NOT mention that you are an AI. "
    "• Do NOT include a subject line in the message body (subject is added seperately).\n"
)


client = OpenAI(api_key=os.getenv("bizcard"))


st.title("Business‑Card Intake Bot")

@st.cache_data(show_spinner=False)
def parse_cards(uploaded_files):
    """Return a DataFrame with extracted contact rows."""
    rows = []
    for i, file in enumerate(uploaded_files, start=1):
        img_bytes = file.read()
        with st.spinner(f"[{i}/{len(uploaded_files)}] Reading {file.name} …"):
            rows.append(extract_contact(img_bytes))
    return pd.DataFrame(rows)

# Nothing else runs unless the user actually picked files
uploaded_files = st.file_uploader(
    "Upload one *or many* business‑card photos",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="card_uploader"          # 👈 unique key solves the error
)


# ────────────────────────────────────────────────────────────────────
# All code below runs ONLY after the user selects at least one file
# ────────────────────────────────────────────────────────────────────
if uploaded_files:
    # -------- 2) write / append CSV, but skip duplicates --------
    df = parse_cards(uploaded_files)

    csv_path = "contacts.csv"
    if os.path.exists(csv_path):
        old_df = pd.read_csv(csv_path)
        new_rows = df[~df["email"].isin(old_df["email"])]      # only brand‑new
    else:
        old_df = pd.DataFrame()
        new_rows = df

    if not new_rows.empty:
        new_rows.to_csv(csv_path, mode="a", index=False,
                        header=old_df.empty)                  # write once
        st.success(f"📄 Added {len(new_rows)} new contact(s) to CSV")
    else:
        st.info("No new contacts to add (all were already in CSV).")


    # 🔸 build an immutable signature for the current batch
    #batch_sig = tuple((f.name, f.size) for f in uploaded_files)

    # 🔸 write to CSV only if this batch hasn’t been saved in this session
    #if st.session_state.get("last_batch_sig") != batch_sig:
    #csv_exists = os.path.exists("contacts.csv")
    #df.to_csv("contacts.csv", mode="a", index=False, header=not csv_exists)
    #st.session_state["last_batch_sig"] = batch_sig        # remember it


    # -------- 3) show batch summary --------
    st.subheader("Batch summary")
    st.dataframe(df)

    # -------- 3) show batch summary --------
    st.subheader("Batch summary")
    st.dataframe(df)

    # -------- 3a) Download full contacts CSV --------
    csv_path = "contacts.csv"
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            st.download_button(
                label="⬇️  Download all contacts as CSV",
                data=f,
                file_name="contacts.csv",
                mime="text/csv"
            )


    # -------- 4) choose contacts FIRST (outside any form) --------
    selected = st.multiselect(
        "Pick contacts to draft follow‑ups for:",
        options=df.index,
        format_func=lambda i: f"{df.loc[i,'name']}  •  {df.loc[i,'email']}"
    )

    # -------- 5) build the form that depends on `selected` --------
    if selected:                                 # only show if something picked
        with st.form("email_form"):
            subject = st.text_input(
                "Email subject",
                value="Great meeting you!"
            )

            user_sys_prompt = st.text_area(
                "Tone / length instructions",
                value="Write a short, professional email follow‑up."
            )

            st.markdown("**Personal note per contact (optional)**")
            personal_notes = {}
            for idx in selected:
                key = f"note_{idx}"
                placeholder = f"Personal note for {df.loc[idx,'name']}…"
                personal_notes[idx] = st.text_input(
                    label="",
                    key=key,
                    placeholder=placeholder
                )

            submitted = st.form_submit_button("Draft in Gmail")
    else:
        personal_notes = {}
        submitted = False


    # -------- 5) create Gmail drafts --------
    if submitted and selected:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import base64
        from email.message import EmailMessage

        creds = Credentials.from_authorized_user_file("token.json")
        gmail = build("gmail", "v1", credentials=creds)

        st.info("Generating drafts…")

        for idx in selected:
            row = df.loc[idx]
            note = personal_notes.get(idx, "").strip()

            user_content = (
                f"Write an email to {row['name']} ({row['organization']}). "
                f"{'Personal note: ' + note if note else ''}"
            )

            # merge hidden + user‑visible prompt
            full_system_prompt = BASE_SYS_PROMPT + user_sys_prompt

            prompt = [
                {"role": "system", "content": full_system_prompt},
                {"role": "user",   "content": user_content}
            ]


            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=prompt,
                temperature=0.7
            )
            body_text = completion.choices[0].message.content.strip()

            msg = EmailMessage()
            msg["To"] = row["email"]
            msg["From"] = "me"
            msg["Subject"] = subject
            msg.set_content(body_text)

            encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            draft = gmail.users().drafts().create(
                userId="me",
                body={"message": {"raw": encoded}}
            ).execute()

            st.success(
                f"Draft created for {row['name']} → Gmail draft ID {draft['id']}"
            )
