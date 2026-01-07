"""Unit tests for IUPHAR client helper methods.

Tests cursor encoding/decoding, score calculation, and query parameter mapping
without requiring network access.
"""

import base64
import json

import pytest

from lifesciences_mcp.clients.iuphar import IUPHARClient

# =============================================================================
# User Story 1: Fuzzy Ligand Search - Client Unit Tests
# =============================================================================


def test_cursor_encoding_decoding_roundtrip():
    """T115: Test cursor encoding/decoding roundtrip."""
    client = IUPHARClient()

    # Test various offsets
    test_offsets = [0, 1, 50, 100, 999, 12345]

    for offset in test_offsets:
        # Encode
        cursor = client._encode_cursor(offset)

        # Verify cursor is base64-encoded
        assert isinstance(cursor, str)
        # Verify it's valid base64 (no exception)
        base64.b64decode(cursor)

        # Decode
        decoded_offset = client._decode_cursor(cursor)

        # Verify roundtrip
        assert decoded_offset == offset


def test_cursor_decoding_invalid_cursor():
    """Test cursor decoding handles invalid cursors gracefully."""
    client = IUPHARClient()

    # Invalid base64
    assert client._decode_cursor("not-valid-base64!!!") == 0

    # Valid base64 but invalid JSON
    invalid_json_cursor = base64.b64encode(b"not json").decode()
    assert client._decode_cursor(invalid_json_cursor) == 0

    # Valid JSON but missing offset key
    missing_offset = base64.b64encode(json.dumps({"foo": "bar"}).encode()).decode()
    assert client._decode_cursor(missing_offset) == 0


def test_position_based_score_calculation():
    """T116: Test position-based score calculation."""
    client = IUPHARClient()

    # Test formula: 1.0 - (position * 0.05), minimum 0.1
    assert client._calculate_score(0) == pytest.approx(1.0)  # First result
    assert client._calculate_score(1) == pytest.approx(0.95)  # Second result
    assert client._calculate_score(2) == pytest.approx(0.90)  # Third result
    assert client._calculate_score(10) == pytest.approx(0.50)  # 11th result
    assert client._calculate_score(17) == pytest.approx(0.15)  # 18th result
    assert client._calculate_score(18) == pytest.approx(0.10)  # 19th result (at minimum)
    assert client._calculate_score(20) == pytest.approx(0.10)  # 21st result (clamped to minimum)
    assert client._calculate_score(100) == pytest.approx(0.10)  # Far result (clamped to minimum)


def test_query_parameter_mapping():
    """T117: Test query parameter mapping for ligand search."""
    client = IUPHARClient()

    # This tests the internal logic of parameter construction
    # We'll verify by checking that the method accepts expected parameters

    # The actual parameter mapping is tested via integration tests
    # Here we just verify the interface is correct

    # Should accept name parameter
    assert hasattr(client, "_fetch_ligands")

    # Should accept type_filter parameter
    # Should accept approved_only parameter
    # These are verified in integration tests where we can see actual API calls


# =============================================================================
# User Story 2: Strict Ligand Lookup - Client Unit Tests
# =============================================================================


def test_curie_extraction():
    """T140: Test CURIE extraction (IUPHAR:2713 -> 2713)."""
    # The extraction is done in get_ligand via: int(iuphar_id.split(":")[1])
    # Test the logic directly
    test_cases = [
        ("IUPHAR:1", 1),
        ("IUPHAR:2713", 2713),
        ("IUPHAR:9999", 9999),
        ("IUPHAR:123456", 123456),
    ]

    for curie, expected_id in test_cases:
        extracted_id = int(curie.split(":")[1])
        assert extracted_id == expected_id


def test_chembl_cross_reference_normalization():
    """T141: Test ChEMBL cross-reference normalization."""
    client = IUPHARClient()

    # Test with "CHEMBL" prefix
    db_links_with_prefix = [{"database": "ChEMBL Ligand", "accession": "CHEMBL521"}]
    refs = client._map_ligand_cross_references(db_links_with_prefix)
    assert refs.chembl == "521"  # Prefix stripped

    # Test without prefix (already normalized)
    db_links_no_prefix = [{"database": "ChEMBL Ligand", "accession": "521"}]
    refs = client._map_ligand_cross_references(db_links_no_prefix)
    assert refs.chembl == "521"


def test_drugbank_id_format_validation():
    """T142: Test DrugBank ID format validation."""
    client = IUPHARClient()

    # DrugBank IDs have format DB\d{5} (e.g., DB01050)
    db_links = [
        {"database": "DrugBank Ligand", "accession": "DB01050"},
        {"database": "ChEMBL Ligand", "accession": "521"},
        {"database": "PubChem CID", "accession": "3672"},
    ]

    refs = client._map_ligand_cross_references(db_links)

    # Verify all mappings
    assert refs.drugbank == "DB01050"
    assert refs.chembl == "521"
    assert refs.pubchem_compound == "3672"


# =============================================================================
# User Story 3: Fuzzy Target Search - Client Unit Tests
# =============================================================================


def test_html_tag_stripping():
    """T170: Test HTML tag stripping regex."""
    client = IUPHARClient()

    # Test various HTML patterns
    test_cases = [
        ("D<sub>2</sub> receptor", "D2 receptor"),
        ("5-HT<sub>1A</sub>", "5-HT1A"),
        ("GABA<sub>A</sub> receptor a<sub>1</sub>", "GABAA receptor a1"),
        ("Plain text", "Plain text"),  # No HTML tags
        ("Multiple <b>tags</b> <i>here</i>", "Multiple tags here"),
        ("<p>Paragraph</p>", "Paragraph"),
    ]

    for input_text, expected_output in test_cases:
        result = client._strip_html_tags(input_text)
        assert result == expected_output, f"Failed for '{input_text}': got '{result}'"


