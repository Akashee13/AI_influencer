# QA Gap Report

## Run Summary

- Workflow: `mumbai-yoga-anchor-faceid-v1.json`
- Prompt ID: `b55a20dc-f27b-44c6-a443-e39f9a6b5def`
- Submitted At: `2026-05-05T14:12:49.387337+00:00`
- Completed At: `2026-05-05T14:12:54.752001+00:00`
- Scene Reference URL: https://www.instagram.com/p/DXoinABDVRc/
- Local Output: `No local download captured.`

## Expected Outcome

Preserve the locked anchor face identity strongly while adapting the reference into a believable premium Indian wellness creator image.
Keep the result as a half-body lifestyle portrait with realistic skin, sharp eyes, natural daylight, and a confident but natural expression.
Use the scene reference only as loose inspiration; the output should not copy the source outfit or background too literally and should still feel like a polished but natural editorial smartphone photo.

## Structured Review

- Face consistency: **fail**
- Scene/style similarity: **fail**
- Wardrobe adaptation quality: **fail**
- Overall outcome: **fail**

## Top Gaps

Execution blocked before image generation, so the pass cannot verify anchor-face retention, scene adaptation, wardrobe adaptation, or realism.
The workflow is currently incompatible with the runtime stack at SamplerCustomAdvanced / FLUX model execution, specifically because forward_orig() rejects the timestep_zero_index argument.

## Recommended Fixes

Align the ComfyUI core, FLUX runtime, and PuLID-Flux/custom sampler stack so the model forward signature matches the runtime calling convention.
Re-run the exact same default QA pass after dependency/version alignment and confirm the gateway exposes a downloadable output artifact in the run record.
If this workflow is expected to use scene-reference latents, verify that the current sampler path is still valid for the installed ComfyUI version.

## Additional Notes

Run completed through the gateway and uploaded the default Instagram scene reference successfully, so intake, workflow discovery, and submission paths are working.
Failure occurred during model execution rather than during upload or gateway submission.

## Runtime Metadata

