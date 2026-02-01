from .validation import (
    ValidationReport,
    ValidationResult,
    InvalidReason
)

from .enrichment import (
    EnrichmentStats,
    CadastroColumnMapping,
    EnrichedRecord
)

from .aggregation import (
    AggregationStats,
    AggregatedGroup,
    VariabilityLevel
)

__all__ = [
    'ValidationReport',
    'ValidationResult',
    'InvalidReason',

    'EnrichmentStats',
    'CadastroColumnMapping',
    'EnrichedRecord',

    'AggregationStats',
    'AggregatedGroup',
    'VariabilityLevel',
]
