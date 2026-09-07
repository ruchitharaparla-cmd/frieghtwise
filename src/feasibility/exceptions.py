"""
Custom exceptions for FreightWise Stage 4 Feasibility Engine.
"""


class DataUnavailableError(Exception):
    """Raised when required constraint data is not available for evaluation."""
    def __init__(self, constraint_name: str, reason: str):
        self.constraint_name = constraint_name
        self.reason = reason
        super().__init__(f"Data unavailable for constraint '{constraint_name}': {reason}")


class InvalidConstraintError(Exception):
    """Raised when constraint input data is invalid or malformed."""
    pass


class IndianPortSpecsUnavailableError(DataUnavailableError):
    """Raised when attempting to evaluate Indian port constraints with no verified specs."""
    def __init__(self, port_name: str):
        super().__init__(
            "Indian Port Infrastructure",
            f"Port '{port_name}' is Indian; no verified infrastructure specs in dataset"
        )


class PortSpecsUnavailableError(DataUnavailableError):
    """Raised when port specifications required for evaluation are not available."""
    pass
