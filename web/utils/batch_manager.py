# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Lightweight batch manager for Streamlit (Simplified YAGNI version)
"""
import time
import traceback
from typing import List, Dict, Any, Optional, Callable
from loguru import logger


class SimpleBatchManager:
    """
    Ultra-simple batch manager following YAGNI principle
    
    Design principles:
    1. Only supports "AI generate content" mode
    2. Same config for all videos, only topics differ
    3. No CSV, no complex validation, just loop and execute
    """
    
    def __init__(self):
        self.results = []
        self.errors = []
        self.current_index = 0
        self.total_count = 0
    
    def execute_batch(
        self,
        pixelle_video,
        topics: List[str],
        shared_config: Dict[str, Any],
        overall_progress_callback: Optional[Callable] = None,
        task_progress_callback_factory: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute batch generation with shared config
        
        Args:
            pixelle_video: PixelleVideoCore instance
            topics: List of topics (one per video)
            shared_config: Shared configuration for all videos
            overall_progress_callback: Callback for overall progress
            task_progress_callback_factory: Factory function to create per-task callback
        
        Returns:
            {
                "results": [...],
                "errors": [...],
                "total_count": N,
                "success_count": M,
                "failed_count": K
            }
        """
        self.results = []
        self.errors = []
        self.total_count = len(topics)
        
        logger.info(f"Starting batch generation: {self.total_count} topics")
        
        import asyncio
        from pathlib import Path

        # Limit concurrency to 10 concurrent requests
        max_concurrent_tasks = 10
        semaphore = asyncio.Semaphore(max_concurrent_tasks)

        completed_tasks = 0

        async def process_task(idx, topic):
            nonlocal completed_tasks
            async with semaphore:
                if overall_progress_callback:
                    overall_progress_callback(
                        current=completed_tasks + 1,
                        total=self.total_count,
                        topic=topic
                    )
                
                try:
                    logger.info(f"Task {idx}/{self.total_count} started: {topic}")

                    title_prefix = shared_config.get("title_prefix")

                    task_params = {
                        "text": topic,
                        "mode": "generate",
                    }

                    for key, value in shared_config.items():
                        if key != "title_prefix" and value is not None:
                            task_params[key] = value

                    if title_prefix:
                        task_params["title"] = f"{title_prefix} - {topic}"
                    else:
                        task_params["title"] = topic

                    if task_progress_callback_factory:
                        task_params["progress_callback"] = task_progress_callback_factory(idx, topic)

                    result = await pixelle_video.generate_video(**task_params)

                    task_id = Path(result.video_path).parent.name

                    self.results.append({
                        "index": idx,
                        "topic": topic,
                        "task_id": task_id,
                        "video_path": result.video_path,
                        "status": "success"
                    })

                    logger.info(f"Task {idx}/{self.total_count} completed: {result.video_path}")

                except Exception as e:
                    error_msg = str(e)
                    error_trace = traceback.format_exc()

                    logger.error(f"Task {idx}/{self.total_count} failed: {error_msg}")
                    logger.debug(f"Error traceback:\n{error_trace}")

                    self.errors.append({
                        "index": idx,
                        "topic": topic,
                        "error": error_msg,
                        "traceback": error_trace,
                        "status": "failed"
                    })
                finally:
                    completed_tasks += 1

        async def run_all_tasks():
            tasks = []
            for idx, topic in enumerate(topics, 1):
                tasks.append(process_task(idx, topic))
            await asyncio.gather(*tasks)

        from web.utils.async_helpers import run_async
        run_async(run_all_tasks())
        
        success_count = len(self.results)
        failed_count = len(self.errors)
        
        logger.info(
            f"Batch generation completed: "
            f"{success_count}/{self.total_count} succeeded, "
            f"{failed_count} failed"
        )
        
        # Cleanup deepseek session by calling ds2api delete-all endpoint after all batch tasks are done
        try:
            import httpx
            from pixelle_video.config import config_manager

            llm_conf = config_manager.config.get("llm", {}) if isinstance(config_manager.config, dict) else config_manager.get_llm_config()
            base_url = llm_conf.get("base_url", "http://ds2api:5001/v1")

            # Strip /v1 to get base api url
            base_url = base_url.replace("/v1", "")
            admin_key = "pixelle_admin_secret_key" # from docker-compose

            logger.info(f"Cleaning up sessions in ds2api...")
            with httpx.Client(timeout=10.0) as client:
                # To loop over all 30 configured accounts and delete their sessions
                import os
                import json

                # Check different possible paths for the config depending on how the app is run
                config_path = "ds2api_config.json"
                if not os.path.exists(config_path):
                    config_path = "/app/ds2api_config.json"
                if not os.path.exists(config_path):
                    config_path = "../ds2api_config.json"

                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        ds2api_config = json.load(f)

                    accounts = ds2api_config.get("accounts", [])
                    for account in accounts:
                        email = account.get("email")
                        if email:
                            resp = client.post(
                                f"{base_url}/admin/accounts/sessions/delete-all",
                                json={"identifier": email},
                                headers={"Authorization": f"Bearer {admin_key}"}
                            )
                            if resp.status_code == 200:
                                logger.info(f"Successfully cleaned up sessions for {email} from ds2api")
                            else:
                                logger.warning(f"Failed to clean up sessions for {email}. Status: {resp.status_code}, Resp: {resp.text}")
                else:
                    logger.warning("Could not find ds2api config to delete sessions.")
        except Exception as e:
            logger.warning(f"Error while calling ds2api cleanup: {e}")

        return {
            "results": self.results,
            "errors": self.errors,
            "total_count": self.total_count,
            "success_count": success_count,
            "failed_count": failed_count
        }

