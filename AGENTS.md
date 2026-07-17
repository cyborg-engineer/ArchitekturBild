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
- in the upper search area of the UI there are two wide two-line search inputs with button "suchen" each
- the left input is labeled "Vektor-Suche" and the right input is labeled "Fuzzy-Suche"
- both searches start only when the user clicks the corresponding "suchen" button
- the fuzzy search runs over model, filename, prompt, and description of current call and history
- the fuzzy search ignores upper/lower case
- fuzzy similar matches are included and sorted by relevance
- all fuzzy matches with reasonable relevance are shown
- an empty fuzzy search input shows all entries
- the vector search runs semantically over persisted LLM calls (model, filename, prompt, description)
- vector search results are sorted by semantic relevance in the existing result list
- an empty vector search input shows all entries
- all application artifacts run in Docker containers (frontend, backend, PostgreSQL, MinIO)
- all persisted data is stored in Docker named volumes

## Limitations

For the MVP, this will run locally on one machine
The full stack is started and stopped via Docker Compose

## Technical Decisions

- NextJS frontend
- Python FastAPI backend, including serving the static NextJS site at /
- Use OpenRouter for the AI calls. An OPENROUTER_API_KEY is in .env in the project root
- Use PostgreSQL for call metadata persistence
- Use MinIO for persistent image object storage and presigned URL delivery
- Start and Stop server scripts for Mac in scripts/
- Use frontend-side relevance ranking for local search result ordering
- Use trigram-based fuzzy matching with a fixed MVP relevance threshold
- Extend PostgreSQL with pgvector for semantic retrieval
- Implement backend RAG pipeline for vector search (query embedding, vector similarity, relevance sorting)
- Generate embeddings via OpenRouter and persist one embedding per LLM call
- Use Docker Compose to orchestrate frontend, backend, PostgreSQL (pgvector), and MinIO
- Persist PostgreSQL and MinIO data only through Docker named volumes

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