import logging
import os


def configure_logging(service_name: str) -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format=f"ts=%(asctime)s level=%(levelname)s service={service_name} logger=%(name)s msg=%(message)s",
    )
