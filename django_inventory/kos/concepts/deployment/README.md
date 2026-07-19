---
id: readme-concepts-deployment
type: system
verified: 2026-07-19
---

# Deployment — running it for real

*(Part of [Concepts](../README.md) → the [KOS](../../README.md).)*

## Teacher's note

Code that isn't running is a rumor. This folder teaches what it takes for
ONE person to run a money system in production — and rebuild it from
nothing by evening. *(Chamak nahi, bharosa.)* Absorbed and superseded the
old `~/knowledge` shelf's deployment/docker/redis lessons, now
project-anchored.

| Page | Real question it answers |
|---|---|
| [first-deploy-from-scratch.md](first-deploy-from-scratch.md) | I've NEVER deployed — what IS deployment, which 5 things do I buy, what are the 11 steps and why? |
| [production-and-docker.md](production-and-docker.md) | How does one person run this in production and sleep — and recover by evening if the VPS dies? |

**After this folder you can:** design a deploy with rehearsed rollback
lanes, a drilled DR pair, and a post-deploy verification gate.

*Grows when the project adopts more (CI/CD, monitoring → after C2 lands).*
