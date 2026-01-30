from typing import Optional

from discord import Embed, Colour


def embed(description: str, colour: Colour = Colour.blue(), title: Optional[str] = None,
          thumbnail: Optional[str] = None) -> Embed:
	embed_object: Embed = Embed(description=description, colour=colour)

	if title:
		embed_object.title = title

	if thumbnail:
		embed_object.set_thumbnail(url=thumbnail)

	return embed_object


def success_embed(description: str) -> Embed:
	return embed(description, Colour.green())


def error_embed(description: str) -> Embed:
	return embed(description, Colour.red())
