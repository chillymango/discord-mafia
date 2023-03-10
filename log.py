import logging


fmt = logging.Formatter("[%(asctime)s]:%(levelname)s [%(name)s]: %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

ch.setFormatter(fmt)
