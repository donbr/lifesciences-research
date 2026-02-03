# CQ14 Temporal Workflow Design

**Date**: January 14, 2026
**Purpose**: Codify the CQ14 Fuzzy-to-Fact validation process as a durable Temporal workflow

---

## Background: Lessons from CQ14 Validation

The manual CQ14 validation process revealed several patterns that benefit from durability:

1. **Multi-phase execution**: Anchor → Enrich → Expand → Traverse → Persist
2. **Parallel API calls**: Multiple MCP tools and curl endpoints called concurrently
3. **Validation with subagents**: Independent agents verifying different aspects
4. **Error discovery**: Typo in NCT ID found through validation
5. **Long-running operations**: Some API calls take seconds to complete

These patterns map directly to Temporal workflow primitives.

---

## Proposed Architecture

### 1. Workflow Definition

```python
from datetime import timedelta
from temporalio import workflow
from pydantic_ai.durable_exec.temporal import TemporalAgent, AgentPlugin

@workflow.defn
class CompetencyQuestionWorkflow:
    """Durable workflow for executing competency questions using Fuzzy-to-Fact protocol."""

    @workflow.run
    async def run(self, question_id: str, question_params: dict) -> dict:
        """
        Execute the 5-phase Fuzzy-to-Fact protocol with durability.

        Phases:
        1. Anchor - Resolve fuzzy entity names to canonical CURIEs
        2. Enrich - Decorate nodes with protein/gene metadata
        3. Expand - Build adjacency list from interaction databases
        4. Traverse - Follow edges to druggable targets
        5. Persist - Store validated graph in Graphiti
        """

        # Phase 1: Anchor Node Resolution
        anchor_results = await workflow.execute_activity(
            anchor_activity,
            args=[question_params.get('entities', [])],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=workflow.RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(minutes=1),
                backoff_coefficient=2.0,
                maximum_attempts=3
            )
        )

        # Phase 2: Enrich Nodes (parallel)
        enrich_tasks = [
            workflow.execute_activity(
                enrich_activity,
                args=[curie],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=_default_retry_policy()
            )
            for curie in anchor_results['curies']
        ]
        enrich_results = await asyncio.gather(*enrich_tasks)

        # Phase 3: Expand Edges (parallel across databases)
        expand_tasks = [
            workflow.execute_activity(
                expand_string_activity,
                args=[anchor_results['string_ids']],
                start_to_close_timeout=timedelta(minutes=10)
            ),
            workflow.execute_activity(
                expand_biogrid_activity,
                args=[anchor_results['gene_symbols']],
                start_to_close_timeout=timedelta(minutes=10)
            ),
            workflow.execute_activity(
                expand_chembl_activity,
                args=[anchor_results['chembl_ids']],
                start_to_close_timeout=timedelta(minutes=10)
            )
        ]
        expand_results = await asyncio.gather(*expand_tasks)

        # Phase 4: Target Traversal
        traverse_results = await workflow.execute_activity(
            traverse_activity,
            args=[expand_results],
            start_to_close_timeout=timedelta(minutes=10)
        )

        # Phase 5: Validation (parallel subagents)
        validation_tasks = [
            workflow.execute_activity(
                validate_identifiers_activity,
                args=[anchor_results],
                start_to_close_timeout=timedelta(minutes=5)
            ),
            workflow.execute_activity(
                validate_mechanisms_activity,
                args=[traverse_results['drugs']],
                start_to_close_timeout=timedelta(minutes=5)
            ),
            workflow.execute_activity(
                validate_trials_activity,
                args=[traverse_results['trials']],
                start_to_close_timeout=timedelta(minutes=5)
            ),
            workflow.execute_activity(
                validate_evidence_activity,
                args=[expand_results],
                start_to_close_timeout=timedelta(minutes=5)
            )
        ]
        validation_results = await asyncio.gather(*validation_tasks)

        # Phase 6: Persist to Graphiti
        persist_result = await workflow.execute_activity(
            persist_activity,
            args=[question_id, anchor_results, enrich_results,
                  expand_results, traverse_results, validation_results],
            start_to_close_timeout=timedelta(minutes=5)
        )

        return {
            'question_id': question_id,
            'anchor': anchor_results,
            'enrich': enrich_results,
            'expand': expand_results,
            'traverse': traverse_results,
            'validation': validation_results,
            'persist': persist_result
        }
```

