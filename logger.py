"""
CogniVera Logger Module
=======================

This module provides CSV-based logging for tracking requests, responses, and validation scores
throughout the human-robot collaboration session.

Reference: https://doi.org/10.1109/ACCESS.2025.3565918
"""

import csv
import os
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class ExperimentLogger:
    """
    Logs experiment interactions to CSV format for analysis and validation.

    Tracks request/response pairs with unique IDs, enabling correlation between
    user requests, robot updates, and validation agent feedback.

    Attributes:
        file_name (str): Path to CSV output file
        pending_requests (dict): In-memory cache of incomplete request records
    """

    def __init__(self, file_name: str = "logs/experiment_log.csv"):
        """
        Initialize experiment logger.

        Args:
            file_name (str): Output CSV file path. Default: logs/experiment_log.csv
        """
        self.file_name = file_name
        self.pending_requests: Dict[str, Dict[str, Any]] = {}

        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.file_name) or ".", exist_ok=True)

        # Initialize CSV file with headers if it doesn't exist
        if not os.path.isfile(self.file_name):
            self._create_csv_file()
            logger.info(f"Created new log file: {self.file_name}")

    def _create_csv_file(self) -> None:
        """Create CSV file with column headers."""
        headers = [
            'Request_ID',
            'Timestamp',
            'Request_Type',
            'Request',
            'Reply',
            'Score',
            'Function_Call',
            'Time_Taken_Seconds'
        ]

        try:
            with open(self.file_name, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.info(f"CSV headers written to {self.file_name}")
        except IOError as e:
            logger.error(f"Error creating CSV file: {str(e)}")
            raise

    def log_request(
            self,
            request_type: str,
            request: str,
            score: Optional[float] = None
    ) -> str:
        """
        Log a new request and return its unique ID.

        Args:
            request_type (str): Type of request (e.g., 'User', 'Cobot', 'VA')
            request (str): Request content/data
            score (float, optional): Validation score if applicable

        Returns:
            str: Unique request ID for correlation with log_reply()
        """
        request_id = str(uuid.uuid4())

        # Store pending request
        self.pending_requests[request_id] = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'request_type': request_type,
            'request': request,
            'text_reply': None,
            'score': score,
            'function_call': None,
            'time_taken': None
        }

        logger.debug(f"Logged request {request_id}: {request_type}")
        return request_id

    def log_reply(
            self,
            request_id: str,
            text_reply: str,
            function_call: Optional[str] = None,
            time_taken: Optional[float] = None,
            score: Optional[float] = None
    ) -> None:
        """
        Complete a request log with reply information and write to CSV.

        Args:
            request_id (str): Request ID from log_request()
            text_reply (str): Reply/response text
            function_call (str, optional): Function executed
            time_taken (float, optional): Execution time in seconds
            score (float, optional): Validation/accuracy score
        """
        if request_id not in self.pending_requests:
            logger.warning(f"Reply logged for unknown request_id: {request_id}")
            return

        # Update pending request
        self.pending_requests[request_id]['text_reply'] = text_reply
        self.pending_requests[request_id]['function_call'] = function_call
        self.pending_requests[request_id]['time_taken'] = time_taken
        self.pending_requests[request_id]['score'] = score

        # Write to CSV and remove from pending
        self._write_to_csv(request_id)
        del self.pending_requests[request_id]

        logger.debug(f"Completed log for request {request_id}")

    def _write_to_csv(self, request_id: str) -> None:
        """
        Write completed request record to CSV file.

        Args:
            request_id (str): Request ID to write
        """
        if request_id not in self.pending_requests:
            logger.error(f"Request ID not found: {request_id}")
            return

        record = self.pending_requests[request_id]

        try:
            with open(self.file_name, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    record['request_id'],
                    record['timestamp'],
                    record['request_type'],
                    record['request'],
                    record['text_reply'],
                    record['score'],
                    record['function_call'],
                    record['time_taken']
                ])
            logger.debug(f"Record written to CSV: {request_id}")
        except IOError as e:
            logger.error(f"Error writing to CSV: {str(e)}")
            raise

    def get_pending_count(self) -> int:
        """
        Get number of incomplete request records.

        Returns:
            int: Number of pending requests
        """
        return len(self.pending_requests)