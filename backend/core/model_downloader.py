"""
Model downloader for ULFD and ArcFace ONNX models.
Automatically downloads models from public sources if not present.
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Tuple
import aiohttp
from tqdm import tqdm
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelDownloader:
    """Handles downloading of ONNX models from public sources."""

    # Model URLs
    ULFD_URL = "https://github.com/Linzaer/Ultra-Light-Fast-Generic-Face-Detector-1MB/raw/master/models/onnx/version-slim-320.onnx"
    ULFD_RFB_URL = "https://github.com/Linzaer/Ultra-Light-Fast-Generic-Face-Detector-1MB/raw/master/models/onnx/version-RFB-320.onnx"
    ARCFACE_URL = "https://huggingface.co/garavv/arcface-onnx/resolve/main/arc.onnx"

    # Local paths
    MODELS_DIR = Path("models")
    ULFD_PATH = MODELS_DIR / "ulfd.onnx"
    ARCFACE_PATH = MODELS_DIR / "arcface.onnx"

    @staticmethod
    async def download_file(url: str, dest_path: Path, description: str = "Downloading", max_retries: int = 3) -> bool:
        """
        Download a file from URL to destination path with progress bar.

        Args:
            url: Source URL
            dest_path: Destination file path
            description: Description for progress bar
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {description} from {url}")
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

                # Create parent directories
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=600)) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to download: HTTP {response.status}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            return False

                        # Get file size for progress bar
                        total_size = int(response.headers.get('content-length', 0))

                        # Download with progress bar
                        with open(dest_path, 'wb') as f:
                            if total_size > 0:
                                with tqdm(
                                    total=total_size,
                                    unit='B',
                                    unit_scale=True,
                                    desc=description,
                                    ncols=80
                                ) as pbar:
                                    async for chunk in response.content.iter_chunked(8192):
                                        f.write(chunk)
                                        pbar.update(len(chunk))
                            else:
                                # No content-length header, download without progress bar
                                logger.info("Downloading (size unknown)...")
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)

                logger.info(f"Downloaded to {dest_path}")
                return True

            except asyncio.TimeoutError:
                logger.warning(f"Download timeout for {url}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as e:
                logger.warning(f"Error downloading {url}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

            # Clean up partial download
            if dest_path.exists():
                dest_path.unlink()

        return False

    @classmethod
    async def ensure_ulfd_model(cls) -> bool:
        """
        Ensure ULFD model is available, download if needed.

        Returns:
            True if model is available, False otherwise
        """
        if cls.ULFD_PATH.exists():
            logger.info(f"ULFD model already exists at {cls.ULFD_PATH}")
            return True

        logger.info("ULFD model not found, downloading...")

        # Try primary URL first (slim-320 variant)
        success = await cls.download_file(
            cls.ULFD_URL,
            cls.ULFD_PATH,
            "Downloading ULFD (slim-320)"
        )

        # If failed, try RFB variant as fallback
        if not success:
            logger.warning("Primary URL failed, trying RFB variant...")
            success = await cls.download_file(
                cls.ULFD_RFB_URL,
                cls.ULFD_PATH,
                "Downloading ULFD (RFB-320)"
            )

        if not success:
            logger.error("Failed to download ULFD model after all attempts")
            logger.error(f"Please manually download from: {cls.ULFD_URL}")
            logger.error(f"and place it at: {cls.ULFD_PATH}")

        return success

    @classmethod
    async def ensure_arcface_model(cls) -> bool:
        """
        Ensure ArcFace model is available, download if needed.

        Returns:
            True if model is available, False otherwise
        """
        if cls.ARCFACE_PATH.exists():
            logger.info(f"ArcFace model already exists at {cls.ARCFACE_PATH}")
            return True

        logger.info("ArcFace model not found, downloading...")

        success = await cls.download_file(
            cls.ARCFACE_URL,
            cls.ARCFACE_PATH,
            "Downloading ArcFace (ResNet100)"
        )

        if not success:
            logger.error("Failed to download ArcFace model from Hugging Face")
            logger.error("Please manually download from: https://huggingface.co/garavv/arcface-onnx/resolve/main/arc.onnx")
            logger.error(f"and place it at: {cls.ARCFACE_PATH}")

        return success

    @classmethod
    async def download_all_models(cls) -> Tuple[bool, bool]:
        """
        Download all required models concurrently.

        Returns:
            Tuple of (ulfd_success, arcface_success)
        """
        logger.info("Checking and downloading required models...")

        # Download both models concurrently for speed
        ulfd_task = cls.ensure_ulfd_model()
        arcface_task = cls.ensure_arcface_model()

        ulfd_success, arcface_success = await asyncio.gather(ulfd_task, arcface_task)

        # Summary
        if ulfd_success and arcface_success:
            logger.info("All models are ready!")
        elif ulfd_success:
            logger.warning("ULFD ready but ArcFace missing")
        elif arcface_success:
            logger.warning("ArcFace ready but ULFD missing")
        else:
            logger.error("Failed to download required models")

        return ulfd_success, arcface_success


async def ensure_models_downloaded() -> Tuple[bool, bool]:
    """
    Convenience function to ensure all models are downloaded.

    Returns:
        Tuple of (ulfd_success, arcface_success)
    """
    return await ModelDownloader.download_all_models()


def ensure_models_downloaded_sync() -> Tuple[bool, bool]:
    """
    Synchronous wrapper for model download (for use in non-async contexts).

    Returns:
        Tuple of (ulfd_success, arcface_success)
    """
    return asyncio.run(ensure_models_downloaded())


if __name__ == "__main__":
    # Test download functionality
    logger.info("Testing model downloader...")
    asyncio.run(ensure_models_downloaded())
