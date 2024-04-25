# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for googlefuzztest engine."""
# pylint: disable=unused-argument

import os
import unittest
import sys

from clusterfuzz._internal.bot.fuzzers import engine_common
from clusterfuzz._internal.bot.fuzzers.googlefuzztest import engine

TEST_PATH = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(TEST_PATH, 'test_data')
TEMP_DIR = os.path.join(TEST_PATH, 'temp')
FAILING_TEST_DIR_SUFFIX = "failing_fuzz_test"
PASSING_TEST_DIR_SUFFIX = "passing_fuzz_test"


class UnitTest(unittest.TestCase):
  """Unit tests."""

  def setUp(self):
    os.chmod(
        os.path.join(DATA_DIR, FAILING_TEST_DIR_SUFFIX,
                     FAILING_TEST_DIR_SUFFIX), 0o755)
    os.chmod(
        os.path.join(DATA_DIR, PASSING_TEST_DIR_SUFFIX,
                     PASSING_TEST_DIR_SUFFIX), 0o755)

  def test_googlefuzztest_invoked_with_low_log_volume(self):
    """Test if we call fuzztest with the correct abseil flags to reduce logging volume."""
    engine_impl = engine.Engine()
    target_path = engine_common.find_fuzzer_path(DATA_DIR,
                                                 PASSING_TEST_DIR_SUFFIX)
    options = engine_impl.prepare(None, target_path, DATA_DIR)
    results = engine_impl.fuzz(target_path, options, TEMP_DIR, 10)
    
    print(results.logs, file=sys.stderr)

    self.assertIn("--logtostderr", results.command)
    self.assertIn("--minloglevel=3", results.command)

  def test_fuzz_no_crash(self):
    """Test fuzzing (no crash)."""
    engine_impl = engine.Engine()
    target_path = engine_common.find_fuzzer_path(DATA_DIR,
                                                 PASSING_TEST_DIR_SUFFIX)
    options = engine_impl.prepare(None, target_path, DATA_DIR)
    results = engine_impl.fuzz(target_path, options, TEMP_DIR, 10)

    print(results.logs, file=sys.stderr)

    self.assertEqual(len(results.crashes), 0)

  def test_fuzz_crash(self):
    """Test fuzzing that results in a crash."""
    engine_impl = engine.Engine()
    target_path = engine_common.find_fuzzer_path(DATA_DIR,
                                                 FAILING_TEST_DIR_SUFFIX)
    options = engine_impl.prepare(None, target_path, DATA_DIR)
    results = engine_impl.fuzz(target_path, options, TEMP_DIR, 10)
    self.assertGreater(len(results.crashes), 0)
    crash = results.crashes[0]

    print(results.logs, file=sys.stderr)

    self.assertIn("ERROR: AddressSanitizer: heap-buffer-overflow on address",
                  crash.stacktrace)