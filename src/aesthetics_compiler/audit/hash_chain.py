from aesthetics_compiler.ir.schemas import AuditRecord, PassRecord


def build_audit(
    pass_records: list[PassRecord],
    extractor_tier: str,
    input_mode: str,
    active_projections: list[str],
    graph_hash: str | None,
    input_sha256: str | None,
) -> AuditRecord:
    ok_count = sum(1 for p in pass_records if p.status == "ok")
    return AuditRecord(
        passes=pass_records,
        extractor_tier=extractor_tier,
        input_mode=input_mode,
        active_projections=active_projections,
        graph_hash=graph_hash,
        input_sha256=input_sha256,
        provenance={
            "schema": "aesthetic_ir_v0.1",
            "passes_completed": ok_count,
        },
    )
