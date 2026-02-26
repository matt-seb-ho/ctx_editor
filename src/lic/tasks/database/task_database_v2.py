import os
import re
import sqlite3
from itertools import chain
from typing import Any, Dict, Tuple

from lic.paths import get_data_path, get_prompt_path
from lic.tasks.database.eval_spider_exec import (
    postprocess,
    replace_cur_year,
    result_eq,
)
from lic.tasks.database.eval_spider_parse import get_all_preds_for_execution, remove_distinct
from lic.tasks.database.task_database import TaskDatabase
from lic.utils import print_colored

TIMEOUT = 60


def _exec_on_db_sync(sqlite_path: str, query: str, timeout: int = TIMEOUT) -> Tuple[str, Any]:
    """Execute a SQL query synchronously with a timeout via sqlite3's interrupt mechanism."""
    query = replace_cur_year(query)
    connection = None
    try:
        if not os.path.exists(sqlite_path):
            print("Opening a new connection %s" % sqlite_path)
        connection = sqlite3.connect(sqlite_path, timeout=timeout)
        connection.text_factory = lambda b: b.decode(errors="ignore")
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return "result", result
    except Exception as e:
        if connection:
            connection.close()
        return "exception", e


def eval_exec_match_sync(
    db: str,
    p_str: str,
    g_str: str,
    plug_value: bool,
    keep_distinct: bool,
    progress_bar_for_each_datapoint: bool,
) -> int:
    """Synchronous version of eval_exec_match that avoids asyncio.run().

    Identical logic to the original eval_exec_match in eval_spider_exec.py but
    calls _exec_on_db_sync instead of asyncio.run(exec_on_db(...)), making it
    safe to call from within a running asyncio event loop.
    """
    p_str, g_str = postprocess(p_str), postprocess(g_str)
    if not keep_distinct:
        p_str = remove_distinct(p_str)
        g_str = remove_distinct(g_str)

    order_matters = "order by" in g_str.lower()

    db_dir = os.path.dirname(db)
    db_paths = [
        os.path.join(db_dir, basename)
        for basename in os.listdir(db_dir)
        if ".sqlite" in basename
    ]

    preds = [p_str]
    if plug_value:
        _, preds = get_all_preds_for_execution(g_str, p_str)
        preds = chain([p_str], preds)

    max_chain_length = 100
    for chain_idx, pred in enumerate(preds):
        if chain_idx >= max_chain_length:
            print_colored(f"[Spider Exec Eval] predicted query is too long: {pred}", "red")
            pred_passes = 0
            break

        pred_passes = 1

        for db_path in db_paths:
            g_flag, g_denotation = _exec_on_db_sync(db_path, g_str)
            p_flag, p_denotation = _exec_on_db_sync(db_path, pred)

            assert g_flag != "exception", "gold query %s has error on database file %s" % (
                g_str,
                db_path,
            )

            if p_flag == "exception":
                pred_passes = 0
            elif not result_eq(g_denotation, p_denotation, order_matters=order_matters):
                pred_passes = 0
            if pred_passes == 0:
                break

        if pred_passes == 1:
            return 1

    return 0


class TaskDatabaseV2(TaskDatabase):
    _initialized_once = False
    """V2 task evaluator for database (Spider SQL) tasks.

    Changes from V1:
    - System prompt instructs model to wrap final SQL in ```sql ... ``` fences
    - answer_extraction_strategy set to "task_specific" so extract_answer is used
    - extract_answer: tries ```sql fences first, then generic code fences containing
      SQL keywords, then last SQL statement in raw text
    - evaluator_function: uses fully synchronous SQL execution, fixing nested
      asyncio.run() crash when called from ctx_editor's async execution pipeline
    """

    def __init__(self):
        super().__init__()
        with open(get_prompt_path("prompts/database/database_system_prompt_v2.txt"), "r") as f:
            self.system_prompt = f.read()
        self.answer_extraction_strategy = "task_specific"
        if not TaskDatabaseV2._initialized_once:
            print("[TaskDatabaseV2] active — task_specific extraction + sync eval")
            TaskDatabaseV2._initialized_once = True

    def extract_answer(self, text: str) -> str:
        """Extract SQL from ```sql fences; fall back to last SELECT/INSERT/... statement."""
        # Primary: extract from ```sql fences
        sql_blocks = re.findall(r"```sql\s*(.*?)\s*```", text, re.DOTALL)
        if sql_blocks:
            return sql_blocks[-1].strip()

        # Fallback: extract from any generic code fence
        code_blocks = re.findall(r"```\s*(.*?)\s*```", text, re.DOTALL)
        for block in reversed(code_blocks):
            if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b", block, re.I):
                return block.strip()

        # Last resort: find the last SQL-looking statement in raw text
        match = re.search(
            r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b.*",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(0).strip()

        return ""

    def evaluator_function(self, extracted_answer: str, sample: Dict[str, Any]) -> dict:
        pred_sql = extracted_answer.replace("```sql", "").replace("```", "")
        pred_sql = re.sub(r"\s+", " ", pred_sql).strip()

        if not pred_sql:
            return {"score": 0.0}

        ref_sql = sample["reference_sql"]
        spider_db_dir = get_data_path("data/spider/databases")
        if not spider_db_dir.exists():
            raise FileNotFoundError(
                "data/spider/databases/ folder not found; "
                "please see data/spider/README.md for instructions"
            )

        try:
            db_id = sample["db_id"]
            is_correct = (
                eval_exec_match_sync(
                    str(spider_db_dir / db_id / f"{db_id}.sqlite"),
                    pred_sql,
                    ref_sql,
                    plug_value=True,
                    keep_distinct=False,
                    progress_bar_for_each_datapoint=False,
                )
                == 1
            )
        except Exception as e:
            print(f"Error evaluating SQL: {e}")
            is_correct = False
        score = 1.0 if is_correct else 0.0
        return {"score": score}
