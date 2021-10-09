#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import asyncio
import pprint
import linecache
import tracemalloc
import _meme_generator as meme_generator

def display_top(snapshot, key_type='lineno', limit=10):
	snapshot = snapshot.filter_traces((
		tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
		tracemalloc.Filter(False, "<unknown>"),
	))
	top_stats = snapshot.statistics(key_type)

	print("Top %s lines" % limit)
	for index, stat in enumerate(top_stats[:limit], 1):
		frame = stat.traceback[0]
		print("#%s: %s:%s: %.1f KiB"
			  % (index, frame.filename, frame.lineno, stat.size / 1024))
		line = linecache.getline(frame.filename, frame.lineno).strip()
		if line:
			print('    %s' % line)

	other = top_stats[limit:]
	if other:
		size = sum(stat.size for stat in other)
		print("%s other: %.1f KiB" % (len(other), size / 1024))
	total = sum(stat.size for stat in top_stats)
	print("Total allocated size: %.1f KiB" % (total / 1024))

async def memeprev():
	(await meme_generator.get_previews_all(meme_generator.get_templates_all())).show()

async def memegen(all_templates: dict, name: str, msg: str):
	print(f"{name=}")

	templates = meme_generator.get_templates(name, all_templates)
	pp.pprint(templates)

	if not templates:
		templates = all_templates
	
	name = random.choice(list(templates.keys()))
	template = templates[name]
	pp.pprint(template)

	(meme, config) = await meme_generator.load_templates(template)

	msg = msg.split('\n')

	for i in range(min(len(config), len(msg))):
		meme_generator.set_default_config(config[i])
		pp.pprint({f"config[{i}]": config[i]})
		text = msg[i].replace(r'\n', '\n')
		img = meme_generator.get_text_image(text, config[i])
		img = meme_generator.resize_text_image(img, config[i])
		img = meme_generator.transform_text_image(img, config[i])
		meme_generator.paste_to_meme_image(img, meme, config[i])

	meme.show()

async def test():
	all_templates = meme_generator.get_templates_all()
	pp.pprint(all_templates)

	msg = '哈哈❤哈\\n喵哈\\nAQj\n哈哈❤哈\\n喵哈\\nAQj'
	# msg = '这是一段有点长的文字\n这是一段有点长的文字'
	# msg = '龍\n龍'

	await memegen(all_templates, '本间向日葵:1', msg)

async def test_all():
	all_templates = meme_generator.get_templates_all()
	pp.pprint(all_templates)

	msg = '哈哈❤哈\\n喵哈\\nAQj\n哈哈❤哈\\n喵哈\\nAQj'
	# msg = '这是一段有点长的文字\n这是一段有点长的文字'

	for name in all_templates.keys():
		await memegen(all_templates, name, msg)

async def main():
	global pp
	pp = pprint.PrettyPrinter(indent=4)

	# await memeprev()
	# await test_all()
	await test()

if __name__ == '__main__':
	tracemalloc.start()
	meme_generator.__test__ = True
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		pass
	snapshot = tracemalloc.take_snapshot()
	display_top(snapshot)
