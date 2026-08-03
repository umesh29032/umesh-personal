---
id: git-course-31-signed-commits
type: lesson
status: active
owner: handwritten
scope: git, version control — proving WHO made a commit, and what "Verified" does and does not mean
anchors: CONTRIBUTING.md, git-hooks/pre-push, .github/workflows/ci.yml, ~/.ssh/id_ed25519_personal.pub
verified: 2026-08-03
---

# 31 — Signed Commits (cryptographic proof of authorship, because the author field is just typed text)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [30 — CHANGELOG](30_Changelog.md). Next: [32 — Dependabot & Supply Chain](32_Dependabot_And_Supply_Chain.md).

# Learning Objectives
By the end of this chapter you can:
- explain why git's `author` and `committer` fields prove **nothing**, and demonstrate it
- read every `%G?` signature code, and say exactly why this repo shows **15 `E`** and **309 `N`**
- set up **SSH commit signing** on this machine with no new key material and no GPG
- state precisely what GitHub's green **Verified** badge proves — and the three things it does not
- explain why signing a **tag** buys more audit value per keystroke than signing every commit
- know what a rebase, a squash-merge and a `--force` do to signatures you already made

# Purpose
Every chapter so far has been about *what* changed. This one is the first about **who**. Git's identity fields are strings you type; a signature is a cryptographic claim that only a key-holder could have made. This chapter shows the real signature state of this repository (measured, not guessed), sets up signing the cheap way, and is honest that the green badge is an *identity* check, never a *quality* check.

# The Problem
Open a terminal and run this — it is not a trick, it is how git works:

```bash
git -c user.name="Linus Torvalds" \
    -c user.email="torvalds@linux-foundation.org" \
    commit -m "feat: definitely written by Linus"
```

Git accepts it without a murmur. There is no password, no challenge, no check. The `author` line in a commit object is **text you supplied**, exactly like the commit message. The same is true of the date — `--date` will happily backdate a commit to 2019.

Now put that in this project's context:

- **The fork flow.** `CONTRIBUTING.md` §9 has collaborators work from a fork and open a PR. What arrives is a branch of commits whose author strings are whatever the contributor's `git config` said. Trustworthy? You have no way to tell from the commit.
- **The money paths.** `CLAUDE.md` rule 5 says each ledger table has exactly one writer service, and settlement is the only money-write boundary. When someone eventually asks *"who changed the rate resolver in March?"*, `git log` gives you a name — a name that is **self-declared**.
- **A stolen laptop, or a leaked CI token.** Anything that can run `git push` can write commits under your name, on your branch, in your history. Nothing about the commit itself objects.

A signature does not fix bad code. It fixes exactly one thing, and it is a thing nothing else in git fixes: after the fact, you can prove **which key** made this object, and reject anything else.

# Theory (from zero)

### Two identities live in every commit
Before signatures, understand what is being signed. Ask git for the raw commit object — this is real output from this repo:

```bash
git cat-file -p 83a144ba
```
```
tree aa3a236e9a1756d2aaa3bc679cbb459277a88b56
parent fa9507d7d9a39c6de0c8506a87a03f65fd89c09d
parent 7fe2bb0e1b50b5bb2b669e51d9f92191909bae3e
author Umesh chaudhary <44035504+umesh29032@users.noreply.github.com> 1785743474 +0530
committer GitHub <noreply@github.com> 1785743474 +0530
```

Two different identities, and beginners never notice:

- **`author`** — who *wrote* the change. Set once, preserved through rebases and cherry-picks.
- **`committer`** — who *created this particular commit object*. Changes whenever the commit is rewritten: rebase, amend, cherry-pick, or (as here) a merge performed by GitHub's web UI.

Both are plain text taken from config. Both are unauthenticated. `git log` shows you the author by default, which is why the distinction is invisible until it matters.

### What a signature actually is, from zero
**Asymmetric cryptography** in three sentences. You hold two mathematically-paired keys: a **private key** (secret, on your machine) and a **public key** (published to the world). Signing = running the private key over some bytes to produce a short blob, the **signature**. Verifying = anyone with the public key can check that this signature matches these exact bytes and could only have come from the paired private key. No secrets are shared to verify.

What git signs is **the commit object itself** — tree hash, parents, author, committer, dates, message. Change any byte and verification fails. And because the signature is stored *inside* the commit as a `gpgsig` header, the commit's SHA-1 covers the signature too. A signed commit is therefore tamper-evident all the way down: alter the history under it and every child hash changes ([Ch 05](05_How_Git_Stores_Everything.md), [Ch 06](06_The_Commit_Graph.md)).

Here is a real `gpgsig` header, from that same merge commit (truncated):

```
gpgsig -----BEGIN PGP SIGNATURE-----

 wsFcBAABCAAQBQJqcEhyCRC1aQ7uu5UhlAAAKgUQABlkiyLuymNbF1agQliOhXQ5
 ...
 =Rdhf
 -----END PGP SIGNATURE-----
```

### Three signing backends — pick one, not three
Git can sign with three different systems. The config knob is `gpg.format`.