```json
{
  "prompt_id": "b55a20dc-f27b-44c6-a443-e39f9a6b5def",
  "workflow_name": "mumbai-yoga-anchor-faceid-v1.json",
  "client_id": "c3a8c0fe-d944-4c67-a041-a63f9d0db5c0",
  "status": "completed",
  "submitted_at": "2026-05-05T14:12:49.387337+00:00",
  "completed_at": "2026-05-05T14:12:54.752001+00:00",
  "error_text": null,
  "overrides": {
    "filename_prefix": "qa-mumbai-yoga-anchor-faceid-v1.json",
    "scene_reference_image": "684168240_18577405549021710_2095548451815178247_n_d689ece2.jpg"
  },
  "outputs": [],
  "history": {
    "b55a20dc-f27b-44c6-a443-e39f9a6b5def": {
      "meta": {},
      "outputs": {},
      "prompt": [
        3,
        "b55a20dc-f27b-44c6-a443-e39f9a6b5def",
        {
          "10": {
            "class_type": "VAELoader",
            "inputs": {
              "vae_name": "ae.safetensors"
            }
          },
          "16": {
            "class_type": "KSamplerSelect",
            "inputs": {
              "sampler_name": "euler"
            }
          },
          "17": {
            "class_type": "BasicScheduler",
            "inputs": {
              "denoise": 1.0,
              "model": [
                "63",
                0
              ],
              "scheduler": "simple",
              "steps": 28
            }
          },
          "25": {
            "class_type": "RandomNoise",
            "inputs": {
              "noise_seed": 774215085774890
            }
          },
          "26": {
            "class_type": "FluxGuidance",
            "inputs": {
              "conditioning": [
                "6",
                0
              ],
              "guidance": 3.5
            }
          },
          "27": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {
              "batch_size": 1,
              "height": 1344,
              "width": 896
            }
          },
          "45": {
            "class_type": "PulidFluxModelLoader",
            "inputs": {
              "pulid_file": "pulid_flux_v0.9.0.safetensors"
            }
          },
          "47": {
            "class_type": "BasicGuider",
            "inputs": {
              "conditioning": [
                "26",
                0
              ],
              "model": [
                "62",
                0
              ]
            }
          },
          "48": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
              "guider": [
                "47",
                0
              ],
              "latent_image": [
                "66",
                0
              ],
              "noise": [
                "25",
                0
              ],
              "sampler": [
                "16",
                0
              ],
              "sigmas": [
                "17",
                0
              ]
            }
          },
          "49": {
            "class_type": "VAEDecode",
            "inputs": {
              "samples": [
                "48",
                0
              ],
              "vae": [
                "10",
                0
              ]
            }
          },
          "50": {
            "class_type": "SaveImage",
            "inputs": {
              "filename_prefix": "qa-mumbai-yoga-anchor-faceid-v1.json",
              "images": [
                "49",
                0
              ]
            }
          },
          "51": {
            "class_type": "PulidFluxEvaClipLoader",
            "inputs": {}
          },
          "53": {
            "class_type": "PulidFluxInsightFaceLoader",
            "inputs": {
              "provider": "CPU"
            }
          },
          "54": {
            "class_type": "LoadImage",
            "inputs": {
              "image": "CompyUI_00016_.png",
              "upload": "image"
            }
          },
          "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
              "clip": [
                "64",
                0
              ],
              "text": "same face identity as the locked Indian wellness anchor, authentic Indian facial features, fair-light wheatish Indian skin with warm golden undertones, deep dark brown eyes, softly wavy dark hair, fit toned feminine wellness creator presence, half body lifestyle portrait, premium creator styling, different outfit from any source reference, different background from any source reference, natural confident expression, realistic smartphone editorial photo, sharp eyes, realistic skin texture, believable daylight, polished but natural"
            }
          },
          "62": {
            "class_type": "ApplyPulidFlux",
            "inputs": {
              "end_at": 1.0,
              "eva_clip": [
                "51",
                0
              ],
              "face_analysis": [
                "53",
                0
              ],
              "image": [
                "54",
                0
              ],
              "model": [
                "63",
                0
              ],
              "pulid_flux": [
                "45",
                0
              ],
              "start_at": 0.0,
              "weight": 1.0
            }
          },
          "63": {
            "class_type": "UNETLoader",
            "inputs": {
              "unet_name": "flux1-dev-fp8.safetensors",
              "weight_dtype": "default"
            }
          },
          "64": {
            "class_type": "DualCLIPLoader",
            "inputs": {
              "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
              "clip_name2": "clip_l.safetensors",
              "type": "flux"
            }
          },
          "65": {
            "class_type": "LoadImage",
            "inputs": {
              "image": "684168240_18577405549021710_2095548451815178247_n_d689ece2.jpg",
              "upload": "image"
            }
          },
          "66": {
            "class_type": "VAEEncode",
            "inputs": {
              "pixels": [
                "65",
                0
              ],
              "vae": [
                "10",
                0
              ]
            }
          }
        },
        {
          "client_id": "c3a8c0fe-d944-4c67-a041-a63f9d0db5c0",
          "create_time": 1777990369385
        },
        [
          "50"
        ]
      ],
      "status": {
        "completed": false,
        "messages": [
          [
            "execution_start",
            {
              "prompt_id": "b55a20dc-f27b-44c6-a443-e39f9a6b5def",
              "timestamp": 1777990369387
            }
          ],
          [
            "execution_cached",
            {
              "nodes": [
                "25",
                "27",
                "16",
                "17",
                "54",
                "53",
                "51",
                "45",
                "62",
                "63",
                "10",
                "64"
              ],
              "prompt_id": "b55a20dc-f27b-44c6-a443-e39f9a6b5def",
              "timestamp": 1777990369397
            }
          ],
          [
            "execution_error",
            {
              "current_inputs": {
                "guider": [
                  "</home/akash_ee13/comfy/comfy_extras/nodes_custom_sampler.Guider_Basic object at 0x78e22a40a0d0>"
                ],
                "latent_image": [
                  "{'samples': tensor([[[[-1.6450e+00, -3.2230e+00, -3.1663e+00,  ..., -3.9350e+00,\n           -3.7845e+00, -1.8091e+00],\n          [-1.8429e+00, -2.9912e+00, -1.4595e+00,  ..., -3.5634e+00,\n           -3.6452e+00, -3.2996e+00],\n          [-1.4820e+00, -1.8075e+00, -2.7698e+00,  ..., -2.1596e+00,\n           -2.7826e+00, -1.5900e+00],\n          ...,\n          [-1.6390e+00, -2.3029e+00, -4.1463e+00,  ..., -2.2177e+00,\n           -2.9603e+00, -1.7860e+00],\n          [ 2.2997e+00,  4.2378e-01, -3.9662e+00,  ..., -2.2587e+00,\n           -2.9815e+00, -1.8673e+00],\n          [-2.3030e+00, -1.8603e+00, -5.5918e+00,  ..., -3.5354e+00,\n           -2.8835e+00, -2.4697e+00]],\n\n         [[-5.8080e-02, -1.0457e+00, -1.1379e+00,  ..., -1.3832e+00,\n           -1.6138e+00, -4.4803e-01],\n          [-4.5072e-01, -7.4537e-01,  7.1483e-01,  ..., -6.2083e-01,\n           -6.1208e-01, -1.8343e+00],\n          [ 2.9240e-01,  6.6324e-01, -1.5609e+00,  ...,  4.4435e-02,\n           -2.1949e+00, -3.6425e-01],\n          ...,\n          [-7.9117e-01, -4.7205e-01, -9.8156e-01,  ..., -1.2181e+00,\n           -2.4055e+00, -1.4997e+00],\n          [-3.4678e+00, -2.4675e+00,  8.9756e-02,  ..., -1.1204e-01,\n           -1.9437e+00, -1.4213e+00],\n          [ 1.3137e+00, -1.5605e+00,  5.2029e-01,  ...,  6.6090e-01,\n           -1.8220e-01,  2.0866e-01]],\n\n         [[ 4.4186e+00,  3.8847e+00,  3.8987e+00,  ...,  4.2619e+00,\n            4.6649e+00,  4.7311e+00],\n          [ 3.7175e+00,  3.6928e+00,  3.0757e+00,  ...,  4.0896e+00,\n            4.1164e+00,  4.1957e+00],\n          [ 3.9249e+00,  4.8096e+00,  4.0884e+00,  ...,  4.9803e+00,\n            4.2172e+00,  2.7529e+00],\n          ...,\n          [ 5.3534e+00,  3.2897e+00,  3.6514e+00,  ...,  4.0124e+00,\n            4.4966e+00,  4.1697e+00],\n          [ 3.7157e+00,  4.0445e+00,  3.1987e+00,  ...,  3.1955e+00,\n            4.7138e+00,  4.1989e+00],\n          [-4.6297e+00, -1.7275e+00,  4.9412e+00,  ...,  4.4789e+00,\n            4.3366e+00,  3.7584e+00]],\n\n         ...,\n\n         [[-4.3443e+00, -4.4256e+00, -4.8081e+00,  ..., -4.2826e+00,\n           -4.0471e+00, -4.1879e+00],\n          [-4.2085e+00, -5.9770e+00, -5.8823e+00,  ..., -6.5469e+00,\n           -5.3788e+00, -3.8143e+00],\n          [-4.8383e+00, -5.3528e+00, -5.1021e+00,  ..., -5.0810e+00,\n           -4.7912e+00, -4.7704e+00],\n          ...,\n          [-4.2196e+00, -4.1062e+00, -4.3721e+00,  ..., -4.8454e+00,\n           -5.0852e+00, -4.3483e+00],\n          [-1.0597e-02, -2.4552e+00, -3.5678e+00,  ..., -4.6696e+00,\n           -4.6224e+00, -3.8871e+00],\n          [ 1.7581e+00,  4.0956e+00, -2.7295e+00,  ..., -4.5597e+00,\n           -4.3864e+00, -3.0843e+00]],\n\n         [[ 3.1715e-01,  4.6308e-01,  7.9713e-01,  ...,  8.9369e-01,\n            1.2233e+00, -1.1281e-01],\n          [-6.2252e-02,  8.4237e-01,  1.7971e+00,  ..., -2.5797e-01,\n            9.7825e-01, -5.2838e-01],\n          [ 9.5817e-01,  6.3230e-01,  3.2104e-01,  ..., -3.5621e-02,\n            2.6781e-01,  1.2358e+00],\n          ...,\n          [-5.8774e-01,  1.2004e+00,  1.8390e+00,  ...,  1.2227e+00,\n            1.9872e+00, -1.9395e-01],\n          [-3.5550e+00, -1.2418e+00,  3.4165e+00,  ...,  1.7903e+00,\n            2.1695e+00, -2.0202e-01],\n          [-4.1683e+00, -5.6776e-01,  1.2310e+00,  ...,  4.3748e-01,\n            1.1073e+00,  3.3703e-01]],\n\n         [[-7.1743e-01, -2.3525e-02, -2.9004e-01,  ...,  1.4711e-01,\n            4.9581e-01, -3.8644e-01],\n          [-2.7621e-01, -3.8848e-01, -8.9646e-01,  ...,  5.7616e-01,\n            4.8324e-01, -1.3305e+00],\n          [-7.2254e-01,  8.2206e-01,  2.1837e-01,  ..., -2.4391e-01,\n            6.8722e-02, -1.5951e+00],\n          ...,\n          [ 3.3545e-01,  5.4973e-03, -1.3877e+00,  ...,  7.9147e-01,\n            1.2874e+00, -1.6178e-01],\n          [-3.3165e+00,  9.0191e-01,  1.0702e-01,  ...,  4.7083e-01,\n            1.4256e+00, -3.0141e-02],\n          [-5.3383e+00, -7.8557e+00, -1.4181e+00,  ..., -4.1013e-01,\n            3.1735e-01, -9.0608e-01]]]])}"
                ],
                "noise": [
                  "</home/akash_ee13/comfy/comfy_extras/nodes_custom_sampler.Noise_RandomNoise object at 0x78e279666f90>"
                ],
                "sampler": [
                  "<comfy.samplers.KSAMPLER object at 0x78e226fdaba0>"
                ],
                "sigmas": [
                  "tensor([1.0000, 0.9884, 0.9762, 0.9634, 0.9499, 0.9356, 0.9205, 0.9045, 0.8876,\n        0.8696, 0.8504, 0.8300, 0.8081, 0.7847, 0.7595, 0.7324, 0.7032, 0.6715,\n        0.6370, 0.5994, 0.5583, 0.5128, 0.4628, 0.4071, 0.3449, 0.2749, 0.1956,\n        0.1050, 0.0000])"
                ]
              },
              "current_outputs": [
                "47",
                "45",
                "51",
                "62",
                "49",
                "66",
                "17",
                "6",
                "65",
                "64",
                "25",
                "27",
                "50",
                "16",
                "54",
                "53",
                "10",
                "63",
                "48",
                "26"
              ],
              "exception_message": "forward_orig() got an unexpected keyword argument 'timestep_zero_index'\n",
              "exception_type": "TypeError",
              "executed": [
                "65",
                "47",
                "26",
                "66",
                "6"
              ],
              "node_id": "48",
              "node_type": "SamplerCustomAdvanced",
              "prompt_id": "b55a20dc-f27b-44c6-a443-e39f9a6b5def",
              "timestamp": 1777990371456,
              "traceback": [
                "  File \"/home/akash_ee13/comfy/execution.py\", line 534, in execute\n    output_data, output_ui, has_subgraph, has_pending_tasks = await get_output_data(prompt_id, unique_id, obj, input_data_all, execution_block_cb=execution_block_cb, pre_execute_cb=pre_execute_cb, v3_data=v3_data)\n                                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/execution.py\", line 334, in get_output_data\n    return_values = await _async_map_node_over_list(prompt_id, unique_id, obj, input_data_all, obj.FUNCTION, allow_interrupt=True, execution_block_cb=execution_block_cb, pre_execute_cb=pre_execute_cb, v3_data=v3_data)\n                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/execution.py\", line 308, in _async_map_node_over_list\n    await process_inputs(input_dict, i)\n",
                "  File \"/home/akash_ee13/comfy/execution.py\", line 296, in process_inputs\n    result = f(**inputs)\n",
                "  File \"/home/akash_ee13/comfy/comfy_api/internal/__init__.py\", line 149, in wrapped_func\n    return method(locked_class, **inputs)\n",
                "  File \"/home/akash_ee13/comfy/comfy_api/latest/_io.py\", line 1826, in EXECUTE_NORMALIZED\n    to_return = cls.execute(*args, **kwargs)\n",
                "  File \"/home/akash_ee13/comfy/comfy_extras/nodes_custom_sampler.py\", line 963, in execute\n    samples = guider.sample(noise.generate_noise(latent), latent_image, sampler, sigmas, denoise_mask=noise_mask, callback=callback, disable_pbar=disable_pbar, seed=noise.seed)\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 1052, in sample\n    output = executor.execute(noise, latent_image, sampler, sigmas, denoise_mask, callback, disable_pbar, seed, latent_shapes=latent_shapes)\n",
                "  File \"/home/akash_ee13/comfy/comfy/patcher_extension.py\", line 112, in execute\n    return self.original(*args, **kwargs)\n           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 995, in outer_sample\n    output = self.inner_sample(noise, latent_image, device, sampler, sigmas, denoise_mask, callback, disable_pbar, seed, latent_shapes=latent_shapes)\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 981, in inner_sample\n    samples = executor.execute(self, sigmas, extra_args, callback, noise, latent_image, denoise_mask, disable_pbar)\n",
                "  File \"/home/akash_ee13/comfy/comfy/patcher_extension.py\", line 112, in execute\n    return self.original(*args, **kwargs)\n           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 751, in sample\n    samples = self.sampler_function(model_k, noise, sigmas, extra_args=extra_args, callback=k_callback, disable=disable_pbar, **self.extra_options)\n",
                "  File \"/home/akash_ee13/.local/lib/python3.14/site-packages/torch/utils/_contextlib.py\", line 124, in decorate_context\n    return func(*args, **kwargs)\n",
                "  File \"/home/akash_ee13/comfy/comfy/k_diffusion/sampling.py\", line 205, in sample_euler\n    denoised = model(x, sigma_hat * s_in, **extra_args)\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 400, in __call__\n    out = self.inner_model(x, sigma, model_options=model_options, seed=seed)\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 954, in __call__\n    return self.outer_predict_noise(*args, **kwargs)\n           ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 961, in outer_predict_noise\n    ).execute(x, timestep, model_options, seed)\n      ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/patcher_extension.py\", line 112, in execute\n    return self.original(*args, **kwargs)\n           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 964, in predict_noise\n    return sampling_function(self.inner_model, x, timestep, self.conds.get(\"negative\", None), self.conds.get(\"positive\", None), self.cfg, model_options=model_options, seed=seed)\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 380, in sampling_function\n    out = calc_cond_batch(model, conds, x, timestep, model_options)\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 205, in calc_cond_batch\n    return _calc_cond_batch_outer(model, conds, x_in, timestep, model_options)\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 213, in _calc_cond_batch_outer\n    return executor.execute(model, conds, x_in, timestep, model_options)\n           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/patcher_extension.py\", line 112, in execute\n    return self.original(*args, **kwargs)\n           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/samplers.py\", line 325, in _calc_cond_batch\n    output = model.apply_model(input_x, timestep_, **c).chunk(batch_chunks)\n             ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/model_base.py\", line 178, in apply_model\n    return comfy.patcher_extension.WrapperExecutor.new_class_executor(\n           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n    ...<2 lines>...\n        comfy.patcher_extension.get_all_wrappers(comfy.patcher_extension.WrappersMP.APPLY_MODEL, transformer_options)\n        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n    ).execute(x, t, c_concat, c_crossattn, control, transformer_options, **kwargs)\n    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/patcher_extension.py\", line 112, in execute\n    return self.original(*args, **kwargs)\n           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/model_base.py\", line 217, in _apply_model\n    model_output = self.diffusion_model(xc, t, context=context, control=control, transformer_options=transformer_options, **extra_conds)\n",
                "  File \"/home/akash_ee13/.local/lib/python3.14/site-packages/torch/nn/modules/module.py\", line 1779, in _wrapped_call_impl\n    return self._call_impl(*args, **kwargs)\n           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/.local/lib/python3.14/site-packages/torch/nn/modules/module.py\", line 1790, in _call_impl\n    return forward_call(*args, **kwargs)\n",
                "  File \"/home/akash_ee13/comfy/comfy/ldm/flux/model.py\", line 345, in forward\n    return comfy.patcher_extension.WrapperExecutor.new_class_executor(\n           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n    ...<2 lines>...\n        comfy.patcher_extension.get_all_wrappers(comfy.patcher_extension.WrappersMP.DIFFUSION_MODEL, transformer_options)\n        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n    ).execute(x, timestep, context, y, guidance, ref_latents, control, transformer_options, **kwargs)\n    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/patcher_extension.py\", line 112, in execute\n    return self.original(*args, **kwargs)\n           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^\n",
                "  File \"/home/akash_ee13/comfy/comfy/ldm/flux/model.py\", line 406, in _forward\n    out = self.forward_orig(img, img_ids, context, txt_ids, timestep, y, guidance, control, timestep_zero_index=timestep_zero_index, transformer_options=transformer_options, attn_mask=kwargs.get(\"attention_mask\", None))\n"
              ]
            }
          ]
        ],
        "status_str": "error"
      }
    }
  },
  "raw_request": {
    "client_id": "c3a8c0fe-d944-4c67-a041-a63f9d0db5c0",
    "prompt": {
      "10": {
        "class_type": "VAELoader",
        "inputs": {
          "vae_name": "ae.safetensors"
        }
      },
      "16": {
        "class_type": "KSamplerSelect",
        "inputs": {
          "sampler_name": "euler"
        }
      },
      "17": {
        "class_type": "BasicScheduler",
        "inputs": {
          "denoise": 1,
          "model": [
            "63",
            0
          ],
          "scheduler": "simple",
          "steps": 28
        }
      },
      "25": {
        "class_type": "RandomNoise",
        "inputs": {
          "noise_seed": 774215085774890
        }
      },
      "26": {
        "class_type": "FluxGuidance",
        "inputs": {
          "conditioning": [
            "6",
            0
          ],
          "guidance": 3.5
        }
      },
      "27": {
        "class_type": "EmptySD3LatentImage",
        "inputs": {
          "batch_size": 1,
          "height": 1344,
          "width": 896
        }
      },
      "45": {
        "class_type": "PulidFluxModelLoader",
        "inputs": {
          "pulid_file": "pulid_flux_v0.9.0.safetensors"
        }
      },
      "47": {
        "class_type": "BasicGuider",
        "inputs": {
          "conditioning": [
            "26",
            0
          ],
          "model": [
            "62",
            0
          ]
        }
      },
      "48": {
        "class_type": "SamplerCustomAdvanced",
        "inputs": {
          "guider": [
            "47",
            0
          ],
          "latent_image": [
            "66",
            0
          ],
          "noise": [
            "25",
            0
          ],
          "sampler": [
            "16",
            0
          ],
          "sigmas": [
            "17",
            0
          ]
        }
      },
      "49": {
        "class_type": "VAEDecode",
        "inputs": {
          "samples": [
            "48",
            0
          ],
          "vae": [
            "10",
            0
          ]
        }
      },
      "50": {
        "class_type": "SaveImage",
        "inputs": {
          "filename_prefix": "qa-mumbai-yoga-anchor-faceid-v1.json",
          "images": [
            "49",
            0
          ]
        }
      },
      "51": {
        "class_type": "PulidFluxEvaClipLoader",
        "inputs": {}
      },
      "53": {
        "class_type": "PulidFluxInsightFaceLoader",
        "inputs": {
          "provider": "CPU"
        }
      },
      "54": {
        "class_type": "LoadImage",
        "inputs": {
          "image": "CompyUI_00016_.png",
          "upload": "image"
        }
      },
      "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
          "clip": [
            "64",
            0
          ],
          "text": "same face identity as the locked Indian wellness anchor, authentic Indian facial features, fair-light wheatish Indian skin with warm golden undertones, deep dark brown eyes, softly wavy dark hair, fit toned feminine wellness creator presence, half body lifestyle portrait, premium creator styling, different outfit from any source reference, different background from any source reference, natural confident expression, realistic smartphone editorial photo, sharp eyes, realistic skin texture, believable daylight, polished but natural"
        }
      },
      "62": {
        "class_type": "ApplyPulidFlux",
        "inputs": {
          "end_at": 1,
          "eva_clip": [
            "51",
            0
          ],
          "face_analysis": [
            "53",
            0
          ],
          "image": [
            "54",
            0
          ],
          "model": [
            "63",
            0
          ],
          "pulid_flux": [
            "45",
            0
          ],
          "start_at": 0,
          "weight": 1
        }
      },
      "63": {
        "class_type": "UNETLoader",
        "inputs": {
          "unet_name": "flux1-dev-fp8.safetensors",
          "weight_dtype": "default"
        }
      },
      "64": {
        "class_type": "DualCLIPLoader",
        "inputs": {
          "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
          "clip_name2": "clip_l.safetensors",
          "type": "flux"
        }
      },
      "65": {
        "class_type": "LoadImage",
        "inputs": {
          "image": "684168240_18577405549021710_2095548451815178247_n_d689ece2.jpg",
          "upload": "image"
        }
      },
      "66": {
        "class_type": "VAEEncode",
        "inputs": {
          "pixels": [
            "65",
            0
          ],
          "vae": [
            "10",
            0
          ]
        }
      }
    }
  },
  "raw_response": {
    "node_errors": {},
    "number": 3,
    "prompt_id": "b55a20dc-f27b-44c6-a443-e39f9a6b5def"
  }
}
```
