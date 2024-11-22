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
"""Holds helpers for reuse across different tasks."""

import datetime
import os
from typing import Optional

from clusterfuzz._internal.datastore import data_handler
from clusterfuzz._internal.datastore import data_types
from clusterfuzz._internal.metrics import logs
from clusterfuzz._internal.metrics import monitoring_metrics

TESTCASE_TRIAGE_DURATION_ANALYZE_LAUNCHED_STEP = 'analyze_launched'
TESTCASE_TRIAGE_DURATION_IMPACT_COMPLETED_STEP = 'impact_completed'
TESTCASE_TRIAGE_DURATION_ANALYZE_COMPLETED_STEP = 'analyze_completed'
TESTCASE_TRIAGE_DURATION_MINIMIZE_COMPLETED_STEP = 'minimize_completed'
TESTCASE_TRIAGE_DURATION_REGRESSION_COMPLETED_STEP = 'regression_completed'
TESTCASE_TRIAGE_DURATION_ISSUE_UPDATED_STEP = 'issue_updated'


def emit_testcase_triage_duration_metric(testcase_id: int, step: str):
  testcase_upload_metadata = get_testcase_upload_metadata(testcase_id)
  if not testcase_upload_metadata:
    logs.warning(f'No upload metadata found for testcase {testcase_id},'
                 ' failed to emit TESTCASE_UPLOAD_TRIAGE_DURATION metric.')
    return
  if not testcase_upload_metadata.timestamp:
    logs.warning(
        f'No timestamp for testcase {testcase_upload_metadata.testcase_id},'
        ' failed to emit TESTCASE_UPLOAD_TRIAGE_DURATION metric.')
    return
  assert step in [
      'analyze_launched', 'analyze_completed', 'minimize_completed',
      'regression_completed', 'impact_completed', 'issue_updated'
  ]
  elapsed_time_since_upload = datetime.datetime.utcnow()
  elapsed_time_since_upload -= testcase_upload_metadata.timestamp
  elapsed_time_since_upload = elapsed_time_since_upload.total_seconds()

  testcase = data_handler.get_testcase_by_id(testcase_id)

  if not testcase:
    logs.warning(f'No testcase found with id {testcase_id},'
                 ' failed to emit TESTCASE_UPLOAD_TRIAGE_DURATION metric.')
    return

  if not testcase.job_type:
    logs.warning(f'No job_type associated to testcase {testcase_id},'
                 ' failed to emit TESTCASE_UPLOAD_TRIAGE_DURATION metric.')
    return

  labels = {
      'job': testcase.job_type,
      'step': step,
  }

  logs.info(
      f'TESTCASE_UPLOAD_TRIAGE_DURATION: adding {elapsed_time_since_upload} for {labels}.'
  )

  monitoring_metrics.TESTCASE_UPLOAD_TRIAGE_DURATION.add(
      elapsed_time_since_upload, labels=labels)


def get_testcase_upload_metadata(
    testcase_id) -> Optional[data_types.TestcaseUploadMetadata]:
  return data_types.TestcaseUploadMetadata.query(
      data_types.TestcaseUploadMetadata.testcase_id == int(testcase_id)).get()
