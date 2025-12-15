import threading
import random
import os
import time
import sys
from pathlib import Path

# Ensure repository root is on sys.path so `from src...` works when running this script directly
# repo_root should be the repository root (parent of tools/)
repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.client import send_file


def make_random_file(dirname, idx):
    os.makedirs(dirname, exist_ok=True)
    path = os.path.join(dirname, f'rand_{idx}.txt')
    with open(path, 'w', encoding='utf-8') as f:
        for _ in range(random.randint(1, 50)):
            f.write('data_line\n')
    return path


def worker_send_thread(host, port, paths):
    for p in paths:
        try:
            send_file(host, port, p)
        except Exception as e:
            print('send error', e)


def run_benchmark(host='127.0.0.1', port=9000, total=1000, concurrency=10):
    tmp = 'benchmark_files'
    paths = [make_random_file(tmp, i) for i in range(total)]

    # split into concurrency buckets
    buckets = [paths[i::concurrency] for i in range(concurrency)]
    threads = []
    start = time.time()
    for b in buckets:
        t = threading.Thread(target=worker_send_thread, args=(host, port, b), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    elapsed = time.time() - start
    print(f'Benchmark completed: {total} files in {elapsed:.2f}s')


if __name__ == '__main__':
    run_benchmark()
