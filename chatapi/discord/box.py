"""
Sandbox I guess
"""
import disnake


class MyClient(disnake.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

intents = disnake.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('MTA3OTg1MDUzNjUwMjgyOTEzNg.GokFWW.MrfXK8bZGcJ_wG09yiAKjvVMiXIy-rnOMLU8pI')
