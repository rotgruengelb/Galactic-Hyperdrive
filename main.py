import random
import os
import sys

package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'packages')
sys.path.insert(0, package_dir)

import discord
from discord.ext import commands
import nacl
from gtts import gTTS
import wavelink

bot = discord.Bot()

async def connect_nodes():
    """Connect to our Lavalink nodes."""
    await bot.wait_until_ready() # wait until the bot is ready

    await wavelink.NodePool.create_node(
        bot=bot,
        host='localhost',
        port=2333,
        password='youshallnotpass'
    ) # create a node


bot = discord.Bot()
connections = {}

def bot_run(token_location):
    token_file = (open(token_location))
    bot_token = str(token_file.readline())
    print(token_file)
    bot.run(bot_token)
    token_file.close

@bot.command()
async def record(ctx, recording_name: str):  # If you're using commands.Bot, this will also work.
    voice = ctx.author.voice

    if not voice:
        await ctx.respond("You aren't in a voice channel!")

    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.WaveSink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel  # The channel to disconnect from.
    )
    await ctx.respond("Started recording!")

async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):  # Our voice client already passes these in.
    
    print(args)

    recorded_users = [  # A list of recorded users
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    await sink.vc.disconnect()  # Disconnect from the voice channel.
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]  # List down the files.
    await channel.send(f"finished recording audio for: {', '.join(recorded_users)}.", files=files)  # Send a message with the accumulated files.

@bot.command()
async def stop_recording(ctx):
    if ctx.guild.id in connections:  # Check if the guild is in the cache.
        vc = connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        del connections[ctx.guild.id]  # Remove the guild from the cache.
        await ctx.delete()  # And delete.
    else:
        await ctx.respond("I am currently not recording here.")  # Respond with this if we aren't recording.

@bot.slash_command(name="play")
async def play(ctx, search: str):
    vc = ctx.voice_client # define our voice client

    if not vc: # check if the bot is not in a voice channel
        vc = await ctx.author.voice.channel.connect(cls=wavelink.Player) # connect to the voice channel

    if ctx.author.voice.channel.id != vc.channel.id: # check if the bot is not in the voice channel
        return await ctx.respond("You must be in the same voice channel as the bot.") # return an error message

    song = await wavelink.YouTubeTrack.search(query=search, return_first=True) # search for the song

    if not song: # check if the song is not found
        return await ctx.respond("No song found.") # return an error message

    await vc.play(song) # play the song
    await ctx.respond(f"Now playing: `{vc.source.title}`") # return a message

@bot.event
async def on_ready():
    await connect_nodes() # connect to the server

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"{node.identifier} is ready.") # print a message


bot_run(token_location=r"C:\Users\Daniel\envirorment\secrets\Galactic Hyperdrive\token.txt")