| Backend | `gpg.format` | Key material | Cost of ownership |
|---|---|---|---|
| **OpenPGP** | `openpgp` (default) | a GPG key in a keyring | keyring, passphrase agent, expiry dates, revocation certificates |
| **SSH** | `ssh` (git ≥ 2.34) | the `~/.ssh` key you already push with | one config line; verification needs an `allowed_signers` file |
| **X.509 / S-MIME** | `x509` | a corporate certificate via `smimesign`/`gitsign` | a PKI, i.e. an organisation |

**Name the confusing bit:** an SSH key used for *authentication* (proving to GitHub you may push) and the same key used for *signing* (proving you made this commit) are the **same file** but two **different roles**. GitHub makes you upload the public key twice — once as an *Authentication key*, once as a *Signing key* — precisely because they are different claims. Uploading it as an auth key does not make your commits verify.

> 💡 **Samjho aise:** Commit ka `author` field = **envelope pe naam likh dena**. Koi bhi kisi ka naam likh sakta hai — git rokta hi nahi. Signature = us naam ke saath apni **mohar** lagana, aur mohar banane wali chaabi sirf tumhare paas hai. Aur GitHub ka hara **Verified** thappa sirf yeh kehta hai *"mohar asli hai"* — yeh nahi kehta ki *"andar ka maal accha hai"*. Mohar ki jaanch identity ki hai, quality ki nahi. Review (Ch 22) quality dekhta hai; signature sirf pehchaan.

### The `%G?` codes — the entire vocabulary in one table
`git log --pretty='%G?'` prints one letter per commit. Learn all of them once and you never guess again:

| Code | Meaning |
|---|---|
| **`G`** | Good signature, from a key you trust |
| **`U`** | Good signature, but the key is **untrusted** (valid maths, you never vouched for the key) |
| **`X`** | Good signature that has **expired** |
| **`Y`** | Good signature made by an **expired key** |
| **`R`** | Good signature made by a **revoked key** |
| **`B`** | **Bad** signature — the content does not match. Treat as hostile |
| **`E`** | Signature present but **cannot be checked** — you do not have the public key |
| **`N`** | **No** signature at all |

`%GS` prints the signer's name, `%GK` the key ID. All three are cheap to add to any `--pretty` format.

### What GitHub's "Verified" badge proves — and three things it does not
GitHub shows **Verified** when *all three* hold:

1. the signature is cryptographically valid;
2. the key is registered as a **signing key** on a GitHub account; and
3. the commit's author email matches a **verified email** on that same account.

Fail any one and you get **Unverified** (badge present, checks failed) or no badge at all (unsigned). The most common cause of an *unexpected* Unverified is #3 — signed with the right key, committed with the wrong email.

What it does **not** prove: (a) that the code is correct or reviewed — that is CI ([Ch 28](28_CI_With_GitHub_Actions.md)) and review ([Ch 22](22_Code_Review.md)); (b) that the human is who the account claims — it proves *the same key-holder as last time*, which is continuity, not identity; (c) that the key was in the owner's possession — a stolen laptop signs beautifully.

GitHub also offers **Vigilant mode** (free, per-account): once on, every *unsigned* commit attributed to you is displayed as **Unverified** instead of silently blank. That turns "signed" from an occasional decoration into a visible default — the cheapest possible enforcement, and it costs nothing.

### Why GitHub signs your merge commits *for* you
This is the fact that explains this repo's numbers. When you click **Merge pull request** in the browser, GitHub creates the commit on its own servers. So:

- `committer` becomes `GitHub <noreply@github.com>` — verified above, in the real object;
- GitHub signs it with **its own** web-flow key, so it shows Verified on the website;
- locally, `git log` reports **`E`** — signature present, but GitHub's public key is not in your keyring.

`E` is not a warning about the commit. It is a statement about *your* keyring. Import GitHub's public key from `https://github.com/web-flow.gpg` and those same commits start reporting a valid signature. Until then, `E` and `N` look equally uninformative and are completely different things.

### Signing a tag beats signing every commit
A release is a tag ([Ch 29](29_Semantic_Versioning_And_Tags.md)). A **signed annotated tag** is one object that says: *"I, key-holder, assert that this exact tree is release erp-v1.0.0."* Because the tag names a commit, and that commit's hash covers its whole history, one signature vouches for everything reachable from it.

That is a far better ratio than signing 324 commits: one keystroke per release, and it protects the artefact that actually gets deployed. `git verify-tag <tag>` is then a one-command release check, and `git describe` / `git tag --verify` fit straight into a deploy runbook.

### Rebase, squash and force — the three signature killers
Signatures are attached to commit objects, and **rewriting history creates new objects**. So:

