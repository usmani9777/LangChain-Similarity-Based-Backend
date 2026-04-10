import os
import logging

logger = logging.getLogger(__name__)

def get_unique_filename(directory, filename):
    if not filename.lower().endswith((".txt", ".pdf")):
        filename += ".txt"
    base, extension = os.path.splitext(filename)
    counter = 1
    unique_name = filename
    
    # Check if the file already exists in the destination folder
    while os.path.exists(os.path.join(directory, unique_name)):
        # Create a new unique name (e.g., "file (1).txt")
        logger.info("File exists. Generating a new name.",extra={"filenae": unique_name})
        unique_name = f"{base} ({counter}){extension}"
        counter += 1
    logger.info("Returning New FileName.",extra={"filenae": unique_name})    
    return unique_name





