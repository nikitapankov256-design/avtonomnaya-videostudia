---
name: video-build-watchdog
description: Diagnose and repair the free Russian animated explainer video build in this repository. Use when a GitHub Actions render fails, when the MP4 needs validation, or when improving the existing video pipeline.
---

# Video build watchdog

## Goal
Deliver a real, validated MP4 for the educational explainer. Never report success until the artifact is downloaded and checked.

## Non-negotiable content constraints
- No company branding, business name, logo, address, phone, prices, reviews, or commercial claims.
- Original plot, characters, dialogue, scene compositions, and shot choices. A visual reference may guide broad aesthetic only; do not reproduce its protected expression.
- Explain symptoms (car pulls aside, off-centre steering wheel, uneven tyre wear), suspension inspection first, camber/toe/caster, measurement on a 3D alignment stand, adjustment to manufacturer specifications, and a control check.
- Do not imply alignment corrects worn or damaged suspension parts.
- Calm, clear, engaging Russian narration without fearmongering.
- Prefer distinct natural Russian neural voices for characters. Do not silently substitute robotic TTS if neural voices fail.
- Free tools only. Never use paid APIs, subscriptions, or hosted generation credits without explicit user approval.

## Visual and motion quality
- Aim for a vertical illustrated 2D/2.5D painterly cartoon, cinematic scene continuity, textured environments, depth, camera movement, expressive acting, and coherent lighting.
- Check believable weight, inertia, contact, wheel rotation, and acceleration/deceleration. Avoid sliding, stiff motion, and abrupt pose changes.
- Do not describe primitive placeholder graphics as polished or reference-matched.

## Failure-handling procedure
1. Inspect the latest failed GitHub Actions run and read the complete failing job logs.
2. Identify the root cause; distinguish transient network/TTS failures from code, asset, codec, and timing defects.
3. Make the smallest targeted fix. Preserve all content constraints above.
4. Run syntax checks and focused tests before committing.
5. Do not repeat a build indefinitely when the same root cause persists. The repository watchdog retries failed runs at most twice; after that, open an issue with the failed run link for diagnosis.
6. If an upstream voice/model download is unavailable, test an official free alternative. Do not fabricate audio or fall back to robotic speech without disclosure.
7. Keep secrets out of logs and commits. Never add paid API keys or request them.

## Artifact validation
- Require the expected MP4 artifact.
- Use ffprobe to verify a valid video stream, an audio stream, vertical dimensions (height greater than width), and duration within the intended approximately 90-second target.
- Decode the full file with ffmpeg to detect corrupt frames/audio.
- Listen to or otherwise inspect the actual rendered narration and inspect representative frames from every scene for clipping, unreadable text, visual continuity, and animation defects.
- If any check fails, do not call the result finished. Fix and rebuild.
- Report exact verified facts and any remaining quality limitations. Never invent a download URL or claim an artifact was checked when it was not.