- **`git rebase`** ([Ch 13](13_Rebase.md)) rewrites every commit it moves. New objects, old signatures dropped. Re-sign with `git rebase --exec 'git commit --amend --no-edit -S'`, or set `commit.gpgsign true` so amends sign automatically.
- **`git commit --amend`** — same thing for one commit.
- **GitHub squash-merge** (`CONTRIBUTING.md` §5 step 5) creates a **brand-new commit** server-side, signed by GitHub, not by the contributor. So a contributor's carefully signed commits do **not** appear signed on `main`; their signatures lived on the branch that was squashed away. This is a real trade-off of squash-merging, and it is worth knowing before you promise anyone an audit trail of contributor signatures.
- **`git push --force`** ([Ch 27](27_Pre_Push_Protection.md)) replaces objects wholesale. Signatures do not survive what they were replacing.

**Always give the undo:** none of this loses anything permanently — the pre-rewrite commits are still in `reflog` for the default 90 days ([Ch 16](16_Reflog.md)), signatures intact. `git reflog` then `git reset --hard <old-sha>` restores the signed versions. And the escape hatch for a single commit you cannot sign right now is `git commit --no-gpg-sign`.

# Real World Example (this repo)
Everything below is measured, right now, in `/home/tech/umesh-personal`.

**The census — one command, and it tells the whole story:**
```bash
git log --pretty='%G?' | sort | uniq -c
```
```
     15 E
    309 N
```

324 commits. **Zero** are signed by a key of yours. Fifteen carry a signature you cannot check. Which fifteen?

```bash
git log --pretty='%h %G? %an — %s' | grep -v ' N '
```
```
83a144ba E  Umesh chaudhary — Merge pull request #15 from umesh29032/new_flask_app
fa9507d7 E  Umesh chaudhary — Merge pull request #14 from umesh29032/new_flask_app
...
9f68df22 E  umesh29032 — Merge pull request #1 from umesh29032/new_flask_app
```

Exactly the 15 GitHub-web merge commits, PR #1 through PR #15. Every commit *you* made is `N`. The theory above predicted this precisely.

**Why `E` and not `G`:**
```bash
git verify-commit 83a144ba
```
```
gpg: Signature made Monday 03 August 2026 01:21:14 PM IST
gpg:                using RSA key B5690EEEBB952194
gpg: Can't check signature: No public key
```
Exit status 1. The key ID is GitHub's; your keyring has never seen it.

**The release tag is annotated but unsigned:**
```bash
git verify-tag erp-v1.0.0
```
```
error: no signature found
```
The tag itself is a proper annotated object with a tagger, a date and a real message (*"Release Certificate: GO WITH ACCEPTED RISKS … Battery 1878/1878"*) — it is just not signed. So the most audit-relevant object in the repository, the one the deploy runbook names, carries no cryptographic proof at all. That is the single highest-value gap this chapter can close.

**And the good news — this machine can sign today, with nothing new installed:**

| Requirement | State here |
|---|---|
| A GPG key | **none** — `gpg --list-secret-keys` prints nothing |
| An SSH key | **two**: `~/.ssh/id_ed25519` (office) and `~/.ssh/id_ed25519_personal` |
| Git version | **2.34.1** — `gpg.format=ssh` needs ≥ 2.34 ✔ |
| OpenSSH version | **8.9p1** — `ssh-keygen -Y sign` needs ≥ 8.2 ✔ |

So the cheap path is open: SSH signing, reusing the key that already pushes to `github-personal`. No keyring, no expiry admin, no new secret to lose.

**One local trap you must know about.** This machine carries **two identities**:

```
file:/home/tech/.gitconfig           user.email=umesh.chaudhary@thesqua.re   (office)
file:/home/tech/.gitconfig-personal  user.email=umesh29mar@gmail.com          (personal)
file:.git/config                     user.email=umesh29mar@gmail.com          (this repo)
```

Sign with the office key while committing as the personal email and GitHub will show **Unverified** — valid signature, wrong account. Set the signing key **per-repo**, next to the email it belongs with.

# Visual Diagram
```
  ── ANATOMY: what signing adds to a commit object ──────────────────────────
   commit 83a144ba
   ├── tree      aa3a236e…            ← the snapshot
   ├── parent    fa9507d7  7fe2bb0e   ← two parents = a merge
   ├── author    Umesh chaudhary <…>  ← TYPED TEXT. proves nothing.
   ├── committer GitHub <noreply@…>   ← TYPED TEXT. GitHub made this object.
   ├── gpgsig    -----BEGIN PGP SIGNATURE-----   ← proof, over everything above
   └── message   "Merge pull request #15 …"
        the commit SHA covers the signature too ⇒ tamper-evident downwards

  ── VERIFY: private key signs, public key checks ───────────────────────────
   you:  [private key] ──sign──► signature stored IN the commit
   them: [public key]  ──check─► G  good & trusted
                                U  good, key not trusted by you
                                E  signature there, PUBLIC KEY MISSING  ← 15 here
                                N  no signature at all                  ← 309 here
                                B  BAD — content altered. stop.

  ── THIS REPO TODAY ────────────────────────────────────────────────────────
   324 commits ─┬─ 309 N   yours, unsigned
                └──15 E   GitHub web-merge commits (PR #1…#15), GitHub's key
   erp-v1.0.0 → annotated, tagger present, NOT signed ("error: no signature found")

  ── WHAT A REWRITE DOES ────────────────────────────────────────────────────
   signed A─B─C   ──rebase/squash/amend──►  new A'─B'─C'  (signatures GONE)
        undo: git reflog → git reset --hard <old-sha>   (90 days, Ch 16)
```

