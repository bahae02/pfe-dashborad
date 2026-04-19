"""
Utility functions for file and data handling
"""
import os
import glob
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def cleanup_old_files(folder, hours=24):
    """
    Delete files older than specified hours to prevent disk overflow
    
    Args:
        folder: Directory to clean
        hours: Age threshold in hours (default 24)
    """
    if not os.path.exists(folder):
        return 0
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    deleted_count = 0
    
    try:
        for filepath in glob.glob(os.path.join(folder, "*")):
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                        logger.info(f"Deleted old file: {filepath}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {filepath}: {e}")
    except Exception as e:
        logger.error(f"Cleanup error in {folder}: {e}")
    
    return deleted_count


def get_folder_size(folder):
    """
    Get total size of all files in folder (in MB)
    
    Args:
        folder: Directory path
        
    Returns:
        Size in MB
    """
    if not os.path.exists(folder):
        return 0
    
    total_size = 0
    try:
        for filepath in glob.glob(os.path.join(folder, "*")):
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Error calculating folder size: {e}")
    
    return total_size / (1024 * 1024)  # Convert to MB


def validate_dataframe_structure(df, required_columns):
    """
    Validate that a dataframe has required columns
    
    Args:
        df: Pandas DataFrame
        required_columns: List of required column names
        
    Returns:
        Tuple: (is_valid, missing_columns)
    """
    df_cols = set(str(col).lower().strip() for col in df.columns)
    req_cols = set(str(col).lower().strip() for col in required_columns)
    
    missing = req_cols - df_cols
    return len(missing) == 0, missing
