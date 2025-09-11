import logging
import os



formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')

def setup_logger():

    if logging.getLogger().hasHandlers():
        return

    ingestion_logger = logging.getLogger("ingestion")
    ingestion_logger.setLevel(logging.DEBUG)
    ingestion_handler = logging.FileHandler(filename= "ingestion.log", mode = "w")
    ingestion_handler.setFormatter(formatter)
    ingestion_logger.addHandler(ingestion_handler)


    generation_logger = logging.getLogger("generation")
    generation_logger.setLevel(logging.DEBUG)
    generation_handler = logging.FileHandler(filename= "generation.log", mode = "w")
    generation_logger.setFormatter(formatter)
    generation_logger.addHandler(generation_handler)

def log_to_all(loggers,level, message):
    for logger in loggers:
        getattr(logger, level)(message)

    