---

### 2. Activity Definitions

Activities are the durable units that interact with external services (MCP tools, APIs).

```python
from temporalio import activity
from pydantic_ai.mcp import MCPServerStreamableHTTP

# MCP Server connections
lifesciences_server = MCPServerStreamableHTTP(
    "http://localhost:8000/lifesciences/",
    id="lifesciences_mcp"
)

@activity.defn
async def anchor_activity(entities: list[str]) -> dict:
    """
    Phase 1: Resolve fuzzy entity names to canonical CURIEs.

    Uses: hgnc_search_genes, hgnc_get_gene, chembl_search_compounds

    Handles MCP failures gracefully - returns partial results with error info.
    """
    results = {
        'curies': [],
        'string_ids': [],
        'gene_symbols': [],
        'chembl_ids': [],
        'errors': []
    }

    for entity in entities:
        try:
            # Try gene resolution first
            gene_result = await mcp_call('hgnc_search_genes', {'query': entity})
            if gene_result['items']:
                top_match = gene_result['items'][0]
                results['curies'].append(top_match['id'])
                results['gene_symbols'].append(top_match['symbol'])

                # Get cross-references for STRING ID
                full_gene = await mcp_call('hgnc_get_gene', {'hgnc_id': top_match['id']})
                if full_gene.get('cross_references', {}).get('ensembl_gene'):
                    results['string_ids'].append(
                        f"STRING:9606.{full_gene['cross_references']['ensembl_gene']}"
                    )
            else:
                # Try compound resolution
                compound_result = await mcp_call('chembl_search_compounds', {'query': entity})
                if compound_result['items']:
                    top_match = compound_result['items'][0]
                    results['curies'].append(top_match['id'])
                    results['chembl_ids'].append(top_match['id'])
        except Exception as e:
            # Log error but continue with other entities
            results['errors'].append({'entity': entity, 'error': str(e)})

    return results


@activity.defn
async def enrich_activity(curie: str) -> dict:
    """
    Phase 2: Enrich a node with detailed metadata.

    Uses: uniprot_get_protein, chembl_get_compound, ensembl_get_gene
    """
    if curie.startswith('HGNC:'):
        gene = await mcp_call('hgnc_get_gene', {'hgnc_id': curie})
        if gene.get('cross_references', {}).get('uniprot'):
            protein = await mcp_call('uniprot_get_protein', {
                'uniprot_id': f"UniProtKB:{gene['cross_references']['uniprot'][0]}"
            })
            return {
                'curie': curie,
                'type': 'gene',
                'symbol': gene['symbol'],
                'name': gene['name'],
                'function': protein.get('function', ''),
                'uniprot': protein.get('accession'),
                'ensembl': gene.get('cross_references', {}).get('ensembl_gene')
            }
    elif curie.startswith('CHEMBL:'):
        compound = await mcp_call('chembl_get_compound', {'chembl_id': curie})
        return {
            'curie': curie,
            'type': 'compound',
            'name': compound['name'],
            'max_phase': compound.get('max_phase'),
            'smiles': compound.get('smiles'),
            'indications': compound.get('indications', [])
        }

    return {'curie': curie, 'type': 'unknown'}


@activity.defn
async def expand_string_activity(string_ids: list[str]) -> list[dict]:
    """
    Phase 3a: Get protein-protein interactions from STRING.

    Uses: string_get_interactions
    """
    results = []
    for string_id in string_ids:
        interactions = await mcp_call('string_get_interactions', {
            'string_id': string_id,
            'required_score': 700,
            'limit': 20
        })
        results.append({
            'source': string_id,
            'interactions': interactions.get('interactions', [])
        })
    return results


@activity.defn
async def expand_biogrid_activity(gene_symbols: list[str]) -> list[dict]:
    """
    Phase 3b: Get genetic interactions from BioGRID.

    Uses: biogrid_get_interactions
    """
    results = []
    for symbol in gene_symbols:
        interactions = await mcp_call('biogrid_get_interactions', {
            'gene_symbol': symbol,
            'organism': 9606,
            'max_results': 100
        })
        # Filter for genetic interactions (synthetic lethality signals)
        genetic = [i for i in interactions.get('interactions', [])
                   if i.get('experimental_system_type') == 'genetic']
        results.append({
            'source': symbol,
            'genetic_interactions': genetic,
            'physical_count': interactions.get('physical_count', 0),
            'genetic_count': interactions.get('genetic_count', 0)
        })
    return results


@activity.defn
async def validate_identifiers_activity(anchor_results: dict) -> dict:
    """
    Validation Agent 1: Cross-validate identifiers across databases.

    Compares HGNC, Ensembl, UniProt cross-references for consistency.
    """
    validation = {'status': 'valid', 'discrepancies': []}

    for curie in anchor_results['curies']:
        if curie.startswith('HGNC:'):
            # Get from HGNC
            hgnc = await mcp_call('hgnc_get_gene', {'hgnc_id': curie})
            ensembl_id = hgnc.get('cross_references', {}).get('ensembl_gene')

            if ensembl_id:
                # Cross-check with Ensembl
                ensembl = await mcp_call('ensembl_get_gene', {'ensembl_id': ensembl_id})

                # Verify HGNC reference matches
                ensembl_hgnc = ensembl.get('cross_references', {}).get('hgnc', '')
                if curie not in ensembl_hgnc:
                    validation['status'] = 'warning'
                    validation['discrepancies'].append({
                        'type': 'hgnc_mismatch',
                        'hgnc': curie,
                        'ensembl_reports': ensembl_hgnc
                    })

    return validation


@activity.defn
async def validate_trials_activity(trials: list[str]) -> dict:
    """
    Validation Agent 3: Verify clinical trial NCT IDs exist.

    This is critical - a single digit error invalidates the reference.
    """
    validation = {'status': 'valid', 'verified': [], 'not_found': []}

    for nct_id in trials:
        try:
            trial = await mcp_call('clinicaltrials_get_trial', {'nct_id': nct_id})
            if trial.get('id'):
                validation['verified'].append({
                    'id': nct_id,
                    'title': trial.get('title'),
                    'status': trial.get('status')
                })
            else:
                validation['status'] = 'error'
                validation['not_found'].append(nct_id)
        except Exception as e:
            validation['status'] = 'error'
            validation['not_found'].append({'id': nct_id, 'error': str(e)})

    return validation
```

