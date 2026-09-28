---
name: capstone-repo-bootstrap
description: 'Create a GitHub repository for the CAPSTONE project and connect an existing local project when authorized. Use for GitHub repository creation, choosing visibility, setting up a remote origin, or handling GitHub-MCP-only limits.'
argument-hint: 'Provide the GitHub owner, repository name, visibility, and whether local Git operations are allowed.'
---

# CAPSTONE GitHub Repository Bootstrap

Set up a remote GitHub repository for the CAPSTONE project without overwriting an existing repository or local Git remote.

## Procedure

1. Extract the requested GitHub owner/account, exact repository name, description, visibility, and any tool restrictions. Do not infer that the authenticated account is the requested owner.
2. Call GitHub MCP `get_me` to confirm the authenticated identity. If it does not match the requested owner, stop and explain the mismatch; do not create the repository under another account.
3. Check whether the repository already exists when the available GitHub MCP tools allow it. Never create a duplicate or silently choose a different name.
4. Create the repository with the requested name, owner, visibility, and description. Initialize it with a README only if appropriate for the local project; an initialized remote can conflict with an existing local history.
5. Report the resulting GitHub URL and clone/remote URL. Do not claim that a local `origin` was configured unless that operation was actually performed and verified.
6. If the user requests local `origin` setup and permits local Git operations, inspect the current repository and its remotes first. Add `origin` only when none exists. If an `origin` already points elsewhere, preserve it and ask before changing it. Verify the resulting remote afterward.
7. If constrained to GitHub MCP only, explain that MCP can create the remote repository but cannot configure the local Git remote. Give the remote URL and state this limitation rather than implying setup is complete.
8. Do not push project files, alter branches, or change repository settings unless explicitly requested.

## Completion Check

- The owner and repository name match the request.
- Visibility and initialization choices match the user's instructions.
- The GitHub repository URL is confirmed from the create result.
- Local remote setup is reported separately and only when verified.
