# Contributing to Life Sciences Research

Thank you for your interest in contributing to Life Sciences Research! This project provides FastMCP wrappers for essential life sciences APIs to accelerate drug discovery and biomedical research.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/graphiti-org/lifesciences-research.git
cd lifesciences-research
```

2. Install dependencies:
```bash
uv sync --extra dev
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys (optional for most servers)
```

4. Run tests to verify setup:
```bash
uv run pytest tests/ -m "not integration" -v
```

## Development Workflow

### Adding a New MCP Server

We follow a specification-driven development process using the SpecKit workflow:

1. Create a specification using `/speckit.specify`
2. Generate implementation plan with `/speckit.plan`
3. Create tasks with `/speckit.tasks`
4. Implement using `/speckit.implement`

See `docs/speckit-standard-prompt.md` for the standard template.

### Code Style

We use:
- `ruff` for linting and formatting
- `pyright` for type checking

Run before committing:
```bash
uv run ruff check --fix . && uv run ruff format .
uv run pyright
```

### Testing

We have three types of tests:

1. **Unit tests** (no external dependencies):
```bash
uv run pytest tests/ -m "not integration" -v
```

2. **Integration tests** (require API access):
```bash
uv run pytest tests/integration/ -m integration -v
```

3. **End-to-end tests**:
```bash
uv run pytest tests/e2e/ -m e2e -v
```

### Architecture Patterns

All MCP servers follow these patterns:

1. **Fuzzy-to-Fact Protocol**
   - Fuzzy search tools return `SearchCandidate` objects
   - Strict lookup tools require CURIE identifiers

2. **Agentic Biolink Schema**
   - Flattened JSON responses
   - Cross-references in dedicated object
   - CURIE-based identifiers

3. **Error Handling**
   - Use `ErrorEnvelope` for all errors
   - Provide actionable recovery hints
   - Standard error codes (see ADR-001)

4. **Pagination**
   - Use `PaginationEnvelope` for list responses
   - Support cursor-based pagination
   - Default page size: 50

See `docs/adr/accepted/adr-001-v1.2.md` for complete architecture specification.

## Pull Request Process

1. Create a feature branch:
```bash
git switch -c feature/<id>-<description>
```

2. Make your changes following the code style and patterns

3. Add tests for new functionality

4. Ensure all tests pass:
```bash
uv run pytest tests/ -v
```

5. Update documentation if needed

6. Submit a pull request with:
   - Clear description of changes
   - Reference to related issues
   - Test results

## API Coverage

Current MCP servers (12 operational):

**Tier 0 - Drug Discovery Core:**
- ChEMBL, Open Targets, DrugBank (blocked - needs API key)

**Tier 1 - Gene/Protein Foundation:**
- HGNC, UniProt, STRING, BioGRID

**Tier 2 - Pharmacology:**
- IUPHAR/GtoPdb, PubChem

**Tier 3 - Pathways & Trials:**
- WikiPathways, ClinicalTrials.gov

**Tier 4 - Genomics:**
- Ensembl, Entrez

See `docs/adr/accepted/adr-001-v1.2.md` for API tier definitions.

## Adding API Keys

Some APIs require authentication. Add keys to `.env`:

```bash
BIOGRID_API_KEY=your_key_here          # BioGRID (free)
DRUGBANK_API_KEY=your_key_here         # DrugBank (commercial)
NCBI_API_KEY=your_key_here             # Entrez (free, optional)
```

Never commit `.env` files or API keys to the repository.

## Documentation

- `CLAUDE.md` - Project-specific instructions for Claude Code
- `README.md` - User-facing documentation
- `docs/adr/` - Architecture Decision Records
- `specs/` - Feature specifications

## Questions?

- Open an issue for bugs or feature requests
- Check existing ADRs for architectural guidance
- Review `docs/platform-engineering-rationale.md` for design philosophy

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