---

### 3. Retry Policy Configuration

The key to durability is proper retry configuration:

```python
def _default_retry_policy():
    """
    Default retry policy for MCP activities.

    - Initial interval: 1 second
    - Maximum interval: 1 minute (exponential backoff caps here)
    - Backoff coefficient: 2.0 (doubles each retry)
    - Maximum attempts: 3

    This handles transient MCP failures gracefully.
    """
    return workflow.RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(minutes=1),
        backoff_coefficient=2.0,
        maximum_attempts=3,
        non_retryable_error_types=['ValidationError', 'EntityNotFoundError']
    )


def _long_running_retry_policy():
    """
    Retry policy for long-running activities like web search or LLM calls.

    - Longer timeouts to handle slow responses
    - More retries to handle rate limiting
    """
    return workflow.RetryPolicy(
        initial_interval=timedelta(seconds=5),
        maximum_interval=timedelta(minutes=5),
        backoff_coefficient=2.0,
        maximum_attempts=5
    )
```

---

### 4. Worker Configuration

```python
async def run_cq_worker():
    """Run the Temporal worker for competency question workflows."""

    client = await Client.connect(
        'localhost:7233',
        plugins=[PydanticAIPlugin(), LogfirePlugin()]
    )

    async with Worker(
        client,
        task_queue='competency_questions',
        workflows=[CompetencyQuestionWorkflow],
        plugins=[
            AgentPlugin(temporal_anchor_agent),
            AgentPlugin(temporal_enrich_agent),
            AgentPlugin(temporal_validation_agent)
        ],
        activities=[
            anchor_activity,
            enrich_activity,
            expand_string_activity,
            expand_biogrid_activity,
            expand_chembl_activity,
            traverse_activity,
            validate_identifiers_activity,
            validate_mechanisms_activity,
            validate_trials_activity,
            validate_evidence_activity,
            persist_activity
        ]
    ):
        print("Competency Question Worker started")
        await asyncio.Event().wait()  # Run forever
```

