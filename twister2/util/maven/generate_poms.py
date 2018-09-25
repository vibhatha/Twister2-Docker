# Copyright (C) 2017 The Dagger Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
from subprocess import check_output
import sys
from workspace_parser import maven_artifacts
from xml_formatting import generate_pom


def _shell(command):
  output = check_output(command,
                        shell=True,
                        stderr=open(os.devnull)).strip()
  return output.splitlines()

def deps_of(label):
  return _shell(
      """bazel query 'let deps = labels(deps, {0}) in $deps
      except attr(tags, "maven:(compile_only|merged|shaded)", $deps)
      '""".format(label))

def exports_for(label):
  return _shell('bazel query "labels(exports, %s)"' % label)

def pom_deps(label):
  accumulated_deps = set()
  for dep in deps_of(label):
    if dep.startswith("@local_jdk//:"): continue
    if dep.startswith(('//:', '//third_party:')):
      for export in exports_for(dep):
        accumulated_deps.add(export)
        accumulated_deps.update(pom_deps(export))
    else:
      accumulated_deps.add(dep)

  return accumulated_deps


GROUP = 'edu.iu.dsc.twister2'

METADATA = {
    '//twister2/data/src/main/java:data-java': {
        'name': 'twister2-data',
        'artifact': 'data',
    },
    '//twister2/common/src/java:common-java': {
        'name': 'twister2-common',
        'artifact': 'common',
    },
    '//twister2/common/src/java:config-java': {
        'name': 'twister2-config',
        'artifact': 'config',
    },
    '//twister2/api/src/java:api-java': {
        'name': 'twister2-api',
        'artifact': 'api',
    },
    '//twister2/comms/src/java:comms-java': {
        'name': 'twister2-comms',
        'artifact': 'comms',
    },
    '//twister2/resource-scheduler/src/java:resource-scheduler-java': {
        'name': 'twister2-resource-scheduler',
        'artifact': 'resource-scheduler',
    },
    '//twister2/proto:proto-resource-scheduler-java': {
        'name': 'twister2-proto-resource-scheduler',
        'artifact': 'proto-resource-scheduler',
    },
    '//twister2/proto:proto-taskscheduleplan-java': {
        'name': 'twister2-proto-taskscheduleplan-java',
        'artifact': 'proto-taskscheduleplan',
    },
    '//twister2/task/src/main/java:task-java': {
        'name': 'twister2-task',
        'artifact': 'task',
    },
    '//twister2/proto:proto_job_java': {
        'name': 'twister2-proto-job',
        'artifact': 'proto_job',
    },
    '//twister2/proto:proto_resource_scheduler_java': {
        'name': 'twister2-proto-resource-scheduler',
        'artifact': 'proto_resource_scheduler',
    },
    '//twister2/proto:proto_job_state_java': {
        'name': 'twister2-proto-job-state',
        'artifact': 'proto_job_state',
    },
    '//twister2/proto:proto_common_java': {
        'name': 'twister2-proto-common',
        'artifact': 'proto_common',
    },
    '//twister2/proto:proto_taskscheduleplan_java': {
        'name': 'twister2-proto-taskchedulerplan',
        'artifact': 'proto_task_scheduler_plan',
    },
    '//gwt:gwt': {
        'name': 'Dagger GWT',
        'artifact': 'dagger-gwt',
        'manual_dependencies': [
            'com.google.dagger:dagger:${project.version}',
            'com.google.dagger:dagger:${project.version}:jar:sources',
            'javax.inject:javax.inject:1:jar:sources',
        ],
    },
    '//java/dagger/internal/codegen:processor': {
        'name': 'Dagger Compiler',
        'artifact': 'dagger-compiler',
    },
    '//java/dagger/producers:producers': {
        'name': 'Dagger Producers',
        'artifact': 'dagger-producers',
    },
    '//java/dagger/model:model': {
        'name': 'Dagger SPI',
        'artifact': 'dagger-spi',
    },
    '//java/dagger/android:android': {
        'name': 'Dagger Android',
        'artifact': 'dagger-android',
        'packaging': 'aar',
    },
    '//java/dagger/android/support:support': {
        'name': 'Dagger Android Support',
        'artifact': 'dagger-android-support',
        'packaging': 'aar',
    },
    '//java/dagger/android/processor:processor': {
        'name': 'Dagger Android Processor',
        'artifact': 'dagger-android-processor',
    },
    '//java/dagger/grpc/server:server': {
        'name': 'Dagger gRPC Server',
        'artifact': 'dagger-grpc-server',
    },
    '//java/dagger/grpc/server:annotations': {
        'name': 'Dagger gRPC Server annotations',
        'artifact': 'dagger-grpc-server-annotations',
    },
    '//java/dagger/grpc/server/processor:processor': {
        'name': 'Dagger gRPC Server processor',
        'artifact': 'dagger-grpc-server-processor',
    },
    # b/37741866 and https://github.com/google/dagger/issues/715
    '//java/dagger/android:libandroid.jar': {
        'name': 'Dagger Android (Jar Impl)',
        'artifact': 'dagger-android-jarimpl',
    },
    '//java/dagger/android/support:libsupport.jar': {
        'name': 'Dagger Android Support (Jar Impl)',
        'artifact': 'dagger-android-support-jarimpl',
    },
}

def dependencies_comparator(first, second):
  if first == second:
    return 0

  first = first.split(':')
  second = second.split(':')

  if first[0] == GROUP and second[0] != GROUP:
    return -1
  if second[0] == GROUP and first[0] != GROUP:
    return 1

  # Compare each item in the list: first sort by group, then artifact
  if first < second:
    return -1
  else:
    return 1

class UnknownDependencyException(Exception): pass


def main():
  if len(sys.argv) < 3:
    print 'Usage: %s <version> <target_for_pom>...' % sys.argv[0]
    sys.exit(1)

  version = sys.argv[1]
  artifacts = maven_artifacts()

  android_sdk_pattern = re.compile(
      r'@androidsdk//([a-z.-]*):([a-z0-9-]*)-([0-9.]*)')

  for label, metadata in METADATA.iteritems():
    artifacts[label] = (
        'edu.iu.dsc.twister2:%s:%s' % (metadata['artifact'], version)
    )

  def artifact_for_dep(label):
    if label in artifacts:
      return artifacts[label]
    match = android_sdk_pattern.match(label)
    if match:
      return ':'.join(match.groups())
    raise UnknownDependencyException('No artifact found for %s' % label)

  for arg in sys.argv[2:]:
    metadata = METADATA[arg]
    with open('%s.pom.xml' % metadata['artifact'], 'w') as pom_file:
      deps = map(artifact_for_dep, pom_deps(arg))
      deps.sort(cmp=dependencies_comparator)
      pom_file.write(generate_pom(artifacts[arg], metadata, deps, version))

if __name__ == '__main__':
  main()
