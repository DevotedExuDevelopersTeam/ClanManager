from asyncio import TimeoutError

from disnake import MessageInteraction
from disnake.ui import Button, View


class ClansButtonsView(View):
    def __init__(self, user_id: int, *button_names: str):
        super().__init__()
        self.user_id = user_id
        self.res: str = None
        for name in button_names:
            self.add_item(CustomButton(name))

    async def interaction_check(self, inter: MessageInteraction):
        if inter.author.id == self.user_id:
            return True
        else:
            await inter.send(f"This button is not for you.", ephemeral=True)
            return False

    async def get_result(self):
        if await self.wait():
            raise TimeoutError()

        return self.res


class CustomButton(Button):
    def __init__(self, label, **kwargs):
        super().__init__(label=label, **kwargs)

    async def callback(self, inter: MessageInteraction):
        view: ClansButtonsView = self.view
        view.res = self.label
        view.stop()
