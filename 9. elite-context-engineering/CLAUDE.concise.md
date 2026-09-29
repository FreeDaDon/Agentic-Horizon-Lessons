# Elite Context Engineering

## Context
This project demonstrates proper CLAUDE.md sizing and content practices. We use TypeScript/Node.js with a focus on clean architecture and test-driven development.

## Tooling

- Frontend:
  - Bun
- Backend:
  - Python 3.12
  - Pydantic 2.10.6
  - Poetry 1.9.0
  - pytest 8.3.4
  - ruff 0.9.2

- Always use `bun` over `npm` or `yarn`
- Always use `uv` over `pip` or `poetry`

## Key Commands
- `bun run test` - Run tests before committing
- `bun run lint` - Fix code style issues
- `bun run build` - Production build with type checking
- `uv run pytest` - Run tests

## Project Structure
- `apps/frontend/` - Frontend source code
- `apps/backend/` - Backend source code
- `ai_docs/` - Additional documentation

## Development Guidelines
1. Write tests first (TDD)
2. Use TypeScript strict mode
3. Follow existing naming conventions
4. Add JSDoc for public APIs
5. Keep functions under 50 lines

## Important Notes
- Always validate inputs using Zod schemas
- Use Result<T, E> pattern for error handling
- Database queries go through repository pattern
- API responses use standardized format
- For python types, never use Dict, always use a concrete pydantic model with typed fields
