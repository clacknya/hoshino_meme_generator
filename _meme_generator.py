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

TypeFilename = str
TypeColor = Union[
	Tuple[int, int, int, Optional[int]],
	List[int, int, int, Optional[int]],
	str,
]

class TypeConfig(TypedDict):
	font: str
	font_size: int
	text_color: TypeColor
	text_spacing: int
	text_align: str
	text_orientation: str
	target_coords: List[
		List[float, float],
		List[float, float],
		List[float, float],
		List[float, float],
	]

TypeTemplate = Tuple[TypeFilename, TypeConfig]
TypeTemplates = Dict[str, TypeTemplate]

__test__ = False

PATH_ROOT = os.path.dirname(os.path.abspath(__file__))
PATH_TEMPLATES = os.path.join(PATH_ROOT, 'templates')
PATH_FONTS = os.path.join(PATH_ROOT, 'fonts')
PATH_FONT_DEFAULT = os.path.join(PATH_FONTS, 'font.ttf')

SEP = ':'

def find_coeffs(source_coords: list, target_coords: list) -> numpy.ndarray:
	matrix = []
	for s, t in zip(source_coords, target_coords):
		matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
		matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
	A = numpy.matrix(matrix, dtype=float)
	B = numpy.array(source_coords).reshape(8)
	res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
	return numpy.array(res).reshape(8)

def set_default_config(config: dict={}) -> dict:
	config.setdefault('font', PATH_FONT_DEFAULT)
	config.setdefault('font_size', 60)
	config.setdefault('text_color', (0, 0, 0, 255))
	config.setdefault('text_spacing', 4)
	config.setdefault('text_align', 'center')
	config.setdefault('text_orientation', 'horizontal')
	if isinstance(config['text_color'], str):
		config['text_color'] = ImageColor.getrgb(config['text_color'])
	elif isinstance(config['text_color'], list):
		config['text_color'] = tuple(config['text_color'])
	if not os.path.isfile(config['font']):
		config['font'] = os.path.join(PATH_FONTS, config['font'])
	return config

# def get_inner_box_coords(config: dict) -> list:
	# (X, Y) = zip(*config['target_coords'])
	# (X, Y) = (sorted(X), sorted(Y))
	# return []

def get_middle_box_coords(config: dict) -> list:
	target_coords = config['target_coords']
	assert len(target_coords) == 4
	(X, Y) = zip(*target_coords)
	X = sorted(X)
	Y = sorted(Y)
	return [((X[0]+X[1])/2, (Y[0]+Y[1])/2), ((X[-2]+X[-1])/2, (Y[-2]+Y[-1])/2)]

def get_outer_box_coords(config: dict) -> list:
	(X, Y) = zip(*config['target_coords'])
	(X, Y) = (sorted(X), sorted(Y))
	return [(X[0], Y[0]), (X[-1], Y[-1])]

async def load_image(path: str) -> Image.Image:
	async with aiofiles.open(path, 'rb') as f:
		return Image.open(io.BytesIO(await f.read()))

def get_templates_all() -> TypeTemplates:
	result = {}
	for path, dirs, files in os.walk(PATH_TEMPLATES):
		if files:
			relpath = os.path.relpath(path, PATH_TEMPLATES)
			components = relpath.split(os.sep)
			if '.' in components:
				components.remove('.')
			for filename in files:
				(basename, ext) = os.path.splitext(filename)
				if ext.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']:
					name = SEP.join(components + [basename])
					if name in result:
						continue
					config_file = basename + '.json'
					if config_file in files:
						result[name] = (
							os.path.join(path, filename),
							os.path.join(path, config_file),
						)
	return result

def get_templates(name: str, templates: dict) -> TypeTemplates:
	r = re.compile(f"^{name}($|:)")
	match = list(filter(r.match, templates.keys()))
	return {k: templates[k] for k in match}

async def load_templates(template: tuple) -> (Image.Image, TypeTemplate):
	(image_file, config_file) = template
	f = await load_image(image_file)
	image = f.convert("RGBA")
	f.close()
	async with aiofiles.open(config_file, 'r') as f:
		config = json.loads(await f.read())
	return (image, config)

