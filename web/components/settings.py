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
System settings component for web UI
"""

import streamlit as st

from web.i18n import tr, get_language
from web.utils.streamlit_helpers import safe_rerun
from pixelle_video.config import config_manager


def render_advanced_settings():
    """Render system configuration (required) with 1-column layout since LLM is removed"""
    # Check if system is configured
    is_configured = config_manager.validate()
    
    # Expand if not configured, collapse if configured
    with st.expander(tr("settings.title"), expanded=not is_configured):
        # ====================================================================
        # ComfyUI Settings Only (LLM is hardcoded to ds2api)
        # ====================================================================
        with st.container():
            with st.container(border=True):
                st.markdown(f"**{tr('settings.comfyui.title')}**")
                
                # Get current configuration
                comfyui_config = config_manager.get_comfyui_config()
                
                # Local/Self-hosted ComfyUI configuration
                st.markdown(f"**{tr('settings.comfyui.local_title')}**")
                url_col, key_col = st.columns(2)
                with url_col:
                    comfyui_url = st.text_input(
                        tr("settings.comfyui.comfyui_url"),
                        value=comfyui_config.get("comfyui_url", "http://127.0.0.1:8188"),
                        help=tr("settings.comfyui.comfyui_url_help"),
                        key="comfyui_url_input"
                    )
                with key_col:
                    comfyui_api_key = st.text_input(
                        tr("settings.comfyui.comfyui_api_key"),
                        value=comfyui_config.get("comfyui_api_key", ""),
                        type="password",
                        help=tr("settings.comfyui.comfyui_api_key_help"),
                        key="comfyui_api_key_input"
                    )
                
                # Test connection button
                if st.button(tr("btn.test_connection"), key="test_comfyui", use_container_width=True):
                    try:
                        import requests
                        response = requests.get(f"{comfyui_url}/system_stats", timeout=5)
                        if response.status_code == 200:
                            st.success(tr("status.connection_success"))
                        else:
                            st.error(tr("status.connection_failed"))
                    except Exception as e:
                        st.error(f"{tr('status.connection_failed')}: {str(e)}")
                
                st.markdown("---")
                
                # RunningHub cloud configuration
                st.markdown(f"**{tr('settings.comfyui.cloud_title')}**")
                runninghub_api_key = st.text_input(
                    tr("settings.comfyui.runninghub_api_key"),
                    value=comfyui_config.get("runninghub_api_key", ""),
                    type="password",
                    help=tr("settings.comfyui.runninghub_api_key_help"),
                    key="runninghub_api_key_input"
                )
                st.caption(
                    f"{tr('settings.comfyui.runninghub_hint')} "
                    f"[{tr('settings.comfyui.runninghub_get_api_key')}]"
                    f"(https://www.runninghub{'.cn' if get_language() == 'zh_CN' else '.ai'}/?inviteCode=bozpdlbj)"
                )
                
                # RunningHub concurrent limit and instance type (in one row)
                limit_col, instance_col = st.columns(2)
                with limit_col:
                    runninghub_concurrent_limit = st.number_input(
                        tr("settings.comfyui.runninghub_concurrent_limit"),
                        min_value=1,
                        max_value=10,
                        value=comfyui_config.get("runninghub_concurrent_limit", 1),
                        help=tr("settings.comfyui.runninghub_concurrent_limit_help"),
                        key="runninghub_concurrent_limit_input"
                    )
                with instance_col:
                    # Check if instance type is "plus" (48G VRAM enabled)
                    current_instance_type = comfyui_config.get("runninghub_instance_type") or ""
                    is_plus_enabled = current_instance_type == "plus"
                    # Instance type options with i18n
                    instance_options = [
                        tr("settings.comfyui.runninghub_instance_24g"),
                        tr("settings.comfyui.runninghub_instance_48g"),
                    ]
                    runninghub_instance_type_display = st.selectbox(
                        tr("settings.comfyui.runninghub_instance_type"),
                        options=instance_options,
                        index=1 if is_plus_enabled else 0,
                        help=tr("settings.comfyui.runninghub_instance_type_help"),
                        key="runninghub_instance_type_input"
                    )
                    # Convert display value back to actual value
                    runninghub_48g_enabled = runninghub_instance_type_display == tr("settings.comfyui.runninghub_instance_48g")
        
        # ====================================================================
        # Action Buttons (full width at bottom)
        # ====================================================================
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(tr("btn.save_config"), use_container_width=True, key="save_config_btn"):
                try:
                    # Save ComfyUI configuration (optional fields, always save what's provided)
                    # Convert checkbox to instance type: True -> "plus", False -> ""
                    instance_type = "plus" if runninghub_48g_enabled else ""
                    config_manager.set_comfyui_config(
                        comfyui_url=comfyui_url if comfyui_url else None,
                        comfyui_api_key=comfyui_api_key if comfyui_api_key else None,
                        runninghub_api_key=runninghub_api_key if runninghub_api_key else None,
                        runninghub_concurrent_limit=int(runninghub_concurrent_limit),
                        runninghub_instance_type=instance_type
                    )
                    
                    config_manager.save()
                    st.success(tr("status.config_saved"))
                    safe_rerun()
                except Exception as e:
                    st.error(f"{tr('status.save_failed')}: {str(e)}")
        
        with col2:
            if st.button(tr("btn.reset_config"), use_container_width=True, key="reset_config_btn"):
                # Reset to default
                from pixelle_video.config.schema import PixelleVideoConfig
                config_manager.config = PixelleVideoConfig()
                config_manager.save()
                st.success(tr("status.config_reset"))
                safe_rerun()

