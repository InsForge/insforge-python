from __future__ import annotations

import logging


def setup_logging(level: int | str = logging.WARNING) -> None:
    """Configure the ``insforge`` logger.

    Parameters
    ----------
    level:
        Logging level.  Accepts standard :mod:`logging` constants
        (``logging.DEBUG``, ``logging.INFO``, …) or their string names
        (``"DEBUG"``, ``"INFO"``, …).

    Examples
    --------
    Show SDK configuration and important operation results::

        import insforge
        insforge.setup_logging("INFO")

    Show full HTTP request / response details for debugging::

        import insforge
        insforge.setup_logging("DEBUG")
    """
    logger = logging.getLogger("insforge")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(name)s %(levelname)s] %(message)s"),
        )
        logger.addHandler(handler)