async def get_previews_all(memes: dict, thumb_size: tuple=(200, 200), font_size: int=20) -> Image.Image:
	nums = len(memes)
	arrs = list(memes.items())
	cols = int(numpy.ceil(numpy.sqrt(nums)))
	rows = int(numpy.ceil(nums/cols))
	arrs = [arrs[i:i+cols] for i in range(0, nums, cols)]
	font = ImageFont.truetype(font=PATH_FONT_DEFAULT, size=font_size, index=0, encoding='unic', layout_engine=None)
	text_height = max([font.getsize(k)[1] for k in memes]) + 8
	image_size = (thumb_size[0]*cols+1, (thumb_size[1]+text_height)*rows+1)
	image = Image.new(mode='RGB', size=image_size, color='white')
	draw = ImageDraw.Draw(image)
	for k in range(nums):
		i = int(k // cols)
		j = k % cols
		thumb_x = thumb_size[0] * j
		thumb_y = (thumb_size[1] + text_height) * i
		text_center_x = thumb_x + thumb_size[0] / 2
		text_center_y = thumb_y + thumb_size[1] + text_height / 2
		# thumb = Image.open(arrs[i][j][1][0])
		thumb = await load_image(arrs[i][j][1][0])
		thumb.thumbnail(size=thumb_size, resample=Image.ANTIALIAS)
		image.paste(
			im=thumb,
			box=(
				int(thumb_x+(thumb_size[0]-thumb.size[0])/2),
				int(thumb_y+(thumb_size[1]-thumb.size[1])/2),
			),
			# mask=thumb
		)
		draw.rectangle(
			[
				(thumb_x, thumb_y),
				(thumb_x+thumb_size[0], thumb_y+thumb_size[1])
			],
			fill=None, outline='green'
		)
		thumb.close()
		text = arrs[i][j][0]
		text_size = font.getsize(text)
		draw.text(
			xy=(text_center_x, text_center_y),
			text=text,
			fill='black',
			font=font,
			anchor='mm',
			spacing=0,
			align='center',
			# direction=None,
			# features=None,
			# language=None,
			stroke_width=0,
			stroke_fill=None,
			embedded_color=False
		)
	return image

def get_multiline_textsize(lines: list, font: ImageFont.FreeTypeFont, spacing: int=4) -> tuple:
	sizes = [font.getsize(line) for line in lines]
	return (max(sizes)[0], sum(list(zip(*sizes))[1])+spacing*(len(sizes)-1))

def get_text_image(text: str, config: dict={}) -> Image.Image:

	font = ImageFont.truetype(font=config['font'], size=config['font_size'], index=0, encoding='unic', layout_engine=None)

	if config['text_orientation'] == 'horizontal':

		text_lines = text.split('\n')
		text_size = get_multiline_textsize(text_lines, font, config['text_spacing'])

		text_image = Image.new(mode='RGBA', size=text_size, color=0)

		text_draw = ImageDraw.Draw(text_image)

		if __test__:
			top = 0
			ascent, descent = font.getmetrics()
			for text_line in text_lines:
				line_size = font.getsize(text_line)
				(width, height), (offset_x, offset_y) = font.font.getsize(text_line)
				width = text_size[0]
				text_draw.rectangle([(0, top), (width, top+offset_y)], fill=(237, 127, 130))              # Red
				text_draw.rectangle([(0, top+offset_y), (width, top+ascent)], fill=(202, 229, 134))       # Green
				text_draw.rectangle([(0, top+ascent), (width, top+ascent+descent)], fill=(134, 190, 229)) # Blue
				top += line_size[1] + config['text_spacing']

		top = 0
		for text_line in text_lines:
			line_size = font.getsize(text_line)
			anchor = None
			if config['text_align'] == 'left':
				x = 0
				anchor = 'la'
			elif config['text_align'] == 'center':
				x = int(text_size[0]/2)
				anchor = 'ma'
			elif config['text_align'] == 'right':
				x = text_size[0]
				anchor = 'ra'
			else:
				raise ValueError('unsupported text_align value')
			text_draw.text(
				xy=(x, top),
				text=text_line,
				fill=config['text_color'],
				font=font,
				anchor=anchor,
				spacing=0,
				align='left',
				# direction=None,
				# features=None,
				# language=None,
				stroke_width=0,
				stroke_fill=None,
				embedded_color=True,
			)
			top += line_size[1] + config['text_spacing']

	elif config['text_orientation'] == 'vertical':
		pass
	else:
		raise ValueError('unsupported text_orientation value')

	return text_image

def resize_text_image(img: Image.Image, config: dict={}) -> Image.Image:

	[(x_min, y_min), (x_max, y_max)] = get_middle_box_coords(config)

	size = (int(x_max-x_min), int(y_max-y_min))

	img.thumbnail(size=size, resample=Image.ANTIALIAS)

	new = Image.new(mode='RGBA', size=size, color=0)

	new.paste(
		im=img,
		box=(
			int((new.size[0]-img.size[0])/2),
			int((new.size[1]-img.size[1])/2),
		),
		mask=img
	)

	return new

def transform_text_image(img: Image.Image, config: dict={}) -> Image.Image:

	# clockwise
	source_coords = [
		(0, 0),
		(img.size[0], 0),
		(img.size[0], img.size[1]),
		(0, img.size[1]),
	]

	target_coords = config['target_coords']

	(X, Y) = zip(*target_coords)

	X = sorted(X)
	Y = sorted(Y)

	target_coords_diff = [(p[0]-X[0], p[1]-Y[0]) for p in target_coords]

	coeffs = find_coeffs(source_coords, target_coords_diff)

	size = (int(X[-1]-X[0]), int(Y[-1]-Y[0]))

	new = Image.new(mode='RGBA', size=size, color=0)
	new.paste(im=img, box=(0, 0), mask=img)
	new = new.transform(size, method=Image.PERSPECTIVE, data=coeffs, resample=Image.BICUBIC, fill=1, fillcolor=None)

	return new

def paste_to_meme_image(img: Image.Image, meme: Image.Image, config: dict={}):

	if __test__:
		ImageDraw.Draw(meme).rectangle(get_middle_box_coords(config), fill=None, outline='green')

	[(x_min, y_min), (x_max, y_max)] = get_outer_box_coords(config)

	meme.paste(
		im=img,
		box=(
			int((x_min+x_max-img.size[0])/2),
			int((y_min+y_max-img.size[1])/2),
		),
		mask=img
	)

if __name__ == '__main__':
	__test__ = True