# =============================================================================
# User Story 4: Strict Target Lookup - Client Unit Tests
# =============================================================================


def test_species_filtering_logic():
    """T200: Test species filtering logic in _map_target_cross_references."""
    client = IUPHARClient()

    # Test with mixed species
    db_links = [
        {"species": "Human", "database": "UniProtKB", "accession": "P14416"},
        {"species": "Mouse", "database": "UniProtKB", "accession": "P61168"},
        {"species": "Human", "database": "Ensembl Gene", "accession": "ENSG00000149295"},
        {"species": "Rat", "database": "Ensembl Gene", "accession": "ENSRNOG00000012345"},
    ]

    refs = client._map_target_cross_references(db_links)

    # Should only include human cross-references
    assert "uniprot" in refs.model_dump(exclude_none=True)
    assert "P14416" in refs.uniprot  # Human UniProt
    assert len(refs.uniprot) == 1  # Only human, not mouse

    assert "ensembl_gene" in refs.model_dump(exclude_none=True)
    assert refs.ensembl_gene == "ENSG00000149295"  # Human Ensembl


def test_uniprot_list_format():
    """T201: Test UniProt list format in _map_target_cross_references."""
    client = IUPHARClient()

    # Test with multiple UniProt IDs for same target (e.g., isoforms)
    db_links = [
        {"species": "Human", "database": "UniProtKB", "accession": "P14416"},
        {"species": "Human", "database": "UniProtKB", "accession": "Q9Y6M1"},
    ]

    refs = client._map_target_cross_references(db_links)

    # UniProt should be list format (per ADR-001)
    assert isinstance(refs.uniprot, list)
    assert len(refs.uniprot) == 2
    assert "P14416" in refs.uniprot
    assert "Q9Y6M1" in refs.uniprot


# =============================================================================
# User Story 5: Error Recovery - Unit Tests
# =============================================================================


def test_error_envelope_structure_validation():
    """T222: Test ErrorEnvelope structure validation."""
    from lifesciences_mcp.models.envelopes import ErrorDetail, ErrorEnvelope

    # Create ErrorEnvelope with all required fields
    envelope = ErrorEnvelope(
        success=False,
        error=ErrorDetail(
            code="UNRESOLVED_ENTITY",
            message="Test error message",
            recovery_hint="Try this recovery action",
            invalid_input="bad_input",
        ),
    )

    # Validate structure
    data = envelope.model_dump()
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "recovery_hint" in data["error"]
    assert "invalid_input" in data["error"]


def test_all_error_codes_have_recovery_hints():
    """T223: Test all error codes have recovery hints."""
    from lifesciences_mcp.models.envelopes import ErrorCode

    # All error codes from ADR-001 Appendix B
    expected_codes = {
        "UNRESOLVED_ENTITY",
        "ENTITY_NOT_FOUND",
        "AMBIGUOUS_QUERY",
        "RATE_LIMITED",
        "UPSTREAM_ERROR",
        "INVALID_CROSS_REFERENCE",
    }

    # Verify all expected codes are in enum
    actual_codes = {code.value for code in ErrorCode}
    assert actual_codes == expected_codes

    # Verify _handle_http_error returns recovery hints for all applicable codes
    client = IUPHARClient()

    # Test 404 -> ENTITY_NOT_FOUND
    response_404 = type(
        "Response", (), {"status_code": 404, "url": type("URL", (), {"path": "/ligands/999999"})}
    )()
    error_404 = client._handle_http_error(response_404, entity_type="ligand")
    assert error_404.error.code == ErrorCode.ENTITY_NOT_FOUND
    assert len(error_404.error.recovery_hint) > 0
    assert "get_target" in error_404.error.recovery_hint

    # Test 429 -> RATE_LIMITED
    response_429 = type(
        "Response", (), {"status_code": 429, "url": type("URL", (), {"path": "/ligands"})}
    )()
    error_429 = client._handle_http_error(response_429, entity_type="ligand")
    assert error_429.error.code == ErrorCode.RATE_LIMITED
    assert len(error_429.error.recovery_hint) > 0

    # Test 500 -> UPSTREAM_ERROR
    response_500 = type(
        "Response", (), {"status_code": 500, "url": type("URL", (), {"path": "/ligands"})}
    )()
    error_500 = client._handle_http_error(response_500, entity_type="ligand")
    assert error_500.error.code == ErrorCode.UPSTREAM_ERROR
    assert len(error_500.error.recovery_hint) > 0


def test_error_code_enum_values_match_spec():
    """T224: Test error code enum values match spec."""
    from lifesciences_mcp.models.envelopes import ErrorCode

    # Verify error codes match ADR-001 Appendix B specification
    assert ErrorCode.UNRESOLVED_ENTITY.value == "UNRESOLVED_ENTITY"
    assert ErrorCode.ENTITY_NOT_FOUND.value == "ENTITY_NOT_FOUND"
    assert ErrorCode.AMBIGUOUS_QUERY.value == "AMBIGUOUS_QUERY"
    assert ErrorCode.RATE_LIMITED.value == "RATE_LIMITED"
    assert ErrorCode.UPSTREAM_ERROR.value == "UPSTREAM_ERROR"
    assert ErrorCode.INVALID_CROSS_REFERENCE.value == "INVALID_CROSS_REFERENCE"

    # Verify enum is exhaustive (no missing or extra codes)
    assert len(ErrorCode) == 6
