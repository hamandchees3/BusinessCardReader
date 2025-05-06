Upload photos of business cards, extract name/title/org/contact to a downloadable .csv, draft follow-up emails in bulk with per-contact personalization.
app.py contains a hidden system prompt appended to the email follow-up prompt. Include your name or prefered salutation in the prompt, otherwise it will use [name] placeholders.
Requires OpenAI API key for gpt-4o-mini. Name your key "bizcard".
Requires Google account oauth credentials for email drafting functionality. 
Warning: Vibe-coded in a few hours for a hackathon; not tested on large bulk uploads, though should work. Double-check the batching logic in app.py before attempting large uploads.
