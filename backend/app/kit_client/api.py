"""
Kit.com API Client for interacting with the Kit.com V4 API.
This module provides a client for making authenticated requests to the Kit.com API.
"""

from typing import Any, Dict, List, Optional
import os
import logging
import httpx
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KitClientConfig(BaseModel):
    """Configuration for the Kit.com API client."""
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    base_url: str = "https://api.kit.com/v4"

class KitClient:
    """Client for interacting with the Kit.com V4 API."""

    def __init__(self, config: KitClientConfig):
        """
        Initialize the Kit.com API client.

        Args:
            config: Configuration for the client
        """
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)

        if not config.api_key and not config.access_token:
            logger.warning("No API key or access token provided. Authentication will fail.")

        logger.info("KitClient initialized successfully")

    async def _make_request(self, method: str, endpoint: str,
                           params: Optional[Dict[str, Any]] = None,
                           data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an authenticated request to the Kit.com API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data

        Returns:
            Response data as a dictionary
        """
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if self.config.api_key:
            headers["X-Kit-Api-Key"] = self.config.api_key
        elif self.config.access_token:
            headers["Authorization"] = f"Bearer {self.config.access_token}"

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            )

            response.raise_for_status()

            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            try:
                error_data = e.response.json()
                logger.error(f"Error details: {error_data}")
            except Exception:
                pass
            raise
        except Exception as e:
            logger.error(f"Error making request to Kit.com API: {str(e)}")
            raise


    async def get_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags from the account.

        Returns:
            List of tag objects
        """
        response = await self._make_request("GET", "/tags")
        return response.get("tags", [])

    async def create_tag(self, name: str) -> Dict[str, Any]:
        """
        Create a new tag.

        Args:
            name: Name of the tag

        Returns:
            Created tag object
        """
        data = {"name": name}
        response = await self._make_request("POST", "/tags", data=data)
        return response.get("tag", {})

    async def tag_subscriber_by_email(self, email: str, tag_id: str) -> Dict[str, Any]:
        """
        Tag a subscriber by email address.

        Args:
            email: Email address of the subscriber
            tag_id: ID of the tag to apply

        Returns:
            Result of the tagging operation
        """
        data = {"email_address": email}
        response = await self._make_request("POST", f"/tags/{tag_id}/subscribers", data=data)
        return response.get("subscriber", {})


    async def get_subscribers(self, limit: int = 10, sort_by: str = "created_at",
                             sort_order: str = "desc") -> List[Dict[str, Any]]:
        """
        Get subscribers from the account.

        Args:
            limit: Maximum number of subscribers to return
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            List of subscriber objects
        """
        params = {
            "per_page": str(limit)
        }

        if sort_by and sort_order:
            params["sort_field"] = str(sort_by)
            params["sort_order"] = str(sort_order)

        response = await self._make_request("GET", "/subscribers", params=params)
        return response.get("subscribers", [])

    async def count_subscribers(self) -> int:
        """
        Count the number of subscribers in the account.

        Returns:
            Number of subscribers
        """
        params = {
            "per_page": 1,
            "include_total_count": "true"
        }

        try:
            response = await self._make_request("GET", "/subscribers", params=params)
            logger.info(f"Subscriber count raw response: {response}")
            
            if "total_count" in response:
                return response.get("total_count", 0)
            
            if "meta" in response and "total_count" in response["meta"]:
                return response["meta"]["total_count"]
            
            if "total_subscribers" in response:
                return response["total_subscribers"]
            
            if "count" in response:
                return response["count"]
            
            if "subscribers" in response and isinstance(response["subscribers"], list):
                if len(response["subscribers"]) > 0:
                    if "pagination" in response and "total" in response["pagination"]:
                        return response["pagination"]["total"]
                    else:
                        large_params = {
                            "per_page": 100,
                            "include_total_count": "true"
                        }
                        large_response = await self._make_request("GET", "/subscribers", params=large_params)
                        logger.info(f"Large subscriber count response: {large_response}")
                        
                        if "total_count" in large_response:
                            return large_response["total_count"]
                        elif "meta" in large_response and "total_count" in large_response["meta"]:
                            return large_response["meta"]["total_count"]
                        elif "pagination" in large_response and "total" in large_response["pagination"]:
                            return large_response["pagination"]["total"]
                        else:
                            return len(large_response.get("subscribers", []))
                
                return len(response["subscribers"])
            
            logger.warning(f"Could not determine subscriber count from response: {response}")
            return 0
            
        except Exception as e:
            logger.error(f"Error counting subscribers: {str(e)}")
            raise

    async def get_subscriber_by_email(self, email: str) -> Dict[str, Any]:
        """
        Get a subscriber by email address.

        Args:
            email: Email address of the subscriber

        Returns:
            Subscriber object
        """
        params = {"email_address": email}
        response = await self._make_request("GET", "/subscribers", params=params)
        subscribers = response.get("subscribers", [])

        if subscribers:
            return subscribers[0]
        else:
            return {}


    async def get_forms(self) -> List[Dict[str, Any]]:
        """
        Get all forms from the account.

        Returns:
            List of form objects
        """
        response = await self._make_request("GET", "/forms")
        return response.get("forms", [])

    async def create_form(self, name: str, redirect_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new form.

        Args:
            name: Name of the form
            redirect_url: URL to redirect to after form submission

        Returns:
            Created form object
        """
        data = {"name": name}

        if redirect_url:
            data["redirect_url"] = redirect_url

        response = await self._make_request("POST", "/forms", data=data)
        return response.get("form", {})


    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated account.

        Returns:
            Account information
        """
        response = await self._make_request("GET", "/account")
        return response


    async def get_broadcasts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get broadcasts from the account.

        Args:
            limit: Maximum number of broadcasts to return

        Returns:
            List of broadcast objects
        """
        params = {"per_page": limit}
        response = await self._make_request("GET", "/broadcasts", params=params)
        return response.get("broadcasts", [])

    async def create_broadcast(self, subject: str, content: str,
                              email_template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new broadcast.

        Args:
            subject: Subject of the broadcast
            content: Content of the broadcast
            email_template_id: ID of the email template to use

        Returns:
            Created broadcast object
        """
        data = {
            "subject": subject,
            "content": content
        }

        if email_template_id:
            data["email_template_id"] = email_template_id

        response = await self._make_request("POST", "/broadcasts", data=data)
        return response.get("broadcast", {})


    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
