#!/bin/sh
set -eu
project_root=${CLAUDE_PROJECT_DIR:?CLAUDE_PROJECT_DIR_REQUIRED}
product_root=$project_root/constraint_box
hooks_dir=$product_root/integrated_system/hooks
CB_PRODUCT_ROOT=$product_root
export CB_PRODUCT_ROOT
if [ -z "${CB_LIGHT_PYTHON:-}" ] && [ -x "$product_root/.venv/bin/python" ]; then
  CB_LIGHT_PYTHON=$product_root/.venv/bin/python
  export CB_LIGHT_PYTHON
fi
exec "$hooks_dir/cb_hook.sh" claude
