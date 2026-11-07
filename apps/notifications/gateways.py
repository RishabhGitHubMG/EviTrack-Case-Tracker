import logging


logger = logging.getLogger(__name__)


class ConsoleSMSGateway:
    def send(self, phone_number: str, message: str) -> None:
        logger.info('Mock SMS to %s: %s', phone_number, message)