---

### 5. Execution and Resume

```python
async def execute_competency_question(question_id: str, params: dict):
    """Execute or resume a competency question workflow."""

    client = await Client.connect('localhost:7233', plugins=[PydanticAIPlugin()])

    # Check for existing workflow
    existing_handle = client.get_workflow_handle(f'cq-{question_id}')

    try:
        # Try to get result of existing workflow
        result = await existing_handle.result()
        print(f"Workflow {question_id} already completed")
        return result
    except:
        pass  # Workflow doesn't exist or hasn't completed

    # Start new workflow
    handle = await client.start_workflow(
        CompetencyQuestionWorkflow.run,
        args=[question_id, params],
        id=f'cq-{question_id}',
        task_queue='competency_questions'
    )

    print(f"Started workflow: {handle.id}")
    return await handle.result()


# Example: Execute CQ14
if __name__ == '__main__':
    asyncio.run(execute_competency_question(
        'cq14-feng-synthetic-lethality',
        {
            'entities': ['TP53', 'TYMS', 'fluorouracil', 'pemetrexed'],
            'validation_level': 'full',
            'persist_to': 'graphiti-docker'
        }
    ))
```

---

## Benefits of Temporal for Life Sciences Research

### 1. Durability
- Workflow state survives crashes
- Resume from exact point of failure
- No lost work on long-running research

### 2. Retry with Backoff
- MCP failures automatically retried
- Rate limiting handled gracefully
- Exponential backoff prevents thundering herd

### 3. Parallel Execution
- Multiple API calls run concurrently
- Activities can timeout independently
- Failed activities don't block others

### 4. Observability
- Logfire integration for tracing
- Workflow history shows exact execution path
- Debugging failures is straightforward

### 5. Reproducibility
- Workflow ID enables exact replay
- Same inputs produce same outputs
- Validation can be re-run anytime

---

## Mapping CQ14 to Workflow Phases

| CQ14 Phase | Temporal Activity | Durability Benefit |
|------------|-------------------|-------------------|
| Anchor | `anchor_activity` | Gene resolution can retry on HGNC timeout |
| Enrich | `enrich_activity` (parallel) | UniProt failures don't block other enrichments |
| Expand | `expand_*_activity` (parallel) | STRING/BioGRID/ChEMBL queried independently |
| Traverse | `traverse_activity` | Drug lookup chains are durable |
| Validate | `validate_*_activity` (parallel) | Validation agents run as isolated activities |
| Persist | `persist_activity` | Graphiti write can retry on connection issues |

---

## Error Handling: The NCT ID Lesson

The typo discovery (NCT:06975892 → NCT:06976892) shows why validation activities are critical.

```python
@activity.defn
async def validate_trials_activity(trials: list[str]) -> dict:
    """
    This activity would have caught the NCT ID typo automatically.

    If get_trial returns ENTITY_NOT_FOUND, we search for similar IDs
    and suggest corrections.
    """
    for nct_id in trials:
        result = await mcp_call('clinicaltrials_get_trial', {'nct_id': nct_id})

        if result.get('error', {}).get('code') == 'ENTITY_NOT_FOUND':
            # Search for similar trials
            search_results = await mcp_call('clinicaltrials_search_trials', {
                'query': nct_id.replace('NCT:', '').replace('0', ''),  # Fuzzy
                'page_size': 5
            })

            # Report potential corrections
            return {
                'status': 'error',
                'invalid_id': nct_id,
                'suggestion': 'Did you mean one of these?',
                'candidates': [t['id'] for t in search_results.get('items', [])]
            }
```

---

## Next Steps

1. **Implement base activities** for MCP tool calls with retry logic
2. **Create workflow templates** for each competency question type
3. **Set up Temporal cluster** with persistence for production use
4. **Add Logfire dashboards** for research workflow monitoring
5. **Build CLI** for executing CQ workflows: `python -m cq run cq14 --entities TP53,TYMS`

---

*Design Date: 2026-01-14*
*Based on: CQ14 Validation Experience*
*Reference: disney-architecture.py from graphiti-test*
