# paper_qa/utils/profiler.py
import time
from functools import wraps

def profile(func):
    """함수 실행 시간 측정 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start

        print(f"⏱️ {func.__name__}: {elapsed:.3f}s")

        return result
    return wrapper

# 사용 예시
@profile
async def retrieve_node(state: QAState) -> dict:
    ...