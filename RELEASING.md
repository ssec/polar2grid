# Releasing the Polar2Grid Python Package

1. Update pyproject.toml with the new version.
2. Create a git tag for the new version:

   ```bash
   git tag -a vX.Y.Z -m "Version X.Y.Z"
   ```

3. Push the tag to github:

   ```bash
   git push --follow-tags
   ```

4. Create a GitHub release for this tag with name "Version X.Y.Z" and add
   release notes to the description.
5. The GitHub release will trigger various GitHub jobs to run. Make sure they succeed.
