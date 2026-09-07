"""
Provenance tracking and lineage utilities for FreightWise Stage 7 AI Agents + RAG foundation.

Provides functions to create, attach, and inspect provenance records for evidence items,
agent contexts, and agent responses. Ensures every data item retains explicit source,
stage, model/document version, and data scope metadata.
"""

import uuid
from typing import Any, Dict, List, Optional, Union

from src.agents.contracts import EvidenceItem, AgentContext, AgentResponse, ProvenanceRecord


def create_provenance_record(
    source: str,
    source_type: str,
    stage: str,
    model_name: Optional[str] = None,
    model_version: Optional[str] = None,
    document_name: Optional[str] = None,
    data_scope: str = "AUTHORIZED",
    metadata: Optional[Dict[str, Any]] = None,
) -> ProvenanceRecord:
    """
    Construct a new ProvenanceRecord with a unique identifier and timestamp.

    Args:
        source: Component or module name originating the data (e.g. 'Stage2ForecastService').
        source_type: Category of source ('MODEL', 'RULE_ENGINE', 'OPTIMIZER', 'DOCUMENT').
        stage: Pipeline stage (e.g. 'Stage 2', 'Stage 3', 'Stage 4', 'Stage 5', 'Stage 6').
        model_name: Optional ML model name (e.g. 'xgboost_freight_model').
        model_version: Optional ML model version string (e.g. '1.0.0').
        document_name: Optional source document name for RAG evidence.
        data_scope: Scope tag ('GLOBAL_CONGESTION_PROXY', 'EAST_COAST_INDIA', 'AUTHORIZED').
        metadata: Extra key-value metadata.

    Returns:
        Populated ProvenanceRecord instance.
    """
    record_id = f"prov-{uuid.uuid4().hex[:12]}"
    return ProvenanceRecord(
        record_id=record_id,
        source=source,
        source_type=source_type,
        stage=stage,
        model_name=model_name,
        model_version=model_version,
        document_name=document_name,
        data_scope=data_scope,
        metadata=dict(metadata) if metadata else {},
    )


def attach_provenance_to_evidence(
    evidence: EvidenceItem,
    provenance: ProvenanceRecord,
) -> EvidenceItem:
    """
    Attach a ProvenanceRecord to an EvidenceItem, preserving immutability of evidence content.

    Args:
        evidence: Target EvidenceItem.
        provenance: ProvenanceRecord to attach.

    Returns:
        Updated EvidenceItem with attached provenance.
    """
    evidence.provenance = provenance
    if provenance.data_scope:
        evidence.metadata["data_scope"] = provenance.data_scope
    return evidence


def extract_provenance_chain(
    target: Union[AgentContext, AgentResponse, EvidenceItem, List[EvidenceItem]]
) -> List[ProvenanceRecord]:
    """
    Extract all ProvenanceRecords present across an AgentContext, AgentResponse, or EvidenceItem(s).

    Args:
        target: An AgentContext, AgentResponse, EvidenceItem, or list of EvidenceItems.

    Returns:
        List of distinct ProvenanceRecords found.
    """
    records: List[ProvenanceRecord] = []
    seen_ids = set()

    def _add_rec(rec: Optional[ProvenanceRecord]):
        if rec and rec.record_id not in seen_ids:
            seen_ids.add(rec.record_id)
            records.append(rec)

    if isinstance(target, EvidenceItem):
        _add_rec(target.provenance)

    elif isinstance(target, list):
        for item in target:
            if isinstance(item, EvidenceItem):
                _add_rec(item.provenance)

    elif isinstance(target, AgentResponse):
        _add_rec(target.provenance)
        for item in target.evidence:
            _add_rec(item.provenance)

    elif isinstance(target, AgentContext):
        for item in target.evidence:
            _add_rec(item.provenance)

    return records
