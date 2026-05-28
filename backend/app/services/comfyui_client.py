"""
Client ComfyUI local — LTX-Video 2B (Lightricks) pour génération vidéo haute qualité.
Modèles requis (models/checkpoints/) :
  - ltx-video-2b-v0.9.5.safetensors  (UNet + VAE, ~5.9 GB)
Modèles requis (models/text_encoders/) :
  - t5-v1_1-xxl-encoder-Q8_0.gguf   (T5-XXL Q8, ~4.7 GB, via ComfyUI-GGUF)
"""
import asyncio
import random
import httpx

COMFYUI_URL = "http://127.0.0.1:8188"
FILENAME_PREFIX = "studio_carton_"

# Dimensions 9:16 (portrait TikTok/Reels), multiples de 32
_WIDTH = 512
_HEIGHT = 896
_FRAMES = 97    # ~3.9 s à 25 fps (length doit satisfaire (length-1) % 8 == 0)
_FPS = 25


def _build_workflow(prompt: str, negative_prompt: str, seed: int) -> dict:
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-video-2b-v0.9.5.safetensors"}
        },
        "2": {
            "class_type": "CLIPLoaderGGUF",
            "inputs": {
                "clip_name": "t5-v1_1-xxl-encoder-Q8_0.gguf",
                "type": "ltxv"
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": prompt}
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": negative_prompt}
        },
        "5": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {
                "width": _WIDTH,
                "height": _HEIGHT,
                "length": _FRAMES,
                "batch_size": 1
            }
        },
        "6": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["3", 0],
                "negative": ["4", 0],
                "frame_rate": float(_FPS)
            }
        },
        "7": {
            "class_type": "ModelSamplingLTXV",
            "inputs": {
                "model": ["1", 0],
                "max_shift": 2.05,
                "base_shift": 0.95,
                "latent": ["5", 0]
            }
        },
        "8": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 20,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["5", 0]
            }
        },
        "9": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
        "10": {
            "class_type": "SamplerCustom",
            "inputs": {
                "model": ["7", 0],
                "add_noise": True,
                "noise_seed": seed,
                "cfg": 3.0,
                "positive": ["6", 0],
                "negative": ["6", 1],
                "sampler": ["9", 0],
                "sigmas": ["8", 0],
                "latent_image": ["5", 0]
            }
        },
        "11": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["10", 0], "vae": ["1", 2]}
        },
        "12": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["11", 0],
                "frame_rate": _FPS,
                "loop_count": 0,
                "filename_prefix": FILENAME_PREFIX,
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True
            }
        }
    }


async def queue_generation(prompt: str, negative_prompt: str) -> str:
    """Soumet le workflow LTX-Video à ComfyUI et retourne le prompt_id."""
    seed = random.randint(0, 2**32 - 1)
    workflow = _build_workflow(prompt, negative_prompt, seed)
    payload = {"prompt": workflow, "client_id": "studio-carton"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{COMFYUI_URL}/prompt", json=payload)
        resp.raise_for_status()
        return resp.json()["prompt_id"]


async def wait_for_completion(prompt_id: str, timeout: int = 600) -> str | None:
    """Attend la fin de génération (LTX-Video est plus lent) et retourne le nom du fichier."""
    async with httpx.AsyncClient(timeout=10) as client:
        for _ in range(timeout // 5):
            await asyncio.sleep(5)
            try:
                resp = await client.get(f"{COMFYUI_URL}/history/{prompt_id}")
                history = resp.json()
                if prompt_id not in history:
                    continue
                outputs = history[prompt_id].get("outputs", {})
                for node_output in outputs.values():
                    for key in ("gifs", "videos"):
                        files = node_output.get(key, [])
                        if files:
                            return files[0].get("filename")
            except Exception:
                continue
    return None


async def download_video(filename: str) -> bytes:
    """Télécharge la vidéo depuis ComfyUI."""
    url = f"{COMFYUI_URL}/view?filename={filename}&type=output"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def check_comfyui() -> bool:
    """Vérifie que ComfyUI est accessible."""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            await client.get(f"{COMFYUI_URL}/system_stats")
        return True
    except Exception:
        return False
