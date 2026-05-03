# AI Influencer Project Plan

## Goal
Build a believable, repeatable Indian AI influencer with:
- consistent face identity
- repeatable Bangalore/India lifestyle scenes
- still posts and reel-ready visual assets
- an operating system that can scale beyond one-off prompting

## Positioning
- Character type: urban Indian lifestyle creator
- Market: Instagram-first
- Primary vibe: relatable, aspirational, local, metro-girl realism
- Anti-goal: generic glamour model or over-polished fantasy influencer

## Working Character
- Name: Manya Rao
- City: Bangalore
- Languages: Kannada, English, Hindi
- Core niche: fashion, cafes, metro life, Bangalore weather, city humor, daily-life aesthetic

## Production System

### Layer 1: Character Identity
- fixed face geometry
- fixed skin tone band
- fixed eye and hair profile
- recurring wardrobe families
- recurring accessories
- recurring pose/attitude style

### Layer 2: Scene System
- metro commute
- cafe table
- apartment mirror selfie
- bookstore
- rain/street/city sidewalk
- coworking desk
- grocery or daily errand

### Layer 3: Content Formats
- portrait post
- carousel post
- reel cover
- selfie talking-frame
- image-to-video lifestyle clip

### Layer 4: Consistency Control
- reference image pack
- prompt templates
- negative prompt guardrails
- accepted facial-anchor checklist
- approved outfit palette
- approved locations library

## Recommended Stack

### Right Now
- ComfyUI on GCP T4 VM
- one lightweight base image model
- reference-image driven generation
- manual prompt iteration

### Next
- add identity-preserving workflow
- add scene presets
- add LoRA training path after we like the face

### Later
- talking-head workflow
- image-to-video workflow
- scheduled content pipeline

## Production Phases

### Phase 1: Lock the Character
Deliverables:
- 1 canonical portrait
- 5 close variants
- 5 outfit/location variants
- 1 profile image

Success condition:
- same person across outputs without obvious drift

### Phase 2: Build the Feed Language
Deliverables:
- 9-post launch grid
- 30 caption starters
- 20 reel ideas
- 10 repeatable scene prompts

### Phase 3: Video
Deliverables:
- 3 reel covers
- 3 talking-head or motion test clips
- 3 lifestyle short loops

### Phase 4: Scale
Deliverables:
- reusable prompt library
- consistency checklist
- weekly content calendar
- monetization experiments

## Immediate Next Step
Get one solid base model into ComfyUI, generate the first working portrait pipeline, and then freeze Manya's face before we add more complexity.
