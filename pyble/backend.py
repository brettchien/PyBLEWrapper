import platform
import logging

logger = logging.getLogger(__name__)

def load(shell=False):
    system = platform.system()
    BLEApp = None

    if system == "Darwin":
        # Mac OSX
        logger.debug("package ble is loaded on OSX")
        import osx.backend as backend
        BLEApp = backend.OSXCentralHandlerApp(shell)
    elif system == "Linux":
        # Linux
        logger.debug("package ble is loaded on Linux")
        logger.info("Not yet implemented")
    else:
        # Windows
        logger.debug("package ble is loaded on Windos")
        logger.info("Not yet implemented")

    if BLEApp:
        BLEApp.start()

    return BLEApp

if __name__ == "__main__":
    load()
