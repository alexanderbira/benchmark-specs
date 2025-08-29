# Configuration parameters for experiments

USE_DWYER_PATTERNS = True  # Whether to use Dwyer patterns when converting to the Spectra format

PATTERN_TIMEOUT = -1  # Timeout for pattern-based BC search in seconds per pattern (-1 for unlimited)
PATTERN_MAX_CANDIDATES = 100  # The maximum number of BC candidates to generate per pattern (-1 for unlimited)
MAX_PATTERN_CONJUNCTS = -1  # The maximum number of conjuncts to use in the BC pattern candidates (-1 for unlimited)

INTERPOLATOR_TIMEOUT = 600  # Timeout for the interpolator in seconds
INTERPOLATOR_REPAIR_LIMIT = 50  # Maximum number of realizable refinements to generate
