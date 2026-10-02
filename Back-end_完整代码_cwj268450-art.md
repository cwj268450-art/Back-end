# 后端项目------完整代码

## GitHub 信息

-   GitHub 用户名：`cwj268450-art`
-   GitHub 仓库：`Back-end`
-   GitHub 地址：`https://github.com/cwj268450-art/Back-end`

## 完整代码

### 1. `calculator-backend/src/__init__.py`

``` python
```

### 2. `calculator-backend/src/main.py`

``` python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes.calculate import router as calculate_router
from .routes.history import router as history_router

app = FastAPI(title="Calculator Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calculate_router)
app.include_router(history_router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "calculator-backend"}
```

### 3. `calculator-backend/src/calculator.py`

``` python
"""安全数学表达式解析器，不使用 eval/exec。"""
import math
import re


class CalculationError(Exception):
    """可预期的计算错误。"""


class Parser:
    NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")

    def __init__(self, expression: str):
        self.text = expression.replace("×", "*").replace("÷", "/")
        self.pos = 0

    def parse(self):
        if not self.text.strip():
            raise CalculationError("表达式不能为空")
        if len(self.text) > 200:
            raise CalculationError("表达式过长")
        value = self.expression()
        self.skip()
        if self.pos != len(self.text):
            raise CalculationError("表达式格式错误或存在非法字符")
        if not math.isfinite(value):
            raise CalculationError("计算结果超出范围")
        return int(value) if value == int(value) else round(value, 12)

    def skip(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def match(self, ch):
        self.skip()
        if self.text.startswith(ch, self.pos):
            self.pos += len(ch)
            return True
        return False

    def expression(self):
        value = self.term()
        while True:
            if self.match("+"):
                value += self.term()
            elif self.match("-"):
                value -= self.term()
            else:
                return value

    def term(self):
        value = self.unary()
        while True:
            if self.match("*"):
                value *= self.unary()
            elif self.match("/"):
                divisor = self.unary()
                if divisor == 0:
                    raise CalculationError("除数不能为 0")
                value /= divisor
            else:
                return value

    def unary(self):
        if self.match("+"):
            return +self.unary()
        if self.match("-"):
            return -self.unary()
        return self.primary()

    def primary(self):
        self.skip()
        if self.match("("):
            value = self.expression()
            if not self.match(")"):
                raise CalculationError("缺少右括号")
            return value

        m = self.NUMBER.match(self.text, self.pos)
        if not m:
            raise CalculationError("需要数字或左括号")
        self.pos = m.end()
        return float(m.group())


def calculate_expression(expression: str):
    if not isinstance(expression, str):
        raise CalculationError("expression 必须是字符串")
    return Parser(expression).parse()
```

### 4. `calculator-backend/src/database.py`

``` python
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent / "calculator.db"


def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calculation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def add_history(expression, result):
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO calculation_history(expression,result,created_at) VALUES(?,?,?)",
            (expression, str(result), now),
        )
        conn.commit()
        return cur.lastrowid


def list_history():
    with connection() as conn:
        rows = conn.execute(
            "SELECT id,expression,result,created_at FROM calculation_history "
            "ORDER BY id DESC LIMIT 100"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_history(record_id):
    with connection() as conn:
        cur = conn.execute("DELETE FROM calculation_history WHERE id=?", (record_id,))
        conn.commit()
        return cur.rowcount > 0


def clear_history():
    with connection() as conn:
        cur = conn.execute("DELETE FROM calculation_history")
        conn.commit()
        return cur.rowcount
```

### 5. `calculator-backend/src/schemas.py`

``` python
from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=200)


class CalculateResponse(BaseModel):
    success: bool
    expression: str
    result: int | float
    history_id: int


class HistoryItem(BaseModel):
    id: int
    expression: str
    result: str
    created_at: str
```

### 6. `calculator-backend/src/routes/__init__.py`

``` python
```

### 7. `calculator-backend/src/routes/calculate.py`

``` python
from fastapi import APIRouter, HTTPException
from ..calculator import CalculationError, calculate_expression
from ..database import add_history
from ..schemas import CalculateRequest, CalculateResponse

router = APIRouter(prefix="/api", tags=["calculate"])


@router.post("/calculate", response_model=CalculateResponse)
def calculate(request: CalculateRequest):
    try:
        result = calculate_expression(request.expression)
        history_id = add_history(request.expression, result)
        return {
            "success": True,
            "expression": request.expression,
            "result": result,
            "history_id": history_id,
        }
    except CalculationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(exc)},
        ) from exc
```

### 8. `calculator-backend/src/routes/history.py`

``` python
from fastapi import APIRouter, HTTPException
from ..database import clear_history, delete_history, list_history
from ..schemas import HistoryItem

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[HistoryItem])
def get_history():
    return list_history()


@router.delete("/{record_id}")
def remove_history(record_id: int):
    if not delete_history(record_id):
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "历史记录不存在"},
        )
    return {"success": True, "message": "删除成功"}


@router.delete("")
def remove_all_history():
    return {"success": True, "deleted": clear_history()}
```

### 9. `calculator-backend/requirements.txt`

``` text
fastapi==0.117.1
uvicorn[standard]==0.36.0
pydantic==2.11.10
```

### 10. `calculator-backend/.gitignore`

``` text
.venv/
__pycache__/
*.pyc
calculator.db
```

## GitHub 上传命令

``` powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/cwj268450-art/Back-end.git
git push -u origin main
```
