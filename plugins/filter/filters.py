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

from ansible import errors


def sort_publications(pubs):
    """Sort a list of publications by repository version.

    Higher repository versions are listed first.
    """
    def key(pub):
        # Format: /pulp/api/v3/repositories/rpm/rpm/<repo UUID>/versions/<version>/
        rv = pub["repository_version"]
        return int(rv.split("/")[-2])

    return sorted(pubs, key=key, reverse=True)


def find_publication_for_distribution(dist, repos, pubs, dists):
    """Find a publication to distribute.

    The distribution object, `dist`, may include different fields to control
    the search:

    * repository: use latest version
    * repository & version: use a specific version
    * distribution: use the same publication as another distribution

    :param dist: Distribution to find a publication for.
    :param repos: Existing repos in Pulp.
    :param pubs: Existing publications in Pulp.
    :param dists: Existing distributions in Pulp.
    """
    if dist.get("state") == "absent":
        return

    if "repository" in dist:
        if "distribution" in dist:
            raise errors.AnsibleFilterError("Cannot specify 'distribution' with 'repository'")
        repository = dist["repository"]
        repository_href = [repo for repo in repos if repo["name"] == repository][0]["pulp_href"]
        if "version" in dist:
            version = dist["version"]
            version_href = "%sversions/%d/" % (repository_href, version)
        else:
            version_href = None

        for pub in pubs:
            if pub["repository"] == repository_href:
                if not version_href or version_href == pub["repository_version"]:
                    return pub
    elif "distribution" in dist:
        if "version" in dist:
            raise errors.AnsibleFilterError("Cannot specify 'version' with 'distribution'")
        other_dist = dist["distribution"]
        pub_href = [d for d in dists if d["name"] == other_dist][0]["publication"]
        for pub in pubs:
            if pub["pulp_href"] == pub_href:
                return pub
    raise errors.AnsibleFilterError("Could not find a matching publication")


def publication_has_distributions(pub, pubs, dists):
    """Return whether a publication has any distributions.

    :param pub: Publication to find a distribution for.
    :param pubs: Existing publications in Pulp.
    :param dists: Existing distributions in Pulp.
    """
    if not pub:
        return False
    pub_href = pub["pulp_href"]
    for dist in dists:
        if dist["publication"] == pub_href:
            return True
    return False


class FilterModule(object):

    def filters(self):
        return {
            "sort_publications": sort_publications,
            "find_publication_for_distribution": find_publication_for_distribution,
            "publication_has_distributions": publication_has_distributions,
        }
