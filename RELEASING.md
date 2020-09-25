# Releasing

pynonymizer is developed using a modified trunk-based workflow. 

pynonymizer uses [Semantic Versioning](https://semver.org/). as a CLI, we consider structural/backwards-incompatible changes to the cli interface or objects exported from the main package to be a breaking change.

Feature branches continuously merge to `master`.

## Process

1. Cut a release-branch from the trunk when you're happy with the current `HEAD` on `master`
2. make any specific changes required for the release. At minimum, you should:
   1. update `version.py` with the release version
   2. update `CHANGELOG.md`, moving the items from `Unreleased` section into a named version
3. When you're ready for release, tag the version `${MAJOR}-${MINOR}-${PATCH}` e.g. `v1.2.3`. This is the version you will deploy. **Only tags should be deployed to production**.
4. You may want to backport some of the divergent work back into master/trunk. If so, create a new branch
   cherry-picking the commits you want (usually the updates to version/changelog) and open a PR. This should be
   merged when the release is deployed.
      - Normally this will merge straight in, but in cases with significant difference the exact backport may result in an entirely different feature making it's way back into trunk. e.g.

Keep the release branch around for the lifetime of the minor version, since all patch/hotfix versions will be deployed from this branch. 

## Release Branches
Release branches follow the pattern `${MAJOR}-${MINOR}-stable`, e.g. `1-10-stable`. 

The idea behind a release branch is that it will contain any specific changes required for the release in a different branch, _and most importantly_ it 
will allow development to continue on the trunk.

The `*-stable` part of the branch name comes from the nature of hotfixes. Hotfixes are small changes on top of _releases_. 

## Hotfixes
Hotfixes are upstream work commited to a `*-stable` release-branch. The reason we do it this way is that a hotfix only has specific relevance to the release it is targeting, and there is no guarantee that the hotfix work will make it's way back into trunk it it's current form. 

Hotfixes to subsequently deprecated/removed functionality will be unable to merge back to trunk, so cherry-picking and resolving conflicts on a PR allows us to backport useful work back into trunk where it belongs.

1. Commit the hotfix work directly to the release branch. 
2. release as above, with a patch bump i.e. `v1.2.0 -> v1.2.1`. 
3. If your hotfix needs to make it's way back into trunk, produce a cherry-picked branch as with a normal release. Only pick the commits that are actually relevant to trunk. 