# Practical — turn signing on, with the key you already have
Run these in `/home/tech/umesh-personal`. Steps 1–4 **write git config** (they change your setup — that is the point); nothing here touches history, and step 6 undoes all of it.

**1. Choose the SSH backend and the key. Per-repo, so it matches this repo's personal email:**
```bash
git config gpg.format ssh
git config user.signingkey /home/tech/.ssh/id_ed25519_personal.pub
```
Note it is the **`.pub`** file. Git derives the private half via `ssh-agent` or the matching filename.

**2. Sign commits and tags by default, so you never have to remember `-S`:**
```bash
git config commit.gpgsign true
git config tag.gpgsign true
```

**3. Teach git which signatures to trust, or verification cannot work.** SSH has no keyring, so you supply an `allowed_signers` file mapping an email to a public key:
```bash
mkdir -p ~/.config/git
printf '%s %s\n' 'umesh29mar@gmail.com' "$(cat ~/.ssh/id_ed25519_personal.pub)" \
  >> ~/.config/git/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
```
Skip this and your own commits verify as `U`/`E` — signed but unattributable. This file is also how you verify *other people's* commits: one line per contributor.

**4. Upload the public key to GitHub a second time** — Settings → SSH and GPG keys → **New SSH key** → Key type **Signing Key**:
```bash
cat ~/.ssh/id_ed25519_personal.pub      # paste this into the browser
```

**5. Prove it, on a real commit:**
```bash
git commit --allow-empty -m "chore(repo): first signed commit"
git log --show-signature -1
```
Expect a `Good "git" signature for umesh29mar@gmail.com` line, and:
```bash
git log -1 --pretty='%h %G? %GS'        # → <sha> G umesh29mar@gmail.com
```
If it says `U`, step 3 is missing or the email does not match the `allowed_signers` line.

**6. The undo — all of it, in three lines:**
```bash
git config --unset commit.gpgsign        # stop signing commits
git config --unset tag.gpgsign           # stop signing tags
git config --unset gpg.format            # back to the default backend
git commit --no-gpg-sign -m "…"          # one-off escape hatch, keeps the setting
```

**7. Make the 15 `E` commits checkable** (this writes to your GPG keyring, not to git):
```bash
curl -sL https://github.com/web-flow.gpg | gpg --import
git log --pretty='%h %G? %GS' | grep -v ' N ' | head -3
```
Expect **`U`** — a valid signature from a key you have not personally vouched for. That is correct and honest; `gpg --lsign-key B5690EEEBB952194` would locally promote it to `G`.

**8. Sign the next release tag** — the highest-value single action in this chapter:
```bash
git tag -s erp-v1.1.0 -m "erp-v1.1.0 — accountant read tier"   # -s = signed annotated
git verify-tag erp-v1.1.0                                       # must exit 0
```
**Undo a local tag** before pushing: `git tag -d erp-v1.1.0`. After pushing, do **not** delete and re-tag ([Ch 29](29_Semantic_Versioning_And_Tags.md)) — cut `erp-v1.1.1` instead.

**9. Verify on the way in, when you merge a fork branch locally:**
```bash
git merge --verify-signatures --no-ff feat/their-thing   # refuses an unsigned tip
git pull --verify-signatures upstream main
```

# Production Walkthrough
How signing would actually land in this project, in the order that gets value soonest:

