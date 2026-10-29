# Documentation site maintenance

The public site is https://owebeeone.github.io/yidl-lifecycle/.
It is built from `docs/` using MkDocs Material. Source-only links to examples,
implementation files or contributor records resolve to GitHub; these files
are not copied into the public site. Validation logs are excluded.

## Preview and verify

From the repository root, use a separate environment:

```sh
python -m venv build/docs-env
build/docs-env/bin/python -m pip install -r docs-requirements.txt
build/docs-env/bin/python -m pip install .
ASTICHI_LOWER_ENGINE=python YIDL_LIFECYCLE_CACHE=off build/docs-env/bin/python dev-docs/documentation/verify_examples.py
build/docs-env/bin/python -m mkdocs build --strict
build/docs-env/bin/python dev-docs/documentation/check_site.py build/docs-site
build/docs-env/bin/python -m mkdocs serve --dev-addr 127.0.0.1:8000
```

On Windows, use the environment's `Scripts/python.exe`. The example checker
uses the installed package and published dependencies, not sibling source
checkouts. It executes runnable examples, tutorial continuations and documented
output checks. The site checker verifies local HTML links, anchors, assets,
search content and exclusions.

## Publish

The `Documentation` Actions workflow checks pull requests and deploys successful
documentation updates pushed to `main`. A manual run on `main` also deploys;
pull requests and other refs cannot deploy. This is the current documentation
for the package, not a versioned archive of every release.

Pages uses the Actions publishing source and the `github-pages` environment,
restricted to `main`. Only the deployment job receives Pages/OIDC write
permissions. This workflow does not create a release, tag or PyPI upload.
Package releases continue to use Gearu and the separate publishing workflow.

After deployment, verify the home page, getting started, navigation/search and
a guide/reference page. To correct documentation, push a reviewed correction
to `main`; do not move package release tags. The root Pages URL and project
path in `mkdocs.yml` must agree with repository settings.
