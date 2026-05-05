# Quickstart: Face-Locked FLUX Runtime Compatibility

## Source Report

- `docs/gap-finding/20260505_194255_mumbai-yoga-anchor-faceid-v1.json_b55a20dc/report.md`

## Goal

Use this checklist to reproduce the runtime compatibility gap and verify that the face-locked FLUX workflow can generate an image again after the fix.

## Preconditions

1. The gateway is reachable at the configured QA harness URL.
2. The local `qa_harness.local.json` points to the intended gateway and workflow defaults.
3. The installed ComfyUI and PuLID-Flux stack matches the environment being repaired.

## Reproduction

1. Open the source QA report and confirm the failing workflow is `mumbai-yoga-anchor-faceid-v1.json`.
2. Review the saved run metadata in `docs/gap-finding/20260505_194255_mumbai-yoga-anchor-faceid-v1.json_b55a20dc/run.json`.
3. Re-run the default QA pass:

```bash
cd "/Users/akash/Documents/PetProjects/AI Influencer"
python3 scripts/qa_harness.py --workflow "mumbai-yoga-anchor-faceid-v1.json" --scene-url "https://www.instagram.com/p/DXoinABDVRc/" --filename-prefix "qa-mumbai-yoga-anchor-faceid-v1.json"
```

4. Use the same expected-outcome baseline from the source report.

Expected pre-fix behavior:

- request submission succeeds
- runtime execution fails before image generation
- the failure includes `forward_orig() got an unexpected keyword argument 'timestep_zero_index'`
- no output image is available for real QA review

## Validation

1. Apply the implementation tied to this spec package.
2. Re-run the same QA path.
3. Confirm the run completes without the recorded sampler/model signature error.
4. Confirm the run yields an output artifact that the harness can download or record.
5. Complete the QA review against the resulting image.

Expected post-fix behavior:

- the face-locked workflow still uses the repo-bound anchor identity
- the scene reference remains operator-editable
- the workflow generates an image successfully
- the QA report now captures visual findings instead of an execution-blocking gap

## Non-Regression Check

Run one older workflow path after the fix, for example:

```bash
cd "/Users/akash/Documents/PetProjects/AI Influencer"
curl -X POST http://34.80.20.228:9000/generate \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer replace-this-with-a-real-long-secret' \
  -d '{
    "workflow": "mumbai-yoga-anchor-v1.json",
    "wait": false,
    "overrides": {
      "filename_prefix": "legacy-non-regression-check"
    }
  }'
```

Expected:

- gateway submission still succeeds
- workflow discovery and submission behavior remain intact