1. **Tags first.** `CONTRIBUTING.md` §7 already prescribes an annotated tag per release. Change `-a` to `-s` and add `git verify-tag` as the first line of the deploy runbook's pre-flight. One keystroke per release; it protects the deployed artefact; nothing else in the workflow changes.
2. **Then your own commits, per machine.** `commit.gpgsign true` in this repo's `.git/config`, with the personal key. Because it is per-repo, the office identity in `~/.gitconfig` is untouched — no risk of signing office work with a personal key or vice versa.
3. **Vigilant mode on the GitHub account.** Free. From then on, an unsigned commit attributed to you is visibly **Unverified** — which is how you notice a machine where step 2 was never done. Same failure mode as the `pre-push` hook's honest gap in `CONTRIBUTING.md` §2 Layer 1: client-side setup only binds where it was installed.
4. **Collaborators.** Add their public key to `allowed_signers` and ask them to sign. Then verify **locally** with `git merge --verify-signatures` before landing, because a GitHub squash-merge replaces their commit with GitHub's own and their signature never reaches `main`. Do not promise an audit trail the merge strategy destroys.
5. **The honest position on enforcement.** Requiring signed commits *server-side* is a branch-protection rule, and branch protection is a **paid** feature on private repos here (`CONTRIBUTING.md` §2). So enforcement is client-side or nothing. A `pre-push` addition — refuse to push any commit whose `%G?` is `N` — is free, in the same file that already refuses pushes to `main` ([Ch 27](27_Pre_Push_Protection.md)), and carries exactly the same limitation: it binds only where `git-hooks/install.sh` has been run.
6. **Never claimed, never faked.** Until step 1 ships, the truthful statement about this repo is the one measured above: 309 unsigned, 15 signed by GitHub, release tag unsigned. Writing that down beats implying an audit trail that does not exist.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `error: gpg failed to sign the data` | no key configured, or the wrong `gpg.format` | check `git config --get user.signingkey` and `gpg.format`; for SSH point at the `.pub` file |
| `gpg: signing failed: Inappropriate ioctl for device` | GPG cannot prompt for the passphrase in this terminal | `export GPG_TTY=$(tty)` in your shell profile (GPG backend only) |
| `gpg: Can't check signature: No public key` → `%G?` = `E` | you do not have the signer's public key | import it — for GitHub merges, `curl -sL https://github.com/web-flow.gpg \| gpg --import` |
| `error: no signature found` from `verify-tag` | the tag is annotated (`-a`) but not signed (`-s`) | tag future releases with `-s`; never re-point an existing tag |
| GitHub shows **Unverified** but local says `G` | commit email is not a verified email on the account that owns the key | make `user.email` match; here that is `umesh29mar@gmail.com` per-repo |
| Signatures vanished after a rebase | rewriting created new objects | re-sign: `git rebase --exec 'git commit --amend --no-edit -S'`; recover originals from `reflog` |
| Contributor's signatures missing from `main` | GitHub squash-merge created a new commit server-side | verify **before** merging with `git merge --verify-signatures`, or merge locally |
| `%G?` prints `U` for your own commits | no `allowed_signers` entry, or the email does not match | add the mapping line and set `gpg.ssh.allowedSignersFile` |
| `%G?` prints `B` | content does not match the signature — tampering or corruption | do not merge; re-fetch, and treat the branch as hostile until explained |
| `fatal: unknown value for config 'gpg.format': ssh` | git older than 2.34 | upgrade git (this machine is 2.34.1, so it works) |
| Everything shows `N` and no error appears anywhere | `commit.gpgsign` is not set — git signs only when told | `git config commit.gpgsign true`; verify with `git log -1 --pretty='%G?'` |

# Performance Notes
- **Signing one commit is milliseconds.** Ed25519 signing is small-constant fast; RSA-4096 is noticeably slower but still under a human's perception threshold. You will never feel it on `git commit`.
- **You will feel it on a bulk rewrite.** A rebase of 200 commits with signing on performs 200 signings and 200 object writes. If GPG asks for a passphrase per signature, use an agent with a cache timeout or the operation becomes unusable.
- **Verification spawns a process per signed commit.** `git log --show-signature` invokes the verifier for each signature — cheap for the 15 signed commits here, a real cost if all 324 were signed and you walk the whole history in a script.
- **Prefer `%G?` over `--show-signature` in scripts.** Same information, one letter, no parsing of human-readable gpg output.
- **Repo size impact is negligible**: a PGP signature header is well under a kilobyte per commit, against a `.git` already at ~64 MiB packed here ([Ch 37](37_Large_Files_And_Performance.md)).
- **CI cost is zero** if you verify a *tag* once per deploy instead of every commit on every run — another reason tags are the better ratio.

# Security Considerations
- **A signature is an identity claim, never a quality claim.** A perfectly signed commit can drop the settlement table. Signing does not replace review ([Ch 22](22_Code_Review.md)) or CI ([Ch 28](28_CI_With_GitHub_Actions.md)).
- **The private key usually lives on the same laptop as the repo.** Whoever steals the machine can sign as you. Mitigations that cost nothing: a passphrase on the key, an agent with a short cache, full-disk encryption. The strong upgrade is a hardware-backed key (`ssh-keygen -t ed25519-sk`), where the private half physically cannot be copied.
- **Rotation and revocation need a plan before you need them.** With SSH signing, an `allowed_signers` entry can carry `valid-after`/`valid-before` so old signatures stay verifiable after you retire a key. Without that, rotating a key silently invalidates every signature it ever made.
- **GitHub's web-flow signing is trust you are delegating.** Every merge you click is signed by *GitHub's* key, on your behalf, showing your name. That is convenient and it is a real trust boundary — worth knowing consciously rather than discovering later.
- **Never sign what you did not read.** A signed dependency bump you merged blind ([Ch 32](32_Dependabot_And_Supply_Chain.md)) is your key vouching for someone else's code.
- **Signing does not encrypt anything.** The diff is still public; a signature only says who made it. If a commit should not be readable, the answer is not to commit it ([Ch 33](33_Secrets_And_Leaks.md)).
- **`B` is an alarm, not a nuisance.** Bad signature means the bytes changed after signing. Stop, ask, do not merge.

