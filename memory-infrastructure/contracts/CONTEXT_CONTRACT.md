# Context API Contract

Base path: `/api/context`

- `POST /retrieve?user_id=` → RetrievedContext
- `POST /voice?user_id=` → VoiceContext
- `GET /suggest?entry_id=&user_id=&limit=` → list[ContextSource]
- `POST /preview?user_id=&prompt_template=` → { final_prompt, token_count, sources_used }
