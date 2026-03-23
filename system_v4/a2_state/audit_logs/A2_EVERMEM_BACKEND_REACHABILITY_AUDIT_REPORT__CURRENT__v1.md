# EverMem Backend Reachability Audit Report

- generated_utc: `2026-03-21T19:43:10Z`
- status: `attention_required`
- cluster_id: `SKILL_CLUSTER::evermem-witness-memory`
- slice_id: `a2-evermem-backend-reachability-audit-operator`
- health_url: `http://localhost:1995/health`
- next_step: `start_docker_daemon`

## Local Repo State
- repo_exists: `True`
- env_template_exists: `True`
- env_exists: `False`
- venv_exists: `False`
- uv_lock_exists: `True`
- docker_compose_file_exists: `True`

## Health Probes
- docker_daemon_ok: `False`
- curl_health_ok: `False`
- python_health_ok: `False`
- curl_error: `curl: (7) Failed to connect to localhost port 1995 after 0 ms: Couldn't connect to server`
- python_error: `URLError: [Errno 1] Operation not permitted`

## Current Ratchet Reports
- sync_status: `sync_failed`
- retrieval_status: `attention_required`
- retrieval_next_step: `hold_at_retrieval_probe`

## Issues
- EverMemOS .env is missing
- EverMemOS .venv is missing
- docker daemon unavailable: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
- curl health probe failed: curl: (7) Failed to connect to localhost port 1995 after 0 ms: Couldn't connect to server
- python health probe failed: URLError: [Errno 1] Operation not permitted
