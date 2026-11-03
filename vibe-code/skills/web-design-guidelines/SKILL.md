---
name: web-design-guidelines
description: Review web UI code or a rendered page for usability, accessibility, responsive behavior, and visual consistency. Use when asked to audit, review, or improve an existing interface.
---

# Web Design Guidelines

Review the requested interface and report evidence-backed findings. Use the
project's actual stack and the files or routes named in the request.

## Review process

1. **Set the scope from available context.** Use the provided files or URL. If
   no target is specified, identify the relevant UI entry points in the
   workspace and state the scope you inspected instead of guessing that the
   whole application was reviewed.
2. **Check the current published guidance when possible.** If network access
   is available, retrieve the latest
   [Vercel Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md)
   and use them as an additional checklist. If they cannot be retrieved,
   disclose that and continue with the local checks below; do not claim the
   latest rules were checked.
3. **Inspect code and rendered behavior.** Use browser tools or screenshots
   when available. Otherwise, base findings on source and label visual
   behavior that could not be confirmed.
4. **Check the essentials.** Look for semantic structure, keyboard access,
   visible focus, accessible names, form feedback, readable contrast, mobile
   overflow, responsive hierarchy, reduced-motion support, loading and error
   states, and visual consistency with the existing product.
5. **Report actionable findings.** For each issue, include file and line (or
   route and element), impact, and a concise fix. Prioritize user-blocking and
   accessibility problems above polish. Separate verified defects from
   suggestions.
6. **Respect review scope.** Do not change files for a review-only request. If
   asked to fix issues, make the smallest relevant changes and verify them
   using the project's available checks.
