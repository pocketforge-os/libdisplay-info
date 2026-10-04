#!/usr/bin/env python3

import configparser
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORK_URL = "https://github.com/pocketforge-os/v4l-utils.git"
PIN = "1316a80455ef70889bea89491f37cd69170f3ee7"
IMAGE_TAG = "2026-10-04.0"


def validate_wrap(path):
	parser = configparser.ConfigParser(interpolation=None)
	with path.open(encoding="utf-8") as stream:
		parser.read_file(stream)
	if parser.sections() != ["wrap-git"]:
		raise ValueError("expected one wrap-git section")
	if parser.get("wrap-git", "url", fallback="") != FORK_URL:
		raise ValueError("v4l-utils wrap does not use the PocketForge fork")
	revision = parser.get("wrap-git", "revision", fallback="")
	if revision != PIN or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
		raise ValueError("v4l-utils wrap is not pinned to the admitted commit")


def validate_ci(text):
	if f"FDO_DISTRIBUTION_TAG: '{IMAGE_TAG}'" not in text:
		raise ValueError("CI image tag does not cover the PocketForge source recipe")
	if f"V4L_UTILS_COMMIT: {PIN}" not in text:
		raise ValueError("CI v4l-utils pin does not match the admitted commit")
	if f"git clone {FORK_URL}" not in text:
		raise ValueError("CI does not clone the PocketForge v4l-utils fork")
	if "git checkout $V4L_UTILS_COMMIT" not in text:
		raise ValueError("CI does not check out its immutable v4l-utils pin")


def validate_meson(text):
	if "find_program('python3', native: true)" not in text:
		raise ValueError("Meson does not locate the Python test runner")
	pattern = (
		r"test\(\s*'pocketforge-source-locator',\s*\w+,\s*"
		r"args:\s*files\('pocketforge-source-locator.py'\),?\s*\)"
	)
	if re.search(pattern, text) is None:
		raise ValueError("Meson does not register the source locator test")


class SourceLocatorTests(unittest.TestCase):
	def test_repository_locator_is_pinned(self):
		validate_wrap(ROOT / "subprojects" / "v4l-utils.wrap")
		validate_ci((ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8"))

	def test_repository_locator_is_registered(self):
		validate_meson((ROOT / "test" / "meson.build").read_text(encoding="utf-8"))

	def test_exact_locator_is_accepted(self):
		with tempfile.TemporaryDirectory() as temp_dir:
			path = Path(temp_dir) / "v4l-utils.wrap"
			path.write_text(
				f"[wrap-git]\nurl = {FORK_URL}\nrevision = {PIN}\n",
				encoding="utf-8",
			)
			validate_wrap(path)
			validate_ci(
				f"FDO_DISTRIBUTION_TAG: '{IMAGE_TAG}'\n"
				f"V4L_UTILS_COMMIT: {PIN}\n"
				f"git clone {FORK_URL}\n"
				"git checkout $V4L_UTILS_COMMIT\n"
			)
			validate_meson(
				"pocketforge_source_locator = find_program('python3', native: true)\n"
				"test(\n"
				"\t'pocketforge-source-locator',\n"
				"\tpocketforge_source_locator,\n"
				"\targs: files('pocketforge-source-locator.py'),\n"
				")\n"
			)

	def test_mutable_revision_is_rejected(self):
		with tempfile.TemporaryDirectory() as temp_dir:
			path = Path(temp_dir) / "v4l-utils.wrap"
			path.write_text(
				f"[wrap-git]\nurl = {FORK_URL}\nrevision = HEAD\n",
				encoding="utf-8",
			)
			with self.assertRaises(ValueError):
				validate_wrap(path)

	def test_upstream_ci_url_is_rejected(self):
		with self.assertRaises(ValueError):
			validate_ci(
				f"FDO_DISTRIBUTION_TAG: '{IMAGE_TAG}'\n"
				f"V4L_UTILS_COMMIT: {PIN}\n"
				"git clone https://git.linuxtv.org/v4l-utils.git\n"
				"git checkout $V4L_UTILS_COMMIT\n"
			)

	def test_stale_ci_image_tag_is_rejected(self):
		with self.assertRaises(ValueError):
			validate_ci(
				"FDO_DISTRIBUTION_TAG: '2025-01-20.0'\n"
				f"V4L_UTILS_COMMIT: {PIN}\n"
				f"git clone {FORK_URL}\n"
				"git checkout $V4L_UTILS_COMMIT\n"
			)

	def test_unregistered_locator_is_rejected(self):
		with self.assertRaises(ValueError):
			validate_meson("test('another-test', another_test)\n")


if __name__ == "__main__":
	unittest.main(verbosity=2)
