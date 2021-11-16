# Copyright (c) 2021 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

def sort_publications(pubs):
    """Sort a list of publications by repository version.

    Higher repository versions are listed first.
    """
    def key(pub):
        # Format: /pulp/api/v3/repositories/rpm/rpm/<repo UUID>/versions/<version>/
        rv = pub["repository_version"]
        return int(rv.split("/")[-2])

    return sorted(pubs, key=key, reverse=True)


class FilterModule(object):

    def filters(self):
        return {
            "sort_publications": sort_publications
        }