# tools.py
import json
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_groq import ChatGroq

# Import the database functions
import database

# --- Pydantic Schemas for Tool Inputs ---
class OrderTrackerInput(BaseModel):
    order_id: str = Field(description="The unique identifier for a customer's order.")
class IssueResolverInput(BaseModel):
    order_id: str = Field(description="The unique identifier for the order with an issue.")
    issue_type: str = Field(description="The type of issue. E.g., 'missing_items', 'poor_quality'.")
    details: str = Field(description="A description of the issue.")
    missing_items: str = Field(default="", description="Specific items that are missing, if applicable.")
    refund_amount: str = Field(default="", description="The amount to refund, if applicable.")

# --- Tool Implementations ---
class OrderTrackerTool(BaseTool):
    name: str = "order_tracker"
    description: str = (
        "Use this tool to get the real-time status of a user's food order. "
        "Use it in Phase 1 to report status/items/ETA and ask for confirmation."
    )
    args_schema: Type[BaseModel] = OrderTrackerInput

    def _run(self, order_id: str) -> str:
        print(f"\n[Tool Action]: Running OrderTrackerTool for {order_id}\n")
        order = database.get_order(order_id)
        if not order:
            return f"Error: Order ID {order_id} not found."
        
        if order["resolution_note"]:
             return f"Status for order {order_id} is '{order['status']}'. Issue already resolved: {order['resolution_note']}"

        details = f"Order {order_id} status is '{order['status']}'."
        if order.get('eta'):
            details += f" ETA: {order['eta']}."
        return details

class IssueResolverTool(BaseTool):
    name: str = "issue_resolver"
    description: str = (
        "Use this tool to log and resolve a user's issue with an order. "
        "Only call this in Phase 2 after the user confirms the details. "
        "For late deliveries, include 'confirmed' in the details when calling this tool."
    )
    args_schema: Type[BaseModel] = IssueResolverInput

    def _run(self, order_id: str, issue_type: str, details: str, missing_items: str = "", refund_amount: str = "") -> str:
        # Normalize and alias scenario labels to internal issue types
        alias_map = {
            "LATE": "late_delivery",
            "QUALITY": "poor_quality",
            "MISS": "missing_items",
            "WRONG": "wrong_order",
            "PAYMENT": "payment_issue",
            "ADDRESS": "address_error",
            "COLD": "cold_food",
        }
        norm = (issue_type or "").strip().upper()
        if norm in alias_map:
            issue_type = alias_map[norm]
        elif norm == "TRACK":
            # Tracking is not a resolution action; direct the agent to use order_tracker instead
            return "Tracking requests are handled by the order tracker tool. Please use 'order_tracker' to fetch status/ETA."
        
        print(f"\n[Tool Action]: Running IssueResolverTool for {order_id}\n")
        resolution = "the issue has been logged for review by our team and will be addressed shortly."
        if issue_type == "missing_items":
            # The tool logic remains simple, but now uses the 'details' field if 'missing_items' is empty
            items_info = missing_items or details or "the missing item"
            resolution = f"a partial refund for {items_info} has been issued."
        
        elif issue_type == "poor_quality":
            # Handles refund for poor quality food
            if refund_amount:
                resolution = f"a full refund of {refund_amount} has been credited to your account for the quality issue."
            else:
                resolution = "a full refund for the affected item has been credited to your account."

        # FIXED: 'payment_issue' now has its own separate logic
        elif issue_type == "payment_issue":
            resolution = "the billing issue has been escalated for immediate investigation. Our team will follow up via email within 24 hours."

        # FIXED: 'wrong_order' now uses the 'details' field to reflect the user's choice
        elif issue_type == "wrong_order":
            if "reship" in details.lower() or "replacement" in details.lower():
                resolution = "a replacement for the correct order has been prepared and is on its way."
            elif "refund" in details.lower():
                resolution = "a full refund has been issued for the incorrect order."
            else:
                # Fallback if details are unclear
                resolution = "the issue has been logged and we will either reship the correct order or issue a refund shortly."

        elif issue_type == "address_error":
            resolution = f"the delivery address has been updated and the driver rerouted. The new ETA will appear in your app. Details: {details}"

        # FIXED: 'cold_food' logic now aligns with the new prompt (no discount)
        elif issue_type == "cold_food":
            resolution = "a formal service complaint has been logged with our delivery operations team to ensure this doesn't happen again. We take this feedback very seriously."

        elif issue_type == "late_delivery":
            # Gate credits until confirmation is present in details (Phase 2)
            if "confirm" not in (details or "").lower():
                return (
                    "Confirmation required before issuing credits for late delivery. "
                    "Ask the user to confirm the delay first (Phase 1), then call 'issue_resolver' again "
                    "with details including 'confirmed' to proceed."
                )
            resolution = (
                "delivery credits have been added to your account for the inconvenience. "
                "We apologize for the delay."
            )
            
        else:
            # A fallback for any other unhandled issue types
            resolution = f"your issue ('{details}') has been logged and escalated for review."

        database.update_order_resolution(order_id, resolution)
        return f"I have processed your request for order {order_id}. The resolution is: {resolution}"

# A list of all tools for easy import
ALL_TOOLS = [OrderTrackerTool(), IssueResolverTool()]