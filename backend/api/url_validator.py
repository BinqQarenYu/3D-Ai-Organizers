import urllib.parse
import socket
import ipaddress
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def validate_url(url: str):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid URL protocol.")

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid URL hostname.")

    try:
        # Resolve hostname to IP
        ip_addr = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_addr)

        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            logger.warning(f"Blocked request to internal/private IP: {ip_addr} for hostname {hostname}")
            raise HTTPException(status_code=403, detail="Access to internal/private IP addresses is forbidden.")

        # specifically check AWS metadata IP
        if str(ip) == "169.254.169.254":
             raise HTTPException(status_code=403, detail="Access to cloud metadata is forbidden.")

    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Could not resolve hostname.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error validating URL {url}: {e}")
        raise HTTPException(status_code=400, detail="Invalid URL.")
