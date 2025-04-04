import json

from discord import ui, SelectOption, Interaction, TextStyle, ButtonStyle


class SetupMenuView(ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.config = cog.user_configs[user_id]

    @ui.select(
        placeholder="Select a setting to configure",
        options=[
            SelectOption(
                label="Entry Color",
                description="Set color for entry points",
                value="entry_color",
            ),
            SelectOption(
                label="Stop Loss Color",
                description="Set color for stop loss points",
                value="stop_loss_color",
            ),
            SelectOption(
                label="Take Profit Color",
                description="Set color for take profit points",
                value="take_profit_color",
            ),
            SelectOption(
                label="Indicators",
                description="Choose technical indicators to use",
                value="indicators",
            ),
            SelectOption(
                label="Output Format",
                description="Customize the output message format",
                value="output_format",
            ),
        ],
    )
    async def select_setting(self, interaction: Interaction, select: ui.Select):
        setting = select.values[0]

        if setting == "entry_color":
            view = ColorSelectView(self.cog, self.user_id, "entry_color", "Entry Point")
            await interaction.response.edit_message(
                content="Select the color to use for entry points:", view=view
            )
        elif setting == "stop_loss_color":
            view = ColorSelectView(
                self.cog, self.user_id, "stop_loss_color", "Stop Loss"
            )
            await interaction.response.edit_message(
                content="Select the color to use for stop loss points:", view=view
            )
        elif setting == "take_profit_color":
            view = ColorSelectView(
                self.cog, self.user_id, "take_profit_color", "Take Profit"
            )
            await interaction.response.edit_message(
                content="Select the color to use for take profit points:", view=view
            )
        elif setting == "indicators":
            view = IndicatorsView(self.cog, self.user_id)
            await interaction.response.edit_message(
                content="Select the technical indicators to use:", view=view
            )
        elif setting == "output_format":
            view = OutputFormatView(self.cog, self.user_id)
            await interaction.response.edit_message(
                content="Customize the output format:", view=view
            )

    @ui.button(label="View Current Settings", style=ButtonStyle.secondary)
    async def view_settings(self, interaction: Interaction, button: ui.Button):

        settings = self.cog.user_configs[self.user_id]
        settings_display = (
            f"**Current Settings**\n"
            f"Entry Color: {settings['entry_color']}\n"
            f"Stop Loss Color: {settings['stop_loss_color']}\n"
            f"Take Profit Color: {settings['take_profit_color']}\n"
            f"Indicators: {', '.join(settings['indicators'])}\n"
            f"Output Format: `{settings['output_format']}`"
        )
        await interaction.response.edit_message(content=settings_display, view=self)

    @ui.button(label="Reset to Default", style=ButtonStyle.danger)
    async def reset_settings(self, interaction: Interaction, button: ui.Button):

        config_path = "src/config/chart_config.json"
        with open(config_path, "r") as file:
            default_config = json.load(file)

        self.cog.user_configs[self.user_id] = default_config.copy()
        self.config = default_config.copy()

        await interaction.response.edit_message(
            content="Settings have been reset to default values.", view=self
        )


class ColorSelectView(ui.View):
    def __init__(self, cog, user_id, setting_key, setting_name):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.setting_key = setting_key
        self.setting_name = setting_name

    @ui.select(
        placeholder="Select a color",
        options=[
            SelectOption(label="Green", value="green"),
            SelectOption(label="Red", value="red"),
            SelectOption(label="Blue", value="blue"),
            SelectOption(label="Yellow", value="yellow"),
            SelectOption(label="Purple", value="purple"),
            SelectOption(label="Orange", value="orange"),
        ],
    )
    async def select_color(self, interaction: Interaction, select: ui.Select):
        self.cog.user_configs[self.user_id][self.setting_key] = select.values[0]

        await interaction.response.edit_message(
            content=f"{self.setting_name} color set to {select.values[0]}.",
            view=SetupMenuView(self.cog, self.user_id),
        )

    @ui.button(label="Back", style=ButtonStyle.secondary)
    async def back(self, interaction: Interaction, button: ui.Button):
        await interaction.response.edit_message(
            content="Welcome to Chart Sayer Setup! Select an option to configure:",
            view=SetupMenuView(self.cog, self.user_id),
        )


class IndicatorsView(ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.selected_indicators = cog.user_configs[user_id]["indicators"].copy()

    @ui.select(
        placeholder="Select indicators",
        options=[
            SelectOption(label="Moving Average", value="moving_average"),
            SelectOption(label="Parabolic SAR", value="parabolic_sar"),
            SelectOption(label="RSI", value="rsi"),
            SelectOption(label="MACD", value="macd"),
            SelectOption(label="Bollinger Bands", value="bollinger_bands"),
        ],
        min_values=0,
        max_values=5,
    )
    async def select_indicators(self, interaction: Interaction, select: ui.Select):
        self.selected_indicators = select.values

        await interaction.response.edit_message(
            content=f"Selected indicators: {', '.join(select.values) if select.values else 'None'}\n"
            f"Click Save to apply these changes.",
            view=self,
        )

    @ui.button(label="Save", style=ButtonStyle.primary)
    async def save(self, interaction: Interaction, button: ui.Button):
        self.cog.user_configs[self.user_id]["indicators"] = self.selected_indicators

        await interaction.response.edit_message(
            content=f"Indicators updated to: {', '.join(self.selected_indicators) if self.selected_indicators else 'None'}",
            view=SetupMenuView(self.cog, self.user_id),
        )

    @ui.button(label="Back", style=ButtonStyle.secondary)
    async def back(self, interaction: Interaction, button: ui.Button):
        await interaction.response.edit_message(
            content="Welcome to Chart Sayer Setup! Select an option to configure:",
            view=SetupMenuView(self.cog, self.user_id),
        )


class OutputFormatView(ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id

    @ui.select(
        placeholder="Select an output format",
        options=[
            SelectOption(
                label="Standard",
                description="Entry: {entry}, Stop Loss: {stop_loss}, Take Profit: {take_profit}",
                value="Entry: {entry}, Stop Loss: {stop_loss}, Take Profit: {take_profit}",
            ),
            SelectOption(
                label="Detailed",
                description="Entry Point: {entry} | SL: {stop_loss} | TP: {take_profit}",
                value="Entry Point: {entry} | SL: {stop_loss} | TP: {take_profit}",
            ),
            SelectOption(
                label="Minimal",
                description="E:{entry} SL:{stop_loss} TP:{take_profit}",
                value="E:{entry} SL:{stop_loss} TP:{take_profit}",
            ),
        ],
    )
    async def select_format(self, interaction: Interaction, select: ui.Select):
        self.cog.user_configs[self.user_id]["output_format"] = select.values[0]

        await interaction.response.edit_message(
            content=f"Output format updated to: `{select.values[0]}`",
            view=SetupMenuView(self.cog, self.user_id),
        )

    @ui.button(label="Custom Format", style=ButtonStyle.primary)
    async def custom_format(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(CustomFormatModal(self.cog, self.user_id))

    @ui.button(label="Back", style=ButtonStyle.secondary)
    async def back(self, interaction: Interaction, button: ui.Button):
        await interaction.response.edit_message(
            content="Welcome to Chart Sayer Setup! Select an option to configure:",
            view=SetupMenuView(self.cog, self.user_id),
        )


class CustomFormatModal(ui.Modal, title="Custom Output Format"):
    format_input = ui.TextInput(
        label="Format String",
        placeholder="Entry: {entry}, Stop Loss: {stop_loss}, Take Profit: {take_profit}",
        required=True,
        style=TextStyle.paragraph,
    )

    def __init__(self, cog, user_id):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.format_input.default = cog.user_configs[user_id]["output_format"]

    async def on_submit(self, interaction: Interaction):

        format_str = self.format_input.value
        required_placeholders = ["{entry}", "{stop_loss}", "{take_profit}"]

        valid = all(placeholder in format_str for placeholder in required_placeholders)

        if valid:

            self.cog.user_configs[self.user_id]["output_format"] = format_str

            await interaction.response.edit_message(
                content=f"Output format updated to: `{format_str}`",
                view=SetupMenuView(self.cog, self.user_id),
            )
        else:
            await interaction.response.edit_message(
                content="Invalid format string. Must contain {entry}, {stop_loss}, and {take_profit} placeholders.",
                view=OutputFormatView(self.cog, self.user_id),
            )