# Architecture Decisions
- **SSH signing over GPG**, if and when this repo turns signing on. The key already exists (`~/.ssh/id_ed25519_personal`), git 2.34.1 and OpenSSH 8.9p1 both support it, and it avoids the whole GPG apparatus — keyring, agent, expiry, revocation certificates. Rejected GPG for a one-developer project: more ceremony than value.
- **Tags before commits.** One signature per release covering the deployed tree beats 324 signatures covering individual edits. `erp-v1.0.0` is annotated-but-unsigned today; that is recorded here as debt rather than glossed over.
- **Per-repo signing config, not global.** This machine has an office identity in `~/.gitconfig` and a personal one for this monorepo. A global `user.signingkey` would eventually sign one identity's work with the other's key, which reads as forgery to GitHub.
- **Rejected: requiring signed commits from collaborators.** Server-side enforcement is paid here, and the squash-merge strategy (`CONTRIBUTING.md` §5) discards contributor commits anyway. Verifying locally at merge time gets the real benefit with no plan upgrade.
- **Rejected: making signing a CI gate today.** Nothing is signed yet, so the gate would fail every PR on day one. The order is: sign tags → sign your own commits → turn on Vigilant mode → *then* consider a gate.
- **Vigilant mode accepted** as the free display layer: it makes the absence of a signature visible, which is the only part of enforcement that free tier gives away.

# Best Practices
- Sign **annotated tags** for every release, and make `git verify-tag` a deploy pre-flight step.
- Set `commit.gpgsign true` per-repo, with a signing key that matches that repo's `user.email`.
- Maintain an `allowed_signers` file — signing without it produces signatures nobody can attribute.
- Turn on **Vigilant mode** so unsigned commits look wrong instead of looking normal.
- Verify at the boundary: `git merge --verify-signatures` on anything arriving from a fork.
- Use `%G?` in scripts, `--show-signature` when reading by hand.
- Put the key behind a passphrase; prefer a hardware-backed key if the repo touches money.
- Re-sign after any rebase — and remember `reflog` still holds the originals for 90 days.
- Write down the truth about your current signing state; never imply an audit trail you do not have.

# Beginner Mistakes
- **Believing the `author` field** → it is text you typed, and `git -c user.name=…` proves it. Only a signature is evidence.
- **Confusing `E` with `N`** → `E` is "signed, key missing on *my* side"; `N` is "not signed at all". Different problems, opposite fixes.
- **Reading Verified as "reviewed"** → it is an identity check. This repo's 15 Verified merges were signed by GitHub, and nobody reviewed them.
- **Uploading the SSH key only as an Authentication key** → GitHub needs it *again* as a Signing key or commits stay Unverified.
- **Setting `user.signingkey` globally on a two-identity machine** → office key signs personal commits, and GitHub calls it Unverified.
- **Signing without an `allowed_signers` file** → your own commits verify as `U`; you get the ceremony and none of the proof.
- **`git tag -a` and then claiming a signed release** → `git verify-tag erp-v1.0.0` answers `error: no signature found`. Use `-s`.
- **Rebasing and assuming signatures survive** → new objects, no signatures. Re-sign, or recover the old commits from `reflog`.
- **Promising contributor signatures on `main` under squash-merge** → the squash commit is GitHub's, not theirs.
- **Thinking signing hides anything** → it authenticates, it does not encrypt. Secrets are [Ch 33](33_Secrets_And_Leaks.md).
- **Losing the key with no rotation plan** → every signature you ever made becomes unverifiable. Plan `valid-after` windows first.

# Interview Questions
- **Junior:** "What does a signed commit prove?" — That the commit object was created by the holder of a specific private key, and that not one byte has changed since. It does **not** prove the code is good, reviewed, or that the person is who they claim beyond "same key as before". Without a signature the `author` field is just text — `git -c user.name="Somebody Else" commit` works, with no check at all.

- **Mid:** "GitHub shows Verified on the website but `git log --show-signature` says `Can't check signature: No public key` locally. Explain." — Two different verifiers with two different key stores. GitHub verifies against keys registered to accounts on its side; my local git verifies against my keyring, which does not contain the signer's public key — so `%G?` reports `E`, meaning "signature present, unverifiable here", not "bad signature". In this repo the 15 signed commits are GitHub-web merge commits, whose committer is `GitHub <noreply@github.com>`; importing `https://github.com/web-flow.gpg` makes them check out locally as `U` — valid, from a key I have not personally trusted. The failure mode to distinguish is `B`, a bad signature, which means the content was altered.

- **Senior:** "You have 324 commits, 309 unsigned. Design a rollout that is honest about cost." — Order by value per keystroke. (1) **Sign the release tags** — one signature per release covering the entire reachable tree, and it protects the artefact the deploy runbook names; today `git verify-tag erp-v1.0.0` returns `error: no signature found`, so this is the real gap. (2) **SSH signing, per-repo** — the key already exists, git is 2.34.1, so `gpg.format=ssh` plus `user.signingkey` costs two config lines and no new secret; per-repo because this machine has two identities and a global signing key would sign personal commits with an office key, which GitHub reports as Unverified. (3) **`allowed_signers`**, or verification is theatre. (4) **Vigilant mode** to make unsigned commits visibly wrong. (5) **Verify at the boundary**, `git merge --verify-signatures`, because squash-merge replaces contributor commits with a GitHub-signed one and their signatures never reach `main`. What I would *not* do is add a CI gate first — every PR would fail on day one — or backfill signatures onto old commits, since that rewrites 324 commits, invalidates every published hash, and proves nothing about the past anyway.

