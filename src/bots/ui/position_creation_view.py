"""
UI components for conversational position creation in Discord.
"""

import logging
import re
import time
from typing import Dict, Optional, Any, Callable, Awaitable

from discord import ui, ButtonStyle, Interaction, SelectOption

from src.bots.utils.position_utils import (
    create_position_from_chart_data,
    get_position_details,
)
from src.positions.models import PlatformType

logger = logging.getLogger(__name__)


class PositionCreationView(ui.View):
    """
    A view for creating a position through conversation after chart analysis.
    This guides the user through the process of confirming or modifying the
    detected entry, stop loss, and take profit levels before creating a position.
    """

    def __init__(
        self,
        user_id: str,
        analysis_result: str,
        timeout: Optional[float] = 180.0,
        on_complete: Optional[Callable[[Optional[str]], Awaitable[None]]] = None,
    ):
        """
        Initialize the position creation view.

        Args:
            user_id: The Discord user ID
            analysis_result: The result of the chart analysis
            timeout: View timeout in seconds
            on_complete: Callback function to call when the position is created
        """
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.analysis_result = analysis_result
        self.on_complete = on_complete
        self.unique_id = f"{user_id}-{int(time.time())}"

        # Extract data from analysis result
        self.extracted_data = self._extract_data_from_analysis(analysis_result)

        # Initialize position data
        self.position_data = {
            "symbol": self.extracted_data.get("symbol", "UNKNOWN"),
            "entry": self.extracted_data.get("entry"),
            "take_profit": self.extracted_data.get("take_profit"),
            "stop_loss": self.extracted_data.get("stop_loss"),
            "position_type": self.extracted_data.get("position_type", "long"),
            "notes": f"Created from chart analysis: {analysis_result}",
        }

        # Add buttons based on extracted data
        if not self.position_data["symbol"] or self.position_data["symbol"] == "UNKNOWN":
            # If symbol is unknown, add a button to set it
            self.add_item(
                ui.Button(
                    label="Set Symbol",
                    custom_id=f"set_symbol_{self.unique_id}",
                    style=ButtonStyle.primary,
                )
            )

        if not self.position_data["entry"]:
            # If entry is unknown, add a button to set it
            self.add_item(
                ui.Button(
                    label="Set Entry Price",
                    custom_id=f"set_entry_{self.unique_id}",
                    style=ButtonStyle.primary,
                )
            )

        # Add type selection if it wasn't detected
        if not self.position_data["position_type"] or self.position_data["position_type"] not in [
            "long",
            "short",
        ]:
            self.add_item(PositionTypeSelect(self.unique_id))

        # Add confirmation button if we have the minimum required data
        if self.has_minimum_data():
            self.add_item(
                ui.Button(
                    label="Create Position",
                    custom_id=f"create_position_{self.unique_id}",
                    style=ButtonStyle.success,
                )
            )

        # Always add cancel button
        self.add_item(
            ui.Button(
                label="Cancel",
                custom_id=f"cancel_{self.unique_id}",
                style=ButtonStyle.danger,
            )
        )

    def _extract_data_from_analysis(self, analysis_result: str) -> Dict[str, Any]:
        """
        Extract position data from the analysis result.

        Args:
            analysis_result: The result of the chart analysis

        Returns:
            Dict with extracted data
        """
        data = {}

        # Try to extract symbol
        symbol_match = re.search(r"Symbol:?\s+([A-Z0-9]+)", analysis_result, re.IGNORECASE)
        if symbol_match:
            data["symbol"] = symbol_match.group(1).upper()
        elif "BTC" in analysis_result or "Bitcoin" in analysis_result:
            data["symbol"] = "BTCUSDT"
        elif "ETH" in analysis_result or "Ethereum" in analysis_result:
            data["symbol"] = "ETHUSDT"

        # Try to extract entry price
        entry_match = re.search(r"Entry:?\s+(\d+\.?\d*)", analysis_result)
        if entry_match:
            try:
                data["entry"] = float(entry_match.group(1))
            except (ValueError, TypeError):
                pass

        # Try to extract take profit
        tp_match = re.search(r"Take Profit:?\s+(\d+\.?\d*)", analysis_result)
        if tp_match:
            try:
                data["take_profit"] = float(tp_match.group(1))
            except (ValueError, TypeError):
                pass

        # Try to extract stop loss
        sl_match = re.search(r"Stop Loss:?\s+(\d+\.?\d*)", analysis_result)
        if sl_match:
            try:
                data["stop_loss"] = float(sl_match.group(1))
            except (ValueError, TypeError):
                pass

        # Try to determine position type
        if "long" in analysis_result.lower():
            data["position_type"] = "long"
        elif "short" in analysis_result.lower():
            data["position_type"] = "short"
        else:
            # If we have entry and take profit/stop loss, try to determine direction
            if "entry" in data and "take_profit" in data and data["take_profit"] > data["entry"]:
                data["position_type"] = "long"
            elif "entry" in data and "take_profit" in data and data["take_profit"] < data["entry"]:
                data["position_type"] = "short"
            elif "entry" in data and "stop_loss" in data and data["stop_loss"] < data["entry"]:
                data["position_type"] = "long"
            elif "entry" in data and "stop_loss" in data and data["stop_loss"] > data["entry"]:
                data["position_type"] = "short"
            else:
                # Default to long if we can't determine
                data["position_type"] = "long"

        return data

    def has_minimum_data(self) -> bool:
        """
        Check if we have the minimum required data to create a position.

        Returns:
            True if we have the minimum required data, False otherwise
        """
        return (
            self.position_data.get("symbol")
            and self.position_data.get("symbol") != "UNKNOWN"
            and self.position_data.get("entry") is not None
            and self.position_data.get("position_type") in ["long", "short"]
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        """
        Check if the user interacting with this view is the user who created it.

        Args:
            interaction: The interaction

        Returns:
            True if the user is allowed to interact with this view, False otherwise
        """
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "This isn't your position creation dialog!", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        # Clean up the view and call the completion callback with None to indicate cancellation
        if self.on_complete:
            await self.on_complete(None)

    @ui.button(label="Create Position", style=ButtonStyle.success)
    async def create_position_button(self, interaction: Interaction, button: ui.Button):
        """Create the position with the current data."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Create the position
            position = await create_position_from_chart_data(
                self.user_id, PlatformType.DISCORD, self.position_data
            )

            if position:
                # Get position details
                position_details = await get_position_details(str(position.id))

                # Send confirmation message
                await interaction.followup.send(
                    f"✅ Position created successfully!\n\n{position_details}",
                    ephemeral=True,
                )

                # Call completion callback with position ID
                if self.on_complete:
                    await self.on_complete(str(position.id))
            else:
                # Send error message
                await interaction.followup.send(
                    "❌ Failed to create position. Please try again.", ephemeral=True
                )

                # Call completion callback with None to indicate failure
                if self.on_complete:
                    await self.on_complete(None)
        except Exception as e:
            logger.error(f"Error creating position: {e}")
            await interaction.followup.send(
                "❌ An error occurred while creating the position. Please try again.",
                ephemeral=True,
            )

            # Call completion callback with None to indicate error
            if self.on_complete:
                await self.on_complete(None)

        # Disable all buttons
        for item in self.children:
            item.disabled = True

        # Update the view
        await interaction.edit_original_response(view=self)

    @ui.button(label="Cancel", style=ButtonStyle.danger)
    async def cancel_button(self, interaction: Interaction, button: ui.Button):
        """Cancel position creation."""
        await interaction.response.defer(ephemeral=True)

        # Send cancellation message
        await interaction.followup.send("Position creation cancelled.", ephemeral=True)

        # Call completion callback with None to indicate cancellation
        if self.on_complete:
            await self.on_complete(None)

        # Disable all buttons
        for item in self.children:
            item.disabled = True

        # Update the view
        await interaction.edit_original_response(view=self)

    @ui.button(label="Set Symbol", style=ButtonStyle.primary)
    async def set_symbol_button(self, interaction: Interaction, button: ui.Button):
        """Prompt the user to set the symbol."""
        # Send a modal to get the symbol
        modal = SymbolModal(self)
        await interaction.response.send_modal(modal)

    @ui.button(label="Set Entry Price", style=ButtonStyle.primary)
    async def set_entry_button(self, interaction: Interaction, button: ui.Button):
        """Prompt the user to set the entry price."""
        # Send a modal to get the entry price
        modal = EntryPriceModal(self)
        await interaction.response.send_modal(modal)


class PositionTypeSelect(ui.Select):
    """Select menu for choosing the position type."""

    def __init__(self, unique_id: str):
        """Initialize the select menu."""
        options = [
            SelectOption(
                label="Long",
                value="long",
                description="Entry → Profit: Price goes up",
                emoji="🟢",
            ),
            SelectOption(
                label="Short",
                value="short",
                description="Entry → Profit: Price goes down",
                emoji="🔴",
            ),
        ]
        super().__init__(
            placeholder="Select position type (Long/Short)",
            options=options,
            custom_id=f"position_type_select_{unique_id}",
        )

    async def callback(self, interaction: Interaction):
        """Handle selection."""
        await interaction.response.defer(ephemeral=True)

        # Get the parent view
        view: PositionCreationView = self.view

        # Update the position type
        view.position_data["position_type"] = self.values[0]

        # Send confirmation message
        await interaction.followup.send(
            f"Position type set to: {self.values[0].upper()}", ephemeral=True
        )

        # Add create button if we have the minimum required data
        if self.has_minimum_data():
            has_create_button = any(item.label == "Create Position" for item in view.children)
            if not has_create_button:
                view.add_item(
                    ui.Button(
                        label="Create Position",
                        custom_id=f"create_position_{view.unique_id}",
                        style=ButtonStyle.success,
                    )
                )

        # Update the view
        await interaction.edit_original_response(view=view)


class SymbolModal(ui.Modal, title="Set Trading Symbol"):
    """Modal for setting the trading symbol."""

    symbol = ui.TextInput(
        label="Symbol (e.g., BTCUSDT)",
        placeholder="Enter the trading pair symbol",
        required=True,
        min_length=1,
        max_length=20,
    )

    def __init__(self, parent_view: PositionCreationView):
        """Initialize the modal."""
        super().__init__(timeout=None)
        self.parent_view = parent_view

    async def on_submit(self, interaction: Interaction):
        """Handle form submission."""
        await interaction.response.defer(ephemeral=True)

        # Update the symbol
        self.parent_view.position_data["symbol"] = self.symbol.value.upper()

        # Send confirmation message
        await interaction.followup.send(
            f"Symbol set to: {self.symbol.value.upper()}", ephemeral=True
        )

        # Remove the set symbol button
        buttons_to_remove = []
        for item in self.parent_view.children:
            if isinstance(item, ui.Button) and item.custom_id == "set_symbol":
                buttons_to_remove.append(item)

        for button in buttons_to_remove:
            self.parent_view.remove_item(button)

        # Add create button if we have the minimum required data
        if self.parent_view.has_minimum_data():
            # Check if we already have a create button
            has_create_button = any(
                item.label == "Create Position" for item in self.parent_view.children
            )
            if not has_create_button:
                self.parent_view.add_item(
                    ui.Button(
                        label="Create Position",
                        custom_id=f"create_position_{self.parent_view.unique_id}",
                        style=ButtonStyle.success,
                    )
                )

        # Update the view
        await interaction.edit_original_response(view=self.parent_view)


class EntryPriceModal(ui.Modal, title="Set Entry Price"):
    """Modal for setting the entry price."""

    entry_price = ui.TextInput(
        label="Entry Price",
        placeholder="Enter the entry price (numeric value)",
        required=True,
        min_length=1,
        max_length=20,
    )

    def __init__(self, parent_view: PositionCreationView):
        """Initialize the modal."""
        super().__init__(timeout=None)
        self.parent_view = parent_view

    async def on_submit(self, interaction: Interaction):
        """Handle form submission."""
        await interaction.response.defer(ephemeral=True)

        # Validate entry price
        try:
            entry_price = float(self.entry_price.value)

            # Update the entry price
            self.parent_view.position_data["entry"] = entry_price

            # Send confirmation message
            await interaction.followup.send(f"Entry price set to: {entry_price}", ephemeral=True)

            # Remove the set entry button
            buttons_to_remove = []
            for item in self.parent_view.children:
                if isinstance(item, ui.Button) and item.custom_id == "set_entry":
                    buttons_to_remove.append(item)

            for button in buttons_to_remove:
                self.parent_view.remove_item(button)

            # Add create button if we have the minimum required data
            if self.parent_view.has_minimum_data():
                # Check if we already have a create button
                has_create_button = any(
                    item.custom_id == "create_position" for item in self.parent_view.children
                )
                if not has_create_button:
                    self.parent_view.add_item(
                        ui.Button(
                            label="Create Position",
                            custom_id="create_position",
                            style=ButtonStyle.success,
                        )
                    )

            # Update the view
            await interaction.edit_original_response(view=self.parent_view)
        except ValueError:
            # Send error message if entry price is not a valid number
            await interaction.followup.send(
                "Entry price must be a valid number. Please try again.", ephemeral=True
            )
