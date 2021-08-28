#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Type, Dict, NoReturn

from hoshino import Service, R
from hoshino.typing import CQEvent, MessageSegment

import os
import json
import random
import aiofiles
import aiorwlock
from . import _meme_generator as meme_generator

sv = Service('表情包生成器', help_='''
[memelist] 查看可用表情包模版
[memeprev] 查看表情包模版预览
[memeset 名称] 设定表情包
[memegen 文字] 生成表情包，支持多区域、多行
'''.strip())

PATH_ROOT = os.path.dirname(os.path.abspath(__file__))
PATH_CONFIG = os.path.join(PATH_ROOT, 'config.json')

LOCK_CONFIG = aiorwlock.RWLock()

async def load_config() -> Dict:
	if not os.path.isfile(PATH_CONFIG):
		sv.logger.error(f"config file \"{PATH_CONFIG}\" not found")
		return {}
	async with LOCK_CONFIG.reader_lock:
		async with aiofiles.open(PATH_CONFIG, 'r') as f:
			config = json.loads(await f.read())
	return config

async def save_config(config: Dict) -> NoReturn:
	async with LOCK_CONFIG.writer_lock:
		async with aiofiles.open(PATH_CONFIG, 'w') as f:
			await f.write(json.dumps(config))

def get_user_image_res(uid: str) -> Type[R.ResImg]:
	image_dir = os.path.join('meme_generator', 'image')
	image_dir_R = R.img(image_dir)
	if not os.path.isdir(image_dir_R.path):
		os.makedirs(image_dir_R.path)
	image_path = os.path.join(image_dir, f"{uid}.png")
	image_path_R = R.img(image_path)
	return image_path_R

@sv.on_fullmatch('memelist')
async def memelist(bot, ev: CQEvent):
	msg = '使用 memeset [标识符] 进行设定\n' + ', '.join(meme_generator.get_templates_all().keys())
	await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('memeprev')
async def memeprev(bot, ev: CQEvent):
	uid = str(ev.user_id)
	img_res = get_user_image_res(uid)
	(await meme_generator.get_previews_all(meme_generator.get_templates_all())).save(img_res.path)
	await bot.send(ev, img_res.cqcode, at_sender=True)

@sv.on_prefix('memeset')
async def memeset(bot, ev: CQEvent):
	msg = str(ev.message).strip()
	uid = str(ev.user_id)
	all_templates = meme_generator.get_templates_all()
	templates = meme_generator.get_templates(msg, all_templates)
	if templates:
		if len(templates) == 1:
			await bot.send(ev, f"表情包已更换为[{msg}]"+MessageSegment.image(f"file:///{list(templates.values())[0][0]}"), at_sender=True)
		else:
			await bot.send(ev, f"表情包已更换为[{msg}]\n每次将从下列表情中随机选择\n{templates.keys()}", at_sender=True)
		config = await load_config()
		config[uid] = msg
		await save_config(config)
	else:
		await bot.send(ev, '找不到此表情包', at_sender=True)

@sv.on_suffix('.meme')
@sv.on_prefix('memegen')
async def memegen(bot, ev: CQEvent):
	msg = ev.message.extract_plain_text()
	msg = msg.split('\n')
	uid = str(ev.user_id)
	config = await load_config()
	name = config.get(uid, '')
	all_templates = meme_generator.get_templates_all()
	templates = meme_generator.get_templates(name, all_templates)
	if not templates:
		templates = all_templates
	name = random.choice(list(templates.keys()))
	sv.logger.info(f"choice meme [{name}]")
	template = templates[name]
	(meme, meme_config) = await meme_generator.load_templates(template)
	for i in range(min(len(meme_config), len(msg))):
		_config = meme_generator.set_default_config(meme_config[i])
		text = msg[i].replace(r'\n', '\n')
		img = meme_generator.get_text_image(text, _config)
		img = meme_generator.resize_text_image(img, _config)
		img = meme_generator.transform_text_image(img, _config)
		meme_generator.paste_to_meme_image(img, meme, _config)
	img_res = get_user_image_res(uid)
	meme.save(img_res.path)
	await bot.send(ev, img_res.cqcode, at_sender=True)
