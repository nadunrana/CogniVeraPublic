"""
CogniVera Socket Communication Module
=====================================

This module provides TCP socket-based communication with robot hardware.
Handles low-level message transmission and reception over network socket.

Reference: https://doi.org/10.1109/ACCESS.2025.3565918
"""

import socket
import time
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Default hardware connection parameters
DEFAULT_HOST = "192.168.125.1"  # Robot controller IP
DEFAULT_PORT = 5000  # Robot controller port


class TCPClient:
    """
    TCP socket client for hardware robot communication.

    Manages connection lifecycle and message transmission to robot controller.
    Includes error handling and reconnection logic.

    Attributes:
        socket (socket.socket): Active socket connection
        host (str): Robot controller hostname/IP
        port (int): Robot controller port
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """
        Initialize TCP client and establish connection.

        Args:
            host (str): Robot IP address. Default: 192.168.125.1
            port (int): Robot port number. Default: 5000

        Raises:
            ConnectionError: If unable to connect to robot
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.socket.settimeout(10)  # 10 second timeout
            logger.info(f"TCP client connected to {host}:{port}")
        except socket.error as e:
            logger.error(f"Failed to initialize socket: {str(e)}")
            raise ConnectionError(f"Cannot connect to robot at {host}:{port}") from e

    def send_message(self, message: str) -> str:
        """
        Send message to robot and receive response.

        Args:
            message (str): Command message to send

        Returns:
            str: Response from robot controller

        Raises:
            RuntimeError: If socket is not connected
            TimeoutError: If no response received within timeout
        """
        if self.socket is None:
            raise RuntimeError("Socket not connected")

        try:
            logger.debug(f"Sending: {message}")
            self.socket.sendall(message.encode('utf-8'))

            # Receive response
            response_data = self.socket.recv(1024)
            response = response_data.decode('utf-8')

            logger.debug(f"Received: {response}")
            time.sleep(0.1)  # Small delay for stability

            return response
        except socket.timeout:
            logger.error("Socket timeout - no response from robot")
            raise TimeoutError("No response from robot controller")
        except socket.error as e:
            logger.error(f"Socket error: {str(e)}")
            raise RuntimeError(f"Communication error: {str(e)}") from e

    def close(self) -> None:
        """Close socket connection."""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Socket connection closed")
            except socket.error as e:
                logger.warning(f"Error closing socket: {str(e)}")
            finally:
                self.socket = None

    def is_connected(self) -> bool:
        """
        Check if socket is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.socket is not None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Legacy alias for backward compatibility
TCPclient = TCPClient