# The ArchitekturBild MVP web app

## Business Requirements

This project is building an Browser App with these Key features:
- A picture is loaded and displayed 
- an external LLM is called for a picture description
- the LLM output is displayed right to the picture
- the system prompt for the LLM call is displayed on to of picture and description
- the system prompt can be edited by the user, the text is saved with a button
- the model can be selected with a dropdown box
- after upload of the picture, save of a changed system prompt or selection of a different model the LLM is called immediately and the description is displayed, picture and description are always in sync, change to one of them triggers change on the other if needed
- all former llm calls are listed in the same design under the current call in chronological order with newest on top
- the llm calls are saved in a database
- the database is postgreSQL
- the calls are persisted and can be recalled after stop and start of the backend
- all future uploaded images are stored in MinIO
- image references are persisted and images are shown in the UI history after backend restart

## Limitations

For the MVP, this will run locally
No full app docker container is required; optional local Docker usage for MinIO is allowed

## Technical Decisions

- NextJS frontend
- Python FastAPI backend, including serving the static NextJS site at /
- Use OpenRouter for the AI calls. An OPENROUTER_API_KEY is in .env in the project root
- Use PostgreSQL for call metadata persistence
- Use MinIO for persistent image object storage and presigned URL delivery
- Start and Stop server scripts for Mac in scripts/

## Starting Point


## Color Scheme

- Accent Yellow: `#ecad0a` - accent lines, highlights
- Blue Primary: `#209dd7` - links, key sections
- Purple Secondary: `#753991` - submit buttons, important actions
- Dark Navy: `#032147` - main headings
- Gray Text: `#888888` - supporting text, labels

## Coding standards

1. Use latest versions of libraries and idiomatic approaches as of today
2. Keep it simple - NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. No extra features - focus on simplicity.
3. Be concise. Keep README minimal. IMPORTANT: no emojis ever
4. When hitting issues, always identify root cause before trying a fix. Do not guess. Prove with evidence, then fix the root cause.

## Working documentation

All documents for planning and executing this project will be in the docs/ directory.
Please review the docs/PLAN.md document before proceeding.