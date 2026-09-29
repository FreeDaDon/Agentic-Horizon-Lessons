# Database Migrations

This directory contains ordered, idempotent SQL migrations for the Multi-Agent Orchestration database schema.

## Why This Approach?

We've structured our database setup this way for several important reasons:

### 🎯 Key Benefits

1. **No Data Loss**: Each migration uses `CREATE IF NOT EXISTS` instead of `DROP TABLE IF EXISTS`, preserving existing data
2. **Modularity**: One file per concern - easy to update individual tables without affecting others
3. **Clear Dependencies**: Numeric prefixes (0-7) make table relationships and creation order explicit
4. **Idempotent Operations**: Safe to run multiple times - won't break existing schema or data
5. **Version Control Friendly**: Clear diffs when individual tables change
6. **Selective Updates**: Only run what changed, not the entire schema
7. **Production Ready**: Follows best practices used in professional database management

### 🚫 What We Avoid

The old approach (`DROP TABLE IF EXISTS CASCADE`) had issues:
- **Destroys all data** every time the schema runs
- **Breaks in production** if there's any existing data
- **All-or-nothing** - can't update just one table
- **Dangerous** - one mistake drops everything

## Migration Structure

```
migrations/
├── 0_orchestrator_agents.sql    # Singleton orchestrator (no dependencies)
├── 1_agents.sql                  # Managed agents (no dependencies)
├── 2_prompts.sql                 # Prompt history (FK → agents)
├── 3_agent_logs.sql              # Event logs (FK → agents)
├── 4_system_logs.sql             # System logs (nullable FK → agents)
├── 5_indexes.sql                 # Performance indexes (all tables)
├── 6_functions.sql               # Trigger functions (for timestamps)
├── 7_triggers.sql                # Auto-update triggers
└── README.md                     # This file
```

### Dependency Order

```
0. orchestrator_agents  ← No dependencies
1. agents               ← No dependencies
   ↓
2. prompts             ← Depends on agents (FK)
3. agent_logs          ← Depends on agents (FK)
4. system_logs         ← Depends on agents (nullable FK)
   ↓
5. indexes             ← Depends on all tables (0-4)
6. functions           ← Depends on tables for triggers
7. triggers            ← Depends on functions
```

## Usage

### Running All Migrations

From the project root:

```bash
uv run apps/orchestrator_db/run_migrations.py
```

This will:
- ✅ Run all migrations in order (0-7)
- ✅ Show progress with rich terminal output
- ✅ Skip already-existing tables/indexes
- ✅ Update functions and triggers
- ✅ Preserve all existing data
- ✅ Display a summary of results

### Running Individual Migrations

If you only need to update a specific part of the schema:

```bash
# Just update indexes
psql $DATABASE_URL -f apps/orchestrator_db/migrations/5_indexes.sql

# Just update functions
psql $DATABASE_URL -f apps/orchestrator_db/migrations/6_functions.sql

# Update a specific table
psql $DATABASE_URL -f apps/orchestrator_db/migrations/1_agents.sql
```

### Adding New Migrations

When you need to modify the schema:

1. **Adding a new table**: Create `8_newtable.sql` with dependencies in mind
2. **Modifying existing table**: Add `ALTER TABLE` statements to the appropriate file
3. **Adding indexes**: Add to `5_indexes.sql` with `IF NOT EXISTS`
4. **Updating functions**: Update `6_functions.sql` with `CREATE OR REPLACE`

## Idempotency Patterns

Each migration type uses specific patterns to ensure safe re-runs:

### Tables
```sql
CREATE TABLE IF NOT EXISTS tablename (
    -- columns
);
```

### Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_name ON table(column);
```

### Functions
```sql
CREATE OR REPLACE FUNCTION function_name()
RETURNS TRIGGER AS $$
-- function body
$$ LANGUAGE plpgsql;
```

### Triggers
```sql
DROP TRIGGER IF EXISTS trigger_name ON table;
CREATE TRIGGER trigger_name
    BEFORE UPDATE ON table
    FOR EACH ROW
    EXECUTE FUNCTION function_name();
```

## Migration Safety Checklist

Before running migrations in production:

- [ ] Backup database first
- [ ] Test migrations on staging environment
- [ ] Review all SQL files for correctness
- [ ] Verify DATABASE_URL points to correct database
- [ ] Check for foreign key dependencies
- [ ] Ensure psql client is installed
- [ ] Run migrations during low-traffic period

## Comparison: Old vs New

### ❌ Old Approach (`schema_orchestrator.sql`)
```sql
DROP TABLE IF EXISTS agents CASCADE;  -- Destroys data!
CREATE TABLE agents (...);
```

**Issues:**
- Deletes all agent records
- Breaks foreign key relationships
- All-or-nothing execution
- Can't update selectively

### ✅ New Approach (Migrations)
```sql
CREATE TABLE IF NOT EXISTS agents (...);
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
```

**Benefits:**
- Preserves existing data
- Maintains relationships
- Granular updates
- Safe to re-run

## Future Enhancements

Consider these improvements as the system grows:

1. **Migration Tracking Table**: Track which migrations have been applied
2. **Rollback Scripts**: Create down migrations for each up migration
3. **Migration Tool**: Use Alembic, Flyway, or golang-migrate for version tracking
4. **CI/CD Integration**: Automated migration testing in pipeline
5. **Blue-Green Deployments**: Zero-downtime schema changes

## References

- PostgreSQL `CREATE TABLE IF NOT EXISTS`: https://www.postgresql.org/docs/current/sql-createtable.html
- PostgreSQL `CREATE INDEX IF NOT EXISTS`: https://www.postgresql.org/docs/current/sql-createindex.html
- Database Migration Best Practices: https://www.enterprisedb.com/postgres-tutorials/postgresql-database-migration-best-practices

## Support

For issues or questions about migrations:
1. Check the migration runner output for specific errors
2. Verify DATABASE_URL is correct
3. Ensure all migration files exist in `migrations/` directory
4. Review PostgreSQL logs for detailed error messages

---

**Note**: The old `schema_orchestrator.sql` file is kept for reference but should not be used directly. Use `run_migrations.py` instead.