- **Staff:** "Signed commits are proposed as a compliance control for a system that pays workers. Assess it." — It is a genuine control with a narrow scope, and the scope is the whole answer. What it gives: tamper-evidence over history, and non-repudiation *of the key*. What it does not give: authorisation, review, or proof the key-holder was the human — and in this codebase the risk that actually matters is a new money-write path outside the single-writer services, which a signature cannot see. So I would place signing as one layer among four: signed release tags verified in the deploy pre-flight (artefact integrity); CI as the mechanical gate (the battery is 2033 tests over 14 apps with byte-identical money assertions — that is what catches a wrong settlement, not a signature); a second reviewer on money paths per `CONTRIBUTING.md` §5; and the application's own audit tables, which record who did what *inside* the product rather than who edited the source. Then I would name the residual risks honestly: the private key sits on a developer laptop, so a hardware-backed key is the real hardening; server-side "require signed commits" is a paid branch-protection feature on this plan, so enforcement is client-side and only binds where the hooks were installed — a gap already written down in `CONTRIBUTING.md` §2 rather than hidden; and GitHub's web-flow signing means a third party holds a key that signs under my name. Compliance value comes from the *combination* plus the documented gaps, not from a green badge.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know git identity is unauthenticated? | "The author field says who wrote it." | Author and committer are typed config strings; demonstrate the impersonation one-liner, then say a signature is the only evidence. |
| Can you read signature states precisely? | "It says unverified, so it is broken." | Distinguish `N` no signature, `E` key missing on my side, `U` valid but untrusted, `B` bad — and name the fix for each. |
| Do you know what Verified does not prove? | "Verified means the commit is trusted." | It proves key-holder continuity and email-to-account match. Not correctness, not review, not possession of the key. |
| Rollout judgement and honesty about limits | "We will require signed commits." | Tags first, per-repo key, allowed_signers, Vigilant mode; note squash-merge discards contributor signatures and server-side enforcement is paid here. |

**The killer follow-up:** *"Your repo says Verified on fifteen commits. Who signed them?"* — The memoriser says "we sign our commits". The user of git says: GitHub did, because those are web-UI merge commits whose committer is `GitHub <noreply@github.com>`, my own 309 commits are unsigned, and my release tag has no signature at all. Knowing which signatures are *yours* is the whole difference.

