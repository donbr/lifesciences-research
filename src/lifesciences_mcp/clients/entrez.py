"""NCBI Entrez E-utilities API client implementing the Fuzzy-to-Fact protocol.

This module provides the EntrezClient for querying NCBI Gene database
using E-utilities endpoints (esearch, esummary, efetch, elink).

Key features:
- Two-step API pattern: esearch (returns IDs) -> efetch/esummary (returns data)
- XML parsing using defusedxml for security (prevents XXE attacks)
- Adaptive rate limiting: 3 req/s default, 10 req/s with NCBI_API_KEY
- Cross-reference extraction from Entrezgene_xref XML elements

Reference: specs/009-entrez-mcp-server/research.md
"""

import asyncio
import base64
import json
import os
import time
from typing import Any

import defusedxml.ElementTree as ET
import httpx

from lifesciences_mcp.clients.base import LifeSciencesClient
from lifesciences_mcp.models.entrez import (
    NCBI_GENE_CURIE_PATTERN,
    EntrezCrossReferences,
    EntrezGene,
    GeneSearchCandidate,
)
from lifesciences_mcp.models.envelopes import (
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    PaginationEnvelope,
)


class EntrezClient(LifeSciencesClient):
    """NCBI Entrez E-utilities API client implementing the Fuzzy-to-Fact protocol.

    Rate limited based on NCBI policy:
    - 3 requests/second without API key
    - 10 requests/second with NCBI_API_KEY environment variable

    Uses exponential backoff on 429/503 errors.

    Can be used as a context manager:
        async with EntrezClient() as client:
            result = await client.search_genes("BRCA1")
    """

    ENTREZ_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    MAX_RETRIES = 3
    SCORE_DECAY = 0.05  # Score reduction per position in results

    def __init__(self) -> None:
        """Initialize the Entrez client with adaptive rate limiting."""
        super().__init__(base_url=self.ENTREZ_BASE_URL)
        self.api_key = os.getenv("NCBI_API_KEY")
        # 10 req/s with API key, 3 req/s without per research.md R4
        self.rate_limit_delay = 0.1 if self.api_key else 0.333
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "EntrezClient":
        """Enter context manager."""
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        """Exit context manager and cleanup resources."""
        await self.close()

    async def _rate_limited_get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make a rate-limited GET request with exponential backoff.

        Implements proper rate limiting with the request inside the lock
        to prevent race conditions. Adds API key if available.

        Args:
            path: API endpoint path.
            params: Query parameters.

        Returns:
            HTTP response from the API.
        """
        if params is None:
            params = {}

        # Add API key if available per research.md R4
        if self.api_key:
            params["api_key"] = self.api_key

        # Initial request with rate limiting
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

            response = await self._get(path, params=params)
            self._last_request_time = time.monotonic()

        # Exponential backoff on rate limit errors
        for attempt in range(self.MAX_RETRIES):
            if response.status_code not in (429, 503):
                break

            # Calculate backoff time per research.md R4
            retry_after = response.headers.get("Retry-After")
            wait_time = int(retry_after) if retry_after else (2**attempt)

            # Sleep OUTSIDE lock to allow other requests to proceed
            await asyncio.sleep(wait_time)

            # Retry with lock - re-check time boundary to prevent thundering herd
            async with self._lock:
                # CRITICAL: Re-check timing after acquiring lock
                now = time.monotonic()
                elapsed = now - self._last_request_time
                if elapsed < self.rate_limit_delay:
                    await asyncio.sleep(self.rate_limit_delay - elapsed)

                response = await self._get(path, params=params)
                self._last_request_time = time.monotonic()

        return response

    # =========================================================================
    # Cursor encoding/decoding per research.md R2
    # =========================================================================

    def _encode_cursor(self, offset: int) -> str:
        """Encode offset to opaque cursor string."""
        return base64.b64encode(json.dumps({"offset": offset}).encode()).decode()

    def _decode_cursor(self, cursor: str | None) -> int | None:
        """Decode cursor to offset, returns None if invalid."""
        if not cursor:
            return None
        try:
            return json.loads(base64.b64decode(cursor).decode())["offset"]
        except (ValueError, KeyError, json.JSONDecodeError):
            return None

    # =========================================================================
    # E-utilities API methods per research.md R1
    # =========================================================================

    async def _esearch(
        self,
        term: str,
        organism: str | None = None,
        retmax: int = 50,
        retstart: int = 0,
    ) -> dict[str, Any]:
        """Query esearch.fcgi endpoint to get ID list.

        Args:
            term: Search query.
            organism: Optional organism filter.
            retmax: Maximum results to return.
            retstart: Offset for pagination.

        Returns:
            Parsed JSON response with idlist, count, retstart.
        """
        # Build search term with organism filter if provided
        search_term = term
        if organism:
            # Map common names to scientific names
            organism_map = {
                "human": "Homo sapiens",
                "mouse": "Mus musculus",
                "rat": "Rattus norvegicus",
                "zebrafish": "Danio rerio",
                "fly": "Drosophila melanogaster",
                "worm": "Caenorhabditis elegans",
                "yeast": "Saccharomyces cerevisiae",
            }
            org_name = organism_map.get(organism.lower(), organism)
            search_term = f"{term} AND {org_name}[Organism]"

        params = {
            "db": "gene",
            "term": search_term,
            "retmax": retmax,
            "retstart": retstart,
            "retmode": "json",
        }

        response = await self._rate_limited_get("/esearch.fcgi", params=params)
        response.raise_for_status()
        return response.json()

    async def _esummary(self, ids: list[str]) -> dict[str, Any]:
        """Query esummary.fcgi endpoint to get document summaries.

        Args:
            ids: List of gene IDs.

        Returns:
            Parsed JSON response with gene summaries.
        """
        params = {
            "db": "gene",
            "id": ",".join(ids),
            "retmode": "json",
        }

        response = await self._rate_limited_get("/esummary.fcgi", params=params)
        response.raise_for_status()
        return response.json()

    async def _efetch(self, gene_id: str) -> str:
        """Query efetch.fcgi endpoint to get full XML record.

        Args:
            gene_id: Numeric gene ID.

        Returns:
            Raw XML string for parsing.
        """
        params = {
            "db": "gene",
            "id": gene_id,
            "retmode": "xml",
        }

        response = await self._rate_limited_get("/efetch.fcgi", params=params)
        response.raise_for_status()
        return response.text

    async def _elink(self, gene_id: str) -> dict[str, Any]:
        """Query elink.fcgi endpoint to get PubMed links.

        Args:
            gene_id: Numeric gene ID.

        Returns:
            Parsed JSON response with linksets.
        """
        params = {
            "dbfrom": "gene",
            "db": "pubmed",
            "id": gene_id,
            "linkname": "gene_pubmed",
            "retmode": "json",
        }

        response = await self._rate_limited_get("/elink.fcgi", params=params)
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # XML Parsing per research.md R3
    # =========================================================================

    def _parse_gene_xml(self, xml_content: str) -> dict[str, Any] | None:
        """Parse NCBI Gene XML to extract gene data.

        Uses defusedxml for security (prevents XXE attacks).

        Args:
            xml_content: Raw XML from efetch response.

        Returns:
            Parsed gene data dict, or None if parsing fails.
        """
        try:
            root = ET.fromstring(xml_content)
            gene_elem = root.find(".//Entrezgene")

            if gene_elem is None:
                return None

            # Extract gene ID
            gene_id = gene_elem.findtext(".//Gene-track_geneid")

            # Extract gene reference data
            gene_ref = gene_elem.find(".//Gene-ref")
            symbol = gene_ref.findtext("Gene-ref_locus") if gene_ref is not None else None
            name = gene_ref.findtext("Gene-ref_desc") if gene_ref is not None else None
            map_location = gene_ref.findtext("Gene-ref_maploc") if gene_ref is not None else None

            # Extract aliases
            aliases = []
            syn_elem = gene_elem.find(".//Gene-ref_syn")
            if syn_elem is not None:
                aliases = [e.text for e in syn_elem.findall("Gene-ref_syn_E") if e.text]

            # Extract summary
            summary = gene_elem.findtext(".//Entrezgene_summary")

            # Extract organism info
            organism = gene_elem.findtext(".//Org-ref_taxname")
            taxon_id = None
            taxon_elem = gene_elem.find(".//BioSource_org//Dbtag[Dbtag_db='taxon']")
            if taxon_elem is not None:
                taxon_id_text = taxon_elem.findtext(".//Object-id_id")
                if taxon_id_text:
                    taxon_id = int(taxon_id_text)

            # Extract chromosome from gene location
            chromosome = None
            # Find Gene-commentary with type='chromosome'
            for commentary in gene_elem.findall(".//Gene-commentary"):
                type_elem = commentary.find(".//Gene-commentary_type")
                if type_elem is not None and type_elem.get("value") == "chromosome":
                    chromosome = commentary.findtext(".//Gene-commentary_text")
                    break
            # Fallback: try to extract from map location
            if not chromosome and map_location:
                # Parse "17p13.1" -> "17"
                import re

                match = re.match(r"^(\d+|[XY]|MT)", map_location)
                if match:
                    chromosome = match.group(1)

            # Extract cross-references
            xrefs: dict[str, str | list[str]] = {}
            for dbtag in gene_elem.findall(".//Entrezgene_xref/Dbtag"):
                db_name = dbtag.findtext("Dbtag_db")
                obj_id = dbtag.findtext(".//Object-id_id") or dbtag.findtext(".//Object-id_str")
                if db_name and obj_id:
                    # Handle multiple values for same database
                    if db_name in xrefs:
                        existing = xrefs[db_name]
                        if isinstance(existing, list):
                            existing.append(obj_id)
                        else:
                            xrefs[db_name] = [existing, obj_id]
                    else:
                        xrefs[db_name] = obj_id

            # Also check for external references in Gene-commentary sections
            for commentary in gene_elem.findall(".//Gene-commentary"):
                for dbtag in commentary.findall(".//Dbtag"):
                    db_name = dbtag.findtext("Dbtag_db")
                    obj_id = dbtag.findtext(".//Object-id_id") or dbtag.findtext(".//Object-id_str")
                    if db_name and obj_id and db_name not in xrefs:
                        xrefs[db_name] = obj_id

            return {
                "gene_id": gene_id,
                "symbol": symbol,
                "name": name,
                "map_location": map_location,
                "chromosome": chromosome,
                "aliases": aliases if aliases else None,
                "summary": summary,
                "organism": organism,
                "taxon_id": taxon_id,
                "xrefs": xrefs,
            }
        except ET.ParseError:
            return None

    def _build_cross_references(self, xrefs: dict[str, str | list[str]]) -> EntrezCrossReferences:
        """Map NCBI Dbtag entries to CrossReferences model.

        Per Constitution Principle III: omit keys with no value.

        Args:
            xrefs: Dictionary of database name to identifier(s).

        Returns:
            EntrezCrossReferences model with mapped values.
        """
        result: dict[str, Any] = {}

        # HGNC - add prefix if needed per research.md R3
        if "HGNC" in xrefs:
            hgnc_id = xrefs["HGNC"]
            if isinstance(hgnc_id, list):
                hgnc_id = hgnc_id[0]
            result["hgnc"] = f"HGNC:{hgnc_id}" if not str(hgnc_id).startswith("HGNC:") else hgnc_id

        # Ensembl - use as-is
        if "Ensembl" in xrefs:
            ensembl_id = xrefs["Ensembl"]
            if isinstance(ensembl_id, list):
                ensembl_id = ensembl_id[0]
            result["ensembl_gene"] = ensembl_id

        # OMIM (MIM in NCBI) - use numeric value
        if "MIM" in xrefs:
            omim_id = xrefs["MIM"]
            if isinstance(omim_id, list):
                omim_id = omim_id[0]
            result["omim"] = str(omim_id)

        # UniProt - add prefix if needed, handle multiple values
        for key in ["UniProtKB/Swiss-Prot", "UniProtKB/TrEMBL"]:
            if key in xrefs:
                uniprot_ids = xrefs[key]
                if not isinstance(uniprot_ids, list):
                    uniprot_ids = [uniprot_ids]
                formatted = [
                    f"UniProtKB:{uid}" if not uid.startswith("UniProtKB:") else uid
                    for uid in uniprot_ids
                ]
                if "uniprot" in result:
                    existing = result["uniprot"]
                    if not isinstance(existing, list):
                        existing = [existing]
                    result["uniprot"] = existing + formatted
                else:
                    result["uniprot"] = formatted[0] if len(formatted) == 1 else formatted

        # RefSeq - may have multiple entries
        refseq_values = []
        for key, value in xrefs.items():
            if key.startswith("RefSeq") or key == "RefSeq":
                if isinstance(value, list):
                    refseq_values.extend(value)
                else:
                    refseq_values.append(value)
        if refseq_values:
            result["refseq"] = refseq_values[0] if len(refseq_values) == 1 else refseq_values

        # STRING
        if "STRING" in xrefs:
            string_id = xrefs["STRING"]
            if isinstance(string_id, list):
                string_id = string_id[0]
            result["string"] = string_id

        # BioGRID
        if "BioGRID" in xrefs:
            biogrid_id = xrefs["BioGRID"]
            if isinstance(biogrid_id, list):
                biogrid_id = biogrid_id[0]
            result["biogrid"] = str(biogrid_id)

        # KEGG
        if "KEGG" in xrefs:
            kegg_id = xrefs["KEGG"]
            if isinstance(kegg_id, list):
                kegg_id = kegg_id[0]
            result["kegg"] = kegg_id

        return EntrezCrossReferences(**result)

    # =========================================================================
    # Error Helpers per research.md R7
    # =========================================================================

    def _create_error_envelope(
        self,
        code: ErrorCode,
        message: str,
        recovery_hint: str,
        invalid_input: str | None = None,
    ) -> ErrorEnvelope:
        """Create standardized ErrorEnvelope."""
        return ErrorEnvelope(
            error=ErrorDetail(
                code=code,
                message=message,
                recovery_hint=recovery_hint,
                invalid_input=invalid_input,
            )
        )

    # =========================================================================
    # Public API Methods
    # =========================================================================

    async def search_genes(
        self,
        query: str,
        organism: str | None = None,
        page_size: int = 50,
        cursor: str | None = None,
    ) -> PaginationEnvelope[GeneSearchCandidate] | ErrorEnvelope:
        """Fuzzy search for genes (Phase 1 of Fuzzy-to-Fact).

        Uses esearch + esummary two-step pattern per research.md R2.

        Args:
            query: Search term (gene symbol, name, or natural language).
            organism: Optional organism filter (e.g., "human", "Homo sapiens").
            page_size: Results per page (1-100).
            cursor: Opaque cursor for pagination.

        Returns:
            PaginationEnvelope with GeneSearchCandidate items, or ErrorEnvelope.
        """
        # Validate query length per contracts/search_genes.yaml
        if len(query.strip()) < 2:
            return self._create_error_envelope(
                code=ErrorCode.AMBIGUOUS_QUERY,
                message="Query too short or too generic",
                recovery_hint="Provide at least 2 characters. Add organism filter to narrow results.",
                invalid_input=query,
            )

        # Clamp page_size to valid range
        page_size = max(1, min(100, page_size))

        # Decode cursor for offset
        offset = self._decode_cursor(cursor) or 0

        try:
            # Step 1: esearch to get ID list
            esearch_response = await self._esearch(
                term=query,
                organism=organism,
                retmax=page_size,
                retstart=offset,
            )

            esearch_result = esearch_response.get("esearchresult", {})
            id_list = esearch_result.get("idlist", [])
            total_count = int(esearch_result.get("count", 0))

            # Empty results - return empty envelope (not error per research.md R7)
            if not id_list:
                return PaginationEnvelope.create(
                    items=[],
                    cursor=None,
                    total_count=total_count,
                    page_size=page_size,
                )

            # Step 2: esummary to get gene summaries
            esummary_response = await self._esummary(ids=id_list)
            result = esummary_response.get("result", {})

            # Transform to GeneSearchCandidate models
            candidates = []
            for i, uid in enumerate(id_list):
                doc = result.get(uid, {})

                # Skip if error in response
                if "error" in doc:
                    continue

                # Calculate relevance score (position-based per research.md R2)
                score = max(0.1, 1.0 - (i * self.SCORE_DECAY))

                # Extract organism name
                org_info = doc.get("organism", {})
                organism_name = (
                    org_info.get("scientificname", "Unknown")
                    if isinstance(org_info, dict)
                    else "Unknown"
                )

                candidate = GeneSearchCandidate(
                    id=f"NCBIGene:{uid}",
                    symbol=doc.get("name", ""),
                    name=doc.get("description", ""),
                    description=doc.get("otherdesignations"),
                    organism=organism_name,
                    score=round(score, 2),
                )
                candidates.append(candidate)

            # Calculate next cursor
            next_cursor = None
            if offset + page_size < total_count:
                next_cursor = self._encode_cursor(offset + page_size)

            return PaginationEnvelope.create(
                items=candidates,
                cursor=next_cursor,
                total_count=total_count,
                page_size=page_size,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return self._create_error_envelope(
                    code=ErrorCode.RATE_LIMITED,
                    message="Exceeded NCBI rate limit",
                    recovery_hint="Wait and retry. Add NCBI_API_KEY environment variable for 10 req/s limit (free from NCBI)",
                )
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"NCBI E-utilities API error: {e.response.status_code}",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )
        except httpx.TimeoutException:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message="Request timeout",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )
        except httpx.RequestError as e:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"Request failed: {e!s}",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )

    async def get_gene(
        self, entrez_id: str, slim: bool = False
    ) -> EntrezGene | dict[str, Any] | ErrorEnvelope:
        """Get complete gene record by NCBIGene CURIE (Phase 2 of Fuzzy-to-Fact).

        Uses efetch with XML parsing per research.md R3.

        Args:
            entrez_id: NCBIGene CURIE in format 'NCBIGene:NNNNN'.
            slim: If True, return minimal dict instead of full model.

        Returns:
            EntrezGene record with cross_references, or ErrorEnvelope.
        """
        # Validate CURIE format (Fuzzy-to-Fact enforcement)
        if not NCBI_GENE_CURIE_PATTERN.match(entrez_id):
            return self._create_error_envelope(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=f"The input '{entrez_id}' is not a valid NCBIGene CURIE.",
                recovery_hint="Call search_genes to resolve the identifier first. Expected format: NCBIGene:<numeric_id>",
                invalid_input=entrez_id,
            )

        # Extract numeric ID from CURIE
        numeric_id = entrez_id.replace("NCBIGene:", "")

        try:
            # Fetch full XML record
            xml_response = await self._efetch(gene_id=numeric_id)

            # Parse XML
            gene_data = self._parse_gene_xml(xml_response)

            if not gene_data or not gene_data.get("symbol"):
                return self._create_error_envelope(
                    code=ErrorCode.ENTITY_NOT_FOUND,
                    message="Gene not found in NCBI Gene database",
                    recovery_hint="Verify the NCBIGene ID or use search_genes to find the correct identifier",
                    invalid_input=entrez_id,
                )

            # Build cross-references
            cross_refs = self._build_cross_references(gene_data.get("xrefs", {}))

            # Build EntrezGene model
            gene = EntrezGene(
                id=entrez_id,
                symbol=gene_data["symbol"],
                name=gene_data.get("name", ""),
                description=gene_data.get("description"),
                summary=gene_data.get("summary"),
                map_location=gene_data.get("map_location"),
                chromosome=gene_data.get("chromosome"),
                aliases=gene_data.get("aliases"),
                organism=gene_data.get("organism", "Unknown"),
                taxon_id=gene_data.get("taxon_id"),
                cross_references=cross_refs,
            )

            if slim:
                return gene.to_slim()

            return gene

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return self._create_error_envelope(
                    code=ErrorCode.RATE_LIMITED,
                    message="Exceeded NCBI rate limit",
                    recovery_hint="Wait and retry. Add NCBI_API_KEY environment variable for 10 req/s limit (free from NCBI)",
                )
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"NCBI E-utilities API error: {e.response.status_code}",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )
        except httpx.TimeoutException:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message="Request timeout",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )
        except httpx.RequestError as e:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"Request failed: {e!s}",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )

    async def get_pubmed_links(self, entrez_id: str, limit: int = 10) -> list[str] | ErrorEnvelope:
        """Get PubMed IDs associated with a gene.

        Uses elink with gene_pubmed linkname per research.md R5.

        Args:
            entrez_id: NCBIGene CURIE in format 'NCBIGene:NNNNN'.
            limit: Maximum number of PubMed IDs to return (1-100).

        Returns:
            List of PubMed ID strings, or ErrorEnvelope.
        """
        # Validate CURIE format
        if not NCBI_GENE_CURIE_PATTERN.match(entrez_id):
            return self._create_error_envelope(
                code=ErrorCode.UNRESOLVED_ENTITY,
                message=f"The input '{entrez_id}' is not a valid NCBIGene CURIE.",
                recovery_hint="Call search_genes to resolve the identifier first. Expected format: NCBIGene:<numeric_id>",
                invalid_input=entrez_id,
            )

        # Extract numeric ID from CURIE
        numeric_id = entrez_id.replace("NCBIGene:", "")

        # Clamp limit to valid range
        limit = max(1, min(100, limit))

        try:
            data = await self._elink(gene_id=numeric_id)

            # Extract PubMed IDs from linksets
            linksets = data.get("linksets", [])
            if not linksets:
                return []  # Empty list, not error per contracts/get_pubmed_links.yaml

            linksetdbs = linksets[0].get("linksetdbs", [])
            if not linksetdbs:
                return []

            pmids = linksetdbs[0].get("links", [])

            # Apply limit
            return pmids[:limit]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return self._create_error_envelope(
                    code=ErrorCode.RATE_LIMITED,
                    message="Exceeded NCBI rate limit",
                    recovery_hint="Wait and retry. Add NCBI_API_KEY environment variable for 10 req/s limit (free from NCBI)",
                )
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"NCBI E-utilities API error: {e.response.status_code}",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )
        except httpx.TimeoutException:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message="Request timeout",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )
        except httpx.RequestError as e:
            return self._create_error_envelope(
                code=ErrorCode.UPSTREAM_ERROR,
                message=f"Request failed: {e!s}",
                recovery_hint="NCBI E-utilities may be temporarily unavailable. Retry after a few seconds.",
            )
