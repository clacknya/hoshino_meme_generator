#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Union, Tuple, List, Dict, TypedDict, NoReturn

import os
import json
import numpy
from PIL import Image, ImageFont, ImageColor, ImageDraw
import re
import io
import aiofiles

TypeColor = Union[
	Tuple[int, int, int, Optional[int]],
	List[int, int, int, Optional[int]],
	str,
]

class TypeMemeConfig(TypedDict):
	pass

TypeFilename = str
TypeTemplate = Tuple[TypeFilename, TypeMemeConfig]
TypeMemename = str
TypeTemplates = Dict[TypeMemename, TypeTemplate]

PATH_ROOT = os.path.dirname(os.path.abspath(__file__))
PATH_TEMPLATES = os.path.join(PATH_ROOT, 'templates')
PATH_FONTS = os.path.join(PATH_ROOT, 'fonts')

class MemeGenerator():

	PATH_FONT_DEFAULT = os.path.join(PATH_FONTS, 'font.ttf')

	def __init__(self, image_file: str, config_file: str):
		self._image_file = image_file
		self._config_file = config_file

	async def __aenter__(self) -> MemeGenerator:
		image = await self.load_image()
		self.image = image.convert("RGBA")
		image.close()
		self.config = self.set_default_config(await self.load_config())
		self.font = ImageFont.truetype(
			font=self.config['font']['file'],
			size=self.config['font']['size'],
			index=0, encoding='unic', layout_engine=None,
		)
		return self

	async def __aexit__(self, exc_type, exc_value, traceback) -> NoReturn:
		self.image.close()

	async def load_image(self) -> Image.Image:
		async with aiofiles.open(self._image_file, 'rb') as f:
			return Image.open(io.BytesIO(await f.read()))

	async def load_config(self) -> TypeMemeConfig:
		async with aiofiles.open(config_file, 'r') as f:
			return json.loads(await f.read())

	def set_default_config(self, config: TypeMemeConfig) -> TypeMemeConfig:
		return config

	def get_multiline_textsize(self, lines: List[str], font: ImageFont.FreeTypeFont, spacing: Optional[int]=None) -> Tuple[int, int]:
		sizes = [font.getsize(line) for line in lines]
		return (max(sizes)[0], sum(list(zip(*sizes))[1])+spacing*(len(sizes)-1))