# Revision Notes
- `author` and `committer` are **typed text**. `git -c user.name=… commit` impersonates anyone. Signatures are the only proof.
- The signature lives in the commit's **`gpgsig`** header, so the commit SHA covers it → tamper-evident downwards.
- `%G?` codes: **G** good · **U** good-untrusted · **X** expired sig · **Y** expired key · **R** revoked · **B** BAD · **E** key missing here · **N** unsigned.
- This repo, measured: **15 `E` + 309 `N`** of 324. The 15 are GitHub-web merge commits (PR #1–#15). `git verify-tag erp-v1.0.0` → `error: no signature found`.
- **Verified** = valid signature **+** key on a GitHub account **+** author email verified on that account. Not correctness, not review.
- **SSH signing** is the cheap path: `gpg.format=ssh` (git ≥ 2.34) + `user.signingkey` = the `.pub` file. No GPG needed.
- Verification needs an **`allowed_signers`** file, or your own commits read as `U`.
- ⚠️ **Rebase, amend, squash-merge and force all destroy signatures** — new objects. Re-sign; originals stay in `reflog` for 90 days.
- **Sign tags** for the best ratio: one signature vouches for the whole reachable tree, and it is the object you deploy.
- Server-side "require signed commits" is **paid** on private repos here → client-side (`pre-push`, Vigilant mode) or nothing.

# Cheat Sheet
```bash
git log --pretty='%G?' | sort | uniq -c            # signature census: 15 E, 309 N here
git log --pretty='%h %G? %GS — %s'                # per-commit: state, signer, subject
git log --show-signature -1                       # full verifier output for HEAD
git verify-commit <sha>                            # exit 0 = verified
git verify-tag erp-v1.0.0                          # "error: no signature found" today
git cat-file -p <sha>                              # see author/committer/gpgsig raw

git config gpg.format ssh                          # SSH backend (git >= 2.34)
git config user.signingkey ~/.ssh/id_ed25519_personal.pub    # the PUBLIC file
git config commit.gpgsign true                     # sign every commit in THIS repo
git config tag.gpgsign true                        # sign every annotated tag
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers

git commit -S -m "msg"                             # sign one commit explicitly
git commit --no-gpg-sign -m "msg"                  # ESCAPE HATCH: skip signing once
git tag -s erp-v1.1.0 -m "…"                       # SIGNED annotated tag
git merge --verify-signatures --no-ff <branch>     # refuse an unsigned tip
git rebase --exec 'git commit --amend --no-edit -S' <base>   # re-sign after a rewrite

git config --unset commit.gpgsign                  # UNDO: stop signing
git config --unset gpg.format                      # UNDO: back to default backend
git tag -d erp-v1.1.0                              # UNDO a local tag (before push)
git reflog && git reset --hard <old-sha>           # UNDO a rewrite; signed originals return
curl -sL https://github.com/web-flow.gpg | gpg --import      # makes the 15 E checkable
```
- **`E` ≠ `N`.** `E` = signed, your keyring lacks the key. `N` = nobody signed it.
- **Signed ≠ reviewed.** Identity only. Review is [Ch 22](22_Code_Review.md); correctness is CI ([Ch 28](28_CI_With_GitHub_Actions.md)).

# My ERP Section
| Concept | In this repo (measured 2026-08-03) |
|---|---|
| Total commits | **324** on `HEAD` (`42a2ecc4`) |
| Signature census | **309 `N`** (unsigned) + **15 `E`** (signature present, key missing locally) |
| The 15 signed | GitHub-web merge commits, PR **#1**–**#15**; committer `GitHub <noreply@github.com>` |
| Their key | RSA `B5690EEEBB952194`, importable from `https://github.com/web-flow.gpg` |
| Release tag | `erp-v1.0.0` = `90c1f2f3`, **annotated but unsigned** → `error: no signature found` |
| GPG keys on this machine | **none** (`gpg --list-secret-keys` prints nothing) |
| SSH keys available | `~/.ssh/id_ed25519` (office) · `~/.ssh/id_ed25519_personal` (this repo, via host alias `github-personal`) |
| Versions | git **2.34.1** (`gpg.format=ssh` needs ≥ 2.34) · OpenSSH **8.9p1** (`-Y sign` needs ≥ 8.2) |
| Identity trap | `~/.gitconfig` = office email; `.git/config` = `umesh29mar@gmail.com`. Sign **per-repo** |
| Enforcement available | client-side only — branch protection is **paid** on private repos (`CONTRIBUTING.md` §2) |
| Recommended first step | `git tag -s` on the next release + `git verify-tag` in the deploy pre-flight |
| Where signing does **not** help | money-write discipline — that is `CLAUDE.md` rules 4/5, CI's 2033 tests, and review |

# Practice Tasks
1. **Prove the problem.** In a scratch repo, commit as a famous developer with `git -c user.name=… -c user.email=… commit`, then run `git log`. Write one sentence on what git checked.
2. **Census this repo.** Run the `%G?` census and the `%h %G? %an` listing. Explain, from the commit objects, why exactly those 15 commits differ from the other 309.
3. **Turn `E` into something checkable.** Import GitHub's web-flow key, re-run the census, and explain why the result is `U` and not `G` — and what one command would make it `G`.
4. **Set up SSH signing** on this machine per-repo, including `allowed_signers`. Make an empty signed commit and show `%G? = G`. Then undo every config change you made.
5. **Sign a tag and break it.** Create `git tag -s test-sign`, verify it, then delete it. Separately, rebase a two-commit signed branch and show with `%G?` that the signatures are gone — then recover the originals from `reflog`.

# Homework
- Write the three-line addition to `git-hooks/pre-push` that refuses to push any commit with `%G?` = `N`. Then argue whether you would actually install it, given the honest gap in `CONTRIBUTING.md` §2 Layer 1.
- Decide this project's position on signing and write it into `CONTRIBUTING.md` as a new subsection: what is signed, by whom, verified where, and what is deliberately not done. Cite the measured numbers so the claim is checkable.
- Read GitHub's docs on Vigilant mode, then explain what a `Partially verified` merge commit means and how it could arise in the fork flow of §9.
- A collaborator's PR shows Verified on their branch but the squashed commit on `main` shows GitHub as the signer. Explain to a non-developer what audit trail you actually have — and what you would change if you needed theirs.
- Compare signing with a passphrase-less key on your laptop against a hardware-backed `ed25519-sk` key. What attack does the second one stop that the first cannot, and what does it cost you in convenience?

---

# Further Reading & Live Resources
- Pro Git — *Signing Your Work* (tags, commits, verification, the whole chapter): https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work
- `git-log` manual — the `%G?` / `%GS` / `%GK` placeholders in `--pretty`: https://git-scm.com/docs/git-log
- `git-config` manual — `gpg.format`, `user.signingkey`, `commit.gpgsign`, `gpg.ssh.allowedSignersFile`: https://git-scm.com/docs/git-config
- GitHub Docs — *Telling Git about your signing key* (SSH and GPG, both paths): https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key
- GitHub Docs — *Displaying verification statuses for all of your commits* (Vigilant mode): https://docs.github.com/en/authentication/managing-commit-signature-verification/displaying-verification-statuses-for-all-of-your-commits
- GitHub's web-flow public key, so `E` becomes verifiable locally: https://github.com/web-flow.gpg
- `ssh-keygen` manual — `-Y sign` / `-Y verify` and the allowed-signers format: https://man.openbsd.org/ssh-keygen.1
- Git 2.34 release notes — where SSH signing arrived: https://github.blog/open-source/git/highlights-from-git-2-34/
