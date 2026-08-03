---
id: feature-learning-courses
type: feature-doc
status: generated
owner: generated
scope: feature — learning-courses
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Learning courses (/learn/)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `learning-courses` |
| Label | Learning courses (/learn/) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `learning:chapter` | `/learn/<slug:course>/<slug:chapter>/` | `ChapterView` | [chapter.md](chapter.md) |
| `learning:course` | `/learn/<slug:course>/` | `CourseDetailView` | [course.md](course.md) |
| `learning:heartbeat` | `/learn/<slug:course>/<slug:chapter>/beat/` | `HeartbeatView` | [heartbeat.md](heartbeat.md) |
| `learning:index` | `/learn/` | `CourseIndexView` | [index.md](index.md) |
| `learning:interview` | `/learn/interview/` | `InterviewPrepView` | [interview.md](interview.md) |
| `learning:revision` | `/learn/revise/<slug:page>/` | `RevisionView` | [revision.md](revision.md) |
| `learning:search` | `/learn/search/` | `SearchView` | [search.md](search.md) |
| `learning:toggle-bookmark` | `/learn/<slug:course>/<slug:chapter>/bookmark/` | `ToggleBookmarkView` | [toggle-bookmark.md](toggle-bookmark.md) |
| `learning:toggle-complete` | `/learn/<slug:course>/<slug:chapter>/complete/` | `ToggleCompleteView` | [toggle-complete.md](toggle-complete.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `learning.Bookmark` | `learning_bookmark` | not machine-known |
| `learning.LessonProgress` | `learning_lessonprogress` | not machine-known |

## Apps touched

- `learning` — [config/learning/README.md](../../../config/learning/README.md) · [docs/apps/learning/GUIDE.md](../../apps/learning/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
