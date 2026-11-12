-- Spend dashboard over the orchestrator schema
-- (14.orchestrator-agent-with-adws-singularity/apps/orchestrator_db/migrations/).
--
-- Each section starts with `-- name: <section>`. cost_report.py runs them one by one.
-- Every column is qualified with its table alias so tests can check it against the migrations.
-- agents.adw_id is TEXT and ai_developer_workflows.id is UUID, hence the ::text join.
-- Costs are cumulative per row; there is no per-event cost table. Daily spend therefore
-- attributes each agent's whole cost to the day the agent was created.

-- name: spend_by_agent
SELECT a.name AS agent, a.model, a.status, a.adw_id, a.adw_step,
       a.input_tokens, a.output_tokens, a.total_cost
FROM agents a
WHERE NOT a.archived
ORDER BY a.total_cost DESC
LIMIT 25;

-- name: spend_by_orchestrator
SELECT o.id AS orchestrator, o.status,
       o.total_cost AS orchestrator_cost,
       COALESCE(SUM(a.total_cost), 0) AS agents_cost,
       o.total_cost + COALESCE(SUM(a.total_cost), 0) AS total_cost,
       COUNT(a.id) AS agents
FROM orchestrator_agents o
LEFT JOIN agents a ON a.orchestrator_agent_id = o.id
GROUP BY o.id, o.status, o.total_cost
ORDER BY total_cost DESC;

-- name: spend_by_adw_step
SELECT w.adw_name, w.workflow_type, a.adw_step,
       COUNT(a.id) AS agents, SUM(a.total_cost) AS step_cost
FROM agents a
JOIN ai_developer_workflows w ON w.id::text = a.adw_id
GROUP BY w.adw_name, w.workflow_type, a.adw_step
ORDER BY w.adw_name, step_cost DESC;

-- name: top_adws
SELECT w.adw_name, w.workflow_type, w.status, w.duration_seconds,
       SUM(a.total_cost) AS adw_cost
FROM ai_developer_workflows w
JOIN agents a ON a.adw_id = w.id::text
GROUP BY w.id, w.adw_name, w.workflow_type, w.status, w.duration_seconds
ORDER BY adw_cost DESC
LIMIT 10;

-- name: daily_spend
SELECT d.day, SUM(d.cost) AS cost
FROM (
    SELECT a.created_at::date AS day, a.total_cost AS cost FROM agents a
    UNION ALL
    SELECT o.created_at::date AS day, o.total_cost AS cost FROM orchestrator_agents o
) d
GROUP BY d.day
ORDER BY d.day DESC
LIMIT 30;

-- name: cost_by_adw_outcome
SELECT c.status, COUNT(*) AS adws,
       SUM(c.adw_cost) AS total_cost,
       ROUND(AVG(c.adw_cost), 4) AS avg_cost_per_adw
FROM (
    SELECT w.id, w.status, COALESCE(SUM(a.total_cost), 0) AS adw_cost
    FROM ai_developer_workflows w
    LEFT JOIN agents a ON a.adw_id = w.id::text
    WHERE w.status IN ('completed', 'failed')
    GROUP BY w.id, w.status
) c
GROUP BY c.status
ORDER BY c.status;
