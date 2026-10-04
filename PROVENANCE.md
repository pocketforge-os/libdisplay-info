# Provenance

| Field | Value |
| --- | --- |
| Canonical upstream | `https://gitlab.freedesktop.org/emersion/libdisplay-info.git` |
| Upstream base | `47a5590e9c4eb35d67651b8c05a55f1a48259329` |
| Licence | `LICENSE` |
| PocketForge patch | Resolve the retained v4l-utils test dependency through its immutable PocketForge fork. |

The PocketForge patch series is based directly on the upstream commit above.
The v4l-utils revision and existing libdisplay-info tests remain unchanged. The
source-locator policy check is registered with Meson, and the CI image tag is
updated with its source-preparation recipe.
